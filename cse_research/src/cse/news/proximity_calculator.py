"""Event Proximity Feature Calculator for CSE News.

Computes:
- days_to_next_known_event (using CSE trading calendar, skipping weekends & holidays)
- in_window_0_7 (1.0 if 0 <= days_to_next <= 7, else 0.0)
- in_window_0_30 (1.0 if 0 <= days_to_next <= 30, else 0.0)
- in_window_0_2, in_window_0_15
- event_type_confidence
- fallback to nearest calendar event when headline does not specify an event
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from cse.news.event_extractor import extract_event_mentions
from cse.news.holiday_calendar import (
    _parse_date,
    is_trading_day,
    trading_days_between,
)
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.proximity_calculator")

_DEFAULT_CALENDAR: Optional[List[Dict[str, Any]]] = None


def get_default_calendar_path() -> Path:
    """Resolve default path to event_calendar.json."""
    project_root = find_project_root()
    p1 = project_root / "data" / "event_calendar.json"
    if p1.exists():
        return p1
    p2 = project_root.parent / "data" / "event_calendar.json"
    if p2.exists():
        return p2
    return p1


def load_event_calendar(
    calendar_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Load and cache CSE event calendar from JSON file."""
    global _DEFAULT_CALENDAR
    if calendar_path is None and _DEFAULT_CALENDAR is not None:
        return _DEFAULT_CALENDAR

    path = Path(calendar_path) if calendar_path else get_default_calendar_path()
    if not path.exists():
        logger.warning("Event calendar not found at %s. Returning empty calendar.", path)
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Sort chronologically
            data.sort(key=lambda x: str(x.get("date", "")))
            if calendar_path is None:
                _DEFAULT_CALENDAR = data
            return data
    except Exception as e:
        logger.error("Failed to load event calendar from %s: %s", path, e)
        return []


def _match_event(e: Dict[str, Any], query_type: str) -> bool:
    """Check if calendar event matches query_type."""
    q = query_type.strip().lower()
    e_type = str(e.get("type", "")).lower()
    e_cat = str(e.get("category", "")).lower()
    e_title = str(e.get("title", "")).lower()

    if q == e_type or q == e_cat:
        return True
    if q in e_type or e_type in q:
        return True
    if q in e_title:
        return True
    return False


def compute_days_to_next(
    event_type: Optional[str],
    news_date: Union[str, date, datetime],
    calendar: Optional[List[Dict[str, Any]]] = None,
) -> float:
    """Compute number of trading days from news_date to next known event.

    Rules:
    - Uses TRADING days (skipping weekends, Sri Lankan Poya days, and CSE market holidays).
    - If event date == news_date, returns 0.0.
    - If an upcoming occurrence exists (event_date >= news_date), returns trading days to earliest one.
    - If no upcoming occurrence exists but past occurrences exist, returns negative trading days to most recent one.
    - If event_type is None, empty, or has no matches, falls back to the nearest event across the entire calendar.
    - If calendar is empty, returns -1.0.

    Parameters
    ----------
    event_type : Optional[str]
        Event type/keyword (e.g. 'election', 'budget', 'monetary_policy', 'imf_review').
    news_date : Union[str, date, datetime]
        Date of the news headline.
    calendar : Optional[list of dict]
        List of calendar events. If None, uses production event_calendar.json.

    Returns
    -------
    float
        Signed trading days to event.
    """
    if calendar is None:
        calendar = load_event_calendar()

    if not calendar:
        return -1.0

    cur_dt = _parse_date(news_date)

    # 1. Filter events matching event_type (if provided)
    matched_events: List[Dict[str, Any]] = []
    if event_type and event_type.strip().lower() not in ("none", "not_relevant", "unknown"):
        matched_events = [e for e in calendar if _match_event(e, event_type)]

    # 2. Fallback to full calendar if no event_type or no matching events found
    target_pool = matched_events if matched_events else calendar

    # Separate into upcoming (>= cur_dt) and past (< cur_dt)
    upcoming_events: List[Tuple[date, Dict[str, Any]]] = []
    past_events: List[Tuple[date, Dict[str, Any]]] = []

    for ev in target_pool:
        raw_d = ev.get("date")
        if not raw_d:
            continue
        ev_dt = _parse_date(raw_d)
        if ev_dt >= cur_dt:
            upcoming_events.append((ev_dt, ev))
        else:
            past_events.append((ev_dt, ev))

    # Priority: Next upcoming occurrence
    if upcoming_events:
        upcoming_events.sort(key=lambda x: x[0])
        earliest_dt, _ = upcoming_events[0]
        days = trading_days_between(cur_dt, earliest_dt)
        return float(days)

    # If all in past, use most recent occurrence (negative trading days)
    if past_events:
        past_events.sort(key=lambda x: x[0], reverse=True)
        latest_past_dt, _ = past_events[0]
        days = trading_days_between(cur_dt, latest_past_dt)
        return float(days)

    return -1.0


