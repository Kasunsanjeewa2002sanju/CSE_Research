"""Unit tests for CSE Live Tick Validator (jump rejection, unit normalisation, monotonicity)."""

from datetime import datetime, timedelta
import pytest

from cse_live.config import IngestionConfig
from cse_live.models import (
    FreshnessState,
    MarketSnapshot,
    MarketStatus,
    MarketStatusType,
    COLOMBO_TZ,
)
from cse_live.validator import TickValidator


def make_valid_snapshot(
    aspi: float = 20059.42,
    prev_close: float = 20059.42,
    change: float = 0.0,
    turnover: float = 1500000.0,
    shares: int = 50000,
    trades: int = 150,
    timestamp: datetime = None
) -> MarketSnapshot:
    ts = timestamp or datetime.now(COLOMBO_TZ)
    return MarketSnapshot(
        aspi_value=aspi,
        aspi_change=change,
        aspi_percent_change=round((change / prev_close) * 100.0, 4) if prev_close else 0.0,
        aspi_previous_close=prev_close,
        sp20_value=5700.75,
        sp20_change=-29.35,
        sp20_percent_change=-0.51,
        sp20_previous_close=5730.10,
        market_turnover=turnover,
        shares_traded=shares,
        total_trades=trades,
        market_status=MarketStatus(raw_status="Regular Trading", status="Regular Trading"),
        freshness=FreshnessState.LIVE,
        source_timestamp=ts,
        source="websocket_stomp"
    )


def test_validator_accepts_valid_tick():
    validator = TickValidator()
    snap = make_valid_snapshot()
    res = validator.validate(snap)
    assert res.is_valid
    assert res.snapshot == snap
    assert validator.last_accepted_snapshot == snap


def test_validator_rejects_negative_turnover():
    validator = TickValidator()
    # Pydantic model itself rejects negative turnover via ge=0.0
    with pytest.raises(Exception):
        make_valid_snapshot(turnover=-500.0)


def test_validator_rejects_erroneously_scaled_turnover():
    validator = TickValidator()
    # 150 trades executed, but turnover reported as 450.0 LKR (likely scaled in Millions incorrectly)
    snap = make_valid_snapshot(turnover=450.0, trades=200)
    res = validator.validate(snap)
    assert not res.is_valid
    assert "erroneously scaled down" in res.anomaly.reason


def test_validator_rejects_non_monotonic_timestamp():
    validator = TickValidator()
    t0 = datetime(2026, 10, 20, 11, 0, 0, tzinfo=COLOMBO_TZ)
    snap1 = make_valid_snapshot(timestamp=t0)
    assert validator.validate(snap1).is_valid

    # Regresses backwards by 10 seconds on the same trading day
    t_backwards = t0 - timedelta(seconds=10)
    snap2 = make_valid_snapshot(timestamp=t_backwards)
    res2 = validator.validate(snap2)
    assert not res2.is_valid
    assert "Non-monotonic timestamp" in res2.anomaly.reason


def test_validator_jump_check_and_consecutive_confirmation():
    config = IngestionConfig(max_tick_jump_pct=10.0)
    validator = TickValidator(config)

    # Initial baseline
    snap0 = make_valid_snapshot(aspi=20000.0, prev_close=20000.0, change=0.0)
    assert validator.validate(snap0).is_valid

    # Large 25% jump to 25,000.0
    snap_jump = make_valid_snapshot(aspi=25000.0, prev_close=20000.0, change=5000.0)
    
    # 1st observation: held and rejected as jump anomaly
    res1 = validator.validate(snap_jump)
    assert not res1.is_valid
    assert "awaiting 2nd confirmation" in res1.anomaly.reason
    assert validator.last_accepted_snapshot.aspi_value == 20000.0

    # 2nd observation: same candidate value 25,000.0 confirms legitimate jump!
    res2 = validator.validate(snap_jump)
    assert res2.is_valid
    assert validator.last_accepted_snapshot.aspi_value == 25000.0


def test_validator_rejects_inconsistent_change():
    validator = TickValidator()
    # Model validation catches change != aspi - prev_close
    with pytest.raises(Exception):
        make_valid_snapshot(aspi=20100.0, prev_close=20000.0, change=500.0)
