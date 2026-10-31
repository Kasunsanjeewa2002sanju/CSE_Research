"""End-Of-Day (EOD) Append Store, Reconciliation Engine, and Merged Market View.

Rules & Guarantees:
1. NEVER modify CSE_data.csv or baseline cse_clean.csv in place.
2. Safe append-only store in cse_data_cache/live_daily.csv.
3. Strictly idempotent: re-running for the same date updates/verifies without duplication.
4. Comprehensive append audit log in cse_data_cache/append_audit.log.
5. Reconciliation engine against official exchange closing prints.
6. Unified MergedMarketHistory read view seamlessly joining historical baseline + live appends.
"""

from __future__ import annotations

import csv
import json
import logging
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cse_live.config import IngestionConfig
from cse_live.models import (
    AuditLogEntry,
    DailyBar,
    MarketSnapshot,
    COLOMBO_TZ,
)

logger = logging.getLogger("cse_live.eod")


@dataclass
class UpsertResult:
    """Result of an idempotent EOD bar upsert."""
    action: str  # "INSERT", "UPDATE", "NOOP"
    date_str: str
    is_duplicate: bool
    aspi: float
    discrepancy: Optional[str] = None


class LiveDailyStore:
    """Append-only store for live daily closing bars with atomic persistence and audit logging."""

    CSV_HEADER = [
        "date",
        "aspi",
        "sp20",
        "has_sp20",
        "turnover_equity_mn",
        "shares_traded_equity_k",
        "aspi_log_return",
    ]

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or IngestionConfig.from_env()
        self.file_path = os.path.abspath(self.config.live_daily_file_path)
        self.audit_log_path = os.path.abspath(self.config.append_audit_log_path)

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)

    def load_rows(self) -> List[Dict[str, str]]:
        """Load all rows from live_daily.csv."""
        if not os.path.exists(self.file_path):
            return []
        rows: List[Dict[str, str]] = []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get("date"):
                        rows.append(r)
        except Exception as e:
            logger.error(f"Error reading live daily store ({self.file_path}): {e}")
        return rows

    def upsert_daily_bar(
        self,
        bar: DailyBar,
        source: str = "cse_live_eod",
        official_close_aspi: Optional[float] = None
    ) -> UpsertResult:
        """Idempotently insert or update a DailyBar by date. Never duplicates rows."""
        date_str = bar.trade_date.isoformat() if isinstance(bar.trade_date, date) else str(bar.trade_date)
        rows = self.load_rows()

        # Check reconciliation against official close if provided
        reconciled = official_close_aspi is not None
        discrepancy: Optional[str] = None
        if official_close_aspi is not None:
            diff = abs(bar.close - official_close_aspi)
            if diff > 0.05:
                discrepancy = f"Captured ASPI ({bar.close}) differs from official ({official_close_aspi}) by {diff:.2f} pts"
                logger.warning(f"EOD Reconciliation Warning for {date_str}: {discrepancy}")

        # Format new row data
        sp20_str = f"{bar.sp20:.2f}" if bar.sp20 is not None else ""
        has_sp20_str = "True" if bar.sp20 is not None else "False"
        turnover_mn = round(bar.turnover_equity_mn or (bar.turnover / 1_000_000.0 if bar.turnover else 0.0), 2)
        shares_k = round(bar.shares_traded_equity_k or (bar.share_volume / 1000.0 if bar.share_volume else 0.0), 1)
        log_ret_str = f"{bar.aspi_log_return:.16f}" if bar.aspi_log_return is not None else ""

        new_row = {
            "date": date_str,
            "aspi": f"{bar.close:.2f}",
            "sp20": sp20_str,
            "has_sp20": has_sp20_str,
            "turnover_equity_mn": f"{turnover_mn:.2f}",
            "shares_traded_equity_k": f"{shares_k:.1f}",
            "aspi_log_return": log_ret_str,
        }

        # Check if row with date_str already exists
        existing_idx = -1
        for idx, r in enumerate(rows):
            if r.get("date") == date_str:
                existing_idx = idx
                break

        action = "INSERT"
        is_duplicate = False

        if existing_idx >= 0:
            existing = rows[existing_idx]
            # Check if all values are identical
            is_same = (
                existing.get("aspi") == new_row["aspi"] and
                existing.get("sp20") == new_row["sp20"] and
                existing.get("turnover_equity_mn") == new_row["turnover_equity_mn"] and
                existing.get("shares_traded_equity_k") == new_row["shares_traded_equity_k"]
            )
            if is_same:
                action = "NOOP"
                is_duplicate = True
                logger.info(f"EOD Idempotency check: bar for {date_str} already exists and is identical. Skipping rewrite.")
            else:
                action = "UPDATE"
                rows[existing_idx] = new_row
                logger.info(f"EOD Idempotency update: updating existing bar for {date_str}.")
        else:
            action = "INSERT"
            rows.append(new_row)
            logger.info(f"EOD Append: appending new bar for {date_str} (ASPI={bar.close:.2f}).")

        # Atomic write back to CSV if modified
        if action in ("INSERT", "UPDATE"):
            self._atomic_write_rows(rows)

        # Audit log entry
        self._write_audit_log(
            AuditLogEntry(
                date=date_str,
                action=action,
                source=source,
                aspi=bar.close,
                sp20=bar.sp20,
                turnover_equity_mn=turnover_mn,
                shares_traded_equity_k=shares_k,
                aspi_log_return=bar.aspi_log_return,
                reconciled=reconciled,
                discrepancy=discrepancy,
            )
        )

        return UpsertResult(
            action=action,
            date_str=date_str,
            is_duplicate=is_duplicate,
            aspi=bar.close,
            discrepancy=discrepancy,
        )

    def _atomic_write_rows(self, rows: List[Dict[str, str]]) -> None:
        """Atomically overwrite live_daily.csv via tempfile and rename."""
        dir_name = os.path.dirname(self.file_path)
        os.makedirs(dir_name, exist_ok=True)
        tmp_path = f"{self.file_path}.tmp.{os.getpid()}"
        try:
            with open(tmp_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
                f.flush()
            os.replace(tmp_path, self.file_path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise

    def _write_audit_log(self, entry: AuditLogEntry) -> None:
        """Append an audit record to append_audit.log."""
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write EOD append audit log: {e}")

    def get_audit_logs(self, limit: int = 50) -> List[AuditLogEntry]:
        """Read recent audit log entries."""
        if not os.path.exists(self.audit_log_path):
            return []
        entries: List[AuditLogEntry] = []
        try:
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_clean = line.strip()
                    if line_clean:
                        entries.append(AuditLogEntry.model_validate_json(line_clean))
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")
        return entries[-limit:]


class MergedMarketHistory:
    """Read view joining historical baseline (cse_clean.csv) and live appends (live_daily.csv).
    
    CRITICAL: Never edits CSE_data.csv or cse_clean.csv. Exposes a clean consolidated view
    with continuous log returns and 20D rolling annualized volatility recalculated across
    the historical-live boundary.
    """

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or IngestionConfig.from_env()
        self.live_store = LiveDailyStore(self.config)

        # Resolve clean panel path
        self.baseline_path = Path(self.config.historical_clean_path)
        if not self.baseline_path.exists():
            curr = Path(__file__).resolve().parent
            candidates = [curr, curr.parent, curr.parent.parent, curr.parent.parent.parent, curr.parent.parent.parent.parent]
            for c in candidates:
                for rel in [
                    "cse_research/data/processed/cse_clean.csv",
                    "data/processed/cse_clean.csv",
                    "cse_research/data/raw/CSE_data.csv",
                ]:
                    cand = (c / rel).resolve()
                    if cand.exists():
                        self.baseline_path = cand
                        break
                if self.baseline_path.exists():
                    break

        self._cached_merged: Optional[List[Dict[str, Any]]] = None
        self._last_merged_at: float = 0.0

    def get_merged_points(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """Load and union baseline + live appends, calculating returns and volatility."""
        # 1-second in-memory caching to avoid disk churn during high API traffic
        if not force_reload and self._cached_merged is not None:
            if (datetime.now().timestamp() - self._last_merged_at) < 1.0:
                return self._cached_merged

        records_by_date: Dict[str, Dict[str, Any]] = {}

        # 1. Load Baseline Data
        if self.baseline_path.exists():
            with open(self.baseline_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    d = row.get("date")
                    if not d:
                        continue
                    aspi_val = float(row["aspi"]) if row.get("aspi") else 0.0
                    sp20_str = row.get("sp20") or ""
                    sp20_val = float(sp20_str) if sp20_str and sp20_str.lower() != "nan" else None
                    turnover_mn = float(row.get("turnover_equity_mn") or 0.0)
                    shares_k = float(row.get("shares_traded_equity_k") or 0.0)
                    records_by_date[d] = {
                        "date": d,
                        "aspi": aspi_val,
                        "sp20": sp20_val,
                        "turnover_equity_mn": turnover_mn,
                        "shares_traded_equity_k": shares_k,
                        "is_live": False,
                    }

        # 2. Load Live Daily Appends (take precedence if date overlaps)
        live_rows = self.live_store.load_rows()
        for r in live_rows:
            d = r.get("date")
            if not d:
                continue
            aspi_val = float(r["aspi"]) if r.get("aspi") else 0.0
            sp20_str = r.get("sp20") or ""
            sp20_val = float(sp20_str) if sp20_str and sp20_str.lower() != "nan" else None
            turnover_mn = float(r.get("turnover_equity_mn") or 0.0)
            shares_k = float(r.get("shares_traded_equity_k") or 0.0)
            records_by_date[d] = {
                "date": d,
                "aspi": aspi_val,
                "sp20": sp20_val,
                "turnover_equity_mn": turnover_mn,
                "shares_traded_equity_k": shares_k,
                "is_live": True,
            }

        # 3. Sort Chronologically
        sorted_dates = sorted(records_by_date.keys())
        points: List[Dict[str, Any]] = []
        recent_log_returns: List[float] = []

        prev_aspi: Optional[float] = None

        for d in sorted_dates:
            item = records_by_date[d]
            aspi_val = item["aspi"]
            sp20_val = item["sp20"]
            turnover_mn = item["turnover_equity_mn"]
            shares_k = item["shares_traded_equity_k"]

            # Continuous log return: r_t = ln(S_t / S_{t-1})
            if prev_aspi is not None and prev_aspi > 0 and aspi_val > 0:
                log_ret = math.log(aspi_val / prev_aspi)
            else:
                log_ret = 0.0
            prev_aspi = aspi_val

            # Rolling 20D Realized Volatility:
            # Sample variance of 20 log returns with sqrt(240) annualization
            recent_log_returns.append(log_ret)
            if len(recent_log_returns) > 20:
                recent_log_returns.pop(0)

            if len(recent_log_returns) >= 5:
                mean_r = sum(recent_log_returns) / len(recent_log_returns)
                var_r = sum((x - mean_r) ** 2 for x in recent_log_returns) / max(len(recent_log_returns) - 1, 1)
                realized_vol_20d = round(math.sqrt(var_r) * math.sqrt(240.0) * 100.0, 2)
            else:
                realized_vol_20d = 18.0

            turnover_lkr = round(turnover_mn * 1_000_000.0, 2)
            shares_unit = int(shares_k * 1000.0)

            pt: Dict[str, Any] = {
                "date": d,
                "value": round(aspi_val, 2),
                "aspi": round(aspi_val, 2),
                "sp20": round(sp20_val, 2) if sp20_val is not None else None,
                "sp_sl20": round(sp20_val, 2) if sp20_val is not None else None,
                "return_pct": round(log_ret * 100.0, 4),
                "return": log_ret,
                "log_return": log_ret,
                "aspi_log_return": log_ret,
                "turnover_equity_mn": turnover_mn,
                "turnover_lkr": turnover_lkr,
                "turnover": turnover_lkr,
                "shares_traded_equity_k": shares_k,
                "volume": shares_unit,
                "volume_shares": shares_unit,
                "realized_vol_20d": realized_vol_20d,
                "is_live": item["is_live"],
            }
            points.append(pt)

        self._cached_merged = points
        self._last_merged_at = datetime.now().timestamp()
        return points

    def get_panel_size(self) -> int:
        """Returns total trading session count in the merged panel."""
        return len(self.get_merged_points())


class EODJob:
    """Executes the official End-of-Day close confirmation, reconciliation, and append."""

    def __init__(
        self,
        config: Optional[IngestionConfig] = None,
        live_store: Optional[LiveDailyStore] = None,
        merged_history: Optional[MergedMarketHistory] = None,
    ) -> None:
        self.config = config or IngestionConfig.from_env()
        self.live_store = live_store or LiveDailyStore(self.config)
        self.merged_history = merged_history or MergedMarketHistory(self.config)

    def is_final_print_confirmed(
        self,
        snapshot1: MarketSnapshot,
        snapshot2: Optional[MarketSnapshot] = None
    ) -> bool:
        """Check if final close print is confirmed.
        
        Criteria:
        1. Official close status field reported (e.g. 'Market Closed', 'Market Close (Statistics Being Finalized)').
        OR
        2. Two identical consecutive polls after market close time (14:30).
        """
        raw_status = snapshot1.market_status.raw_status.lower()
        if "close" in raw_status or "finalize" in raw_status:
            return True

        if snapshot2 is not None:
            # Check if after 14:30 Colombo time
            t1 = snapshot1.source_timestamp.astimezone(COLOMBO_TZ)
            t2 = snapshot2.source_timestamp.astimezone(COLOMBO_TZ)
            close_h, close_m = [int(x) for x in self.config.market_close.split(":")]
            is_after_close = (t1.hour > close_h or (t1.hour == close_h and t1.minute >= close_m))

            if is_after_close:
                # Two identical consecutive polls
                if abs(snapshot1.aspi_value - snapshot2.aspi_value) < 0.001:
                    return True

        return False

    def build_daily_bar(
        self,
        confirmed_snapshot: MarketSnapshot,
        prev_close_aspi: Optional[float] = None
    ) -> DailyBar:
        """Construct a validated DailyBar from confirmed closing snapshot."""
        trade_date = confirmed_snapshot.source_timestamp.astimezone(COLOMBO_TZ).date()
        aspi_close = confirmed_snapshot.aspi_value
        prev_close = prev_close_aspi or confirmed_snapshot.aspi_previous_close

        log_return = math.log(aspi_close / prev_close) if prev_close > 0 else 0.0
        pct_change = ((aspi_close - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0

        return DailyBar(
            trade_date=trade_date,
            close=aspi_close,
            aspi=aspi_close,
            sp20=confirmed_snapshot.sp20_value,
            change=confirmed_snapshot.aspi_change,
            percent_change=pct_change,
            turnover=confirmed_snapshot.market_turnover,
            turnover_equity_mn=round(confirmed_snapshot.market_turnover / 1_000_000.0, 2),
            share_volume=confirmed_snapshot.shares_traded,
            shares_traded_equity_k=round(confirmed_snapshot.shares_traded / 1000.0, 1),
            trades=confirmed_snapshot.total_trades,
            aspi_log_return=log_return,
        )

    def execute_eod_append(
        self,
        confirmed_snapshot: MarketSnapshot,
        official_close_aspi: Optional[float] = None,
        source: str = "cse_live_eod"
    ) -> UpsertResult:
        """Build DailyBar, reconcile, and idempotently upsert to live_daily.csv."""
        # Find previous day close from merged history
        merged_pts = self.merged_history.get_merged_points()
        prev_close = merged_pts[-1]["aspi"] if merged_pts else confirmed_snapshot.aspi_previous_close

        bar = self.build_daily_bar(confirmed_snapshot, prev_close_aspi=prev_close)
        result = self.live_store.upsert_daily_bar(
            bar,
            source=source,
            official_close_aspi=official_close_aspi
        )
        return result
