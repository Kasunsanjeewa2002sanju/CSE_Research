"""Unit tests for CSE Live Ingestion Parser using recorded fixtures only."""

import json
import os
import pytest
from datetime import datetime

from cse_live.parser import CSEDataParser
from cse_live.models import MarketStatusType

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "cse")


def load_fixture(filename: str):
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_parse_market_status_fixture():
    data = load_fixture("market_status.json")
    status = CSEDataParser.parse_market_status(data)
    assert status.status == MarketStatusType.OPENING_AUCTION
    assert not status.is_open


def test_parse_aspi_chart_intraday_fixture():
    data = load_fixture("aspi_intraday_chart.json")
    points = CSEDataParser.parse_chart_data_intraday(data)
    assert len(points) >= 1
    assert points[0].value == 20059.42
    assert points[0].timestamp.year == 2026


def test_parse_aspi_daily_bars_5d_fixture():
    data = load_fixture("aspi_daily_bars_5d.json")
    bars = CSEDataParser.parse_chart_data_daily(data)
    assert len(bars) == 5
    assert bars[-1].close == 20087.86
    assert round(bars[-1].percent_change, 2) == -0.48


def test_parse_all_sectors_asi_fixture():
    data = load_fixture("all_sectors_asi.json")
    asi = CSEDataParser.parse_all_sectors_asi(data)
    assert asi is not None
    assert asi["value"] == 20059.42
    assert asi["previous_close"] == 20059.42
    assert asi["change"] == 0.0


def test_parse_sp20_daily_bars_5d_fixture():
    data = load_fixture("sp20_daily_bars_5d.json")
    bars = CSEDataParser.parse_chart_data_daily(data)
    assert len(bars) == 5
    assert bars[-1].close == 5700.75


def test_parse_websocket_stomp_session_fixture():
    data = load_fixture("websocket_stomp_session.json")
    aspi_tick = CSEDataParser.parse_aspi_tick(data["aspi"])
    assert aspi_tick["value"] == 20059.42
    assert aspi_tick["change"] == 0.0
    assert aspi_tick["previous_close"] == 20059.42

    summary = CSEDataParser.parse_summary(data["summary"])
    assert summary["turnover_lkr"] == 0.0
    assert summary["shares_traded"] == 0
    assert summary["trades_count"] == 0
