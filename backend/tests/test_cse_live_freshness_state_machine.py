"""Unit tests for Freshness State Machine transitions."""

import pytest
from cse_live.models import ClockState, FreshnessState
from cse_live.scheduler import FreshnessStateMachine


def test_freshness_live_when_open_reachable_and_fresh():
    state = FreshnessStateMachine.evaluate(
        clock_state=ClockState.OPEN,
        source_reachable=True,
        last_tick_age_seconds=15.0,
        stale_threshold_seconds=120.0
    )
    assert state == FreshnessState.LIVE


def test_freshness_delayed_when_open_reachable_but_tick_aging():
    # Between 60s and 120s
    state = FreshnessStateMachine.evaluate(
        clock_state=ClockState.OPEN,
        source_reachable=True,
        last_tick_age_seconds=75.0,
        stale_threshold_seconds=120.0
    )
    assert state == FreshnessState.DELAYED


def test_freshness_stale_when_open_reachable_but_age_exceeds_threshold():
    state = FreshnessStateMachine.evaluate(
        clock_state=ClockState.OPEN,
        source_reachable=True,
        last_tick_age_seconds=150.0,
        stale_threshold_seconds=120.0
    )
    assert state == FreshnessState.STALE


def test_freshness_delayed_when_open_and_source_temporarily_unreachable():
    # Source dropped, but last tick is still recent (< 120s)
    state = FreshnessStateMachine.evaluate(
        clock_state=ClockState.OPEN,
        source_reachable=False,
        last_tick_age_seconds=30.0,
        stale_threshold_seconds=120.0
    )
    assert state == FreshnessState.DELAYED


def test_freshness_stale_when_open_and_source_unreachable_past_threshold():
    state = FreshnessStateMachine.evaluate(
        clock_state=ClockState.OPEN,
        source_reachable=False,
        last_tick_age_seconds=130.0,
        stale_threshold_seconds=120.0
    )
    assert state == FreshnessState.STALE


def test_freshness_closed_when_market_session_closed():
    state = FreshnessStateMachine.evaluate(
        clock_state=ClockState.CLOSED,
        source_reachable=True,
        last_tick_age_seconds=300.0,
        stale_threshold_seconds=120.0
    )
    assert state == FreshnessState.CLOSED


def test_freshness_closed_when_holiday():
    state = FreshnessStateMachine.evaluate(
        clock_state=ClockState.HOLIDAY_OR_NO_TRADING,
        source_reachable=False,
        last_tick_age_seconds=86400.0,
        stale_threshold_seconds=120.0
    )
    assert state == FreshnessState.CLOSED
