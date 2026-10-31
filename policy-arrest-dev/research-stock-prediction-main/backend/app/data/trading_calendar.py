from typing import List, Optional, Tuple
import bisect
import pandas as pd

class TradingCalendar:
    """
    Constructs and queries the active CSE trading calendar derived strictly
    from actual historical stock market sessions. Does NOT assume all weekdays are trading days.
    """
    def __init__(self, trading_dates: List[str]):
        # Store sorted unique dates in ISO format 'YYYY-MM-DD'
        self.trading_dates: List[str] = sorted(list(set(d for d in trading_dates if isinstance(d, str) and len(d) == 10)))
        self._date_set = set(self.trading_dates)
        self._date_to_idx = {d: i for i, d in enumerate(self.trading_dates)}

    def is_trading_day(self, date_str: str) -> bool:
        """Check if date is a verified active CSE trading day."""
        return date_str in self._date_set

    def get_index(self, date_str: str) -> Optional[int]:
        """Return integer index of trading day, or None."""
        return self._date_to_idx.get(date_str)

    def get_date_by_index(self, idx: int) -> Optional[str]:
        """Return date string for a given integer trading day index."""
        if 0 <= idx < len(self.trading_dates):
            return self.trading_dates[idx]
        return None

    def align_to_trading_day(self, date_str: str) -> Tuple[str, str, int]:
        """
        Align a target date to a CSE trading session.
        Returns:
            (aligned_date, alignment_type, calendar_lag_days)
            alignment_type: 'Same-Day Trading' or 'Next-Session (Weekend/Holiday)'
        """
        if self.is_trading_day(date_str):
            return date_str, "Same-Day Trading", 0

        # Bisect to find next trading day strictly greater than date_str
        pos = bisect.bisect_right(self.trading_dates, date_str)
        if pos < len(self.trading_dates):
            next_date = self.trading_dates[pos]
            lag = (pd.to_datetime(next_date) - pd.to_datetime(date_str)).days
            return next_date, "Next-Session (Weekend/Holiday)", max(1, lag)
        
        # If beyond latest available trading date, return the input date as fallback
        return date_str, "Unmatched (Beyond Historical Range)", 0

    def get_offset_date(self, base_date: str, offset: int) -> Optional[str]:
        """
        Get the trading date that is `offset` trading days away from base_date.
        Offset can be negative (pre-event) or positive (post-event).
        """
        idx = self.get_index(base_date)
        if idx is None:
            aligned_date, _, _ = self.align_to_trading_day(base_date)
            idx = self.get_index(aligned_date)
            if idx is None:
                return None
                
        target_idx = idx + offset
        if 0 <= target_idx < len(self.trading_dates):
            return self.trading_dates[target_idx]
        return None
