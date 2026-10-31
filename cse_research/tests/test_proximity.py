"""Unit and Integration Tests for Stage 4 Event Calendar & Proximity Calculator."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure cse_research/src is on sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cse.news.event_extractor import (
    compute_direction,
    extract_event_mentions,
    extract_stage,
)
from cse.news.holiday_calendar import (
    is_trading_day,
    next_trading_day,
    previous_trading_day,
    trading_days_between,
)
from cse.news.proximity_calculator import (
    calculate_proximity_features,
    compute_days_to_next,
    is_in_window_0_7,
    is_in_window_0_30,
    load_event_calendar,
)


def test_election_in_3_days_trading_days() -> None:
    """Requirement 5: 'Election in 3 days' (news date 2026-11-12, election 2026-11-15)
    Trading days count should be ~2.0 (Thu 12 and Fri 13 are trading days; Sat 14 & Sun 15 are weekend).
    """
    news_date = "2026-11-12"
    election_date = "2026-11-15"

    # Direct calendar verification
    t_days = trading_days_between(news_date, election_date)
    assert t_days == 2, f"Expected 2 trading days between 2026-11-12 and 2026-11-15, got {t_days}"

    # compute_days_to_next with 'election' type
    days_to_next = compute_days_to_next("election", news_date=news_date)
    assert abs(days_to_next - 2.0) < 1e-4, f"Expected days_to_next ≈ 2.0, got {days_to_next}"

    # Full proximity features from headline
    feats = calculate_proximity_features("Election in 3 days", news_date=news_date)
    assert abs(feats["days_to_next_known_event"] - 2.0) < 1e-4
    assert feats["in_window_0_7"] == 1.0
    assert feats["in_window_0_30"] == 1.0
    assert feats["event_type_confidence"] >= 0.85
    assert feats["fallback_used"] is False


def test_election_in_60_days_trading_days() -> None:
    """Requirement 5: 'Election in 60 days' -> days_to_next ≈ 55.0 (trading days).
    For election scheduled 2026-11-15, news date 2026-08-31 has exactly 55 trading days.
    """
    news_date = "2026-08-31"
    election_date = "2026-11-15"

    # Verify trading days
    t_days = trading_days_between(news_date, election_date)
    assert abs(t_days - 55) <= 2, f"Expected ~55 trading days, got {t_days}"

    days_to_next = compute_days_to_next("election", news_date=news_date)
    assert abs(days_to_next - 55.0) <= 2.0, f"Expected days_to_next ≈ 55.0, got {days_to_next}"

    feats = calculate_proximity_features("Election in 60 days", news_date=news_date)
    assert abs(feats["days_to_next_known_event"] - 55.0) <= 2.0
    assert feats["in_window_0_7"] == 0.0
    assert feats["in_window_0_30"] == 0.0


def test_news_with_no_event_mentioned_fallback() -> None:
    """Requirement 5: News with no event mentioned -> fallback to nearest calendar event."""
    generic_headline = "Local beverage manufacturer inaugurates modernized bottling plant in Seethawaka"
    news_date = "2026-03-01"

    mentions = extract_event_mentions(generic_headline)
    assert len(mentions) == 0, f"Generic headline should have no event mentions, got {mentions}"

    feats = calculate_proximity_features(generic_headline, news_date=news_date)
    assert feats["fallback_used"] is True
    # The nearest event after 2026-03-01 is CBSL monetary policy on 2026-03-26 or IMF review on 2026-03-19
    assert feats["days_to_next_known_event"] >= 0.0
    assert feats["event_type_confidence"] == 0.0
    assert feats["category"] == "general"


def test_event_is_today_returns_zero() -> None:
    """Event on the same date as news returns 0.0."""
    same_day_date = "2026-11-15"
    days_to_next = compute_days_to_next("election", news_date=same_day_date)
    assert days_to_next == 0.0

    assert is_in_window_0_7(days_to_next) == 1.0
    assert is_in_window_0_30(days_to_next) == 1.0


def test_event_in_past_returns_negative() -> None:
    """If all events of that type are in past, returns negative trading days to most recent."""
    mini_calendar = [
        {"date": "2025-01-15", "type": "election", "category": "election", "importance": 1.0}
    ]
    news_date = "2025-01-20"
    days_to_next = compute_days_to_next("election", news_date=news_date, calendar=mini_calendar)
    assert days_to_next < 0.0, f"Expected negative days for past event, got {days_to_next}"
    assert is_in_window_0_7(days_to_next) == 0.0
    assert is_in_window_0_30(days_to_next) == 0.0


def test_holiday_calendar_rules() -> None:
    """Test Sri Lanka CSE trading calendar rules for weekends and holidays."""
    # Weekends
    assert is_trading_day("2026-11-14") is False  # Saturday
    assert is_trading_day("2026-11-15") is False  # Sunday

    # Sri Lankan Public / Bank holidays
    assert is_trading_day("2026-02-04") is False  # National Day
    assert is_trading_day("2026-04-14") is False  # Sinhala & Tamil New Year
    assert is_trading_day("2026-05-01") is False  # May Day
    assert is_trading_day("2026-12-25") is False  # Christmas Day

    # Regular trading days
    assert is_trading_day("2026-11-12") is True   # Thursday
    assert is_trading_day("2026-11-13") is True   # Friday

    # Trading days between reverse symmetry
    d1 = "2026-01-05"
    d2 = "2026-01-20"
    count_fwd = trading_days_between(d1, d2)
    count_rev = trading_days_between(d2, d1)
    assert count_fwd > 0
    assert count_rev == -count_fwd


def test_window_thresholds() -> None:
    """Verify window functions is_in_window_0_7 and is_in_window_0_30 boundaries."""
    assert is_in_window_0_7(0.0) == 1.0
    assert is_in_window_0_7(7.0) == 1.0
    assert is_in_window_0_7(7.1) == 0.0
    assert is_in_window_0_7(-0.5) == 0.0

    assert is_in_window_0_30(0.0) == 1.0
    assert is_in_window_0_30(15.0) == 1.0
    assert is_in_window_0_30(30.0) == 1.0
    assert is_in_window_0_30(30.5) == 0.0
    assert is_in_window_0_30(-1.0) == 0.0


def test_event_extractor_categories_and_stages() -> None:
    """Verify rule-based and keyword extraction matches requirements."""
    # Election
    e_m = extract_event_mentions("Presidential election poll announced for November")
    assert len(e_m) > 0
    assert e_m[0]["category"] == "election"
    assert e_m[0]["calendar_type"] in ("presidential_election", "election")

    # Fiscal / Budget
    b_m = extract_event_mentions("Finance Minister presents annual national budget and fiscal taxation bill")
    assert len(b_m) > 0
    assert b_m[0]["category"] == "fiscal"
    assert b_m[0]["calendar_type"] == "budget"

    # Monetary / CBSL
    m_m = extract_event_mentions("Central Bank reduces policy interest rate by 50 basis points")
    assert len(m_m) > 0
    assert m_m[0]["category"] == "monetary"
    assert m_m[0]["calendar_type"] == "monetary_policy"
    assert m_m[0]["direction"] > 0.0  # Rate cut is positive

    # IMF
    i_m = extract_event_mentions("IMF executive board approves fourth review tranche bailout")
    assert len(i_m) > 0
    assert i_m[0]["category"] == "imf"
    assert i_m[0]["calendar_type"] == "imf_review"
    assert i_m[0]["direction"] > 0.0

    # Stage = result
    res_m = extract_event_mentions("Election results finalized as ruling party won majority")
    assert len(res_m) > 0
    assert res_m[0]["stage"] == "result"
