"""Sri Lanka / Colombo Stock Exchange (CSE) Trading & Holiday Calendar (2023-2027).

Observes:
- Saturdays & Sundays (regular weekend market closures)
- Monthly Sri Lankan Full Moon Poya Days (Mercantile & Bank holidays)
- Statutory Public and Commercial Bank Holidays observed by CSE:
  Tamil Thai Pongal, National Day, Mahasivarathri, Id Ul-Fitr, Sinhala & Tamil New Year,
  Good Friday, May Day, Day following Vesak, Poson Poya, Id-Ul-Alha, Milad-Un-Nabi,
  Deepavali, Christmas Day.

Provides:
- is_trading_day(d) -> bool
- trading_days_between(d1, d2) -> int (signed: negative if d1 > d2)
- next_trading_day(d) -> date
- previous_trading_day(d) -> date
- get_trading_days(start_date, end_date) -> list[date]
"""

from __future__ import annotations

import bisect
from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional, Set, Union


# CSE Market Statutory & Poya Holidays (2023 - 2027)
CSE_HOLIDAYS_2023_2027: Set[date] = {
    # --- 2023 ---
    date(2023, 1, 6),    # Duruthu Full Moon Poya
    date(2023, 1, 15),   # Tamil Thai Pongal (Sunday)
    date(2023, 1, 16),   # Thai Pongal additional bank holiday
    date(2023, 2, 4),    # National Day
    date(2023, 2, 5),    # Navam Full Moon Poya
    date(2023, 2, 18),   # Mahasivarathri Day
    date(2023, 3, 6),    # Medin Full Moon Poya
    date(2023, 4, 5),    # Bak Full Moon Poya
    date(2023, 4, 7),    # Good Friday
    date(2023, 4, 13),   # Day prior to Sinhala & Tamil New Year
    date(2023, 4, 14),   # Sinhala & Tamil New Year Day
    date(2023, 4, 22),   # Id Ul-Fitr
    date(2023, 5, 1),    # May Day
    date(2023, 5, 5),    # Vesak Full Moon Poya
    date(2023, 5, 6),    # Day following Vesak Poya
    date(2023, 6, 3),    # Poson Full Moon Poya
    date(2023, 6, 29),   # Id-Ul-Alha
    date(2023, 7, 3),    # Esala Full Moon Poya
    date(2023, 8, 1),    # Nikini Full Moon Poya
    date(2023, 8, 30),   # Adhi Nikini Full Moon Poya
    date(2023, 9, 28),   # Milad-Un-Nabi
    date(2023, 9, 29),   # Binara Full Moon Poya
    date(2023, 10, 28),  # Vap Full Moon Poya
    date(2023, 11, 12),  # Deepavali
    date(2023, 11, 27),  # Il Full Moon Poya
    date(2023, 12, 25),  # Christmas Day
    date(2023, 12, 26),  # Unduvap Full Moon Poya

    # --- 2024 ---
    date(2024, 1, 15),   # Tamil Thai Pongal
    date(2024, 1, 25),   # Duruthu Full Moon Poya
    date(2024, 2, 4),    # National Day
    date(2024, 2, 23),   # Navam Full Moon Poya
    date(2024, 3, 8),    # Mahasivarathri Day
    date(2024, 3, 24),   # Medin Full Moon Poya
    date(2024, 3, 29),   # Good Friday
    date(2024, 4, 11),   # Id Ul-Fitr
    date(2024, 4, 12),   # Day prior to Sinhala & Tamil New Year
    date(2024, 4, 13),   # Sinhala & Tamil New Year Day
    date(2024, 4, 23),   # Bak Full Moon Poya Day
    date(2024, 5, 1),    # May Day
    date(2024, 5, 23),   # Vesak Full Moon Poya Day
    date(2024, 5, 24),   # Day following Vesak Poya
    date(2024, 6, 17),   # Id-Ul-Alha
    date(2024, 6, 21),   # Poson Full Moon Poya Day
    date(2024, 7, 20),   # Esala Full Moon Poya Day
    date(2024, 8, 19),   # Nikini Full Moon Poya Day
    date(2024, 9, 16),   # Milad-Un-Nabi
    date(2024, 9, 17),   # Binara Full Moon Poya Day
    date(2024, 10, 17),  # Vap Full Moon Poya Day
    date(2024, 10, 31),  # Deepavali
    date(2024, 11, 14),  # Parliamentary General Election Special Holiday
    date(2024, 11, 15),  # Il Full Moon Poya Day
    date(2024, 12, 14),  # Unduvap Full Moon Poya Day
    date(2024, 12, 25),  # Christmas Day

    # --- 2025 ---
    date(2025, 1, 13),   # Duruthu Full Moon Poya
    date(2025, 1, 14),   # Tamil Thai Pongal
    date(2025, 2, 4),    # National Day
    date(2025, 2, 12),   # Navam Full Moon Poya
    date(2025, 2, 26),   # Mahasivarathri Day
    date(2025, 3, 13),   # Medin Full Moon Poya
    date(2025, 3, 31),   # Id Ul-Fitr
    date(2025, 4, 11),   # Day prior to Sinhala & Tamil New Year
    date(2025, 4, 14),   # Sinhala & Tamil New Year Day
    date(2025, 4, 18),   # Good Friday
    date(2025, 5, 1),    # May Day
    date(2025, 5, 12),   # Vesak Full Moon Poya Day
    date(2025, 5, 13),   # Day following Vesak Poya
    date(2025, 6, 6),    # Id-Ul-Alha
    date(2025, 6, 10),   # Poson Full Moon Poya Day
    date(2025, 7, 10),   # Esala Full Moon Poya Day
    date(2025, 8, 8),    # Nikini Full Moon Poya Day
    date(2025, 9, 5),    # Milad-Un-Nabi
    date(2025, 9, 7),    # Binara Full Moon Poya Day
    date(2025, 10, 6),   # Vap Full Moon Poya Day
    date(2025, 10, 20),  # Deepavali
    date(2025, 11, 5),   # Il Full Moon Poya Day
    date(2025, 12, 4),   # Unduvap Full Moon Poya Day
    date(2025, 12, 25),  # Christmas Day

    # --- 2026 ---
    date(2026, 1, 2),    # Duruthu Full Moon Poya
    date(2026, 1, 15),   # Tamil Thai Pongal
    date(2026, 2, 1),    # Navam Full Moon Poya (Sunday)
    date(2026, 2, 4),    # National Day
    date(2026, 2, 17),   # Mahasivarathri Day
    date(2026, 3, 3),    # Medin Full Moon Poya
    date(2026, 3, 20),   # Id Ul-Fitr
    date(2026, 4, 2),    # Bak Full Moon Poya
    date(2026, 4, 3),    # Good Friday
    date(2026, 4, 13),   # Day prior to Sinhala & Tamil New Year
    date(2026, 4, 14),   # Sinhala & Tamil New Year Day
    date(2026, 5, 1),    # May Day
    date(2026, 5, 27),   # Id-Ul-Alha
    date(2026, 5, 30),   # Vesak Full Moon Poya (Saturday)
    date(2026, 5, 31),   # Day following Vesak Poya (Sunday)
    date(2026, 6, 29),   # Poson Full Moon Poya
    date(2026, 7, 28),   # Esala Full Moon Poya
    date(2026, 8, 26),   # Milad-Un-Nabi
    date(2026, 8, 27),   # Nikini Full Moon Poya
    date(2026, 9, 26),   # Binara Full Moon Poya (Saturday)
    date(2026, 10, 25),  # Vap Full Moon Poya (Sunday)
    date(2026, 11, 8),   # Deepavali (Sunday)
    date(2026, 11, 24),  # Il Full Moon Poya
    date(2026, 12, 24),  # Unduvap Full Moon Poya
    date(2026, 12, 25),  # Christmas Day

    # --- 2027 ---
    date(2027, 1, 15),   # Tamil Thai Pongal
    date(2027, 1, 22),   # Duruthu Full Moon Poya
    date(2027, 2, 4),    # National Day
    date(2027, 2, 20),   # Navam Full Moon Poya (Saturday)
    date(2027, 3, 7),    # Mahasivarathri Day (Sunday)
    date(2027, 3, 10),   # Id Ul-Fitr
    date(2027, 3, 22),   # Medin Full Moon Poya
    date(2027, 3, 26),   # Good Friday
    date(2027, 4, 13),   # Day prior to Sinhala & Tamil New Year
    date(2027, 4, 14),   # Sinhala & Tamil New Year Day
    date(2027, 4, 20),   # Bak Full Moon Poya
    date(2027, 5, 1),    # May Day (Saturday)
    date(2027, 5, 17),   # Id-Ul-Alha
    date(2027, 5, 20),   # Vesak Full Moon Poya
    date(2027, 5, 21),   # Day following Vesak Poya
    date(2027, 6, 19),   # Poson Full Moon Poya (Saturday)
    date(2027, 7, 18),   # Esala Full Moon Poya (Sunday)
    date(2027, 8, 16),   # Milad-Un-Nabi
    date(2027, 8, 17),   # Nikini Full Moon Poya
    date(2027, 9, 15),   # Binara Full Moon Poya
    date(2027, 10, 15),  # Vap Full Moon Poya
    date(2027, 10, 29),  # Deepavali
    date(2027, 11, 13),  # Il Full Moon Poya (Saturday)
    date(2027, 12, 13),  # Unduvap Full Moon Poya
    date(2027, 12, 25),  # Christmas Day (Saturday)
}


