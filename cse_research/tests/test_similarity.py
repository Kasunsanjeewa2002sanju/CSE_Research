"""Unit and Integration Tests for Stage 2 Semantic Embedding & Similarity Index."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest

# Ensure cse_research/src is on sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cse.news.embedder import EMBEDDING_DIM, EmbeddingEngine
from cse.news.similarity import (
    NumpyFlatIPIndex,
    SimilarityIndex,
    find_similar,
    get_default_index_path,
    get_default_meta_path,
)


@pytest.fixture
def temp_cache_dir() -> Path:
    """Provide isolated directory for cache and test index artifacts."""
    cache_dir = root_dir / ".cache" / "pytest_sim"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yield cache_dir


def test_embedding_vector_properties(temp_cache_dir: Path) -> None:
    """Verify that embeddings are 384-dimensional and unit-normalized (L2 norm == 1.0)."""
    engine = EmbeddingEngine(cache_path=temp_cache_dir / "test_cache.pkl")
    vec = engine.embed("Central Bank cuts policy rate")

    assert isinstance(vec, np.ndarray), "Embedding must be a numpy ndarray"
    assert vec.shape == (EMBEDDING_DIM,), f"Expected shape ({EMBEDDING_DIM},), got {vec.shape}"
    assert vec.dtype == np.float32, f"Expected float32, got {vec.dtype}"

    norm = float(np.linalg.norm(vec))
    assert abs(norm - 1.0) < 1e-4, f"Vector must be unit normalized, got norm={norm}"


def test_required_semantic_similarity_thresholds(temp_cache_dir: Path) -> None:
    """Verify core semantic matching requirements:
    1. 'Central Bank cuts policy rate' matches 'CB reduces rates' (sim > 0.7)
    2. 'President announces election date' does NOT match 'IMF approves tranche' (sim < 0.5)
    """
    engine = EmbeddingEngine(cache_path=temp_cache_dir / "test_cache.pkl")

    # 1. High similarity match (> 0.7)
    v_cb1 = engine.embed("Central Bank cuts policy rate")
    v_cb2 = engine.embed("CB reduces rates")
    sim_cb = float(np.dot(v_cb1, v_cb2))

    assert sim_cb > 0.7, (
        f"Expected similarity > 0.7 between 'Central Bank cuts policy rate' and 'CB reduces rates', "
        f"got {sim_cb:.4f}"
    )

    # 2. Low similarity mismatch (< 0.5)
    v_pres = engine.embed("President announces election date")
    v_imf = engine.embed("IMF approves tranche")
    sim_mismatch = float(np.dot(v_pres, v_imf))

    assert sim_mismatch < 0.5, (
        f"Expected similarity < 0.5 between 'President announces election date' and 'IMF approves tranche', "
        f"got {sim_mismatch:.4f}"
    )


def test_sentiment_scoring(temp_cache_dir: Path) -> None:
    """Verify financial sentiment scoring returns positive, negative, neutral, and compound."""
    engine = EmbeddingEngine(cache_path=temp_cache_dir / "test_cache.pkl")

    # Positive headline
    pos_res = engine.sentiment("Central Bank cuts rates to boost growth and corporate earnings")
    assert all(k in pos_res for k in ["positive", "negative", "neutral", "compound"])
    assert pos_res["positive"] > pos_res["negative"]
    assert pos_res["compound"] > 0

    # Negative headline
    neg_res = engine.sentiment("Debt crisis deepens as sovereign default triggers nationwide protests")
    assert all(k in neg_res for k in ["positive", "negative", "neutral", "compound"])
    assert neg_res["negative"] > neg_res["positive"]
    assert neg_res["compound"] < 0


def test_numpy_fallback_index() -> None:
    """Verify NumpyFlatIPIndex produces correct inner-product ranking."""
    idx = NumpyFlatIPIndex(d=EMBEDDING_DIM)
    assert idx.ntotal == 0

    v1 = np.zeros(EMBEDDING_DIM, dtype=np.float32)
    v1[0] = 1.0  # Unit vector along axis 0

    v2 = np.zeros(EMBEDDING_DIM, dtype=np.float32)
    v2[1] = 1.0  # Orthogonal unit vector along axis 1

    idx.add(v1)
    idx.add(v2)
    assert idx.ntotal == 2

    q = np.zeros(EMBEDDING_DIM, dtype=np.float32)
    q[0] = 1.0  # Matches v1 exactly
    scores, indices = idx.search(q, k=2)

    assert indices[0][0] == 0
    assert abs(scores[0][0] - 1.0) < 1e-5
    assert abs(scores[0][1] - 0.0) < 1e-5


def test_similarity_index_build_and_query(temp_cache_dir: Path) -> None:
    """Verify SimilarityIndex building and querying with isolated records."""
    test_records = [
        {
            "id": 101,
            "headline": "CB reduces rates to stimulate lending",
            "published_at": "2024-05-15",
            "event_category": "central_bank_or_monetary_policy",
            "stage": "none",
            "car_1d": 0.0125,
            "car_5d": 0.0350,
            "car_10d": 0.0480,
        },
        {
            "id": 102,
            "headline": "IMF approves tranche under EFF facility",
            "published_at": "2024-06-20",
            "event_category": "debt_restructuring_or_imf",
            "stage": "none",
            "car_1d": -0.0050,
            "car_5d": 0.0180,
            "car_10d": -0.0120,
        },
        {
            "id": 103,
            "headline": "President announces parliamentary election date",
            "published_at": "2024-09-01",
            "event_category": "parliamentary_election",
            "stage": "announcement",
            "car_1d": -0.0080,
            "car_5d": -0.0220,
            "car_10d": -0.0350,
        },
    ]

    engine = EmbeddingEngine(cache_path=temp_cache_dir / "sim_cache.pkl")
    index_path = temp_cache_dir / "isolated_index.faiss"
    meta_path = temp_cache_dir / "isolated_meta.pkl"

    sim_idx = SimilarityIndex(
        index_path=index_path,
        meta_path=meta_path,
        embedder=engine,
        auto_load=False,
    )
    stats = sim_idx.build(records=test_records, save=True)

    assert stats["num_indexed"] == 3
    assert index_path.exists()
    assert meta_path.exists()

    # Query for rate cuts
    matches = sim_idx.find_similar("Central Bank cuts policy rate", k=5, min_similarity=0.5)
    assert len(matches) >= 1
    top_match = matches[0]

    assert top_match["news_id"] == 101
    assert "CB reduces rates" in top_match["headline"]
    assert top_match["similarity"] > 0.7
    assert top_match["car_1d"] == 0.0125
    assert top_match["car_5d"] == 0.0350
    assert top_match["car_10d"] == 0.0480

    # Ensure IMF item is NOT returned for rate cut query (similarity < 0.5)
    matched_ids = [m["news_id"] for m in matches]
    assert 102 not in matched_ids, "IMF item should not match rate cut query"


def test_same_category_filtering(temp_cache_dir: Path) -> None:
    """Verify that same_category_only=True restricts results to matching event_category."""
    test_records = [
        {
            "id": 201,
            "headline": "Central Bank cuts interest corridor by 50 bps",
            "published_at": "2024-04-10",
            "event_category": "central_bank_or_monetary_policy",
            "car_1d": 0.010,
            "car_5d": 0.020,
            "car_10d": 0.030,
        },
        {
            "id": 202,
            "headline": "Cabinet approves revision of value added tax and tariffs",
            "published_at": "2024-04-12",
            "event_category": "government_policy_or_budget_or_tax",
            "car_1d": -0.005,
            "car_5d": -0.010,
            "car_10d": -0.015,
        },
    ]

    engine = EmbeddingEngine(cache_path=temp_cache_dir / "cat_cache.pkl")
    sim_idx = SimilarityIndex(
        index_path=temp_cache_dir / "cat_index.faiss",
        meta_path=temp_cache_dir / "cat_meta.pkl",
        embedder=engine,
        auto_load=False,
    )
    sim_idx.build(records=test_records, save=False)

    # When filtered to same category
    results = sim_idx.find_similar(
        "Central Bank cuts policy rate",
        k=10,
        same_category_only=True,
        min_similarity=0.4,
    )

    for item in results:
        assert item["event_category"] == "central_bank_or_monetary_policy"


def test_top_level_find_similar_function() -> None:
    """Verify top-level find_similar() function against default indexed database."""
    matches = find_similar("Central Bank cuts policy rate", k=10)

    assert isinstance(matches, list)
    assert len(matches) <= 10
    assert len(matches) > 0, "Expected matches for Central Bank rate cut query"

    for m in matches:
        # Check required return dictionary keys
        for key in ["news_id", "headline", "published_at", "car_1d", "car_5d", "car_10d", "similarity"]:
            assert key in m, f"Missing required key '{key}' in match"

        # Similarity threshold verification
        assert m["similarity"] >= 0.5, f"Returned match has similarity < 0.5: {m['similarity']}"

    # Results must be in descending order of similarity
    sims = [m["similarity"] for m in matches]
    assert sims == sorted(sims, reverse=True), "Matches must be ordered descending by similarity"


def test_weak_match_filtering() -> None:
    """Verify that completely unrelated queries return no matches with similarity >= 0.5."""
    unrelated_query = "Astrophysicists observe stellar collision in distant spiral galaxy"
    matches = find_similar(unrelated_query, k=10, min_similarity=0.5)

    assert len(matches) == 0, f"Expected 0 matches for unrelated astrophysical query, got {len(matches)}"
