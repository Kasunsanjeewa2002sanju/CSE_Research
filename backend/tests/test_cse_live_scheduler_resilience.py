"""Unit tests for Scheduler Resilience (single-flight lock, persistence fallback stub)."""

import os
import shutil
import pytest
from datetime import datetime

from cse_live.models import (
    FreshnessState,
    MarketSnapshot,
    MarketStatus,
    COLOMBO_TZ,
)
from cse_live.scheduler import SingleFlightLock, SnapshotPersistenceStub


@pytest.fixture
def workspace_tmp_dir():
    test_dir = os.path.join(os.path.dirname(__file__), ".tmp_test_resilience")
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    try:
        shutil.rmtree(test_dir, ignore_errors=True)
    except Exception:
        pass


def test_single_flight_lock_leader_and_standby(workspace_tmp_dir):
    lock_file = os.path.join(workspace_tmp_dir, "test_scheduler.lock")

    lock1 = SingleFlightLock(lock_file)
    lock2 = SingleFlightLock(lock_file)

    # First worker acquires leader
    assert lock1.acquire()
    assert lock1.is_leader

    # Second worker attempts to acquire: must fail and be standby
    assert not lock2.acquire()
    assert not lock2.is_leader

    # First worker releases lock
    lock1.release()
    assert not lock1.is_leader

    # Now second worker can acquire
    assert lock2.acquire()
    assert lock2.is_leader
    lock2.release()


def test_snapshot_persistence_stub_save_and_reload(workspace_tmp_dir):
    cache_file = os.path.join(workspace_tmp_dir, "last_snapshot.json")
    stub = SnapshotPersistenceStub(cache_file)

    # Initial load when empty
    assert stub.load() is None

    # Create valid snapshot
    snap = MarketSnapshot(
        aspi_value=20059.42,
        aspi_change=0.0,
        aspi_percent_change=0.0,
        aspi_previous_close=20059.42,
        sp20_value=5700.75,
        sp20_change=-29.35,
        sp20_percent_change=-0.51,
        sp20_previous_close=5730.10,
        market_turnover=50000000.0,
        shares_traded=1200000,
        total_trades=1500,
        market_status=MarketStatus(raw_status="Regular Trading", status="Regular Trading"),
        freshness=FreshnessState.LIVE,
        source_timestamp=datetime.now(COLOMBO_TZ),
        source="websocket_stomp"
    )

    # Save and verify
    stub.save(snap)
    assert os.path.exists(cache_file)

    # Reload on startup
    loaded = stub.load()
    assert loaded is not None
    assert loaded.aspi_value == 20059.42
    assert loaded.market_turnover == 50000000.0
    assert loaded.total_trades == 1500