def _parse_date(d: Union[str, date, datetime]) -> date:
    """Normalize str/datetime to datetime.date."""
    if isinstance(d, datetime):
        return d.date()
    elif isinstance(d, date):
        return d
    elif isinstance(d, str):
        # Handle ISO strings like '2026-11-12' or '2026-11-12T10:00:00'
        return date.fromisoformat(d.split("T")[0].split(" ")[0])
    raise TypeError(f"Cannot parse date from type {type(d)}: {d}")


def is_trading_day(d: Union[str, date, datetime], holidays: Optional[Set[date]] = None) -> bool:
    """Check whether date is a valid CSE trading day (not weekend or statutory holiday)."""
    dt = _parse_date(d)
    # 5=Saturday, 6=Sunday
    if dt.weekday() in (5, 6):
        return False
    h_set = holidays if holidays is not None else CSE_HOLIDAYS_2023_2027
    return dt not in h_set


# Precompute all trading days from 2020-01-01 to 2030-12-31 for fast bisect indexing
def _build_trading_calendar_index(
    start_year: int = 2020,
    end_year: int = 2030,
    holidays: Optional[Set[date]] = None,
) -> List[date]:
    h_set = holidays if holidays is not None else CSE_HOLIDAYS_2023_2027
    cur = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    one_day = timedelta(days=1)
    trading_days: List[date] = []

    while cur <= end:
        if cur.weekday() not in (5, 6) and cur not in h_set:
            trading_days.append(cur)
        cur += one_day

    return trading_days


