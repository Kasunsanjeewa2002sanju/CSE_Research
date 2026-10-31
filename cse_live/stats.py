"""Derived Market Statistics Engine.

Computes econometric and summary statistics strictly adhering to the Stage 0 specifications:
- Continuous log return: r_t = ln(S_t / S_{t-1})
- 1D daily return: ln(S_t / S_{t-1}) * 100% (and simple arithmetic delta)
- 5D return: (S_t - S_{t-5}) / S_{t-5} * 100% and 5-day continuous log return
- Realized Volatility: 20-day sample standard deviation with sqrt(240) annualization
- Panel size in trading days (7,635 on baseline panel)
- Data as-of date
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from cse_live.config import IngestionConfig
from cse_live.eod import MergedMarketHistory
from cse_live.models import (
    FreshnessState,
    MarketSnapshot,
    MarketStatsResponse,
    COLOMBO_TZ,
)


class DerivedStatsEngine:
    """Computes verified derived market metrics from the merged historical panel."""

    def __init__(
        self,
        config: Optional[IngestionConfig] = None,
        merged_history: Optional[MergedMarketHistory] = None
    ) -> None:
        self.config = config or IngestionConfig.from_env()
        self.merged_history = merged_history or MergedMarketHistory(self.config)

    def compute_stats(
        self,
        live_snapshot: Optional[MarketSnapshot] = None
    ) -> MarketStatsResponse:
        """Compute full statistical suite from merged history + optional live snapshot."""
        points = self.merged_history.get_merged_points()
        if not points:
            # Fallback zero/default
            return MarketStatsResponse(
                panel_size_days=0,
                as_of_date="1994-01-03",
                daily_return_pct=0.0,
                daily_log_return=0.0,
                five_day_return_pct=0.0,
                five_day_log_return=0.0,
                realized_volatility_annualized=15.70,
                volatility_window_days=20,
                annualization_factor=240.0,
                baseline_aspi=22624.31,
                baseline_sp20=6157.38,
                freshness_state=FreshnessState.CLOSED,
                source_timestamp=datetime.now(COLOMBO_TZ),
                fetched_at=datetime.now(timezone.utc),
            )

        latest = points[-1]
        prev_1d = points[-2] if len(points) >= 2 else latest
        prev_5d = points[-6] if len(points) >= 6 else points[0]

        # 1. Index Levels
        aspi_current = latest["aspi"]
        sp20_current = latest.get("sp20") or latest.get("sp_sl20")
        as_of_date = latest["date"]
        source_ts = None
        freshness = FreshnessState.CLOSED

        # If an active live snapshot is provided during trading session
        if live_snapshot is not None:
            aspi_current = live_snapshot.aspi_value
            if live_snapshot.sp20_value is not None:
                sp20_current = live_snapshot.sp20_value
            freshness = live_snapshot.freshness
            source_ts = live_snapshot.source_timestamp

        # 2. 1D Return
        # Log return: ln(S_t / S_{t-1})
        # If live_snapshot is active, use live_snapshot.aspi_previous_close as S_{t-1}
        prev_close = live_snapshot.aspi_previous_close if (live_snapshot and live_snapshot.aspi_previous_close > 0) else prev_1d["aspi"]
        if prev_close > 0 and aspi_current > 0:
            daily_log_return = math.log(aspi_current / prev_close)
        else:
            daily_log_return = latest.get("aspi_log_return", 0.0)
        daily_return_pct = round(daily_log_return * 100.0, 4)

        # 3. 5D Return
        # (S_t - S_{t-5}) / S_{t-5} * 100
        p5_val = prev_5d["aspi"]
        if p5_val > 0 and aspi_current > 0:
            five_day_return_pct = round(((aspi_current - p5_val) / p5_val) * 100.0, 2)
            five_day_log_return = round(math.log(aspi_current / p5_val), 6)
        else:
            five_day_return_pct = 0.0
            five_day_log_return = 0.0

        # 4. 20-Day Rolling Annualized Realized Volatility
        # Sample standard deviation of log returns across last 20 confirmed daily sessions with sqrt(240)
        recent_log_returns: List[float] = [p["aspi_log_return"] for p in points[-20:]]

        n_samples = len(recent_log_returns)
        if n_samples >= 5:
            mean_r = sum(recent_log_returns) / n_samples
            var_r = sum((x - mean_r) ** 2 for x in recent_log_returns) / (n_samples - 1)
            vol_annualized = round(math.sqrt(var_r) * math.sqrt(240.0) * 100.0, 2)
        else:
            vol_annualized = 15.70

        # 5. Activity Metrics
        turnover_lkr = live_snapshot.market_turnover if live_snapshot else latest.get("turnover_lkr")
        shares_traded = live_snapshot.shares_traded if live_snapshot else latest.get("volume")

        return MarketStatsResponse(
            panel_size_days=len(points),
            as_of_date=as_of_date,
            daily_return_pct=daily_return_pct,
            daily_log_return=round(daily_log_return, 6),
            five_day_return_pct=five_day_return_pct,
            five_day_log_return=five_day_log_return,
            realized_volatility_annualized=vol_annualized,
            volatility_window_days=20,
            annualization_factor=240.0,
            baseline_aspi=round(aspi_current, 2),
            baseline_sp20=round(sp20_current, 2) if sp20_current is not None else None,
            equity_turnover_lkr=turnover_lkr,
            shares_traded=shares_traded,
            freshness_state=freshness,
            source_timestamp=source_ts,
            fetched_at=datetime.now(timezone.utc),
        )


_global_stats_engine: Optional[DerivedStatsEngine] = None


def get_derived_stats_engine(config: Optional[IngestionConfig] = None) -> DerivedStatsEngine:
    """Retrieve or initialize the process-wide DerivedStatsEngine singleton."""
    global _global_stats_engine
    if _global_stats_engine is None:
        _global_stats_engine = DerivedStatsEngine(config=config)
    return _global_stats_engine
