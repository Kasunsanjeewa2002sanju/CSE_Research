"""Cumulative Abnormal Return (CAR) Calculation Engine for CSE News Events.

Calculates Abnormal Returns (AR) and Cumulative Abnormal Returns (CAR) around news events:
- Market model: R_i,t = alpha + beta * R_m,t + epsilon
  (estimation window = 120 trading days BEFORE event, gap = 10 days before event)
- Abnormal return AR_t = R_i,t - (alpha + beta * R_m,t)
- CAR_h = sum of AR over h trading days post-event
- For index-level news (no specific ticker), uses market-adjusted return:
  AR = R_aspi - mean(R_aspi, estimation_window)
- Clamps CAR to [-10%, +10%] (-0.10 to +0.10) to remove outliers from noisy data
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from cse.news.historical_db import get_aspi_range, get_default_db_path

INDEX_ALIASES = {None, "", "aspi", "^cse", "index", "all share", "market"}


def parse_date_string(date_input: Union[str, date, datetime]) -> Tuple[str, int]:
    """Parse date and hour from various date/datetime/string formats.
    
    Returns
    -------
    Tuple[str, int]
        (YYYY-MM-DD string, hour of day 0-23)
    """
    if isinstance(date_input, datetime):
        return date_input.strftime("%Y-%m-%d"), date_input.hour
    if isinstance(date_input, date):
        return date_input.strftime("%Y-%m-%d"), 12

    date_str = str(date_input).strip()
    hour = 12

    # Match ISO format or standard date
    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}):(\d{2})", date_str)
    if iso_match:
        return iso_match.group(1), int(iso_match.group(2))

    ymd_match = re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
    if ymd_match:
        return ymd_match.group(1), hour

    # Fallback to pandas
    try:
        dt = pd.to_datetime(date_str)
        return dt.strftime("%Y-%m-%d"), dt.hour
    except Exception:
        return date_str[:10], hour


def map_to_trading_day(
    date_input: Union[str, date, datetime],
    trading_days: List[str],
) -> Optional[str]:
    """Map a calendar date/timestamp to the nearest appropriate CSE trading day.
    
    Rules:
    - If published after trading hours (>= 15:00 Colombo time), news reaction
      applies to the next calendar date.
    - If date falls on weekend/holiday, maps to the next available trading day (>= date).
    - If after the latest available trading day, maps to the latest trading day.
    - If before the earliest available trading day, maps to the earliest trading day.
    """
    if not trading_days:
        return None

    date_part, hour = parse_date_string(date_input)

    # If published after market close (CSE closes at 14:30), effective reaction is next day
    if hour >= 15:
        try:
            next_cal = pd.to_datetime(date_part) + pd.Timedelta(days=1)
            date_part = next_cal.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Exact match
    if date_part in trading_days:
        return date_part

    # Find first trading day >= date_part
    for td in trading_days:
        if td >= date_part:
            return td

    # If beyond all known trading days, return latest
    return trading_days[-1]


class CARCalculator:
    """Cumulative Abnormal Return calculator using CSE historical prices."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        aspi_df: Optional[pd.DataFrame] = None,
        estimation_window: int = 120,
        gap_days: int = 10,
        car_clip: float = 0.10,
    ) -> None:
        self.db_path = db_path or get_default_db_path()
        self.estimation_window = estimation_window
        self.gap_days = gap_days
        self.car_clip = car_clip

        self._load_aspi_data(aspi_df)

    def _load_aspi_data(self, aspi_df: Optional[pd.DataFrame] = None) -> None:
        """Load ASPI prices and calculate daily returns."""
        if aspi_df is not None:
            df = aspi_df.copy()
        else:
            df = get_aspi_range(db_path=self.db_path, as_dataframe=True)

        if df.empty:
            self.trading_days: List[str] = []
            self.closes: np.ndarray = np.array([])
            self.returns: np.ndarray = np.array([])
            self._day_to_idx: Dict[str, int] = {}
            return

        df["date"] = df["date"].astype(str).str[:10]
        df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

        closes = df["close"].astype(float).values
        if "return_1d" in df.columns and not df["return_1d"].isna().all():
            returns = df["return_1d"].astype(float).values
            # replace leading nan/null
            if np.isnan(returns[0]):
                returns[0] = 0.0
        else:
            returns = np.zeros(len(closes))
            if len(closes) > 1:
                returns[1:] = (closes[1:] - closes[:-1]) / closes[:-1]

        self.trading_days = df["date"].tolist()
        self.closes = closes
        self.returns = returns
        self._day_to_idx = {d: i for i, d in enumerate(self.trading_days)}

    def refresh(self) -> None:
        """Reload ASPI prices from database."""
        self._load_aspi_data(None)

    def get_event_trading_index(self, event_date: Union[str, date, datetime]) -> Tuple[Optional[str], Optional[int]]:
        """Map event date to nearest trading day and return (mapped_date, index)."""
        if not self.trading_days:
            return None, None
        mapped = map_to_trading_day(event_date, self.trading_days)
        if mapped is None:
            return None, None
        idx = self._day_to_idx.get(mapped)
        return mapped, idx

    def calculate_car(
        self,
        ticker_or_index: Optional[str],
        event_date: Union[str, date, datetime],
        horizon: int = 1,
        ticker_series: Optional[pd.DataFrame] = None,
    ) -> Optional[float]:
        """Compute Cumulative Abnormal Return (CAR) for horizon h post-event.
        
        Parameters
        ----------
        ticker_or_index : Optional[str]
            Stock ticker symbol or None/'ASPI' for index-level news.
        event_date : Union[str, date, datetime]
            Date or timestamp of news item.
        horizon : int
            Post-event trading days horizon (e.g. 1, 2, 5, 10).
        ticker_series : Optional[pd.DataFrame]
            If specific ticker is provided with price data.

        Returns
        -------
        Optional[float]
            Cumulative abnormal return clamped to [-0.10, +0.10], or None if
            insufficient data.
        """
        if len(self.trading_days) < self.estimation_window:
            return None

        mapped_date, t0 = self.get_event_trading_index(event_date)
        if t0 is None:
            return None

        # Check prior data availability: require at least 120 days prior to event
        if t0 < self.estimation_window:
            return None

        # Estimation window: 120 trading days BEFORE event, gap = 10 days before event
        # t0 - 10 is the last day before the gap
        # est window ends at t0 - 10 (exclusive) or t0 - gap_days
        est_end = max(1, t0 - self.gap_days)
        est_start = max(0, est_end - self.estimation_window)

        est_returns = self.returns[est_start:est_end]
        if len(est_returns) < min(60, self.estimation_window // 2):
            return None

        # Post-event window: h trading days post-event (t0 + 1 to t0 + horizon inclusive)
        post_start = t0 + 1
        post_end = t0 + 1 + horizon

        if post_end > len(self.returns):
            # Not enough post-event trading days in history
            return None

        aspi_evt_returns = self.returns[post_start:post_end]
        if len(aspi_evt_returns) < horizon:
            return None

        # Determine model: Market Model for ticker if ticker series supplied,
        # otherwise Market-Adjusted Return for index-level news
        is_index = (
            ticker_or_index is None
            or str(ticker_or_index).strip().lower() in INDEX_ALIASES
            or ticker_series is None
        )

        if is_index:
            # AR_t = R_aspi,t - mean(R_aspi, estimation_window)
            r_bar = float(np.mean(est_returns))
            ar = aspi_evt_returns - r_bar
            raw_car = float(np.sum(ar))
        else:
            # Market model: R_i,t = alpha + beta * R_m,t + epsilon
            # Fallback to market-adjusted if ticker series incomplete
            try:
                # Align ticker returns
                ticker_df = ticker_series.copy()
                ticker_df["date"] = ticker_df["date"].astype(str).str[:10]
                ticker_map = dict(zip(ticker_df["date"], ticker_df["close"].astype(float)))

                # Calculate ticker returns for estimation and event periods
                est_dates = self.trading_days[est_start:est_end]
                evt_dates = self.trading_days[post_start:post_end]

                p_est = [ticker_map.get(d) for d in est_dates]
                p_evt = [ticker_map.get(d) for d in evt_dates]

                if any(p is None for p in p_est) or any(p is None for p in p_evt):
                    # Incomplete ticker prices, fallback to index
                    r_bar = float(np.mean(est_returns))
                    ar = aspi_evt_returns - r_bar
                    raw_car = float(np.sum(ar))
                else:
                    r_i_est = np.diff(p_est) / np.array(p_est[:-1])
                    r_m_est = est_returns[1:]
                    var_m = np.var(r_m_est, ddof=1)
                    if var_m > 1e-12:
                        beta = float(np.cov(r_i_est, r_m_est)[0, 1] / var_m)
                    else:
                        beta = 0.0
                    alpha = float(np.mean(r_i_est) - beta * np.mean(r_m_est))

                    # Event window abnormal returns
                    r_i_evt = np.diff([p_est[-1]] + p_evt) / np.array([p_est[-1]] + p_evt[:-1])
                    ar = r_i_evt - (alpha + beta * aspi_evt_returns)
                    raw_car = float(np.sum(ar))
            except Exception:
                r_bar = float(np.mean(est_returns))
                ar = aspi_evt_returns - r_bar
                raw_car = float(np.sum(ar))

        # Clamp CAR to [-10%, +10%] to remove outliers from noisy data
        clamped_car = float(np.clip(raw_car, -self.car_clip, self.car_clip))
        return round(clamped_car, 6)

    def calculate_aspi_return(
        self,
        event_date: Union[str, date, datetime],
        horizon: int = 1,
    ) -> Optional[float]:
        """Compute simple ASPI return from event day t0 to t0 + horizon."""
        mapped_date, t0 = self.get_event_trading_index(event_date)
        if t0 is None:
            return None

        target_idx = t0 + horizon
        if target_idx >= len(self.closes):
            return None

        c0 = self.closes[t0]
        c_h = self.closes[target_idx]
        if c0 <= 0:
            return None

        ret = (c_h - c0) / c0
        return round(float(ret), 6)

    def calculate_all_metrics(
        self,
        ticker_or_index: Optional[str],
        event_date: Union[str, date, datetime],
    ) -> Dict[str, Optional[float]]:
        """Calculate car_1d, car_2d, car_5d, car_10d, aspi_return_1d, aspi_return_5d."""
        return {
            "car_1d": self.calculate_car(ticker_or_index, event_date, horizon=1),
            "car_2d": self.calculate_car(ticker_or_index, event_date, horizon=2),
            "car_5d": self.calculate_car(ticker_or_index, event_date, horizon=5),
            "car_10d": self.calculate_car(ticker_or_index, event_date, horizon=10),
            "aspi_return_1d": self.calculate_aspi_return(event_date, horizon=1),
            "aspi_return_5d": self.calculate_aspi_return(event_date, horizon=5),
        }


# Module-level shared calculator singleton
_shared_calculator: Optional[CARCalculator] = None


def get_shared_calculator(db_path: Optional[Union[str, Path]] = None) -> CARCalculator:
    """Retrieve or initialize shared CARCalculator instance."""
    global _shared_calculator
    target_path = Path(db_path) if db_path is not None else get_default_db_path()
    if _shared_calculator is None or _shared_calculator.db_path != target_path:
        _shared_calculator = CARCalculator(db_path=target_path)
    return _shared_calculator


def calculate_car(
    ticker_or_index: Optional[str],
    event_date: Union[str, date, datetime],
    horizon: int = 1,
    db_path: Optional[Union[str, Path]] = None,
) -> Optional[float]:
    """Calculate Cumulative Abnormal Return (CAR) for given ticker/index and horizon.
    
    Parameters
    ----------
    ticker_or_index : Optional[str]
        Ticker or None for ASPI index-level return.
    event_date : Union[str, date, datetime]
        Date or timestamp of event.
    horizon : int
        Horizon in trading days post-event (default: 1).
    db_path : Optional[str | Path]
        Path to SQLite database.

    Returns
    -------
    Optional[float]
        CAR clamped to [-10%, +10%] or None if insufficient data.
    """
    calc = get_shared_calculator(db_path)
    return calc.calculate_car(ticker_or_index, event_date, horizon=horizon)
