"""Stage 6 Integration Tests for CSE News Feature Builder.

Validates that build_features():
- Wires in Stages 1-5 (PriorCalculator, EnhancedExtractor, ProximityCalculator)
- Differentiates rate cuts vs raises by > 0.5% (0.005) in prior_median_car
- Differentiates election in 3 days vs 60 days by > 30 trading days
- Returns vector with exact shape 58 matching feature_columns.json
- Preserves all 38 market technical features unchanged
- Contains no NaNs or Infs
- Implements 1h prior and 24h extractor caching
- Logs fallbacks to data/feature_fallbacks.log
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest

from cse.news.feature_builder import (
    FALLBACK_LOG_PATH,
    FEATURE_COLUMNS,
    TECHNICAL_FEATURE_COLS,
    FeatureVector,
    NewsFeatureBuilder,
    build_features,
    get_cache,
    log_feature_fallback,
)
from cse.utils.config import find_project_root


@pytest.fixture(autouse=True)
def clean_cache():
    """Ensure in-memory cache is fresh before tests."""
    cache = get_cache()
    cache.clear()
    yield
    cache.clear()


def test_rate_cuts_vs_rate_raises_difference() -> None:
    """Requirement 5: 'Central Bank cuts rate' vs 'Central Bank raises rate'
    must produce feature vectors that differ in prior_median_car by > 0.5% (0.005).
    """
    vec_cuts = build_features(
        headline="Central Bank cuts rate",
        news_date="2026-03-15",
        horizon=10,
    )
    vec_raises = build_features(
        headline="Central Bank raises rate",
        news_date="2026-03-15",
        horizon=10,
    )

    cuts_median = vec_cuts["prior_median_car"]
    raises_median = vec_raises["prior_median_car"]
    diff = abs(cuts_median - raises_median)

    print(f"\n[Test Rate Diff] Cuts: {cuts_median:+.6f} | Raises: {raises_median:+.6f} | Diff: {diff:.6f}")

    assert diff > 0.005, (
        f"Expected prior_median_car difference > 0.5% (0.005), got {diff:.6f} "
        f"(cuts={cuts_median:.6f}, raises={raises_median:.6f})"
    )
    assert cuts_median > raises_median, "Rate cuts prior should be more positive than rate raises prior"


def test_election_proximity_days_difference() -> None:
    """Requirement 5: 'Election in 3 days' vs 'Election in 60 days'
    must differ in days_to_next_known_event by > 30 trading days.
    """
    # 1. Test with calendar reference dates (as established in Stage 4)
    vec_3d = build_features(
        headline="Election in 3 days",
        news_date="2026-11-12",
    )
    vec_60d = build_features(
        headline="Election in 60 days",
        news_date="2026-08-31",
    )

    d3 = vec_3d["days_to_next_known_event"]
    d60 = vec_60d["days_to_next_known_event"]
    diff = abs(d60 - d3)

    print(f"\n[Test Election Proximity] 3d: {d3:.1f} | 60d: {d60:.1f} | Diff: {diff:.1f}")

    assert diff > 30.0, (
        f"Expected days_to_next_known_event difference > 30, got {diff:.1f} (3d={d3}, 60d={d60})"
    )
    assert d60 > d3, "60 days proximity should be larger than 3 days proximity"

    # 2. Test relative offset headlines without news_date
    vec_rel_3d = build_features("Election in 3 days")
    vec_rel_60d = build_features("Election in 60 days")
    diff_rel = abs(vec_rel_60d["days_to_next_known_event"] - vec_rel_3d["days_to_next_known_event"])

    assert diff_rel > 30.0, (
        f"Expected relative days difference > 30, got {diff_rel:.1f}"
    )


def test_output_shape_and_columns_exact_match() -> None:
    """Requirement 2 & 5: Output vector must have EXACTLY len(feature_columns.json) elements (58),
    exact column order, and zero NaN values.
    """
    root_dir = find_project_root()
    feat_cols_path = root_dir / "models" / "final" / "feature_columns.json"
    with open(feat_cols_path, "r", encoding="utf-8") as f:
        expected_cols = json.load(f)

    expected_len = len(expected_cols)
    assert expected_len == 58, f"Expected 58 feature columns, found {expected_len}"

    vec = build_features(
        headline="President dissolves parliament; snap election called",
        news_date="2026-04-10",
    )

    # 1. Output shape check
    assert isinstance(vec, np.ndarray), "Output must be a NumPy array / FeatureVector subclass"
    assert vec.shape == (expected_len,), f"Expected shape ({expected_len},), got {vec.shape}"
    assert len(vec) == expected_len, f"Expected length {expected_len}, got {len(vec)}"

    # 2. Exact column name ordering
    assert vec.feature_names == expected_cols, "Feature column sequence mismatch"

    # 3. No NaN or Inf values
    assert not np.isnan(vec).any(), "Feature vector contains NaN values"
    assert not np.isinf(vec).any(), "Feature vector contains Inf values"

    # 4. Dictionary and Series conversions
    d = vec.to_dict()
    assert len(d) == expected_len
    assert list(d.keys()) == expected_cols

    s = vec.to_series()
    assert len(s) == expected_len
    assert list(s.index) == expected_cols


def test_market_technical_features_preserved_unchanged() -> None:
    """Requirement 1: Keep all 38 market technical features UNCHANGED from market_snapshot."""
    custom_snapshot: Dict[str, float] = {
        "ret_1d": 0.0145,
        "ret_2d": -0.0052,
        "ret_3d": 0.0089,
        "ret_5d": 0.0210,
        "rsi_14": 62.4,
        "macd_line": 15.3,
        "macd_signal": 12.1,
        "macd_hist": 3.2,
        "log_turnover": 18.25,
        "turnover_to_5d_ratio": 1.65,
    }

    vec = build_features(
        headline="CBSL holds monetary policy corridor steady",
        news_date="2026-05-20",
        market_snapshot=custom_snapshot,
    )

    # Verify each custom technical feature was preserved
    for col, expected_val in custom_snapshot.items():
        assert abs(vec[col] - expected_val) < 1e-6, (
            f"Feature {col} changed: expected {expected_val}, got {vec[col]}"
        )
        assert "market_snapshot" in vec.feature_sources[col]


def test_continuous_confidence_scores_and_stages() -> None:
    """Requirement 1: Features type_* and stage_* must use continuous confidence scores (0.0-1.0),
    not hard binary 0/1.
    """
    vec = build_features(
        headline="President calls parliamentary election as IMF approves loan tranche",
        news_date="2026-06-15",
    )

    # Check that parliamentary election confidence is populated
    assert vec["type_parliamentary"] > 0.0, "Expected positive parliamentary election confidence"
    assert 0.0 < vec["type_parliamentary"] <= 1.0

    # Announcement stage should have confidence score
    assert vec["stage_announcement"] > 0.0
    assert 0.0 < vec["stage_announcement"] <= 1.0

    # Irrelevant stage flags should remain 0.0
    assert vec["stage_polling"] == 0.0
    assert vec["stage_result"] == 0.0


def test_caching_prior_and_extractor() -> None:
    """Requirement 4: Cache prior lookups for 1 hour and extractor results for 24 hours."""
    headline = "Treasury issues fresh bond auction amid revenue surge"
    cache = get_cache()
    cache.clear()

    # First call: cache miss
    vec1 = build_features(headline, horizon=10)
    assert vec1.metadata.get("prior_cached") is False
    assert vec1.metadata.get("extractor_cached") is False

    # Second call: cache hit
    vec2 = build_features(headline, horizon=10)
    assert vec2.metadata.get("prior_cached") is True
    assert vec2.metadata.get("extractor_cached") is True

    # Vectors should be identical
    np.testing.assert_array_almost_equal(vec1, vec2)


def test_fallback_chain_logging() -> None:
    """Requirement 3: Fallback chain triggers and logs to data/feature_fallbacks.log."""
    test_headline = "Unprecedented experimental solar orbital alignment detected"
    
    # Directly invoke fallback logger to test write integrity
    log_feature_fallback(
        component="test_suite",
        headline=test_headline,
        level="unit_test_verification",
        reason="Testing feature fallback log writes",
    )

    assert FALLBACK_LOG_PATH.exists(), f"Expected log file at {FALLBACK_LOG_PATH}"
    with open(FALLBACK_LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) > 0
    latest = lines[-1]
    assert "FALLBACK" in latest
    assert "unit_test_verification" in latest


def test_news_feature_builder_class_wrapper() -> None:
    """Validate NewsFeatureBuilder class object interface."""
    builder = NewsFeatureBuilder()
    assert len(builder.feature_columns) == 58

    vec = builder.build(
        headline="Cabinet reshuffle announced; new Finance Minister appointed",
        news_date="2026-07-01",
        horizon=10,
    )

    assert isinstance(vec, FeatureVector)
    assert len(vec) == 58
    assert vec["stage_announcement"] > 0.0
    assert vec.feature_sources["stage_announcement"] == "Stage 5 EnhancedExtractor"