def is_in_window_0_7(days_to_next: float) -> float:
    """Return 1.0 if 0 <= days_to_next <= 7, else 0.0."""
    return 1.0 if 0.0 <= days_to_next <= 7.0 else 0.0


def is_in_window_0_30(days_to_next: float) -> float:
    """Return 1.0 if 0 <= days_to_next <= 30, else 0.0."""
    return 1.0 if 0.0 <= days_to_next <= 30.0 else 0.0


def is_in_window_0_2(days_to_next: float) -> float:
    """Return 1.0 if 0 <= days_to_next <= 2, else 0.0."""
    return 1.0 if 0.0 <= days_to_next <= 2.0 else 0.0


def is_in_window_0_15(days_to_next: float) -> float:
    """Return 1.0 if 0 <= days_to_next <= 15, else 0.0."""
    return 1.0 if 0.0 <= days_to_next <= 15.0 else 0.0


def calculate_proximity_features(
    headline: str,
    news_date: Optional[Union[str, date, datetime]] = None,
    calendar: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Extract event mentions from headline and calculate trading-day proximity features.

    Parameters
    ----------
    headline : str
        News headline.
    news_date : Optional[Union[str, date, datetime]]
        Date of the news. Defaults to today's date if None.
    calendar : Optional[List[Dict[str, Any]]]
        Custom event calendar list. Defaults to production event_calendar.json.

    Returns
    -------
    dict
        {
            "days_to_next_known_event": float,
            "in_window_0_7": float,
            "in_window_0_30": float,
            "in_window_0_2": float,
            "in_window_0_15": float,
            "event_type": str,
            "event_type_confidence": float,
            "category": str,
            "stage": str,
            "direction": float,
            "fallback_used": bool,
        }
    """
    if news_date is None:
        news_date = date.today().isoformat()

    mentions = extract_event_mentions(headline)
    if mentions:
        top_mention = mentions[0]
        event_type = top_mention.get("calendar_type") or top_mention.get("event_type")
        confidence = float(top_mention.get("confidence", 0.0))
        category = str(top_mention.get("category", "unknown"))
        stage = str(top_mention.get("stage", "none"))
        direction = float(top_mention.get("direction", 0.0))
        fallback_used = False
    else:
        event_type = None
        confidence = 0.0
        category = "general"
        stage = "none"
        from cse.news.event_extractor import compute_direction
        direction = compute_direction(headline)
        fallback_used = True

    days_next = compute_days_to_next(
        event_type=event_type,
        news_date=news_date,
        calendar=calendar,
    )

    return {
        "days_to_next_known_event": float(days_next),
        "in_window_0_7": float(is_in_window_0_7(days_next)),
        "in_window_0_30": float(is_in_window_0_30(days_next)),
        "in_window_0_2": float(is_in_window_0_2(days_next)),
        "in_window_0_15": float(is_in_window_0_15(days_next)),
        "event_type": str(event_type if event_type else "fallback_nearest"),
        "event_type_confidence": float(confidence),
        "category": category,
        "stage": stage,
        "direction": float(direction),
        "fallback_used": bool(fallback_used),
    }


class ProximityCalculator:
    """Class wrapper for event calendar proximity calculations."""

    def __init__(self, calendar_path: Optional[Union[str, Path]] = None) -> None:
        self.calendar_path = calendar_path
        self.calendar = load_event_calendar(calendar_path)

    def compute_days_to_next(
        self,
        event_type: Optional[str],
        news_date: Union[str, date, datetime],
    ) -> float:
        return compute_days_to_next(event_type, news_date, self.calendar)

    def is_in_window_0_7(self, days_to_next: float) -> float:
        return is_in_window_0_7(days_to_next)

    def is_in_window_0_30(self, days_to_next: float) -> float:
        return is_in_window_0_30(days_to_next)

    def is_in_window_0_2(self, days_to_next: float) -> float:
        return is_in_window_0_2(days_to_next)

    def is_in_window_0_15(self, days_to_next: float) -> float:
        return is_in_window_0_15(days_to_next)

    def calculate_proximity_features(
        self,
        headline: str,
        news_date: Optional[Union[str, date, datetime]] = None,
    ) -> Dict[str, Any]:
        return calculate_proximity_features(headline, news_date, self.calendar)


_PROXIMITY_CALCULATOR: Optional[ProximityCalculator] = None


def get_proximity_calculator(calendar_path: Optional[Union[str, Path]] = None) -> ProximityCalculator:
    """Return singleton ProximityCalculator instance."""
    global _PROXIMITY_CALCULATOR
    if _PROXIMITY_CALCULATOR is None or calendar_path is not None:
        _PROXIMITY_CALCULATOR = ProximityCalculator(calendar_path)
    return _PROXIMITY_CALCULATOR
