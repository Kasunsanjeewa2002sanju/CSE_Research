"""Cryptographic hash utilities for data integrity and artifact verification.

Adheres to:
- Rule R7: Reproducibility, tracking data hashes across runs.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union


def compute_file_sha256(file_path: Union[str, Path], chunk_size: int = 65536) -> str:
    """Compute the SHA-256 cryptographic hash of a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()
