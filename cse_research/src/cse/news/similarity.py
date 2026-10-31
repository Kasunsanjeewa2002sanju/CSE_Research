"""Semantic Similarity Index for Colombo Stock Exchange News.

Loads historical news from news_history (Stage 1), computes 384-dimensional
dense embeddings, and indexes them using FAISS IndexFlatIP (with resilient
NumPy inner-product cosine fallback if FAISS is unavailable).

Supports:
- Persistent serialization to data/news_index.faiss and data/news_index_meta.pkl
- Top-k similarity queries with CAR returns (car_1d, car_5d, car_10d)
- Event category filtering (same_category_only=True)
- Similarity thresholding (min_similarity >= 0.5)
"""

from __future__ import annotations

import logging
import os
import pickle
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from cse.news.embedder import EMBEDDING_DIM, EmbeddingEngine
from cse.news.historical_db import get_all_news, get_default_db_path
from cse.news.offline import OfflineEventExtractor
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.similarity")

try:
    import faiss  # type: ignore

    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False


def get_default_index_path() -> Path:
    """Resolve default FAISS/NumPy index path in <project_root>/data/news_index.faiss."""
    root = find_project_root()
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "news_index.faiss"


def get_default_meta_path() -> Path:
    """Resolve default metadata path in <project_root>/data/news_index_meta.pkl."""
    root = find_project_root()
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "news_index_meta.pkl"


