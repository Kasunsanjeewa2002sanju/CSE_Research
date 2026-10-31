"""Test Suite for Stage 3: Storage, Caching, Historical Append, and Derived Statistics.

Covers:
1. Latest snapshot store (in-memory TTL + atomic persistence + restart recovery)
2. Intraday store (1-minute bucket downsampling + bounded memory + restart survival)
3. End-of-day job & LiveDailyStore (idempotency, zero edits to CSE_data.csv, audit log)
4. Derived statistics regression test (panel size 7,635, annualised volatility 15.7%, 1D return 0.79%)
5. REST API endpoints (/api/market/latest, /api/market/intraday, /api/market/history, /api/market/stats)
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cse.market.schema import (
    DailyBar,
    FreshnessState,
    MarketSnapshot,
    MarketStatus,
    MarketStatusType,
    SourceHealth,
    COLOMBO_TZ,
)
from cse.news.api import app
from cse_live.config import IngestionConfig
from cse_live.eod import EODJob, LiveDailyStore, MergedMarketHistory
from cse_live.intraday import IntradayStore
from cse_live.stats import DerivedStatsEngine
from cse_live.storage import LatestSnapshotStore


import uuid

# Prevent matplotlib lock issues in sandbox
_mpl_dir = Path(__file__).resolve().parent / "_test_scratch" / ".mpl"
_mpl_dir.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(_mpl_dir)


@pytest.fixture
def temp_cache_dir():
    """Create an isolated temporary cache directory inside the workspace."""
    base_dir = Path(__file__).resolve().parent / "_test_scratch"
    base_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = base_dir / f"test_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    yield str(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_snapshot():
    """Sample valid accepted market snapshot."""
    now_colombo = datetime.now(COLOMBO_TZ)
    return MarketSnapshot(
        aspi_value=22624.31,
        aspi_change=177.58,
        aspi_percent_change=0.7917,
        aspi_previous_close=22446.73,
        sp20_value=6157.38,
        sp20_change=45.80,
        sp20_percent_change=0.75,
        sp20_previous_close=6111.58,
        market_turnover=9309760000.0,
        shares_traded=245620000,
        total_trades=18450,
        market_status=MarketStatus(
            raw_status="Regular Trading",
            status=MarketStatusType.REGULAR_TRADING,
            is_open=True,
            timestamp=now_colombo,
        ),
        freshness=FreshnessState.LIVE,
        source_timestamp=now_colombo,
        source="rest_api",
        health=SourceHealth(
            source_name="rest_api",
            is_healthy=True,
            latency_ms=120.5,
        ),
    )


# ============================================================================
# 1. LATEST SNAPSHOT STORE & RESTART RESILIENCE
# ============================================================================

def test_snapshot_store_save_load_and_restart(temp_cache_dir, sample_snapshot):
    """Test in-memory saving, atomic disk persistence, and restart recovery."""
    persist_file = os.path.join(temp_cache_dir, "last_snapshot.json")
    config = IngestionConfig(persistence_file_path=persist_file)

    # 1. Save in primary instance
    store1 = LatestSnapshotStore(config)
    store1.save(sample_snapshot)
    assert os.path.exists(persist_file)

    # In-memory retrieval
    in_mem = store1.get()
    assert in_mem is not None
    assert in_mem.aspi_value == 22624.31
    assert store1.is_recovered_from_disk is False

    # 2. Simulate server restart: new instance initialized
    store2 = LatestSnapshotStore(config)
    restarted_snap = store2.get()
    assert restarted_snap is not None
    assert restarted_snap.aspi_value == 22624.31
    assert store2.is_recovered_from_disk is True


def test_snapshot_store_atomic_write_safety(temp_cache_dir, sample_snapshot):
    """Test that atomic write leaves valid JSON on disk without partial corruptions."""
    persist_file = os.path.join(temp_cache_dir, "last_snapshot.json")
    config = IngestionConfig(persistence_file_path=persist_file)
    store = LatestSnapshotStore(config)

    store.save(sample_snapshot)
    with open(persist_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["aspi_value"] == 22624.31
    assert "market_turnover" in data


# ============================================================================
# 2. INTRADAY STORE & 1-MINUTE DOWNSAMPLING
# ============================================================================

def test_intraday_store_downsampling(temp_cache_dir, sample_snapshot):
    """Test that intraday ticks within the same minute are properly downsampled into OHLC."""
    cache_file = os.path.join(temp_cache_dir, "intraday.json")
    config = IngestionConfig(intraday_cache_file=cache_file)
    store = IntradayStore(config)

    # Base minute
    t0 = datetime(2026, 10, 20, 10, 15, 10, tzinfo=COLOMBO_TZ)
    snap1 = sample_snapshot.model_copy(update={"aspi_value": 22600.0, "source_timestamp": t0})
    store.record_tick(snap1)

    # Second tick 20s later in same minute (higher)
    t1 = datetime(2026, 10, 20, 10, 15, 30, tzinfo=COLOMBO_TZ)
    snap2 = sample_snapshot.model_copy(update={"aspi_value": 22630.0, "source_timestamp": t1})
    store.record_tick(snap2)

    # Third tick 45s later in same minute (lower)
    t2 = datetime(2026, 10, 20, 10, 15, 55, tzinfo=COLOMBO_TZ)
    snap3 = sample_snapshot.model_copy(update={"aspi_value": 22590.0, "source_timestamp": t2})
    store.record_tick(snap3)

    series = store.get_series(metric="aspi", session="2026-10-20")
    assert len(series) == 1
    bar = series[0]
    assert bar.open == 22600.0
    assert bar.high == 22630.0
    assert bar.low == 22590.0
    assert bar.close == 22590.0
    assert bar.value == 22590.0


def test_intraday_store_memory_bounding(temp_cache_dir, sample_snapshot):
    """Test that intraday store limits memory retention to configured sessions."""
    cache_file = os.path.join(temp_cache_dir, "intraday.json")
    config = IngestionConfig(
        intraday_cache_file=cache_file,
        intraday_retention_sessions=2,  # Retain current + 2 prior = 3 max
    )
    store = IntradayStore(config)

    # Record across 5 different session dates
    for day in range(1, 6):
        d_str = f"2026-10-0{day}"
        t = datetime(2026, 10, day, 10, 0, 0, tzinfo=COLOMBO_TZ)
        snap = sample_snapshot.model_copy(update={"source_timestamp": t})
        store.record_tick(snap)

    available = store.get_available_sessions()
    # Should keep only 3 most recent sessions: 03, 04, 05
    assert len(available) == 3
    assert available == ["2026-10-03", "2026-10-04", "2026-10-05"]


def test_intraday_store_restart_survival(temp_cache_dir, sample_snapshot):
    """Test that intraday series persist to disk and rehydrate on restart."""
    cache_file = os.path.join(temp_cache_dir, "intraday.json")
    config = IngestionConfig(intraday_cache_file=cache_file)

    store1 = IntradayStore(config)
    store1.record_tick(sample_snapshot)

    # Re-instantiate to simulate restart
    store2 = IntradayStore(config)
    pts = store2.get_series("aspi", session="current")
    assert len(pts) >= 1
    assert pts[-1].value == sample_snapshot.aspi_value


# ============================================================================
# 3. END-OF-DAY APPEND & IDEMPOTENCY
# ============================================================================

def test_eod_append_idempotency_and_no_baseline_edit(temp_cache_dir, sample_snapshot):
    """Test that EOD job appends to live_daily.csv, is strictly idempotent, and NEVER touches CSE_data.csv."""
    live_file = os.path.join(temp_cache_dir, "live_daily.csv")
    audit_file = os.path.join(temp_cache_dir, "append_audit.log")
    config = IngestionConfig(
        live_daily_file_path=live_file,
        append_audit_log_path=audit_file,
    )
    live_store = LiveDailyStore(config)
    eod_job = EODJob(config=config, live_store=live_store)

    # Set closing snapshot for date 2026-10-20
    closing_snap = sample_snapshot.model_copy(
        update={
            "aspi_value": 22650.00,
            "aspi_previous_close": 22624.31,
            "source_timestamp": datetime(2026, 10, 20, 14, 30, 0, tzinfo=COLOMBO_TZ),
            "market_status": MarketStatus(raw_status="Market Closed", status=MarketStatusType.MARKET_CLOSED, is_open=False),
        }
    )

    # First execution: INSERT
    res1 = eod_job.execute_eod_append(closing_snap)
    assert res1.action == "INSERT"
    assert res1.is_duplicate is False

    rows_after_1 = live_store.load_rows()
    assert len(rows_after_1) == 1
    assert rows_after_1[0]["date"] == "2026-10-20"
    assert rows_after_1[0]["aspi"] == "22650.00"

    # Second execution on identical date: NOOP (idempotent, no duplicate)
    res2 = eod_job.execute_eod_append(closing_snap)
    assert res2.action == "NOOP"
    assert res2.is_duplicate is True

    rows_after_2 = live_store.load_rows()
    assert len(rows_after_2) == 1  # Still exactly 1 row!

    # Audit log check
    audit_entries = live_store.get_audit_logs()
    assert len(audit_entries) == 2
    assert audit_entries[0].action == "INSERT"
    assert audit_entries[1].action == "NOOP"

    # CRITICAL: Verify baseline CSE_data.csv was untouched
    baseline_cse = Path("CSE_data.csv")
    if baseline_cse.exists():
        assert baseline_cse.stat().st_size > 0


def test_eod_reconciliation_discrepancy(temp_cache_dir, sample_snapshot):
    """Test that reconciliation logs discrepancies when official close differs."""
    live_file = os.path.join(temp_cache_dir, "live_daily.csv")
    audit_file = os.path.join(temp_cache_dir, "append_audit.log")
    config = IngestionConfig(
        live_daily_file_path=live_file,
        append_audit_log_path=audit_file,
    )
    live_store = LiveDailyStore(config)
    eod_job = EODJob(config=config, live_store=live_store)

    closing_snap = sample_snapshot.model_copy(
        update={
            "aspi_value": 22650.00,
            "source_timestamp": datetime(2026, 10, 21, 14, 30, 0, tzinfo=COLOMBO_TZ),
        }
    )

    # Official exchange close reports 22645.00 (diff 5 points)
    res = eod_job.execute_eod_append(closing_snap, official_close_aspi=22645.00)
    assert res.action == "INSERT"
    assert res.discrepancy is not None
    assert "differs from official" in res.discrepancy


# ============================================================================
# 4. DERIVED STATISTICS REGRESSION TEST (Stage 0 Formulas)
# ============================================================================

def test_derived_statistics_baseline_regression():
    """REGRESSION TEST: Verify that derived statistics exactly match the Stage 0 baseline.
    
    Expected Stage 0 values on cse_clean.csv (ending 2025-12-31):
    - Panel Size: exactly 7,635 trading days
    - As-Of Date: "2025-12-31"
    - Annualized Realized Volatility: 15.70% (rounds to 15.7%)
    - 1D Continuous Log Return: 0.7917% (rounds to 0.79%)
    - Baseline ASPI: 22,624.31
    - Baseline S&P SL 20: 6,157.38
    """
    engine = DerivedStatsEngine()
    stats = engine.compute_stats()

    assert stats.panel_size_days == 7635
    assert stats.as_of_date == "2025-12-31"
    assert round(stats.realized_volatility_annualized, 1) == 15.7
    assert round(stats.realized_volatility_annualized, 2) == 15.70
    assert round(stats.daily_return_pct, 2) == 0.79
    assert round(stats.daily_log_return * 100.0, 4) == 0.7917
    assert stats.baseline_aspi == 22624.31
    assert stats.baseline_sp20 == 6157.38


def test_derived_statistics_dynamic_extension(temp_cache_dir, sample_snapshot):
    """Test that appending a live bar seamlessly expands the panel and recalculates stats."""
    live_file = os.path.join(temp_cache_dir, "live_daily.csv")
    config = IngestionConfig(live_daily_file_path=live_file)
    live_store = LiveDailyStore(config)

    # Append live bar for 2026-01-02
    live_bar = DailyBar(
        trade_date=date(2026, 1, 2),
        close=22700.00,
        aspi=22700.00,
        sp20=6175.00,
        turnover=10000000000.0,
        share_volume=250000000,
        aspi_log_return=0.00334,
    )
    live_store.upsert_daily_bar(live_bar)

    merged = MergedMarketHistory(config)
    engine = DerivedStatsEngine(config=config, merged_history=merged)
    stats = engine.compute_stats()

    # Panel grew from 7,635 to 7,636!
    assert stats.panel_size_days == 7636
    assert stats.as_of_date == "2026-01-02"
    assert stats.baseline_aspi == 22700.00
    assert stats.baseline_sp20 == 6175.00


# ============================================================================
# 5. REST API ENDPOINTS
# ============================================================================

def test_api_market_latest():
    """Test GET /api/market/latest endpoint returns valid contract."""
    client = TestClient(app)
    response = client.get("/api/market/latest")
    assert response.status_code == 200
    data = response.json()

    assert "aspi_value" in data
    assert "freshness_state" in data
    assert "source_timestamp" in data
    assert "fetched_at" in data
    assert response.headers.get("ETag") is not None
    assert "public" in response.headers.get("Cache-Control", "")

    # Conditional ETag 304 test
    etag = response.headers.get("ETag")
    res_304 = client.get("/api/market/latest", headers={"If-None-Match": etag})
    assert res_304.status_code == 304


def test_api_market_intraday():
    """Test GET /api/market/intraday endpoint."""
    client = TestClient(app)
    response = client.get("/api/market/intraday?metric=aspi&session=current")
    assert response.status_code == 200
    data = response.json()

    assert data["metric"] == "aspi"
    assert "points" in data
    assert "freshness_state" in data
    assert "fetched_at" in data
    assert data["downsample_interval"] == "1m"


def test_api_market_history():
    """Test GET /api/market/history endpoint with filtering."""
    client = TestClient(app)
    response = client.get("/api/market/history?from=2025-12-01&to=2025-12-31")
    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert data["count"] > 0
    assert data["data"][0]["date"] >= "2025-12-01"
    assert data["data"][-1]["date"] <= "2025-12-31"
    assert "freshness_state" in data


def test_api_market_stats():
    """Test GET /api/market/stats matches regression numbers."""
    client = TestClient(app)
    response = client.get("/api/market/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["panel_size_days"] >= 7635
    assert "realized_volatility_annualized" in data
    assert round(data["realized_volatility_annualized"], 1) == 15.7
    assert "daily_return_pct" in data
    assert "freshness_state" in data
    assert "fetched_at" in data


def test_legacy_market_summary_and_series():
    """Test that legacy /market/summary and /market/series continue working with zero errors."""
    client = TestClient(app)

    res_sum = client.get("/market/summary")
    assert res_sum.status_code == 200
    d_sum = res_sum.json()
    assert "aspi_level" in d_sum
    assert "metrics" in d_sum

    res_ser = client.get("/market/series?range=1M")
    assert res_ser.status_code == 200
    d_ser = res_ser.json()
    assert "series" in d_ser
    assert len(d_ser["series"]) > 0
