"""
Flat CSV Storage and Deduplication Engine for Stage 12 Ingested News.

Schema strictly matches the specifications of STAGE 12:
- Flat CSV table at results/tables/news_ingested.csv (append-only, no SQLite/DB).
- Canonical URL exact match and fuzzy title deduplication (>0.85 similarity threshold).
- Update existing row only when Stage 11 prediction result is missing.
"""

from __future__ import annotations

import csv
import difflib
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("cse.news.storage")

STORAGE_COLUMNS: List[str] = [
    # Ingestion & Provenance Metadata
    "item_id",
    "url",
    "headline",
    "description",
    "publication_date",
    "source",
    "language",
    "fetched_at",
    # Stage 10 Semantic Extraction
    "event_category",
    "stage",
    "expected_direction",
    "confidence",
    "entities",
    "affected_sectors",
    "is_relevant",
    # Stage 11 Horizon 1
    "if_true_aspi_h1",
    "if_false_aspi_h1",
    "diff_h1",
    "trend_h1",
    "prob_up_h1",
    "interval_80_lo_h1",
    "interval_80_hi_h1",
    "interval_95_lo_h1",
    "interval_95_hi_h1",
    # Stage 11 Horizon 2
    "if_true_aspi_h2",
    "if_false_aspi_h2",
    "diff_h2",
    "trend_h2",
    "prob_up_h2",
    "interval_80_lo_h2",
    "interval_80_hi_h2",
    "interval_95_lo_h2",
    "interval_95_hi_h2",
    # Stage 11 Horizon 5
    "if_true_aspi_h5",
    "if_false_aspi_h5",
    "diff_h5",
    "trend_h5",
    "prob_up_h5",
    "interval_80_lo_h5",
    "interval_80_hi_h5",
    "interval_95_lo_h5",
    "interval_95_hi_h5",
    # Stage 11 Horizon 10
    "if_true_aspi_h10",
    "if_false_aspi_h10",
    "diff_h10",
    "trend_h10",
    "prob_up_h10",
    "interval_80_lo_h10",
    "interval_80_hi_h10",
    "interval_95_lo_h10",
    "interval_95_hi_h10",
    # Historical Evidence
    "evidence_strength",
    "evidence_n",
    "evidence_mean_car",
    # Pipeline Status
    "processed",
    "notes",
]


def normalize_title(title: str) -> str:
    """Normalize headline for robust fuzzy similarity comparison."""
    if not title:
        return ""
    # Lowercase, strip non-alphanumeric chars, collapse whitespace
    s = title.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def compute_title_similarity(t1: str, t2: str) -> float:
    """Compute fuzzy similarity ratio between two titles."""
    n1 = normalize_title(t1)
    n2 = normalize_title(t2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return difflib.SequenceMatcher(None, n1, n2).ratio()


class NewsStorage:
    """Append-only flat CSV storage manager with URL and fuzzy title deduplication."""

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.seen_urls: Set[str] = set()
        self.seen_titles: List[str] = []
        self.rows: List[Dict[str, Any]] = []
        self._url_to_index: Dict[str, int] = {}
        
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing CSV table into memory for deduplication index."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    self.rows.append(row)
                    url = row.get("url", "").strip()
                    if url:
                        self.seen_urls.add(url)
                        self._url_to_index[url] = idx
                    headline = row.get("headline", "").strip()
                    if headline:
                        self.seen_titles.append(normalize_title(headline))
            logger.info(
                f"[Storage] Loaded {len(self.rows)} existing rows from {self.storage_path}. "
                f"Index contains {len(self.seen_urls)} unique URLs."
            )
        except Exception as e:
            logger.error(f"[Storage] Failed to read existing storage table at {self.storage_path}: {e}")

    def is_duplicate(
        self,
        canonical_url: str,
        headline: str,
        similarity_threshold: float = 0.85,
    ) -> Tuple[bool, str]:
        """
        Check if an item is a duplicate by canonical URL or fuzzy title similarity.

        Returns:
            (is_duplicate, reason)
        """
        clean_url = canonical_url.strip()
        if clean_url and clean_url in self.seen_urls:
            return True, "EXACT_URL"

        norm_title = normalize_title(headline)
        if norm_title:
            for existing_title in self.seen_titles:
                if difflib.SequenceMatcher(None, norm_title, existing_title).ratio() > similarity_threshold:
                    return True, "FUZZY_TITLE"

        return False, ""

    def append_or_update_item(self, item_row: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Add new row or update existing row if Stage 11 result was previously missing.

        Returns:
            (saved_success, action_type) where action_type is 'APPENDED', 'UPDATED', or 'SKIPPED'
        """
        url = str(item_row.get("url", "")).strip()
        headline = str(item_row.get("headline", "")).strip()

        # Check if URL exists and is missing Stage 11
        if url in self._url_to_index:
            idx = self._url_to_index[url]
            existing = self.rows[idx]
            # Check if Stage 11 result is missing
            has_stage11 = (
                existing.get("processed") in (True, "True", "true", "1")
                and existing.get("if_true_aspi_h1") not in (None, "", "None")
            )
            if not has_stage11:
                # Update existing row with Stage 11 predictions
                for col in STORAGE_COLUMNS:
                    if col in item_row and item_row[col] is not None:
                        existing[col] = item_row[col]
                self._persist_all()
                return True, "UPDATED"
            else:
                return False, "DUPLICATE_URL"

        # Check fuzzy title duplicate
        is_dup, reason = self.is_duplicate(url, headline)
        if is_dup:
            return False, f"DUPLICATE_{reason}"

        # New unique item -> Append
        clean_row = {col: item_row.get(col, "") for col in STORAGE_COLUMNS}
        self.rows.append(clean_row)
        if url:
            self.seen_urls.add(url)
            self._url_to_index[url] = len(self.rows) - 1
        if headline:
            self.seen_titles.append(normalize_title(headline))

        self._append_to_disk(clean_row)
        return True, "APPENDED"

    def _append_to_disk(self, row: Dict[str, Any]) -> None:
        """Append a single row to CSV on disk."""
        file_exists = self.storage_path.exists()
        with open(self.storage_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=STORAGE_COLUMNS)
            if not file_exists or self.storage_path.stat().st_size == 0:
                writer.writeheader()
            writer.writerow(row)

    def _persist_all(self) -> None:
        """Rewrite entire table when an existing row was updated."""
        with open(self.storage_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=STORAGE_COLUMNS)
            writer.writeheader()
            for r in self.rows:
                writer.writerow(r)
