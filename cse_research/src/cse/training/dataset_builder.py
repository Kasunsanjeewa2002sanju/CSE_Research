"""Dataset Builder for Event-Driven CAR Model Retraining (Stage 8).

Builds and persists the comprehensive training dataset for candidate model retraining:
- Extracts 57 Stage 6 market technical and news-specific event features.
- Computes FinBERT sentiment scores (positive, negative, neutral).
- Aligns actual Cumulative Abnormal Return (CAR) as prediction target.
- Enforces time-based cross-validation splits:
    * 2022-2023: train
    * 2024: val
    * 2025: test
    * 2026: holdout
- Persists high-efficiency columnar dataset to data/training_data.parquet.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from cse.news.car_calculator import CARCalculator
from cse.news.embedder import EmbeddingEngine
from cse.news.feature_builder import FEATURE_COLUMNS, build_features
from cse.news.historical_db import get_default_db_path
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.training.dataset_builder")

# Global paths
ROOT_DIR = find_project_root()
DEFAULT_PARQUET_PATH = ROOT_DIR / "data" / "training_data.parquet"
CSV_HEADLINES_PATH = ROOT_DIR / "data" / "news_headlines.csv"
CLEAN_PARQUET_PATH = ROOT_DIR / "data" / "processed" / "cse_clean.parquet"

# Feature column definitions
SENTIMENT_FEATURE_COLS: List[str] = [
    "sentiment_positive",
    "sentiment_negative",
    "sentiment_neutral",
]

# Combined 60-feature set for candidate models
CANDIDATE_FEATURE_COLUMNS: List[str] = list(FEATURE_COLUMNS) + list(SENTIMENT_FEATURE_COLS)

# Target column definitions
TARGET_COLUMN = "target"  # Alias for car_5d (h=5 standard)
CAR_COLUMNS = ["car_1d", "car_2d", "car_5d", "car_10d"]


def clean_headline_text(text: str) -> str:
    """Standardize headline string whitespace and formatting."""
    if not text:
        return ""
    t = str(text).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def parse_event_year(date_val: Union[str, date, datetime]) -> int:
    """Extract integer year from date representation."""
    d_str = str(date_val).strip()[:10]
    try:
        return int(d_str[:4])
    except (ValueError, TypeError):
        return 2024


def assign_time_split(date_val: Union[str, date, datetime]) -> str:
    """Assign deterministic temporal split based on news publication year.
    
    Splits:
    - year <= 2023: train (includes 2022-2023 primary baseline)
    - year == 2024: val
    - year == 2025: test
    - year >= 2026: holdout
    """
    year = parse_event_year(date_val)
    if year <= 2023:
        return "train"
    elif year == 2024:
        return "val"
    elif year == 2025:
        return "test"
    else:
        return "holdout"


def _load_historical_aspi_history(db_path: Path) -> pd.DataFrame:
    """Load combined ASPI daily prices from cse_clean.parquet and cse_history.db."""
    dfs: List[pd.DataFrame] = []
    
    # 1. Load long-term historical clean data (1994-2025)
    if CLEAN_PARQUET_PATH.exists():
        try:
            df_clean = pd.read_parquet(CLEAN_PARQUET_PATH)
            if "date" in df_clean.columns and "aspi" in df_clean.columns:
                sub = df_clean[["date", "aspi"]].rename(columns={"aspi": "close"})
                sub["date"] = sub["date"].astype(str).str[:10]
                dfs.append(sub)
        except Exception as e:
            logger.warning("Could not read %s: %s", CLEAN_PARQUET_PATH, e)

    # 2. Load recent ASPI prices from DB (2023-2026)
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            df_db = pd.read_sql("SELECT date, close FROM aspi_prices", conn)
            conn.close()
            if not df_db.empty:
                df_db["date"] = df_db["date"].astype(str).str[:10]
                dfs.append(df_db)
        except Exception as e:
            logger.warning("Could not read aspi_prices from DB: %s", e)

    if not dfs:
        return pd.DataFrame(columns=["date", "close", "return_1d"])

    combined = pd.concat(dfs, ignore_index=True)
    combined["close"] = combined["close"].astype(float)
    combined = combined.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    
    # Calculate daily returns
    closes = combined["close"].values
    returns = np.zeros(len(closes))
    if len(closes) > 1:
        returns[1:] = (closes[1:] - closes[:-1]) / closes[:-1]
    combined["return_1d"] = returns

    return combined


def gather_raw_news_records(
    db_path: Optional[Path] = None,
    csv_path: Optional[Path] = None,
    min_year: int = 2022,
) -> List[Dict[str, Any]]:
    """Gather, normalize, and deduplicate news events from DB and CSV."""
    db_p = db_path or get_default_db_path()
    csv_p = csv_path or CSV_HEADLINES_PATH
    
    records: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # 1. Load existing records from SQLite DB
    if db_p.exists():
        try:
            conn = sqlite3.connect(str(db_p))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, headline, published_at, source, event_category, stage,
                       car_1d, car_2d, car_5d, car_10d, aspi_return_1d, aspi_return_5d
                FROM news_history
                """
            )
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                headline = clean_headline_text(row["headline"])
                pub_date = str(row["published_at"])[:10]
                if not headline or parse_event_year(pub_date) < min_year:
                    continue
                
                key = (headline.lower(), pub_date)
                records[key] = {
                    "id": row["id"],
                    "headline": headline,
                    "published_at": str(row["published_at"]),
                    "date": pub_date,
                    "source": row["source"] or "historical_db",
                    "event_category": row["event_category"] or "macro",
                    "stage": row["stage"] or "announcement",
                    "car_1d": row["car_1d"],
                    "car_2d": row["car_2d"],
                    "car_5d": row["car_5d"],
                    "car_10d": row["car_10d"],
                    "aspi_return_1d": row["aspi_return_1d"],
                    "aspi_return_5d": row["aspi_return_5d"],
                }
            logger.info("Loaded %d records from SQLite database (%s)", len(records), db_p)
        except Exception as e:
            logger.warning("Error reading from %s: %s", db_p, e)

    # 2. Augment from news_headlines.csv (adds 2022-2023 events)
    if csv_p.exists():
        try:
            df_csv = pd.read_csv(csv_p)
            col_date = "date" if "date" in df_csv.columns else "published_at"
            
            added_from_csv = 0
            for idx, r in df_csv.iterrows():
                headline = clean_headline_text(r.get("headline", ""))
                raw_date = str(r.get(col_date, ""))
                pub_date = raw_date[:10]
                if not headline or parse_event_year(pub_date) < min_year:
                    continue

                key = (headline.lower(), pub_date)
                if key not in records:
                    records[key] = {
                        "id": f"csv_{idx}",
                        "headline": headline,
                        "published_at": raw_date,
                        "date": pub_date,
                        "source": r.get("source", "csv_archive"),
                        "event_category": r.get("category", r.get("event_category", "macro")),
                        "stage": r.get("stage", "announcement"),
                        "car_1d": r.get("car_1d", None),
                        "car_2d": r.get("car_2d", None),
                        "car_5d": r.get("car_5d", None),
                        "car_10d": r.get("car_10d", None),
                        "aspi_return_1d": None,
                        "aspi_return_5d": None,
                    }
                    added_from_csv += 1
            logger.info("Augmented with %d unique records from %s", added_from_csv, csv_p)
        except Exception as e:
            logger.warning("Error reading CSV %s: %s", csv_p, e)

    out = list(records.values())
    out.sort(key=lambda x: str(x.get("published_at", "")))
    return out