class NumpyFlatIPIndex:
    """Resilient pure-NumPy index implementing exact inner-product (cosine) search.
    
    Provides an identical interface to faiss.IndexFlatIP for vector addition,
    similarity search, and dimension validation.
    """

    def __init__(self, d: int = EMBEDDING_DIM) -> None:
        self.d = d
        self.vectors: np.ndarray = np.empty((0, d), dtype=np.float32)

    def add(self, x: np.ndarray) -> None:
        """Add unit vectors of shape (N, d) or (d,)."""
        x = np.asarray(x, dtype=np.float32)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        if x.shape[1] != self.d:
            raise ValueError(f"Vector dimension {x.shape[1]} does not match index dimension {self.d}")
        if self.vectors.size == 0:
            self.vectors = x.copy()
        else:
            self.vectors = np.vstack([self.vectors, x])

    def reset(self) -> None:
        """Clear all stored vectors."""
        self.vectors = np.empty((0, self.d), dtype=np.float32)

    @property
    def ntotal(self) -> int:
        """Total number of indexed vectors."""
        return self.vectors.shape[0]

    def search(self, q: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Search query vector(s) against indexed vectors using dot product.
        
        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (scores, indices) of shapes (1, k)
        """
        if self.ntotal == 0:
            return np.empty((1, 0), dtype=np.float32), np.empty((1, 0), dtype=np.int64)

        q = np.asarray(q, dtype=np.float32).reshape(-1, self.d)
        sims = np.dot(self.vectors, q[0])
        k = min(k, self.ntotal)
        top_k_indices = np.argsort(-sims)[:k]
        top_k_scores = sims[top_k_indices]
        return top_k_scores.reshape(1, -1).astype(np.float32), top_k_indices.reshape(1, -1).astype(np.int64)


class SimilarityIndex:
    """Semantic news similarity index with FAISS backend and NumPy fallback."""

    def __init__(
        self,
        index_path: Optional[Union[str, Path]] = None,
        meta_path: Optional[Union[str, Path]] = None,
        embedder: Optional[EmbeddingEngine] = None,
        auto_load: bool = True,
    ) -> None:
        self.index_path = Path(index_path) if index_path else get_default_index_path()
        self.meta_path = Path(meta_path) if meta_path else get_default_meta_path()
        self.embedder = embedder if embedder is not None else EmbeddingEngine()

        self.index: Any = None
        self.metadata: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None
        self.backend: str = "faiss" if FAISS_AVAILABLE else "numpy"

        if auto_load and self.index_path.exists() and self.meta_path.exists():
            self.load()

    def is_ready(self) -> bool:
        """Check if index and metadata are loaded and ready for querying."""
        return self.index is not None and len(self.metadata) > 0

    def load(
        self,
        index_path: Optional[Union[str, Path]] = None,
        meta_path: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Load index and metadata from disk."""
        target_index = Path(index_path) if index_path else self.index_path
        target_meta = Path(meta_path) if meta_path else self.meta_path

        if not target_index.exists() or not target_meta.exists():
            logger.warning("Index files missing: %s or %s", target_index, target_meta)
            return False

        # 1. Load Metadata
        try:
            with open(target_meta, "rb") as f:
                raw_meta = pickle.load(f)
            if isinstance(raw_meta, list):
                self.metadata = raw_meta
            elif isinstance(raw_meta, dict):
                if "items" in raw_meta:
                    self.metadata = raw_meta["items"]
                elif "records" in raw_meta:
                    self.metadata = raw_meta["records"]
                else:
                    # Integer index dictionary mapping
                    int_keys = [k for k in raw_meta.keys() if isinstance(k, int)]
                    if int_keys:
                        self.metadata = [raw_meta[i] for i in sorted(int_keys)]
                    else:
                        self.metadata = list(raw_meta.values())
            else:
                self.metadata = list(raw_meta)
        except Exception as e:
            logger.error("Failed loading metadata from %s: %s", target_meta, e)
            return False

        # 2. Load Vector Index
        loaded_index = None
        if FAISS_AVAILABLE:
            try:
                loaded_index = faiss.read_index(str(target_index))
                self.backend = "faiss"
                logger.info("Loaded FAISS index with %d vectors from %s", loaded_index.ntotal, target_index)
            except Exception as e:
                logger.debug("faiss.read_index failed (%s). Attempting NumPy unpickle.", e)

        if loaded_index is None:
            try:
                with open(target_index, "rb") as f:
                    data = pickle.load(f)
                if isinstance(data, NumpyFlatIPIndex):
                    loaded_index = data
                elif isinstance(data, np.ndarray):
                    loaded_index = NumpyFlatIPIndex(d=data.shape[1])
                    loaded_index.add(data)
                elif isinstance(data, dict) and "vectors" in data:
                    vecs = data["vectors"]
                    loaded_index = NumpyFlatIPIndex(d=vecs.shape[1])
                    loaded_index.add(vecs)
                else:
                    raise ValueError(f"Unrecognized index structure in {target_index}")
                self.backend = "numpy"
                logger.info("Loaded NumPy index with %d vectors from %s", loaded_index.ntotal, target_index)
            except Exception as e:
                logger.error("Failed loading index from %s: %s", target_index, e)
                return False

        self.index = loaded_index

        # Reconstruct or cache dense vector matrix for category filtering
        if hasattr(self.index, "vectors"):
            self.vectors = self.index.vectors
        elif FAISS_AVAILABLE and hasattr(self.index, "reconstruct_n"):
            try:
                self.vectors = self.index.reconstruct_n(0, self.index.ntotal)
            except Exception:
                self.vectors = None

        return True

    def save(
        self,
        index_path: Optional[Union[str, Path]] = None,
        meta_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Persist index and metadata to disk."""
        target_index = Path(index_path) if index_path else self.index_path
        target_meta = Path(meta_path) if meta_path else self.meta_path

        target_index.parent.mkdir(parents=True, exist_ok=True)
        target_meta.parent.mkdir(parents=True, exist_ok=True)

        # 1. Save metadata
        with open(target_meta, "wb") as f:
            pickle.dump(self.metadata, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info("Saved %d metadata records to %s", len(self.metadata), target_meta)

        # 2. Save vector index
        if FAISS_AVAILABLE and isinstance(self.index, faiss.Index):
            faiss.write_index(self.index, str(target_index))
            logger.info("Saved FAISS index to %s", target_index)
        else:
            with open(target_index, "wb") as f:
                pickle.dump(self.index, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.info("Saved NumPy index to %s", target_index)

        # Mirror to parent data/ directory if exists
        try:
            root = find_project_root()
            parent_data = root.parent / "data"
            if parent_data.exists() and parent_data != target_index.parent:
                shutil.copy2(target_index, parent_data / target_index.name)
                shutil.copy2(target_meta, parent_data / target_meta.name)
        except Exception as e:
            logger.debug("Parent data mirror skipped: %s", e)

    def build(
        self,
        records: Optional[List[Dict[str, Any]]] = None,
        db_path: Optional[Union[str, Path]] = None,
        save: bool = True,
    ) -> Dict[str, Any]:
        """Build similarity index from historical news records.
        
        Parameters
        ----------
        records : Optional[List[Dict[str, Any]]]
            List of news records. If None, loaded from SQLite news_history table.
        db_path : Optional[str | Path]
            Path to SQLite database file.
        save : bool, default True
            Whether to save the built index and metadata to disk.

        Returns
        -------
        Dict[str, Any]
            Build statistics dictionary.
        """
        start_time = time.perf_counter()

        if records is None:
            records = get_all_news(db_path=db_path)

        if not records:
            raise ValueError("No historical news records found to build index.")

        headlines = [str(r.get("headline", "")).strip() for r in records]

        # 1. Compute unit-normalized embeddings (uses persistent cache)
        logger.info("Embedding %d historical news headlines...", len(headlines))
        vectors = self.embedder.embed_batch(headlines)

        # 2. Build Index (FAISS IndexFlatIP or NumPy fallback)
        if FAISS_AVAILABLE:
            index = faiss.IndexFlatIP(EMBEDDING_DIM)
            index.add(vectors)
            self.backend = "faiss"
        else:
            index = NumpyFlatIPIndex(d=EMBEDDING_DIM)
            index.add(vectors)
            self.backend = "numpy"

        self.index = index
        self.vectors = vectors

        # 3. Construct structured metadata
        metadata: List[Dict[str, Any]] = []
        for r in records:
            metadata.append(
                {
                    "news_id": r.get("id"),
                    "id": r.get("id"),
                    "headline": r.get("headline"),
                    "published_at": str(r.get("published_at", "")),
                    "source": r.get("source"),
                    "event_category": r.get("event_category"),
                    "stage": r.get("stage"),
                    "car_1d": r.get("car_1d"),
                    "car_2d": r.get("car_2d"),
                    "car_5d": r.get("car_5d"),
                    "car_10d": r.get("car_10d"),
                    "aspi_return_1d": r.get("aspi_return_1d"),
                    "aspi_return_5d": r.get("aspi_return_5d"),
                }
            )

        self.metadata = metadata

        if save:
            self.save()

        elapsed = time.perf_counter() - start_time
        stats = {
            "num_indexed": len(metadata),
            "build_time_seconds": round(elapsed, 4),
            "embedding_model": self.embedder.model_name,
            "backend": self.backend,
            "index_path": str(self.index_path),
            "meta_path": str(self.meta_path),
        }
        logger.info("Index build completed in %.2fs (%s, %d items)", elapsed, self.backend, len(metadata))
        return stats

    def find_similar(
        self,
        query_text: str,
        k: int = 10,
        same_category_only: bool = False,
        min_similarity: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Find past news headlines semantically similar to query_text.
        
        Parameters
        ----------
        query_text : str
            Incoming news headline or text.
        k : int, default 10
            Maximum number of top matches to return.
        same_category_only : bool, default False
            If True, only return matches with the same event_category.
        min_similarity : float, default 0.5
            Minimum cosine similarity threshold to avoid weak matches.

        Returns
        -------
        List[Dict[str, Any]]
            List of matching records:
            [{news_id, headline, published_at, car_1d, car_5d, car_10d, similarity, ...}]
        """
        if not self.is_ready():
            if self.index_path.exists() and self.meta_path.exists():
                self.load()
            else:
                self.build()

        if not self.is_ready() or len(self.metadata) == 0:
            return []

        # 1. Compute query embedding vector (unit length)
        q_vec = self.embedder.embed(query_text)

        # 2. Event category filtering
        if same_category_only:
            extractor = OfflineEventExtractor()
            target_category = extractor.extract(query_text).event_category

            candidate_indices = [
                i for i, item in enumerate(self.metadata)
                if item.get("event_category") == target_category
            ]

            if not candidate_indices:
                return []

            # Score candidates using vector dot product
            if self.vectors is not None:
                cand_vecs = self.vectors[candidate_indices]
                cand_sims = np.dot(cand_vecs, q_vec)
            else:
                # Fallback: embed on demand if matrix unavailable
                cand_headlines = [self.metadata[i]["headline"] for i in candidate_indices]
                cand_vecs = self.embedder.embed_batch(cand_headlines)
                cand_sims = np.dot(cand_vecs, q_vec)

            sort_order = np.argsort(-cand_sims)
            scores = cand_sims[sort_order]
            indices = [candidate_indices[i] for i in sort_order]
        else:
            # Full index search
            search_k = min(len(self.metadata), max(k * 3, 50))
            if FAISS_AVAILABLE and isinstance(self.index, faiss.Index):
                raw_scores, raw_indices = self.index.search(q_vec.reshape(1, -1), search_k)
                scores = raw_scores[0]
                indices = raw_indices[0]
            else:
                if self.vectors is not None:
                    sims = np.dot(self.vectors, q_vec)
                    sort_order = np.argsort(-sims)[:search_k]
                    scores = sims[sort_order]
                    indices = sort_order
                else:
                    raw_scores, raw_indices = self.index.search(q_vec.reshape(1, -1), search_k)
                    scores = raw_scores[0]
                    indices = raw_indices[0]

        # 3. Filter by min_similarity threshold and assemble results
        results: List[Dict[str, Any]] = []
        for sim, idx in zip(scores, indices):
            idx_int = int(idx)
            if idx_int < 0 or idx_int >= len(self.metadata):
                continue

            sim_val = float(sim)
            if sim_val < min_similarity:
                continue

            item = self.metadata[idx_int]
            match_dict = {
                "news_id": item.get("news_id", item.get("id")),
                "headline": item.get("headline"),
                "published_at": item.get("published_at"),
                "car_1d": item.get("car_1d"),
                "car_5d": item.get("car_5d"),
                "car_10d": item.get("car_10d"),
                "similarity": round(sim_val, 4),
                "event_category": item.get("event_category"),
                "stage": item.get("stage"),
            }
            results.append(match_dict)
            if len(results) >= k:
                break

        return results


# Module-level singleton
_DEFAULT_INDEX: Optional[SimilarityIndex] = None


def get_similarity_index() -> SimilarityIndex:
    """Retrieve or initialize the global singleton SimilarityIndex instance."""
    global _DEFAULT_INDEX
    if _DEFAULT_INDEX is None:
        _DEFAULT_INDEX = SimilarityIndex()
        if not _DEFAULT_INDEX.is_ready():
            if _DEFAULT_INDEX.index_path.exists() and _DEFAULT_INDEX.meta_path.exists():
                _DEFAULT_INDEX.load()
            else:
                _DEFAULT_INDEX.build()
    return _DEFAULT_INDEX


def find_similar(
    new_headline: str,
    k: int = 10,
    same_category_only: bool = False,
    min_similarity: float = 0.5,
) -> List[Dict[str, Any]]:
    """Retrieve up to 10 most similar past news headlines with CAR values.
    
    Parameters
    ----------
    new_headline : str
        The incoming news headline to query against historical news.
    k : int, default 10
        Maximum number of matching items to return.
    same_category_only : bool, default False
        If True, restricts search to historical news of the same event_category.
    min_similarity : float, default 0.5
        Threshold to exclude weak or unrelated matches.

    Returns
    -------
    List[Dict[str, Any]]
        List of dicts each containing:
        {news_id, headline, published_at, car_1d, car_5d, car_10d, similarity}
    """
    idx = get_similarity_index()
    return idx.find_similar(
        query_text=new_headline,
        k=k,
        same_category_only=same_category_only,
        min_similarity=min_similarity,
    )
