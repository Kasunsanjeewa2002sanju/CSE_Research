"""Reusable prior event statistical aggregator for zero-lookahead feature engineering.

Adheres strictly to:
- Rule R2: Zero lookahead. Uses ONLY events whose full event window ended before as_of_date.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd

from cse.utils.config import find_project_root
from cse.utils.logger import get_logger

logger = get_logger("cse.events.prior_stats")


class PriorEventStatsCalculator:
    """Calculates historical prior event CAR statistics as of any point in time."""

    def __init__(
        self,
        df_per_event: Optional[pd.DataFrame] = None,
        df_cse: Optional[pd.DataFrame] = None,
    ) -> None:
        """Initialize calculator with precomputed per-event CAR table and price panel."""
        root = find_project_root()
        if df_per_event is None:
            csv_path = root / "results" / "tables" / "event_study_per_event.csv"
            if not csv_path.exists():
                raise FileNotFoundError(
                    f"Event study per-event table not found at {csv_path}. Run Stage 4 first."
                )
            self.df_events = pd.read_csv(csv_path)
        else:
            self.df_events = df_per_event.copy()

        if df_cse is None:
            parquet_path = root / "data" / "processed" / "cse_clean.parquet"
            self.df_cse = pd.read_parquet(parquet_path)
        else:
            self.df_cse = df_cse.copy()

        self.df_cse["date"] = pd.to_datetime(self.df_cse["date"]).dt.strftime("%Y-%m-%d")

        # Precompute the exact calendar date on which each event's window concluded
        self._enrich_window_end_dates()

    def _enrich_window_end_dates(self) -> None:
        """Calculate the absolute calendar end date for each event window."""
        n_total = len(self.df_cse)
        window_end_dates = []

        for _, row in self.df_events.iterrows():
            t0 = int(row["trading_day_index"])
            w_end = int(row["w_end"])
            end_idx = t0 + w_end

            if 0 <= end_idx < n_total:
                end_date = str(self.df_cse.loc[end_idx, "date"])
            else:
                end_date = "9999-12-31"  # beyond dataset bounds
            window_end_dates.append(end_date)

        self.df_events["window_end_date"] = window_end_dates

    def get_stats(
        self,
        as_of_date: Union[str, datetime.date, datetime.datetime],
        election_type: Optional[str] = None,
        stage: Optional[str] = None,
        window: str = "[0,+7]",
    ) -> Dict[str, Any]:
        """Return prior CAR mean, median, std, and n using ONLY events whose window ended before as_of_date.
        
        Args:
            as_of_date: Forecast origin date (ISO string 'YYYY-MM-DD' or date object).
            election_type: Optional filter ('Presidential', 'Parliamentary', 'Provincial Council', or None).
            stage: Optional filter ('polling', 'result', 'announcement', etc., or None).
            window: Event window identifier (e.g. '[0,+2]', '[0,+7]', '[-7,-1]').
            
        Returns:
            Dict containing 'as_of_date', 'election_type', 'stage', 'window',
            'mean', 'median', 'std', and 'n'.
        """
        if isinstance(as_of_date, (datetime.date, datetime.datetime)):
            as_of_str = as_of_date.strftime("%Y-%m-%d")
        else:
            as_of_str = str(as_of_date)

        # Strict chronological filtering (Rule R2): window must have concluded strictly before as_of_date
        mask = (self.df_events["window_end_date"] < as_of_str) & (self.df_events["window"] == window)

        if election_type is not None:
            mask = mask & (self.df_events["election_type"] == election_type)
        if stage is not None:
            mask = mask & (self.df_events["stage"] == stage)

        sub = self.df_events[mask]
        cars = sub["car"].dropna().values
        n = len(cars)

        if n == 0:
            mean_val = float("nan")
            med_val = float("nan")
            std_val = float("nan")
        elif n == 1:
            mean_val = float(cars[0])
            med_val = float(cars[0])
            std_val = 0.0
        else:
            mean_val = float(np.mean(cars))
            med_val = float(np.median(cars))
            std_val = float(np.std(cars, ddof=1))

        return {
            "as_of_date": as_of_str,
            "election_type": election_type,
            "stage": stage,
            "window": window,
            "mean": mean_val,
            "median": med_val,
            "std": std_val,
            "n": n,
        }


# Global singleton cache for quick module-level access
_CALCULATOR_CACHE: Optional[PriorEventStatsCalculator] = None


def prior_event_stats(
    as_of_date: Union[str, datetime.date, datetime.datetime],
    election_type: Optional[str] = None,
    stage: Optional[str] = None,
    window: str = "[0,+7]",
    df_per_event: Optional[pd.DataFrame] = None,
    df_cse: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Retrieve historical prior event CAR statistics as of any date.
    
    Guarantees strict zero lookahead (Rule R2): only events whose full window ended
    strictly before as_of_date are included in the statistics.
    """
    global _CALCULATOR_CACHE
    if df_per_event is not None or df_cse is not None or _CALCULATOR_CACHE is None:
        calc = PriorEventStatsCalculator(df_per_event=df_per_event, df_cse=df_cse)
        if df_per_event is None and df_cse is None:
            _CALCULATOR_CACHE = calc
    else:
        calc = _CALCULATOR_CACHE

    return calc.get_stats(
        as_of_date=as_of_date,
        election_type=election_type,
        stage=stage,
        window=window,
    )