def build_training_dataset(
    output_path: Optional[Union[str, Path]] = None,
    db_path: Optional[Union[str, Path]] = None,
    csv_path: Optional[Union[str, Path]] = None,
    min_year: int = 2022,
    horizon: int = 5,
    force_rebuild: bool = False,
) -> pd.DataFrame:
    """Build and persist the complete Stage 8 training dataset."""
    out_p = Path(output_path) if output_path else DEFAULT_PARQUET_PATH
    db_p = Path(db_path) if db_path else get_default_db_path()
    csv_p = Path(csv_path) if csv_path else CSV_HEADLINES_PATH

    if not force_rebuild and out_p.exists():
        logger.info("Loading existing training dataset from %s", out_p)
        return pd.read_parquet(out_p)

    logger.info("Building Stage 8 training dataset from historical events...")
    
    # 1. Gather news records
    raw_records = gather_raw_news_records(db_path=db_p, csv_path=csv_p, min_year=min_year)
    if not raw_records:
        raise ValueError("No historical news records found to build training dataset.")

    # 2. Setup CARCalculator for any records needing CAR calculation
    df_aspi = _load_historical_aspi_history(db_p)
    car_calc = CARCalculator(aspi_df=df_aspi)

    # 3. Setup FinBERT / Lexicon sentiment engine
    embedder_engine = EmbeddingEngine()

    rows: List[Dict[str, Any]] = []
    n_total = len(raw_records)
    logger.info("Processing %d headlines (features, sentiment, CAR)...", n_total)

    for i, rec in enumerate(raw_records):
        headline = rec["headline"]
        pub_at = rec["published_at"]
        clean_date = rec["date"]

        # Ensure CAR target is populated
        car_5d = rec.get("car_5d")
        if car_5d is None or pd.isna(car_5d):
            try:
                metrics = car_calc.calculate_all_metrics("aspi", clean_date)
                car_1d = float(metrics.get("car_1d", 0.0))
                car_2d = float(metrics.get("car_2d", 0.0))
                car_5d = float(metrics.get("car_5d", 0.0))
                car_10d = float(metrics.get("car_10d", 0.0))
            except Exception:
                car_1d, car_2d, car_5d, car_10d = 0.0, 0.0, 0.0, 0.0
        else:
            car_1d = float(rec.get("car_1d", 0.0) or 0.0)
            car_2d = float(rec.get("car_2d", 0.0) or 0.0)
            car_5d = float(car_5d)
            car_10d = float(rec.get("car_10d", 0.0) or 0.0)

        # Build Stage 6 feature vector (57 features)
        try:
            fv = build_features(headline=headline, news_date=pub_at, horizon=horizon)
            feature_dict = fv.to_dict()
        except Exception as e:
            logger.warning("Feature builder error for '%s' (%s). Using zeroes.", headline[:30], e)
            feature_dict = {col: 0.0 for col in FEATURE_COLUMNS}

        # Build FinBERT sentiment scores
        try:
            sent = embedder_engine.sentiment(headline)
            sent_pos = float(sent.get("positive", 0.33))
            sent_neg = float(sent.get("negative", 0.33))
            sent_neu = float(sent.get("neutral", 0.34))
            sent_comp = float(sent.get("compound", sent_pos - sent_neg))
        except Exception as e:
            logger.warning("Sentiment error for '%s' (%s). Using neutral.", headline[:30], e)
            sent_pos, sent_neg, sent_neu, sent_comp = 0.05, 0.05, 0.90, 0.0

        # Assign time-based split
        split = assign_time_split(pub_at)

        # Assemble full dataset record
        row_data: Dict[str, Any] = {
            "id": rec["id"],
            "headline": headline,
            "published_at": pub_at,
            "event_category": rec.get("event_category", "macro"),
            "stage": rec.get("stage", "announcement"),
            "split": split,
            "target": car_5d,  # Primary target
            "car_1d": car_1d,
            "car_2d": car_2d,
            "car_5d": car_5d,
            "car_10d": car_10d,
        }

        # Add 57 Stage 6 features
        for col in FEATURE_COLUMNS:
            val = feature_dict.get(col, 0.0)
            row_data[col] = float(0.0 if np.isnan(val) or np.isinf(val) else val)

        # Add sentiment features
        row_data["sentiment_positive"] = sent_pos
        row_data["sentiment_negative"] = sent_neg
        row_data["sentiment_neutral"] = sent_neu
        row_data["sentiment_compound"] = sent_comp

        rows.append(row_data)

        if (i + 1) % 100 == 0 or (i + 1) == n_total:
            logger.info("Processed %d / %d headlines (%.1f%%)", i + 1, n_total, (i + 1) / n_total * 100)

    df_out = pd.DataFrame(rows)

    # Validate types for parquet serialization
    df_out["id"] = df_out["id"].astype(str)
    df_out["headline"] = df_out["headline"].astype(str)
    df_out["published_at"] = df_out["published_at"].astype(str)
    df_out["event_category"] = df_out["event_category"].astype(str)
    df_out["stage"] = df_out["stage"].astype(str)
    df_out["split"] = df_out["split"].astype(str)

    # Validate no missing values in feature columns
    for col in CANDIDATE_FEATURE_COLUMNS:
        df_out[col] = df_out[col].fillna(0.0).astype(float)

    # Save to parquet
    out_p.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(out_p, index=False)
    logger.info("Successfully saved training dataset with %d rows and %d columns to %s", len(df_out), len(df_out.columns), out_p)
    logger.info("Split distribution:\n%s", df_out["split"].value_counts().to_string())

    return df_out


def load_training_dataset(path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load the persisted training dataset from parquet, building it if missing."""
    p = Path(path) if path else DEFAULT_PARQUET_PATH
    if not p.exists():
        logger.info("%s not found. Building now...", p)
        return build_training_dataset(output_path=p)
    return pd.read_parquet(p)


def main() -> None:
    """CLI entry point for dataset building."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Build CSE Stage 8 Retraining Dataset")
    parser.add_argument("--output", type=str, default=str(DEFAULT_PARQUET_PATH), help="Target parquet file path")
    parser.add_argument("--force", action="store_true", help="Force rebuild even if file exists")
    parser.add_argument("--min-year", type=int, default=2022, help="Earliest year of headlines to include")
    args = parser.parse_args()

    df = build_training_dataset(output_path=args.output, min_year=args.min_year, force_rebuild=args.force)
    print(f"\nTraining dataset created at {args.output}:")
    print(f"Total rows: {len(df)}")
    print(f"Features: {len(CANDIDATE_FEATURE_COLUMNS)} ({len(FEATURE_COLUMNS)} Stage 6 + {len(SENTIMENT_FEATURE_COLS)} sentiment)")
    print(f"Splits:\n{df['split'].value_counts()}")


if __name__ == "__main__":
    main()
