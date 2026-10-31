"""Build Historical News + Cumulative Abnormal Return (CAR) Database for CSE.

Stage 1 News Impact Prediction Infrastructure:
1. Reads data/news_headlines.csv (columns: headline, published_at, source)
2. Classifies each headline into event_category and stage using the existing extractor (cse.news.offline)
3. Maps each headline publication date to nearest trading day
4. Skips news with < 120 days of prior ASPI data (insufficient estimation window)
5. Computes CAR for h=1, 2, 5, 10 and ASPI returns for h=1, 5
6. Populates the news_history table in data/cse_history.db
7. Prints progress and summary stats (n_news, n_with_car, date_range)
"""

from __future__ import annotations

import argparse
import collections
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Add src to path if executed directly
project_root = Path(__file__).resolve().parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cse.news.car_calculator import CARCalculator
from cse.news.historical_db import (
    get_all_news,
    get_aspi_range,
    get_default_db_path,
    init_db,
    insert_news,
)
from cse.news.offline import OfflineEventExtractor
from cse.utils.config import find_project_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_historical_db")


def resolve_input_csv(input_arg: Optional[str], root: Path) -> Path:
    """Find and return input news headlines CSV path."""
    if input_arg:
        p = Path(input_arg)
        if p.exists():
            return p
        if (root / input_arg).exists():
            return root / input_arg
        if (root.parent / input_arg).exists():
            return root.parent / input_arg

    candidates = [
        root / "data" / "news_headlines.csv",
        root.parent / "data" / "news_headlines.csv",
        root / "data" / "processed" / "news_headlines.csv",
    ]
    for c in candidates:
        if c.exists():
            return c

    raise FileNotFoundError(
        f"Input news CSV not found. Looked for {input_arg} and {[str(c) for c in candidates]}"
    )


