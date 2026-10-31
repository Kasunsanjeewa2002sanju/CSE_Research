"""Build Semantic Similarity Index for Colombo Stock Exchange News.

Stage 2 Semantic Search Infrastructure:
1. Loads all headlines from news_history table in data/cse_history.db (Stage 1)
2. Computes 384-dimensional dense semantic embeddings (using embedding cache)
3. Builds FAISS IndexFlatIP (or NumPy cosine fallback if FAISS is not installed)
4. Saves index to data/news_index.faiss and metadata to data/news_index_meta.pkl
5. Prints required statistics: num indexed, build time, embedding model used
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Add src to path if executed directly
project_root = Path(__file__).resolve().parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cse.news.embedder import EmbeddingEngine
from cse.news.historical_db import get_all_news, get_default_db_path
from cse.news.similarity import (
    FAISS_AVAILABLE,
    SimilarityIndex,
    find_similar,
    get_default_index_path,
    get_default_meta_path,
)
from cse.utils.config import find_project_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_index")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAISS similarity index from CSE news history.")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database (default: data/cse_history.db)",
    )
    parser.add_argument(
        "--index-path",
        type=str,
        default=None,
        help="Path to output FAISS/NumPy index file (default: data/news_index.faiss)",
    )
    parser.add_argument(
        "--meta-path",
        type=str,
        default=None,
        help="Path to output metadata pickle file (default: data/news_index_meta.pkl)",
    )
    args = parser.parse_args()

    root = find_project_root()
    db_path = Path(args.db_path) if args.db_path else get_default_db_path()
    index_path = Path(args.index_path) if args.index_path else get_default_index_path()
    meta_path = Path(args.meta_path) if args.meta_path else get_default_meta_path()

    print("=" * 70)
    print("CSE News Semantic Similarity Index Builder (Stage 2)")
    print("=" * 70)
    print(f"Project root:    {root}")
    print(f"Database path:   {db_path} (exists: {db_path.exists()})")
    print(f"Target index:    {index_path}")
    print(f"Target metadata: {meta_path}")
    print(f"FAISS available: {FAISS_AVAILABLE}")

    if not db_path.exists():
        print(f"ERROR: Database file not found: {db_path}")
        return 1

    # Initialize index and engine
    engine = EmbeddingEngine()
    sim_index = SimilarityIndex(
        index_path=index_path,
        meta_path=meta_path,
        embedder=engine,
        auto_load=False,
    )

    # Build index from news_history table
    print("\nLoading headlines from news_history and generating embeddings...")
    start_time = time.perf_counter()
    stats = sim_index.build(db_path=db_path, save=True)
    build_time = time.perf_counter() - start_time

    num_indexed = stats["num_indexed"]
    embedding_model = stats["embedding_model"]

    print("\n" + "=" * 70)
    print("INDEX BUILD STATISTICS")
    print("=" * 70)
    print(f"num indexed:          {num_indexed}")
    print(f"build time:           {build_time:.4f}s")
    print(f"embedding model used: {embedding_model}")
    print(f"backend:              {stats['backend']}")
    print(f"index file saved:     {index_path} ({index_path.stat().st_size:,} bytes)")
    print(f"metadata file saved:  {meta_path} ({meta_path.stat().st_size:,} bytes)")
    print("=" * 70)

    # Verification sample queries
    print("\n--- SAMPLE QUERY VERIFICATION ---")
    sample_queries = [
        "Central Bank cuts policy rate",
        "President announces election date",
        "IMF approves tranche under EFF program",
    ]

    for q in sample_queries:
        print(f"\nQuery: '{q}'")
        matches = sim_index.find_similar(q, k=3, min_similarity=0.5)
        if not matches:
            print("  No matches found with similarity >= 0.5")
        for rank, m in enumerate(matches, 1):
            car1 = f"{m['car_1d']:+.4f}" if m.get("car_1d") is not None else "N/A"
            car5 = f"{m['car_5d']:+.4f}" if m.get("car_5d") is not None else "N/A"
            car10 = f"{m['car_10d']:+.4f}" if m.get("car_10d") is not None else "N/A"
            print(
                f"  [{rank}] Sim: {m['similarity']:.4f} | Published: {m['published_at']} | "
                f"CAR(1d, 5d, 10d): ({car1}, {car5}, {car10})\n"
                f"      Headline: {m['headline']}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
