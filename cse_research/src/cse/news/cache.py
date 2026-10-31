"""
Persistent response cache for news event extractions.

Saves LLM and offline extraction responses to disk using cryptographic hashes
of input headline, description, and publication date. Prevents redundant API calls
and guarantees deterministic reproducibility.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def find_project_root() -> Path:
    """Find the cse_research repository root directory dynamically."""
    curr = Path(__file__).resolve()
    for parent in [curr] + list(curr.parents):
        if (parent / "src" / "cse").exists():
            return parent
    return Path("d:/SLIIT/YEAR 04/Research/NEW Dev/cse_research")


ROOT_DIR = find_project_root()
DEFAULT_CACHE_PATH = ROOT_DIR / "data" / "processed" / "news_cache.json"


def compute_cache_key(headline: str, description: str = "", date: str = "") -> str:
    """Compute SHA-256 fingerprint for a given news item input."""
    raw = f"{headline.strip().lower()}|{description.strip().lower()}|{date.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class NewsCache:
    """Disk-backed key-value cache for structured news extractions."""

    def __init__(self, cache_file: str | Path = DEFAULT_CACHE_PATH):
        if isinstance(cache_file, Path):
            self.cache_file = cache_file.resolve()
        else:
            p = Path(cache_file)
            self.cache_file = (ROOT_DIR / p).resolve() if not p.is_absolute() else p.resolve()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ensure_cache_dir()
        self.load()

    def _ensure_cache_dir(self) -> None:
        """Create parent directory if it does not exist."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.cache_file.exists():
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)
        except Exception:
            pass

    def load(self) -> None:
        """Load cached entries from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}
        else:
            self._cache = {}

    def save(self) -> None:
        """Persist cache dictionary to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, headline: str, description: str = "", date: str = "") -> Optional[Dict[str, Any]]:
        """Retrieve cached extraction if present."""
        key = compute_cache_key(headline, description, date)
        return self._cache.get(key)

    def set(self, headline: str, description: str, date: str, data: Dict[str, Any]) -> None:
        """Store extraction result in cache and persist to disk."""
        key = compute_cache_key(headline, description, date)
        self._cache[key] = data
        self.save()

    def contains(self, headline: str, description: str = "", date: str = "") -> bool:
        """Check if an item is cached."""
        key = compute_cache_key(headline, description, date)
        return key in self._cache

    def __len__(self) -> int:
        return len(self._cache)

    def clear(self) -> None:
        """Clear cache memory and disk file."""
        self._cache = {}
        self.save()


_cached_instance: Optional[NewsCache] = None


def get_default_cache() -> NewsCache:
    """Lazy singleton accessor for the default cache."""
    global _cached_instance
    if _cached_instance is None:
        _cached_instance = NewsCache(DEFAULT_CACHE_PATH)
    return _cached_instance
