"""Unit and Integration Tests for Stage 3 Prior Calculator."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest

# Ensure cse_research/src is on sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cse.news.historical_db import init_db
from cse.news.prior_calculator import PriorCalculator, get_default_log_path
from cse.news.similarity import NumpyFlatIPIndex, SimilarityIndex
from cse.scenario.feature_builder import ScenarioFeatureBuilder
from cse.news.schema import NewsExtraction


@pytest.fixture
def prior_calculator() -> PriorCalculator:
    """Fixture providing initialized PriorCalculator connected to production index."""
    return PriorCalculator()


def test_a_rate_cuts_vs_rate_raises_difference(prior_calculator: PriorCalculator) -> None:
    """Test A: 'Central Bank cuts policy rate' vs 'Central Bank raises policy rate'
    must produce DIFFERENT prior_median_car (difference > 0.5% = 0.005).
    """
    p_cuts = prior_calculator.get_prior("Central Bank cuts policy rate", horizon=10)
    p_raises = prior_calculator.get_prior("Central Bank raises policy rate", horizon=10)

    cuts_median = p_cuts["prior_median_car"]
    raises_median = p_raises["prior_median_car"]
    diff = abs(cuts_median - raises_median)

    print(f"\n[Test A] Cuts 10d: {cuts_median:+.6f} | Raises 10d: {raises_median:+.6f} | Diff: {diff:.6f}")

    assert diff > 0.005, (
        f"Expected prior_median_car difference > 0.5% (0.005), but got {diff:.6f} "
        f"(cuts={cuts_median:.6f}, raises={raises_median:.6f})"
    )
    assert cuts_median > raises_median, "Rate cuts prior should be more positive than rate raises prior"


def test_b_imf_approves_vs_delays_difference(prior_calculator: PriorCalculator) -> None:
    """Test B: 'IMF approves loan tranche' vs 'IMF delays loan tranche'
    must produce DIFFERENT priors.
    """
    p_app = prior_calculator.get_prior("IMF approves loan tranche", horizon=5)
    p_del = prior_calculator.get_prior("IMF delays loan tranche", horizon=5)

    print(f"\n[Test B] IMF Approves: {p_app['prior_median_car']:+.6f} | Delays: {p_del['prior_median_car']:+.6f}")

    assert p_app["prior_median_car"] != p_del["prior_median_car"], (
        f"Expected different priors for approval vs delay, but both got {p_app['prior_median_car']}"
    )
    assert p_app["direction"] > p_del["direction"], (
        f"Expected direction for approval ({p_app['direction']}) > delay ({p_del['direction']})"
    )


def test_c_unknown_irrelevant_news_fallback(prior_calculator: PriorCalculator) -> None:
    """Test C: Unknown/irrelevant news -> fallback to category average, log fallback_used=True."""
    irrelevant_headline = "Unidentified astronomical satellite completes solar orbit maneuver"
    res = prior_calculator.get_prior(irrelevant_headline, horizon=5)

    assert res["fallback_used"] is True, "Expected fallback_used=True for unknown/irrelevant news"
    assert res["fallback_level"] in {"category", "overall", "zero"}

    # Verify audit entry was logged to data/prior_calls.log
    log_path = get_default_log_path()
    assert log_path.exists(), f"Expected log file at {log_path}"

    with open(log_path, "r", encoding="utf-8") as f:
        log_lines = f.readlines()

    assert len(log_lines) > 0, "Log file should contain entries"
    latest_line = log_lines[-1]
    assert "fallback_used=True" in latest_line
    assert "horizon=5" in latest_line


def test_d_empty_db_graceful_fallback() -> None:
    """Test D: Empty DB -> prior = 0.0, no crash."""
    scratch_dir = root_dir / ".cache" / "pytest_empty_db"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    empty_db_path = scratch_dir / "empty_test.db"

    if empty_db_path.exists():
        try:
            os.remove(empty_db_path)
        except Exception:
            pass

    # Initialize empty schema with 0 news items
    init_db(empty_db_path)
    empty_conn = sqlite3.connect(str(empty_db_path))

    # Initialize empty similarity index
    empty_index = SimilarityIndex(
        index_path=scratch_dir / "empty.faiss",
        meta_path=scratch_dir / "empty.pkl",
        auto_load=False,
    )
    empty_index.index = NumpyFlatIPIndex(d=384)
    empty_index.metadata = []

    empty_calc = PriorCalculator(
        similarity_index=empty_index,
        db_conn=empty_conn,
        log_path=scratch_dir / "empty_prior.log",
    )

    res = empty_calc.get_prior("Central Bank cuts policy rate", horizon=5)

    assert res["prior_median_car"] == 0.0
    assert res["prior_mean_car"] == 0.0
    assert res["prior_std"] == 0.0
    assert res["n_effective"] == 0.0
    assert res["fallback_used"] is True
    assert res["fallback_level"] == "zero"

    empty_conn.close()


def test_prior_clamping(prior_calculator: PriorCalculator) -> None:
    """Verify that returned priors are clamped to [-0.05, +0.05] (-5% to +5%)."""
    for h in [1, 2, 5, 10]:
        res = prior_calculator.get_prior("Central Bank cuts policy rate", horizon=h)
        assert -0.05 <= res["prior_median_car"] <= 0.05
        assert -0.05 <= res["prior_mean_car"] <= 0.05


def test_feature_builder_integration() -> None:
    """Verify that ScenarioFeatureBuilder populates prior_median_car and prior_mean_car
    via PriorCalculator when headline is provided.
    """
    builder = ScenarioFeatureBuilder()
    news = NewsExtraction(
        is_relevant=True,
        event_category="central_bank_or_monetary_policy",
        stage="none",
        expected_direction="positive",
    )

    x_true, x_false, meta = builder.build_scenario_features(
        news_item=news,
        row_idx=0,
        as_of_date="2025-01-10",
        headline="Central Bank cuts policy rate",
    )

    assert "prior_knn_info" in meta, "Expected prior_knn_info in event_meta when headline is provided"
    knn_info = meta["prior_knn_info"]

    prior_med_col_idx = builder.feature_cols.index("prior_median_car")
    val_in_vector = x_true[0, prior_med_col_idx]

    assert abs(val_in_vector - knn_info["prior_median_car"]) < 1e-6
    assert abs(val_in_vector) <= 0.05
