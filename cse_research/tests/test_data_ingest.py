"""Unit tests for Stage 1: CSE data ingestion, parsing, and monotonicity guarantees (Rule R1, R2, R4)."""

import datetime
import math
from pathlib import Path
import pytest
import numpy as np

from cse.data.ingest import (
    parse_raw_date,
    parse_numeric_cell,
    ingest_cse_raw,
    SP20_INCEPTION_DATE,
)
from cse.utils.config import find_project_root


def test_parse_raw_date_century_mapping() -> None:
    """Verify robust two-digit year parsing without century errors."""
    d94 = parse_raw_date("3-Jan-94")
    assert d94 == datetime.date(1994, 1, 3)

    d99 = parse_raw_date("31-Dec-99")
    assert d99 == datetime.date(1999, 12, 31)

    d00 = parse_raw_date("1-Jan-00")
    assert d00 == datetime.date(2000, 1, 1)

    d25 = parse_raw_date("31-Dec-25")
    assert d25 == datetime.date(2025, 12, 31)

    # Century bounds check
    with pytest.raises(ValueError):
        parse_raw_date("1-Jan-80")  # Out of 1990-2030 range


def test_parse_numeric_cell() -> None:
    """Verify comma stripping, dash-to-NaN conversions, and float conversions."""
    assert parse_numeric_cell("987.3") == 987.3
    assert parse_numeric_cell(" 1,462.5 ") == 1462.5
    assert parse_numeric_cell(" 124,703.5 ") == 124703.5
    assert math.isnan(parse_numeric_cell("-"))
    assert math.isnan(parse_numeric_cell("  -  "))
    assert math.isnan(parse_numeric_cell("—"))
    assert math.isnan(parse_numeric_cell(""))
    assert math.isnan(parse_numeric_cell(None))


def test_no_duplicate_dates() -> None:
    """Verify that every date in the raw dataset is unique."""
    root = find_project_root()
    raw_path = root / "data" / "raw" / "CSE_data.csv"
    if not raw_path.exists():
        raw_path = Path("D:/SLIIT/YEAR 04/Research/NEW Dev/CSE_data.csv")

    records = ingest_cse_raw(raw_path)
    dates = [r["date"] for r in records]
    unique_dates = set(dates)
    assert len(dates) == len(unique_dates), f"Found {len(dates) - len(unique_dates)} duplicate dates"
    assert len(dates) == 7635


def test_strictly_monotonic_dates() -> None:
    """Verify that dates are sorted strictly chronologically ascending."""
    root = find_project_root()
    raw_path = root / "data" / "raw" / "CSE_data.csv"
    if not raw_path.exists():
        raw_path = Path("D:/SLIIT/YEAR 04/Research/NEW Dev/CSE_data.csv")

    records = ingest_cse_raw(raw_path)
    for i in range(1, len(records)):
        prev_dt = records[i - 1]["date"]
        curr_dt = records[i]["date"]
        assert curr_dt > prev_dt, f"Non-monotonic date order at index {i}: {prev_dt} -> {curr_dt}"


def test_sp20_no_backfill_and_has_sp20_flag() -> None:
    """Verify Rule R1: S&P SL 20 is not back-filled prior to 2012-06-27."""
    root = find_project_root()
    raw_path = root / "data" / "raw" / "CSE_data.csv"
    if not raw_path.exists():
        raw_path = Path("D:/SLIIT/YEAR 04/Research/NEW Dev/CSE_data.csv")

    records = ingest_cse_raw(raw_path)
    for r in records:
        if r["date"] < SP20_INCEPTION_DATE:
            assert not r["has_sp20"]
            assert math.isnan(r["sp20"])
        else:
            if not math.isnan(r["sp20"]):
                assert r["has_sp20"]


def test_aspi_log_returns() -> None:
    """Verify Rule R4: ASPI log returns are accurately computed without lookahead."""
    root = find_project_root()
    raw_path = root / "data" / "raw" / "CSE_data.csv"
    if not raw_path.exists():
        raw_path = Path("D:/SLIIT/YEAR 04/Research/NEW Dev/CSE_data.csv")

    records = ingest_cse_raw(raw_path)
    assert math.isnan(records[0]["aspi_log_return"])

    for i in range(1, 10):
        prev = records[i - 1]["aspi"]
        curr = records[i]["aspi"]
        expected_ret = math.log(curr / prev)
        assert abs(records[i]["aspi_log_return"] - expected_ret) < 1e-9