def ensure_aspi_prices_available(db_path: Path, root: Path) -> None:
    """Ensure aspi_prices table is populated with at least 600 trading days."""
    prices = get_aspi_range(db_path=db_path)
    if len(prices) >= 600:
        logger.info("Found %d pre-existing trading days in aspi_prices.", len(prices))
        return

    logger.warning("aspi_prices table has insufficient records (%d). Automatically running fetch_aspi_history...", len(prices))
    try:
        from scripts.fetch_aspi_history import build_aspi_dataset
    except ImportError:
        sys.path.insert(0, str(root / "scripts"))
        from fetch_aspi_history import build_aspi_dataset

    df = build_aspi_dataset(period_years=3, include_all=False, root=root)
    from cse.news.historical_db import insert_aspi_prices
    insert_aspi_prices(df, db_path=db_path)
    logger.info("Populated aspi_prices with %d trading days.", len(df))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 1 historical news + CAR database.")
    parser.add_argument("--input", type=str, default="data/news_headlines.csv", help="Input news headlines CSV path.")
    parser.add_argument("--db-path", type=str, default=None, help="Target SQLite database file path.")
    parser.add_argument("--min-prior-days", type=int, default=120, help="Minimum prior trading days required (default: 120).")
    parser.add_argument("--reset-news", action="store_true", help="Clear existing news_history before rebuilding.")
    args = parser.parse_args()

    root = find_project_root()
    db_file = Path(args.db_path) if args.db_path else get_default_db_path()
    init_db(db_file)

    # 1. Verify ASPI prices
    ensure_aspi_prices_available(db_file, root)

    # 2. Load input headlines CSV
    csv_path = resolve_input_csv(args.input, root)
    logger.info("Loading news headlines from: %s", csv_path)
    df_raw = pd.read_csv(csv_path)

    # Validate required columns
    required_cols = {"headline", "published_at"}
    if not required_cols.issubset(set(df_raw.columns)):
        raise ValueError(f"Input CSV must contain columns {required_cols}, found {list(df_raw.columns)}")

    if "source" not in df_raw.columns:
        df_raw["source"] = "Unknown"

    total_input = len(df_raw)
    logger.info("Loaded %d headlines from input CSV.", total_input)

    # 3. Initialize Extractor and CAR Calculator
    logger.info("Initializing offline semantic extractor and CAR calculator...")
    extractor = OfflineEventExtractor()
    car_calc = CARCalculator(db_path=db_file, estimation_window=args.min_prior_days)

    logger.info(
        "CAR Calculator initialized with %d trading days (%s to %s).",
        len(car_calc.trading_days),
        car_calc.trading_days[0] if car_calc.trading_days else "N/A",
        car_calc.trading_days[-1] if car_calc.trading_days else "N/A",
    )

    if args.reset_news:
        logger.info("Resetting news_history table...")
        import sqlite3
        with sqlite3.connect(str(db_file)) as conn:
            conn.execute("DELETE FROM news_history")
            conn.commit()

    # 4. Process headlines
    records_to_insert: List[Dict[str, Any]] = []
    skipped_insufficient_prior = 0
    skipped_empty = 0
    category_counter: collections.Counter = collections.Counter()
    valid_dates: List[str] = []

    for idx, row in df_raw.iterrows():
        headline = str(row.get("headline", "")).strip()
        pub_at = str(row.get("published_at", "")).strip()
        source = str(row.get("source", "")).strip() or "General"

        if not headline or headline.lower() == "nan" or len(headline) < 5 or not pub_at or pub_at.lower() == "nan":
            skipped_empty += 1
            continue

        # Step 4a: Classify event_category and stage using existing extractor
        extraction = extractor.extract(
            headline=headline,
            publication_date=pub_at,
            source=source,
        )
        category = extraction.event_category
        stage = extraction.stage
        category_counter[category] += 1

        # Step 4b: Map to nearest trading day
        mapped_date, t0 = car_calc.get_event_trading_index(pub_at)
        if t0 is None:
            skipped_insufficient_prior += 1
            continue

        # Step 4e: Skip news with < 120 days of prior ASPI data
        if t0 < args.min_prior_days:
            skipped_insufficient_prior += 1
            continue

        # Step 4c: Compute CAR for h=1, 2, 5, 10 using ASPI data
        car_1d = car_calc.calculate_car(None, mapped_date, horizon=1)
        car_2d = car_calc.calculate_car(None, mapped_date, horizon=2)
        car_5d = car_calc.calculate_car(None, mapped_date, horizon=5)
        car_10d = car_calc.calculate_car(None, mapped_date, horizon=10)

        aspi_1d = car_calc.calculate_aspi_return(mapped_date, horizon=1)
        aspi_5d = car_calc.calculate_aspi_return(mapped_date, horizon=5)

        records_to_insert.append({
            "headline": headline,
            "published_at": pub_at,
            "source": source,
            "event_category": category,
            "stage": stage,
            "car_1d": car_1d,
            "car_2d": car_2d,
            "car_5d": car_5d,
            "car_10d": car_10d,
            "aspi_return_1d": aspi_1d,
            "aspi_return_5d": aspi_5d,
        })
        valid_dates.append(pub_at[:10])

        if (idx + 1) % 100 == 0 or (idx + 1) == total_input:
            logger.info("Processed %d/%d items (Eligible: %d, Skipped <120D: %d)...",
                        idx + 1, total_input, len(records_to_insert), skipped_insufficient_prior)

    # Step 4d: Insert into news_history table
    logger.info("Inserting %d processed news records into news_history table...", len(records_to_insert))
    n_inserted = insert_news(records_to_insert, db_path=db_file)

    # 5. Summary Statistics
    stored_news = get_all_news(db_path=db_file)
    n_news = len(stored_news)

    # Count rows where at least one CAR metric is non-null
    n_with_car = sum(
        1 for r in stored_news
        if any(r.get(k) is not None for k in ("car_1d", "car_2d", "car_5d", "car_10d"))
    )

    all_dates = [str(r.get("published_at"))[:10] for r in stored_news if r.get("published_at")]
    date_min = min(all_dates) if all_dates else "N/A"
    date_max = max(all_dates) if all_dates else "N/A"
    date_range_str = f"{date_min} to {date_max}"

    print("\n" + "=" * 65)
    print("HISTORICAL NEWS & CAR DATABASE SUMMARY")
    print("=" * 65)
    print(f"Target Database           : {db_file}")
    print(f"Total Input Headlines     : {total_input}")
    print(f"Skipped (<120d prior ASPI): {skipped_insufficient_prior}")
    print(f"Skipped (Empty/Malformed) : {skipped_empty}")
    print(f"Total News Inserted       : {n_news}")
    print(f"News with Valid CAR       : {n_with_car}")
    print(f"Date Range (published_at) : {date_range_str}")
    print("-" * 65)
    print("Top Event Categories Distribution:")
    for cat, count in category_counter.most_common(8):
        print(f"  - {cat:<32}: {count}")
    print("=" * 65)

    if n_news < 500:
        err_msg = f"Requirement check FAILED: expected at least 500 news rows in news_history, got {n_news}."
        logger.error(err_msg)
        raise ValueError(err_msg)

    logger.info("Stage 1 Historical News + CAR Database build SUCCESSFUL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
