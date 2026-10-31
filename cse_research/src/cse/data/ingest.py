"""Ingestion and parsing module for raw Colombo Stock Exchange (CSE) data (Rule R1, R4).

Loads raw CSE_data.csv, performs robust century mapping, strips formatting artifacts,
validates monotonicity and date uniqueness, filters to specified modelling series,
and computes zero-lookahead ASPI log returns.
"""

import csv
import datetime
import hashlib
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

SP20_INCEPTION_DATE = datetime.date(2012, 6, 27)


def compute_file_sha256(filepath: Path) -> str:
    """Compute the SHA-256 hash of a file for reproducibility tracking (Rule R7)."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_raw_date(date_str: str) -> datetime.date:
    """Parse a two-digit year date string (e.g. '3-Jan-94' or '31-Dec-25').

    Guarantees century resolution (90-99 -> 1990-1999; 00-49 -> 2000-2049)
    and asserts that the result falls strictly within 1990 <= year <= 2030.
    """
    clean_str = date_str.strip()
    parts = clean_str.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date format (expected d-Mon-yy): '{date_str}'")

    day = int(parts[0])
    month_name = parts[1].lower()
    if month_name not in MONTH_MAP:
        raise ValueError(f"Unknown month abbreviation in date: '{date_str}'")
    month = MONTH_MAP[month_name]

    year_raw = int(parts[2])
    if year_raw >= 90:
        year = 1900 + year_raw
    else:
        year = 2000 + year_raw

    if not (1990 <= year <= 2030):
        raise ValueError(f"Century out of bounds error: parsed {year} from '{date_str}'")

    return datetime.date(year, month, day)


def parse_numeric_cell(cell_val: Optional[str]) -> float:
    """Parse a numeric string with commas, dashes ('-'), or empty whitespace into float.

    Dashes, whitespace, and empty strings are converted to NaN.
    """
    if cell_val is None:
        return float("nan")
    cleaned = cell_val.strip().replace(",", "")
    if cleaned in ("", "-", "—", "N/A", "null"):
        return float("nan")
    try:
        return float(cleaned)
    except ValueError:
        return float("nan")


def ingest_cse_raw(
    csv_path: Path,
    expected_header_rows: int = 4,
) -> List[Dict[str, Any]]:
    """Parse raw CSE_data.csv into sorted records with strict validation.

    Parameters
    ----------
    csv_path : Path
        Path to raw CSE_data.csv.
    expected_header_rows : int
        Number of leading title/header lines to bypass (default 4).

    Returns
    -------
    List[Dict[str, Any]]
        List of parsed record dictionaries sorted chronologically by date.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw CSE data not found at: {csv_path.resolve()}")

    records: List[Dict[str, Any]] = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for line_num, row in enumerate(reader, start=1):
            if line_num <= expected_header_rows:
                continue
            if not row or not any(cell.strip() for cell in row):
                continue  # skip trailing empty lines

            # Column 0: Date
            dt = parse_raw_date(row[0])

            # Column 1: ASPI
            aspi = parse_numeric_cell(row[1])
            if math.isnan(aspi):
                raise ValueError(f"Missing ASPI value encountered at line {line_num} (date {dt})")

            # Column 3: S&P SL 20
            sp20 = parse_numeric_cell(row[3]) if len(row) > 3 else float("nan")

            # Column 4: TURNOVER EQUITY-Mn
            turnover_equity = parse_numeric_cell(row[4]) if len(row) > 4 else float("nan")

            # Column 8: SHARES TRADED EQUITY '000
            shares_equity = parse_numeric_cell(row[8]) if len(row) > 8 else float("nan")

            # Boolean flag has_sp20 (Rule R1: Do NOT backfill or interpolate S&P 20)
            has_sp20 = (not math.isnan(sp20)) and (dt >= SP20_INCEPTION_DATE)

            records.append({
                "date": dt,
                "aspi": aspi,
                "sp20": sp20 if has_sp20 else float("nan"),
                "has_sp20": has_sp20,
                "turnover_equity_mn": turnover_equity,
                "shares_traded_equity_k": shares_equity,
            })

    # Sort strictly by date ascending
    records.sort(key=lambda r: r["date"])

    # Assert date uniqueness and strict monotonicity
    seen_dates = set()
    for i, r in enumerate(records):
        dt = r["date"]
        if dt in seen_dates:
            raise ValueError(f"Duplicate date detected in CSE data: {dt}")
        seen_dates.add(dt)
        if i > 0 and dt <= records[i - 1]["date"]:
            raise ValueError(f"Non-monotonic date sequence detected at index {i}: {records[i-1]['date']} -> {dt}")

    # Compute ASPI log returns (Rule R4: r_t = ln(ASPI_t / ASPI_{t-1}))
    for i in range(len(records)):
        if i == 0:
            records[i]["aspi_log_return"] = float("nan")
        else:
            prev_aspi = records[i - 1]["aspi"]
            curr_aspi = records[i]["aspi"]
            records[i]["aspi_log_return"] = math.log(curr_aspi / prev_aspi)

    return records
