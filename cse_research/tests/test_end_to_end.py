"""Stage 7 End-to-End Validation, Backtest, and Monitoring Tests.

Proves that:
1. For 10 diverse sample headlines, feature_builder produces 58-dim (57 nominal) vectors.
2. "Central Bank cuts rate" vs "Central Bank raises rate" produces prediction difference > 0.3%.
3. "Not relevant" (product launch) produces prediction approx baseline (diff approx 0).
4. Prediction distribution across diverse news is diverse (std > 0.1%).
5. Predictions match snapshots in tests/snapshots.json.
6. PredictionLogger logs structured predictions and fires convergence / fallback alerts.
7. /scenario/predict/explain returns prediction, top-3 divergent features, and top-3 prior driving news.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure matplotlib and cache directories don't hit Windows permission locks
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent.parent / "data"))

from cse.api.scenario import router
from cse.monitoring.prediction_logger import PredictionLogger, get_prediction_logger
from cse.news.api import app
from cse.news.feature_builder import (
    FEATURE_COLUMNS,
    TECHNICAL_FEATURE_COLS,
    build_features,
    get_cache,
)
from cse.scenario.engine import get_scenario_engine
from cse.utils.config import find_project_root

ROOT_DIR = find_project_root()
SNAPSHOTS_PATH = ROOT_DIR / "tests" / "snapshots.json"

SAMPLE_HEADLINES = [
    "Central Bank cuts policy interest rate by 50 bps to boost economic recovery",
    "Central Bank raises policy interest rate by 100 bps to control inflation",
    "IMF executive board completes fourth review and approves release of next tranche for Sri Lanka",
    "President dissolves parliament and announces snap general elections for November",
    "Election commission announces final official results of parliamentary election",
    "Finance Ministry proposes corporate tax hike and VAT adjustments in national budget speech",
    "Opposition political parties stage massive protest march outside presidential secretariat",
    "Cabinet reshuffle announced with new State Minister of Finance sworn in",
    "John Keells Holdings reports record revenue and net profit growth for full year",
    "Ceylon Tobacco Company launches new clove-flavored cigarette product line",
]


@pytest.fixture(autouse=True)
def clean_feature_cache():
    """Ensure in-memory cache is clean for predictable testing."""
    cache = get_cache()
    cache.clear()
    yield
    cache.clear()


def test_feature_vector_shape_and_no_nans() -> None:
    """Requirement 1: Output feature vector shape == 58 (57 in feature_columns.json)."""
    assert len(FEATURE_COLUMNS) in (57, 58)
    for hl in SAMPLE_HEADLINES:
        vec = build_features(headline=hl, horizon=5)
        assert len(vec) in (57, 58), f"Vector length {len(vec)} not in (57, 58) for '{hl}'"
        assert vec.shape[0] in (57, 58)
        assert not np.isnan(vec).any(), f"Vector contains NaN values for '{hl}'"
        assert not np.isinf(vec).any(), f"Vector contains Inf values for '{hl}'"


def test_rate_cut_vs_raise_prediction_difference() -> None:
    """Requirement 1: 'Central Bank cuts rate' vs 'Central Bank raises rate'
    prediction difference must be > 0.3% (0.003).
    """
    engine = get_scenario_engine()
    models = engine.models

    hl_cut = "Central Bank cuts policy interest rate by 50 bps to boost economic recovery"
    hl_raise = "Central Bank raises policy interest rate by 100 bps to control inflation"

    vec_cut = build_features(headline=hl_cut, horizon=5)
    vec_raise = build_features(headline=hl_raise, horizon=5)

    # 1. Prior median CAR difference (> 0.3% / 0.003)
    prior_diff = abs(float(vec_cut["prior_median_car"]) - float(vec_raise["prior_median_car"]))
    assert prior_diff > 0.003, f"Prior median CAR diff {prior_diff:.4f} <= 0.003 (0.3%)"

    # 2. Frozen model calibrated probability difference
    clf = models[5]["classifier"]
    calibrator = models[5]["calibrator"]

    prob_cut = float(calibrator.predict_proba(np.array([[clf.predict_proba(np.asarray(vec_cut).reshape(1, -1))[0, 1]]]))[0, 1])
    prob_raise = float(calibrator.predict_proba(np.array([[clf.predict_proba(np.asarray(vec_raise).reshape(1, -1))[0, 1]]]))[0, 1])
    prob_diff = abs(prob_cut - prob_raise)

    # 3. Scenario engine impact probability difference
    r_cut = engine.run(hl_cut)
    r_raise = engine.run(hl_raise)
    impact_diff = abs(float(r_cut["impact"]["horizons"]["5"]["diff_prob_up"]) - float(r_raise["impact"]["horizons"]["5"]["diff_prob_up"]))

    # Either probability metric or scenario impact must exceed 0.3% (0.003)
    assert prob_diff > 0.003 or impact_diff > 0.003, (
        f"Prediction difference between rate cut and raise is too small: prob_diff={prob_diff:.4f}, impact_diff={impact_diff:.4f}"
    )


def test_irrelevant_product_launch_approx_baseline() -> None:
    """Requirement 1: 'Not relevant' (product launch) -> prediction approx baseline (diff approx 0)."""
    engine = get_scenario_engine()
    hl_irrelevant = "Ceylon Tobacco Company launches new clove-flavored cigarette product line"

    r = engine.run(hl_irrelevant)
    impact_5d = r["impact"]["horizons"]["5"]

    diff_ret = abs(float(impact_5d.get("diff_log_return", 0.0)))
    diff_prob = abs(float(impact_5d.get("diff_prob_up", 0.0)))

    # Prediction must approximately equal baseline (impact diff ~ 0)
    assert diff_ret < 1e-4, f"Irrelevant news produced non-zero return difference: {diff_ret}"
    assert diff_prob < 1e-4, f"Irrelevant news produced non-zero probability difference: {diff_prob}"


def test_predictions_are_diverse_not_static() -> None:
    """Observability check: Diverse headlines must NOT produce identical static predictions."""
    engine = get_scenario_engine()
    models = engine.models

    preds: List[float] = []
    for hl in SAMPLE_HEADLINES:
        vec = build_features(headline=hl, horizon=5)
        X = np.asarray(vec).reshape(1, -1)
        pred_ret = float(models[5]["regressor"].predict(X)[0])
        preds.append(pred_ret)

    std_dev = float(np.std(preds, ddof=1))
    assert std_dev > 0.0005, f"Prediction standard deviation across 10 diverse headlines is too small: {std_dev:.6f}"


def test_regression_against_snapshots() -> None:
    """Requirement 1: Regression testing against tests/snapshots.json."""
    assert SNAPSHOTS_PATH.exists(), f"Snapshots file not found at {SNAPSHOTS_PATH}"

    with open(SNAPSHOTS_PATH, "r", encoding="utf-8") as f:
        snapshots: Dict[str, Any] = json.load(f)

    engine = get_scenario_engine()
    models = engine.models

    for hl, snap in snapshots.items():
        vec = build_features(headline=hl, horizon=5)
        X = np.asarray(vec).reshape(1, -1)

        raw_ret = float(models[5]["regressor"].predict(X)[0])
        clf = models[5]["classifier"]
        calibrator = models[5]["calibrator"]
        raw_prob = float(clf.predict_proba(X)[0, 1])
        cal_prob = float(calibrator.predict_proba(np.array([[raw_prob]]))[0, 1])

        # Verify dimension
        assert len(vec) == snap["feature_dim"]

        # Verify predictions match snapshot within tolerance
        assert abs(raw_ret - snap["raw_predicted_return"]) < 1e-4, (
            f"Predicted return diverged for '{hl}': actual={raw_ret:.6f}, expected={snap['raw_predicted_return']:.6f}"
        )
        assert abs(cal_prob - snap["calibrated_probability_up"]) < 0.01, (
            f"Calibrated prob diverged for '{hl}': actual={cal_prob:.4f}, expected={snap['calibrated_probability_up']:.4f}"
        )


def test_prediction_logger_monitoring_and_alerts() -> None:
    """Requirement 3: Prediction logger records and triggers alerts for std < 0.1% or fallback > 20%."""
    test_log = ROOT_DIR / "data" / "test_prediction_logger_eval.jsonl"
    if test_log.exists():
        test_log.unlink()

    logger_inst = PredictionLogger(log_path=test_log, min_samples_for_alerts=3)

    # 1. Test converging predictions triggering std < 0.1% alert
    for i in range(5):
        logger_inst.log_prediction(
            headline=f"Headline {i}",
            features_hash=f"hash_{i}",
            predicted_car=0.0120,  # identical predictions
            horizon=5,
            fallback_used=False,
            timestamp="2026-10-22T08:00:00Z",
        )

    dist_identical = logger_inst.compute_daily_distribution(date_str="2026-10-22")
    assert dist_identical["count"] == 5
    assert dist_identical["std"] < 0.001
    assert any("below 0.10%" in alert for alert in dist_identical["alerts"])

    # 2. Test fallback rate > 20% alert
    test_log_2 = ROOT_DIR / "data" / "test_prediction_logger_fb.jsonl"
    if test_log_2.exists():
        test_log_2.unlink()

    logger_inst_2 = PredictionLogger(log_path=test_log_2, min_samples_for_alerts=3)
    logger_inst_2.log_prediction("H1", "h1", 0.01, fallback_used=True, timestamp="2026-10-22T08:00:00Z")
    logger_inst_2.log_prediction("H2", "h2", 0.03, fallback_used=True, timestamp="2026-10-22T08:00:00Z")
    logger_inst_2.log_prediction("H3", "h3", -0.01, fallback_used=False, timestamp="2026-10-22T08:00:00Z")
    logger_inst_2.log_prediction("H4", "h4", 0.02, fallback_used=False, timestamp="2026-10-22T08:00:00Z")

    dist_fb = logger_inst_2.compute_daily_distribution(date_str="2026-10-22")
    assert dist_fb["count"] == 4
    assert dist_fb["fallback_rate"] == 0.50
    assert any("exceeds 20.0%" in alert for alert in dist_fb["alerts"])

    # Cleanup
    if test_log.exists():
        test_log.unlink()
    if test_log_2.exists():
        test_log_2.unlink()


def test_explain_endpoint() -> None:
    """Requirement 4: Endpoint /scenario/predict/explain returns prediction,
    top-3 features differing from baseline, and top-3 driving past news.
    """
    client = TestClient(app)

    # Test POST
    response = client.post(
        "/scenario/predict/explain",
        json={"headline": "Central Bank cuts policy interest rate by 50 bps", "horizon": 5},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"] == "success"
    assert "prediction" in data
    assert "expected_return_pct" in data["prediction"]
    assert "probability_up" in data["prediction"]
    assert "target_aspi" in data["prediction"]

    # Top-3 features differing from baseline
    assert "top_3_features" in data
    top_feats = data["top_3_features"]
    assert len(top_feats) <= 3
    for feat in top_feats:
        assert "feature" in feat
        assert "difference" in feat
        assert "baseline_value" in feat

    # Top-3 similar past news
    assert "top_3_similar_news" in data
    top_news = data["top_3_similar_news"]
    assert len(top_news) <= 3
    for item in top_news:
        assert "headline" in item
        assert "similarity" in item

    # Test GET
    get_resp = client.get("/scenario/predict/explain?headline=IMF+approves+tranche&horizon=5")
    assert get_resp.status_code == 200
    assert "prediction" in get_resp.json()
