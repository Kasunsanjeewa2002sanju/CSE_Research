"""Unit and Integration Tests for Stage 1 Historical News & CAR Database Infrastructure."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import pytest

# Ensure cse_research/src is on sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cse.news.car_calculator import CARCalculator, calculate_car, map_to_trading_day
from cse.news.historical_db import (
    get_all_news,
    get_aspi_range,
    get_default_db_path,
    init_db,
    insert_aspi_prices,
    insert_news,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Fixture providing an isolated temporary SQLite database path within workspace."""
    # Place temporary test db in workspace scratch directory to avoid sandbox permission errors
    scratch_dir = root_dir / ".cache" / "pytest_dbs"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    db_file = scratch_dir / f"test_{os.getpid()}_{id(tmp_path)}.db"
    if db_file.exists():
        try:
            os.remove(db_file)
        except Exception:
            pass
    init_db(db_file)
    yield db_file
    if db_file.exists():
        try:
            os.remove(db_file)
        except Exception:
            pass


def test_schema_initialization(temp_db: Path) -> None:
    """Verify that tables and indexes are created with correct columns."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    # Check news_history columns
    cursor.execute("PRAGMA table_info(news_history)")
    cols_news = {row[1]: row[2] for row in cursor.fetchall()}
    expected_news = {
        "id": "INTEGER",
        "headline": "TEXT",
        "published_at": "TEXT",
        "source": "TEXT",
        "event_category": "TEXT",
        "stage": "TEXT",
        "car_1d": "REAL",
        "car_2d": "REAL",
        "car_5d": "REAL",
        "car_10d": "REAL",
        "aspi_return_1d": "REAL",
        "aspi_return_5d": "REAL",
    }
    for col, dtype in expected_news.items():
        assert col in cols_news, f"Missing column {col} in news_history"

    # Check aspi_prices columns
    cursor.execute("PRAGMA table_info(aspi_prices)")
    cols_aspi = {row[1]: row[2] for row in cursor.fetchall()}
    expected_aspi = {"date": "TEXT", "close": "REAL", "return_1d": "REAL"}
    for col, dtype in expected_aspi.items():
        assert col in cols_aspi, f"Missing column {col} in aspi_prices"

    conn.close()


def test_aspi_prices_crud(temp_db: Path) -> None:
    """Test inserting and querying ASPI prices with date ranges."""
    sample_prices = [
        {"date": "2024-01-01", "close": 10000.0, "return_1d": 0.0},
        {"date": "2024-01-02", "close": 10050.0, "return_1d": 0.005},
        {"date": "2024-01-03", "close": 10100.0, "return_1d": 0.004975},
        {"date": "2024-01-04", "close": 10080.0, "return_1d": -0.00198},
    ]
    inserted = insert_aspi_prices(sample_prices, db_path=temp_db)
    assert inserted == 4

    # Query full range
    all_prices = get_aspi_range(db_path=temp_db)
    assert len(all_prices) == 4
    assert all_prices[0]["date"] == "2024-01-01"
    assert all_prices[-1]["date"] == "2024-01-04"

    # Query filtered range
    sub_prices = get_aspi_range(start_date="2024-01-02", end_date="2024-01-03", db_path=temp_db)
    assert len(sub_prices) == 2
    assert sub_prices[0]["date"] == "2024-01-02"
    assert sub_prices[1]["date"] == "2024-01-03"


def test_news_history_crud(temp_db: Path) -> None:
    """Test inserting and retrieving news items."""
    sample_news = [
        {
            "headline": "Central Bank cuts rates by 50 bps",
            "published_at": "2024-05-15T10:00:00",
            "source": "Daily FT",
            "event_category": "central_bank_or_monetary_policy",
            "stage": "none",
            "car_1d": 0.0042,
            "car_2d": 0.0075,
            "car_5d": 0.0120,
            "car_10d": 0.0185,
            "aspi_return_1d": 0.0045,
            "aspi_return_5d": 0.0130,
        },
        {
            "headline": "Election Commission announces voting date",
            "published_at": "2024-07-26T18:00:00",
            "source": "Ada Derana",
            "event_category": "presidential_election",
            "stage": "announcement",
            "car_1d": -0.0021,
            "car_2d": -0.0040,
            "car_5d": -0.0062,
            "car_10d": -0.0080,
            "aspi_return_1d": -0.0018,
            "aspi_return_5d": -0.0055,
        },
    ]
    n_ins = insert_news(sample_news, db_path=temp_db)
    assert n_ins == 2

    retrieved = get_all_news(db_path=temp_db)
    assert len(retrieved) == 2
    assert retrieved[0]["event_category"] == "central_bank_or_monetary_policy"
    assert retrieved[1]["stage"] == "announcement"
    assert abs(retrieved[0]["car_5d"] - 0.0120) < 1e-6


def test_map_to_trading_day() -> None:
    """Test mapping calendar dates and evening hours to nearest trading day."""
    trading_days = ["2024-07-22", "2024-07-23", "2024-07-24", "2024-07-25", "2024-07-26", "2024-07-29"]

    # Direct match during day
    assert map_to_trading_day("2024-07-24", trading_days) == "2024-07-24"

    # Evening news (after 15:00) on Friday 2024-07-26 advances to Monday 2024-07-29
    assert map_to_trading_day("2024-07-26T18:30:00", trading_days) == "2024-07-29"

    # Weekend news (Saturday 2024-07-27) maps to Monday 2024-07-29
    assert map_to_trading_day("2024-07-27", trading_days) == "2024-07-29"


def test_car_calculator_mechanics() -> None:
    """Test CAR calculation with synthetic series matching specification."""
    # Build 250 trading days
    np.random.seed(42)
    dates = [d.strftime("%Y-%m-%d") for d in pd.date_range("2024-01-01", periods=250, freq="B")]
    daily_returns = np.random.normal(0.0005, 0.008, 250)
    prices = 10000.0 * np.cumprod(1.0 + daily_returns)

    df_aspi = pd.DataFrame({
        "date": dates,
        "close": prices,
        "return_1d": daily_returns,
    })

    calc = CARCalculator(aspi_df=df_aspi, estimation_window=120, gap_days=10, car_clip=0.10)

    # 1. Event with < 120 prior days: index 50 should return None
    car_insufficient = calc.calculate_car(None, dates[50], horizon=1)
    assert car_insufficient is None, "Events with < 120 prior days must return None"

    # 2. Event with >= 120 prior days: index 180
    t0 = 180
    event_date = dates[t0]
    car_1d = calc.calculate_car(None, event_date, horizon=1)
    car_2d = calc.calculate_car(None, event_date, horizon=2)
    car_5d = calc.calculate_car(None, event_date, horizon=5)
    car_10d = calc.calculate_car(None, event_date, horizon=10)

    assert car_1d is not None
    assert car_2d is not None
    assert car_5d is not None
    assert car_10d is not None

    # Check bounds [-0.10, +0.10]
    for c in (car_1d, car_2d, car_5d, car_10d):
        assert -0.10 <= c <= 0.10, f"CAR {c} out of clamped bounds [-0.10, +0.10]"

    # Verify manual formula
    est_returns = daily_returns[t0 - 10 - 120 : t0 - 10]
    mean_est = np.mean(est_returns)
    post_returns_5 = daily_returns[t0 + 1 : t0 + 1 + 5]
    expected_car_5d = float(np.clip(np.sum(post_returns_5 - mean_est), -0.10, 0.10))
    assert abs(car_5d - expected_car_5d) < 1e-5


def test_production_db_validation() -> None:
    """Verify that the production database data/cse_history.db satisfies all requirements."""
    db_path = root_dir / "data" / "cse_history.db"
    assert db_path.exists(), f"Production database {db_path} does not exist"

    # Check ASPI prices
    aspi_prices = get_aspi_range(db_path=db_path)
    assert len(aspi_prices) >= 600, f"aspi_prices has {len(aspi_prices)} rows, expected >= 600"

    # Check news history
    all_news = get_all_news(db_path=db_path)
    assert len(all_news) >= 500, f"news_history has {len(all_news)} rows, expected >= 500"

    # Check CAR computation presence
    with_car = [
        n for n in all_news
        if any(n.get(k) is not None for k in ("car_1d", "car_2d", "car_5d", "car_10d"))
    ]
    assert len(with_car) >= 400, f"Found only {len(with_car)} news with valid CAR"
