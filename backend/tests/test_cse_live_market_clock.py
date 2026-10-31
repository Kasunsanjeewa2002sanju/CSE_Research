"""Unit tests for Market Clock (weekday open, closed, weekend, holiday, boundary seconds)."""

from datetime import datetime
from zoneinfo import ZoneInfo
import pytest

from cse_live.market_clock import MarketClock
from cse_live.models import ClockState, COLOMBO_TZ


def test_market_clock_weekday_regular_trading():
    clock = MarketClock()
    # Wednesday 2026-10-21 at 11:30:00 Colombo time
    dt = datetime(2026, 10, 21, 11, 30, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt) == ClockState.OPEN


def test_market_clock_weekday_pre_open():
    clock = MarketClock()
    # Wednesday 2026-10-21 at 09:15:00 Colombo time
    dt = datetime(2026, 10, 21, 9, 15, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt) == ClockState.PRE_OPEN


def test_market_clock_weekday_post_close():
    clock = MarketClock()
    # Wednesday 2026-10-21 at 15:00:00 Colombo time
    dt = datetime(2026, 10, 21, 15, 0, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt) == ClockState.CLOSED


def test_market_clock_weekday_before_pre_open():
    clock = MarketClock()
    # Wednesday 2026-10-21 at 08:30:00 Colombo time
    dt = datetime(2026, 10, 21, 8, 30, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt) == ClockState.CLOSED


def test_market_clock_weekend():
    clock = MarketClock()
    # Saturday 2026-10-24 at 11:00:00 Colombo time
    dt_sat = datetime(2026, 10, 24, 11, 0, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_sat) == ClockState.HOLIDAY_OR_NO_TRADING

    # Sunday 2026-10-25 at 11:00:00 Colombo time
    dt_sun = datetime(2026, 10, 25, 11, 0, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_sun) == ClockState.HOLIDAY_OR_NO_TRADING


def test_market_clock_holiday():
    clock = MarketClock()
    # Sinhala & Tamil New Year Day (2026-04-14)
    dt_holiday = datetime(2026, 4, 14, 11, 0, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_holiday) == ClockState.HOLIDAY_OR_NO_TRADING


def test_market_clock_boundary_seconds():
    clock = MarketClock()
    # 09:29:59 is PRE_OPEN
    dt_pre = datetime(2026, 10, 21, 9, 29, 59, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_pre) == ClockState.PRE_OPEN

    # 09:30:00 is OPEN
    dt_open = datetime(2026, 10, 21, 9, 30, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_open) == ClockState.OPEN

    # 14:29:59 is OPEN
    dt_late = datetime(2026, 10, 21, 14, 29, 59, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_late) == ClockState.OPEN

    # 14:30:00 is CLOSED
    dt_close = datetime(2026, 10, 21, 14, 30, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_close) == ClockState.CLOSED


def test_market_clock_site_reported_status_priority():
    clock = MarketClock()
    # Even if local time says closed, if exchange explicitly says Regular Trading, report OPEN
    dt_night = datetime(2026, 10, 21, 23, 0, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_night, reported_status="Regular Trading") == ClockState.OPEN

    # Even if local time says open, if exchange says Market Closed (e.g. unexpected emergency holiday), report CLOSED
    dt_day = datetime(2026, 10, 21, 11, 0, 0, tzinfo=COLOMBO_TZ)
    assert clock.evaluate_state(dt=dt_day, reported_status="Market Closed") == ClockState.CLOSED
