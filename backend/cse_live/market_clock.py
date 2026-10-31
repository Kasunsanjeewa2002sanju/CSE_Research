"""Market Clock for Colombo Stock Exchange trading sessions and calendar.

Handles:
- Session states: PRE_OPEN, OPEN, CLOSED, HOLIDAY_OR_NO_TRADING
- Priority resolution: site reported status takes precedence when available
- Schedule: Monday - Friday, 09:30 - 14:30 Asia/Colombo
- Pre-Open: 09:00 - 09:30
- Post-Close statistics capture: 14:30 - 15:30
- Sri Lankan market holidays
"""

from __future__ import annotations

import os
import json
from datetime import datetime, time, date
from typing import Optional, Set
from zoneinfo import ZoneInfo

from cse_live.models import ClockState, COLOMBO_TZ
from cse_live.config import IngestionConfig

# Default statutory/bank/market holidays for Sri Lanka (GRCh/CSE market calendar)
DEFAULT_SRI_LANKAN_HOLIDAYS_2025_2026: Set[date] = {
    # 2025
    date(2025, 1, 13), # Duruthu Full Moon Poya
    date(2025, 1, 14), # Tamil Thai Pongal
    date(2025, 2, 4),  # National Day
    date(2025, 2, 12), # Navam Full Moon Poya
    date(2025, 2, 26), # Mahasivarathri Day
    date(2025, 3, 13), # Medin Full Moon Poya
    date(2025, 3, 31), # Id Ul-Fitr
    date(2025, 4, 11), # Day prior to Sinhala & Tamil New Year Day
    date(2025, 4, 14), # Sinhala & Tamil New Year Day
    date(2025, 4, 18), # Good Friday
    date(2025, 5, 1),  # May Day
    date(2025, 5, 12), # Vesak Full Moon Poya Day
    date(2025, 5, 13), # Day following Vesak Full Moon Poya Day
    date(2025, 6, 10), # Poson Full Moon Poya Day
    date(2025, 12, 25),# Christmas Day
    # 2026
    date(2026, 1, 2),  # Duruthu Full Moon Poya
    date(2026, 1, 15), # Tamil Thai Pongal
    date(2026, 2, 4),  # National Day
    date(2026, 2, 17), # Mahasivarathri Day
    date(2026, 3, 20), # Id Ul-Fitr
    date(2026, 4, 3),  # Good Friday
    date(2026, 4, 13), # Day prior to Sinhala & Tamil New Year Day
    date(2026, 4, 14), # Sinhala & Tamil New Year Day
    date(2026, 5, 1),  # May Day
    date(2026, 5, 30), # Vesak Full Moon Poya Day
    date(2026, 5, 31), # Day following Vesak Full Moon Poya Day
    date(2026, 6, 29), # Poson Full Moon Poya Day
    date(2026, 12, 25),# Christmas Day
}


class MarketClock:
    """Evaluates CSE session operational state and schedules polling cadence."""

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self.config = config or IngestionConfig.from_env()
        self.tz = ZoneInfo(self.config.timezone)

        # Parse trading boundaries
        open_parts = [int(p) for p in self.config.market_open.split(":")]
        close_parts = [int(p) for p in self.config.market_close.split(":")]
        self.open_time = time(open_parts[0], open_parts[1])
        self.close_time = time(close_parts[0], close_parts[1])
        self.pre_open_time = time(9, 0)
        self.post_close_capture_time = time(15, 30)

        self.holidays = set(DEFAULT_SRI_LANKAN_HOLIDAYS_2025_2026)
        if self.config.holiday_file and os.path.exists(self.config.holiday_file):
            self._load_holidays(self.config.holiday_file)

    def _load_holidays(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for d_str in data:
                        self.holidays.add(date.fromisoformat(d_str))
        except Exception:
            pass

    def now(self) -> datetime:
        """Current datetime in Colombo timezone."""
        return datetime.now(self.tz)

    def is_holiday_or_weekend(self, dt: datetime) -> bool:
        """Return True if given datetime falls on a weekend or public holiday."""
        dt_colombo = dt.astimezone(self.tz)
        if dt_colombo.weekday() in (5, 6): # Saturday or Sunday
            return True
        if dt_colombo.date() in self.holidays:
            return True
        return False

    def evaluate_state(
        self,
        dt: Optional[datetime] = None,
        reported_status: Optional[str] = None
    ) -> ClockState:
        """Determine trading state, prioritizing live exchange status when provided."""
        # 1. Prioritize upstream exchange status if provided
        if reported_status:
            clean = reported_status.strip().lower()
            if clean in ("regular trading", "open"):
                return ClockState.OPEN
            if clean in ("opening auction call", "open auction call", "pre-trading", "pre trading"):
                return ClockState.PRE_OPEN
            if clean in ("market closed", "closed", "market close (statistics being finalized)", "halt", "market halted"):
                return ClockState.CLOSED

        # 2. Fall back to calendar and time evaluation
        eval_dt = (dt or self.now()).astimezone(self.tz)
        if self.is_holiday_or_weekend(eval_dt):
            return ClockState.HOLIDAY_OR_NO_TRADING

        current_time = eval_dt.time()
        if self.pre_open_time <= current_time < self.open_time:
            return ClockState.PRE_OPEN
        if self.open_time <= current_time < self.close_time:
            return ClockState.OPEN
        return ClockState.CLOSED

    def get_poll_interval(
        self,
        clock_state: ClockState,
        final_close_captured: bool = False
    ) -> float:
        """Determine poll sleep interval in seconds based on session state."""
        if clock_state == ClockState.OPEN:
            return self.config.poll_interval_open_seconds
        if clock_state == ClockState.PRE_OPEN:
            return max(self.config.poll_interval_open_seconds * 2.0, 10.0)
        if clock_state == ClockState.CLOSED and not final_close_captured:
            # Post-close active capture window until statistics finalized
            return self.config.poll_interval_closed_seconds
        # Long idle when market is closed and final close captured or holiday
        return max(self.config.poll_interval_closed_seconds, 60.0)
