"""Tests for CSE Market schemas, validation rules, and recorded fixtures."""

import os
import json
import pytest
from datetime import datetime, timezone
from cse.market.schema import (
    MarketSnapshot,
    MarketStatus,
    MarketStatusType,
    FreshnessState,
    IntradayPoint,
    DailyBar,
    SourceHealth,
    COLOMBO_TZ,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "cse")


def test_market_status_normalization():
    """Verify market status string normalization."""
    status_auction = MarketStatus(raw_status="Opening Auction Call", status="Opening Auction Call")
    assert status_auction.status == MarketStatusType.OPENING_AUCTION
    assert not status_auction.is_open

    status_trading = MarketStatus(raw_status="Regular Trading", status="Regular Trading")
    assert status_trading.status == MarketStatusType.REGULAR_TRADING
    assert status_trading.is_open

    status_closed = MarketStatus(raw_status="Market Closed", status="Market Closed")
    assert status_closed.status == MarketStatusType.MARKET_CLOSED
    assert not status_closed.is_open


def test_market_snapshot_validations():
    """Verify MarketSnapshot field validation and constraints."""
    snap = MarketSnapshot(
        aspi_value=20059.42,
        aspi_change=0.0,
        aspi_percent_change=0.0,
        aspi_previous_close=20059.42,
        sp20_value=5700.75,
        sp20_change=-29.35,
        sp20_percent_change=-0.51,
        sp20_previous_close=5730.10,
        market_turnover=15234567.89,
        shares_traded=1234567,
        total_trades=1234,
        market_status=MarketStatus(raw_status="Opening Auction Call", status="Opening Auction Call"),
        freshness=FreshnessState.LIVE,
        source_timestamp=datetime.now(COLOMBO_TZ),
        source="websocket_stomp"
    )
    assert snap.aspi_value == 20059.42
    assert snap.market_turnover == 15234567.89
    assert snap.shares_traded == 1234567
    assert snap.total_trades == 1234


def test_market_snapshot_inconsistency_fails():
    """Verify validation fails if index change contradicts previous close."""
    with pytest.raises(ValueError, match="ASPI change mismatch"):
        MarketSnapshot(
            aspi_value=20059.42,
            aspi_change=500.0,  # Contradicts prev close of 20059.42!
            aspi_percent_change=2.5,
            aspi_previous_close=20059.42,
            market_turnover=0.0,
            shares_traded=0,
            total_trades=0,
            market_status=MarketStatus(raw_status="Regular Trading", status="Regular Trading"),
            freshness=FreshnessState.LIVE,
            source_timestamp=datetime.now(COLOMBO_TZ),
            source="websocket_stomp"
        )


def test_recorded_fixtures_exist_and_parse():
    """Verify all 8 recorded test fixtures parse properly."""
    expected_files = [
        "market_status.json",
        "aspi_intraday_chart.json",
        "aspi_daily_bars_5d.json",
        "aspi_annual_bars_240d.json",
        "sp20_daily_bars_5d.json",
        "all_sectors_asi.json",
        "aspi_annual_returns.json",
        "websocket_stomp_session.json",
    ]
    for fname in expected_files:
        path = os.path.join(FIXTURES_DIR, fname)
        assert os.path.exists(path), f"Fixture missing: {path}"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data is not None
