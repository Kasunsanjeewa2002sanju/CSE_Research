"""Intraday Rolling Series Store with 1-Minute Downsampling and Bounded Memory.

Features:
- Rolling series per metric: ASPI, S&P SL 20, turnover, and shares traded.
- 1-minute bucket downsampling (tracks open, high, low, close/value, turnover, volume).
- Bounded memory: keeps the current trading session plus a configurable number of prior sessions (e.g. 3 sessions).
- Atomic disk persistence (cse_data_cache/intraday_series.json) so sparklines survive server restarts.
- Session isolation (queryable by session date or 'current').
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from cse_live.config import IngestionConfig
from cse_live.models import (
    IntradaySeriesPoint,
    MarketSnapshot,
    COLOMBO_TZ,
)

logger = logging.getLogger("cse_live.intraday")


class IntradayStore:
    """Stores and downsamples intraday tick feeds into 1-minute bars with bounded memory."""

    SUPPORTED_METRICS = {"aspi", "sp20", "sp_sl20", "turnover", "shares_traded", "volume"}

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or IngestionConfig.from_env()

        # Structure: sessions[session_date_str][metric_name] = Dict[bucket_iso, bar_dict]
        # Where bar_dict = {"timestamp": dt_iso, "open": float, "high": float, "low": float, "close": float, ...}
        self._sessions: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
        self._latest_session_date: Optional[str] = None

        # Load persisted intraday series if available
        self.load()

    def _get_minute_bucket_iso(self, dt: datetime) -> str:
        """Floor datetime to the minute and return ISO string in Colombo timezone."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc).astimezone(COLOMBO_TZ)
        else:
            dt = dt.astimezone(COLOMBO_TZ)
        bucket_dt = dt.replace(second=0, microsecond=0)
        return bucket_dt.isoformat()

    def _get_session_date(self, dt: datetime) -> str:
        """Extract session date YYYY-MM-DD in Colombo timezone."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc).astimezone(COLOMBO_TZ)
        else:
            dt = dt.astimezone(COLOMBO_TZ)
        return dt.strftime("%Y-%m-%d")

    def record_tick(self, snapshot: MarketSnapshot) -> None:
        """Update 1-minute buckets for all metrics from an accepted MarketSnapshot."""
        ts = snapshot.source_timestamp
        session_date = self._get_session_date(ts)
        bucket_iso = self._get_minute_bucket_iso(ts)

        self._latest_session_date = session_date

        # 1. ASPI Index
        self._update_bucket(
            session_date=session_date,
            metric="aspi",
            bucket_iso=bucket_iso,
            timestamp_dt=ts,
            val=snapshot.aspi_value,
            turnover=snapshot.market_turnover,
            volume=snapshot.shares_traded,
        )

        # 2. S&P SL 20 Index
        if snapshot.sp20_value is not None:
            self._update_bucket(
                session_date=session_date,
                metric="sp20",
                bucket_iso=bucket_iso,
                timestamp_dt=ts,
                val=snapshot.sp20_value,
            )

        # 3. Market Turnover (LKR)
        self._update_bucket(
            session_date=session_date,
            metric="turnover",
            bucket_iso=bucket_iso,
            timestamp_dt=ts,
            val=snapshot.market_turnover,
            turnover=snapshot.market_turnover,
        )

        # 4. Shares Traded (Volume)
        self._update_bucket(
            session_date=session_date,
            metric="shares_traded",
            bucket_iso=bucket_iso,
            timestamp_dt=ts,
            val=float(snapshot.shares_traded),
            volume=snapshot.shares_traded,
        )

        # Enforce memory bounding
        self._enforce_retention_and_capacity()

        # Atomic persist
        self.save()

    def _update_bucket(
        self,
        session_date: str,
        metric: str,
        bucket_iso: str,
        timestamp_dt: datetime,
        val: float,
        turnover: Optional[float] = None,
        volume: Optional[int] = None,
    ) -> None:
        """Update or insert a 1-minute bar for a given metric."""
        metric_dict = self._sessions[session_date][metric]

        if bucket_iso not in metric_dict:
            metric_dict[bucket_iso] = {
                "timestamp": bucket_iso,
                "value": round(val, 2),
                "open": round(val, 2),
                "high": round(val, 2),
                "low": round(val, 2),
                "close": round(val, 2),
                "turnover": round(turnover, 2) if turnover is not None else None,
                "volume": volume,
            }
        else:
            bar = metric_dict[bucket_iso]
            bar["high"] = max(bar["high"], round(val, 2))
            bar["low"] = min(bar["low"], round(val, 2))
            bar["close"] = round(val, 2)
            bar["value"] = round(val, 2)
            if turnover is not None:
                bar["turnover"] = round(turnover, 2)
            if volume is not None:
                bar["volume"] = volume

    def _enforce_retention_and_capacity(self) -> None:
        """Trim older sessions to guarantee strictly bounded memory usage."""
        sorted_sessions = sorted(self._sessions.keys())
        max_sessions = self.config.intraday_retention_sessions + 1  # Current + configured prior sessions

        # Evict old sessions beyond retention limit
        if len(sorted_sessions) > max_sessions:
            to_remove = sorted_sessions[:-max_sessions]
            for s in to_remove:
                del self._sessions[s]

        # Enforce max points per metric per session
        for session_dict in self._sessions.values():
            for metric, buckets in session_dict.items():
                if len(buckets) > self.config.intraday_max_points_per_metric:
                    sorted_buckets = sorted(buckets.keys())
                    excess = len(sorted_buckets) - self.config.intraday_max_points_per_metric
                    for k in sorted_buckets[:excess]:
                        del buckets[k]

    def get_series(
        self,
        metric: str = "aspi",
        session: str = "current"
    ) -> List[IntradaySeriesPoint]:
        """Query downsampled points for a specific metric and session."""
        normalized_metric = metric.lower().replace("-", "_")
        if normalized_metric in ("sp_sl20", "spsl20", "sp_20"):
            normalized_metric = "sp20"
        elif normalized_metric == "volume":
            normalized_metric = "shares_traded"

        # Determine target session date
        target_session = session
        if session == "current" or not session:
            target_session = self._latest_session_date or (
                sorted(self._sessions.keys())[-1] if self._sessions else None
            )

        if not target_session or target_session not in self._sessions:
            return []

        metric_buckets = self._sessions[target_session].get(normalized_metric, {})
        points: List[IntradaySeriesPoint] = []

        for bucket_key in sorted(metric_buckets.keys()):
            raw_bar = metric_buckets[bucket_key]
            try:
                ts = datetime.fromisoformat(raw_bar["timestamp"])
                points.append(
                    IntradaySeriesPoint(
                        timestamp=ts,
                        value=raw_bar["value"],
                        open=raw_bar.get("open"),
                        high=raw_bar.get("high"),
                        low=raw_bar.get("low"),
                        close=raw_bar.get("close"),
                        turnover=raw_bar.get("turnover"),
                        volume=raw_bar.get("volume"),
                    )
                )
            except Exception as e:
                logger.warning(f"Error parsing intraday point: {e}")

        return points

    def get_available_sessions(self) -> List[str]:
        """Return list of session dates currently held in memory."""
        return sorted(self._sessions.keys())

    def save(self) -> None:
        """Atomically persist intraday series to disk."""
        target_path = os.path.abspath(self.config.intraday_cache_file)
        dir_name = os.path.dirname(target_path)
        os.makedirs(dir_name, exist_ok=True)
        tmp_path = f"{target_path}.tmp.{os.getpid()}"

        try:
            payload = {
                "latest_session_date": self._latest_session_date,
                "sessions": self._sessions,
            }
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
                f.flush()
            os.replace(tmp_path, target_path)
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            logger.error(f"Failed atomic persistence of intraday series: {e}")

    def load(self) -> None:
        """Load persisted intraday series from disk if available."""
        target_path = os.path.abspath(self.config.intraday_cache_file)
        if not os.path.exists(target_path):
            return

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._latest_session_date = data.get("latest_session_date")
            raw_sessions = data.get("sessions", {})
            for session_date, metrics in raw_sessions.items():
                for metric, buckets in metrics.items():
                    self._sessions[session_date][metric] = buckets

            logger.info(f"Loaded intraday series across {len(self._sessions)} sessions.")
        except Exception as e:
            logger.error(f"Failed to load intraday series from disk: {e}")

    def clear(self) -> None:
        """Clear memory and cache (for testing)."""
        self._sessions.clear()
        self._latest_session_date = None
        target_path = os.path.abspath(self.config.intraday_cache_file)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass


_global_intraday_store: Optional[IntradayStore] = None


def get_intraday_store(config: Optional[IngestionConfig] = None) -> IntradayStore:
    """Retrieve or initialize the process-wide IntradayStore singleton."""
    global _global_intraday_store
    if _global_intraday_store is None:
        _global_intraday_store = IntradayStore(config=config)
    return _global_intraday_store
