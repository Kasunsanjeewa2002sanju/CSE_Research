"""Reclassify Historical News in cse_history.db using Stage 5 Enhanced Extractor.

1. Loads all records from news_history table in data/cse_history.db
2. Re-runs EnhancedEventExtractor on every headline
3. Updates event_category and stage columns in the database
4. Rebuilds the Stage 2 Semantic Similarity FAISS/NumPy index
5. Reports comprehensive distribution and reclassification statistics
"""

from __future__ import annotations

import argparse
import collections
import logging
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cse.news.enhanced_extractor import EnhancedEventExtractor
from cse.news.historical_db import get_default_db_path
from cse.news.similarity import (
    SimilarityIndex,
    get_default_index_path,
    get_default_meta_path,
)
from cse.utils.config import find_project_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reclassify_history")


def reclassify_database(
    db_path: Path,
    extractor: EnhancedEventExtractor,
) -> Dict[str, Any]:
    """Reclassify all rows in news_history table of db_path."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, headline, published_at, source, event_category, stage FROM news_history")
    rows = cursor.fetchall()
    total_count = len(rows)

    category_counts: collections.Counter = collections.Counter()
    stage_counts: collections.Counter = collections.Counter()
    updates: List[Tuple[str, str, int]] = []

    print(f"\nProcessing {total_count} historical news records...")
    start_time = time.perf_counter()

    for idx, r in enumerate(rows, 1):
        row_id = r["id"]
        headline = r["headline"]
        pub_at = r["published_at"]
        source = r["source"]

        # Run enhanced extraction
        result = extractor.extract(
            headline=headline,
            published_at=pub_at,
            source=source,
        )

        new_category = result["primary_category"]
        new_stage = result["stage"]

        category_counts[new_category] += 1
        stage_counts[new_stage] += 1
        updates.append((new_category, new_stage, row_id))

        if idx % 100 == 0 or idx == total_count:
            print(f"  Processed {idx}/{total_count} headlines...")

    # Execute batch update
    cursor.executemany(
        "UPDATE news_history SET event_category = ?, stage = ? WHERE id = ?",
        updates,
    )
    conn.commit()
    conn.close()

    elapsed = time.perf_counter() - start_time
    return {
        "total_records": total_count,
        "elapsed_seconds": elapsed,
        "category_counts": dict(category_counts),
        "stage_counts": dict(stage_counts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reclassify cse_history.db with Stage 5 enhanced extractor.")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database (default: data/cse_history.db)",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip rebuilding the semantic similarity index",
    )
    args = parser.parse_args()

    root = find_project_root()
    primary_db = Path(args.db_path) if args.db_path else get_default_db_path()
    mirror_db = root.parent / "data" / "cse_history.db"

    print("=" * 70)
    print("CSE News Historical Reclassification Engine (Stage 5)")
    print("=" * 70)
    print(f"Target Database: {primary_db}")

    extractor = EnhancedEventExtractor()

    # 1. Reclassify primary DB
    stats = reclassify_database(primary_db, extractor)

    # 2. Reclassify mirror DB if present
    if mirror_db.exists() and mirror_db.resolve() != primary_db.resolve():
        print(f"\nMirroring updates to {mirror_db}...")
        reclassify_database(mirror_db, extractor)

    print("\n" + "=" * 70)
    print("RECLASSIFICATION SUMMARY")
    print("=" * 70)
    print(f"Total headlines reclassified: {stats['total_records']}")
    print(f"Time elapsed:                 {stats['elapsed_seconds']:.2f}s")
    print("\nCategory Distribution:")
    for cat, cnt in sorted(stats["category_counts"].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat:<36} : {cnt:>4} ({cnt/stats['total_records']*100:.1f}%)")

    print("\nStage Distribution:")
    for stg, cnt in sorted(stats["stage_counts"].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {stg:<28} : {cnt:>4} ({cnt/stats['total_records']*100:.1f}%)")
    print("=" * 70)

    # 3. Rebuild Semantic Index
    if not args.skip_index:
        print("\nRebuilding Stage 2 Semantic Similarity Index...")
        index_path = get_default_index_path()
        meta_path = get_default_meta_path()

        sim_index = SimilarityIndex(
            index_path=index_path,
            meta_path=meta_path,
            embedder=extractor.embedder,
            auto_load=False,
        )
        build_stats = sim_index.build(db_path=primary_db, save=True)
        print(f"Index rebuild complete: {build_stats['num_indexed']} records indexed in {build_stats.get('build_time', 0.0):.2f}s")

    print("\nStage 5 reclassification complete successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