ALL_TRADING_DAYS: List[date] = _build_trading_calendar_index()


def trading_days_between(
    d1: Union[str, date, datetime],
    d2: Union[str, date, datetime],
    trading_days: Optional[List[date]] = None,
) -> int:
    """Compute number of CSE trading days between d1 and d2.

    Returns
    -------
    int
        Count of trading days in [d1, d2).
        If d1 == d2, returns 0.
        If d1 > d2, returns negative count (-trading_days_between(d2, d1)).
    """
    dt1 = _parse_date(d1)
    dt2 = _parse_date(d2)

    if dt1 == dt2:
        return 0

    calendar = trading_days if trading_days is not None else ALL_TRADING_DAYS

    # bisect_left finds the insertion point for dt in sorted trading days
    # (i.e. the index of the first trading day >= dt)
    idx1 = bisect.bisect_left(calendar, dt1)
    idx2 = bisect.bisect_left(calendar, dt2)

    return int(idx2 - idx1)


def next_trading_day(
    d: Union[str, date, datetime],
    include_today: bool = False,
    trading_days: Optional[List[date]] = None,
) -> date:
    """Return next trading day strictly after d (or on/after if include_today=True)."""
    dt = _parse_date(d)
    calendar = trading_days if trading_days is not None else ALL_TRADING_DAYS

    if include_today:
        idx = bisect.bisect_left(calendar, dt)
    else:
        idx = bisect.bisect_right(calendar, dt)

    if idx < len(calendar):
        return calendar[idx]
    # Fallback if beyond precomputed range
    cur = dt + timedelta(days=1)
    while not is_trading_day(cur):
        cur += timedelta(days=1)
    return cur


def previous_trading_day(
    d: Union[str, date, datetime],
    include_today: bool = False,
    trading_days: Optional[List[date]] = None,
) -> date:
    """Return previous trading day strictly before d (or on/before if include_today=True)."""
    dt = _parse_date(d)
    calendar = trading_days if trading_days is not None else ALL_TRADING_DAYS

    if include_today:
        idx = bisect.bisect_right(calendar, dt) - 1
    else:
        idx = bisect.bisect_left(calendar, dt) - 1

    if idx >= 0:
        return calendar[idx]
    cur = dt - timedelta(days=1)
    while not is_trading_day(cur):
        cur -= timedelta(days=1)
    return cur


def get_trading_days(
    start_date: Union[str, date, datetime],
    end_date: Union[str, date, datetime],
    trading_days: Optional[List[date]] = None,
) -> List[date]:
    """Return all trading days in closed interval [start_date, end_date]."""
    s = _parse_date(start_date)
    e = _parse_date(end_date)
    if s > e:
        return []

    calendar = trading_days if trading_days is not None else ALL_TRADING_DAYS
    idx1 = bisect.bisect_left(calendar, s)
    idx2 = bisect.bisect_right(calendar, e)
    return calendar[idx1:idx2]
