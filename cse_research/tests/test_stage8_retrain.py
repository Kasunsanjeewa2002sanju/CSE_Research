"""Stage 8 Retraining, Validation, and Model Comparison Test Suite.

Verifies:
1. dataset_builder produces valid training_data.parquet with:
   - 57 Stage 6 tabular features + 3 FinBERT sentiment features (60 candidate features).
   - Target = actual CAR (car_5d).
   - Correct time-based splits: 2022-2023 train, 2024 val, 2025 test, 2026 holdout.
2. retrain pipeline:
   - Runs walk-forward cross-validation across historical years.
   - Computes CatBoost Tree SHAP feature importances.
   - Generates interactive reports/shap_YYYYMMDD.html.
   - Saves candidate model to models/candidate_YYYYMMDD.cbm.
3. compare_models script:
   - Evaluates Frozen Model (57 feats) vs Candidate Model (60 feats) on holdout.
   - Checks promotion gates: MAE beat > 5% AND Event feature share > 25%.
   - Generates structured decision report.
4. STRICT INVARIANT: Frozen model (models/final/scenario_models.pkl) is NEVER modified.
"""

from __future__ import annotations

import json
import os
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

# Ensure project directories and scripts are on sys.path
_TEST_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _TEST_DIR.parent
_SRC_DIR = _PROJECT_ROOT / "src"
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"

for _p in [str(_SRC_DIR), str(_PROJECT_ROOT), str(_SCRIPTS_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Ensure matplotlib / cache directories don't hit Windows permission locks
os.environ.setdefault("MPLCONFIGDIR", str(_PROJECT_ROOT / "data"))

from cse.training.dataset_builder import (
    CANDIDATE_FEATURE_COLUMNS,
    DEFAULT_PARQUET_PATH,
    SENTIMENT_FEATURE_COLS,
    TARGET_COLUMN,
    build_training_dataset,
    load_training_dataset,
)
from cse.training.retrain import (
    CandidateModelTrainer,
    FROZEN_MODEL_PATH,
    MODELS_DIR,
    REPORTS_DIR,
    get_event_feature_names,
    load_base_hyperparameters,
    train_candidate_model,
)
from cse.utils.config import find_project_root
try:
    from scripts.compare_models import compare_models, load_candidate_model, load_frozen_model
except ImportError:
    import importlib
    _mod = importlib.import_module("compare_models")
    compare_models = _mod.compare_models
    load_candidate_model = _mod.load_candidate_model
    load_frozen_model = _mod.load_frozen_model

ROOT_DIR = find_project_root()
FEATURE_COLS_PATH = ROOT_DIR / "models" / "final" / "feature_columns.json"


@pytest.fixture(scope="module")
def training_df() -> pd.DataFrame:
    """Fixture providing loaded training dataset from data/training_data.parquet."""
    return load_training_dataset(DEFAULT_PARQUET_PATH)


def test_training_dataset_columns_and_splits(training_df: pd.DataFrame):
    """Test dataset column conformity, absence of nulls, and temporal splits."""
    assert not training_df.empty, "training_data.parquet should not be empty"
    assert len(training_df) >= 500, f"Expected at least 500 headlines, found {len(training_df)}"

    # 1. Target verification
    assert TARGET_COLUMN in training_df.columns, f"Target column '{TARGET_COLUMN}' missing"
    assert not training_df[TARGET_COLUMN].isna().any(), "Target column should contain no NaN values"
    assert "car_5d" in training_df.columns, "'car_5d' column missing"

    # 2. Stage 6 57-feature verification
    with open(FEATURE_COLS_PATH, "r", encoding="utf-8") as f:
        stage6_cols = json.load(f)
    assert len(stage6_cols) == 57, f"Expected 57 stage 6 columns, got {len(stage6_cols)}"
    for col in stage6_cols:
        assert col in training_df.columns, f"Stage 6 column '{col}' missing from training dataset"
        assert not training_df[col].isna().any(), f"Column '{col}' contains NaN values"

    # 3. Sentiment feature verification (3 FinBERT columns)
    for sent_col in SENTIMENT_FEATURE_COLS:
        assert sent_col in training_df.columns, f"Sentiment column '{sent_col}' missing"
        assert not training_df[sent_col].isna().any(), f"Sentiment column '{sent_col}' contains NaN values"
        assert (training_df[sent_col] >= 0.0).all() and (training_df[sent_col] <= 1.0).all(), (
            f"Sentiment scores for '{sent_col}' should be bounded in [0.0, 1.0]"
        )

    # 4. Total candidate feature count
    assert len(CANDIDATE_FEATURE_COLUMNS) == 60, (
        f"Candidate model should have exactly 60 features (57 nominal + 3 sentiment), got {len(CANDIDATE_FEATURE_COLUMNS)}"
    )

    # 5. Temporal splits verification
    splits = set(training_df["split"].unique())
    assert "train" in splits, "Split 'train' (2022-2023) should exist"
    assert "val" in splits, "Split 'val' (2024) should exist"
    assert "test" in splits, "Split 'test' (2025) should exist"
    assert "holdout" in splits, "Split 'holdout' (2026) should exist"

    # Check temporal partitioning logic
    train_dates = training_df[training_df["split"] == "train"]["published_at"].str[:4].astype(int)
    assert (train_dates <= 2023).all(), "Train split must be <= 2023"

    val_dates = training_df[training_df["split"] == "val"]["published_at"].str[:4].astype(int)
    assert (val_dates == 2024).all(), "Val split must be 2024"

    test_dates = training_df[training_df["split"] == "test"]["published_at"].str[:4].astype(int)
    assert (test_dates == 2025).all(), "Test split must be 2025"

    holdout_dates = training_df[training_df["split"] == "holdout"]["published_at"].str[:4].astype(int)
    assert (holdout_dates >= 2026).all(), "Holdout split must be >= 2026"


def test_walk_forward_trainer_and_shap(training_df: pd.DataFrame):
    """Test candidate model trainer, walk-forward CV, and SHAP calculation."""
    trainer = CandidateModelTrainer(dataset=training_df)

    # 1. Walk-forward cross-validation
    wf_res = trainer.run_walk_forward_validation()
    assert len(wf_res.folds) >= 2, "Expected at least 2 walk-forward validation folds"
    assert 0.0 < wf_res.mean_mae < 0.15, f"Mean MAE {wf_res.mean_mae} outside reasonable financial range"
    assert 0.40 <= wf_res.mean_directional_accuracy <= 1.0, f"Hit rate {wf_res.mean_directional_accuracy} out of bounds"

    # 2. Final model fitting
    model, df_train, df_test = trainer.fit_final_model(train_max_year=2024)
    assert len(df_train) > 0 and len(df_test) > 0, "Train and test partitions must be non-empty"

    # 3. SHAP feature analysis
    shap_data = trainer.compute_shap_analysis(model, df_test)
    assert "event_feature_importance_pct" in shap_data
    assert "sentiment_feature_importance_pct" in shap_data
    assert "ranked_features" in shap_data
    assert len(shap_data["ranked_features"]) == 60, "SHAP should rank all 60 candidate features"

    # Check that sentiment features are ranked
    sent_ranked = [f for f in shap_data["ranked_features"] if f["is_sentiment"]]
    assert len(sent_ranked) == 3, "Expected 3 sentiment features in SHAP rankings"


def test_train_candidate_model_end_to_end():
    """Test complete train_candidate_model execution and output artifact creation."""
    assert FROZEN_MODEL_PATH.exists(), "Frozen model must exist"
    frozen_mtime_before = FROZEN_MODEL_PATH.stat().st_mtime

    cand_path, shap_path, meta = train_candidate_model()

    # 1. Verify candidate model file
    assert cand_path.exists(), f"Candidate model not found at {cand_path}"
    assert cand_path.name.startswith("candidate_") and cand_path.suffix == ".cbm"
    assert cand_path.resolve() != FROZEN_MODEL_PATH.resolve(), "Candidate path must NOT equal frozen path!"

    # 2. Verify SHAP HTML report
    assert shap_path.exists(), f"SHAP HTML report not found at {shap_path}"
    with open(shap_path, "r", encoding="utf-8") as f:
        html = f.read()
    assert "<!DOCTYPE html>" in html
    assert "Tree SHAP Feature Importance Analysis" in html
    assert "FinBERT Sentiment" in html

    # 3. Verify metadata json
    assert meta["n_features"] == 60
    assert "event_feature_importance_pct" in meta["shap_summary"]

    # 4. STRICT GUARANTEE: Frozen model was NOT modified
    frozen_mtime_after = FROZEN_MODEL_PATH.stat().st_mtime
    assert frozen_mtime_before == frozen_mtime_after, "INVARIANT VIOLATION: scenario_models.pkl was modified!"


def test_model_comparison_and_promotion_gate():
    """Test scripts/compare_models.py evaluation logic and promotion gate checks."""
    frozen_mtime_before = FROZEN_MODEL_PATH.stat().st_mtime

    result = compare_models(split="test", horizon=5)

    # 1. Validate metrics structure
    m = result["metrics"]
    assert "frozen_mae" in m and "candidate_mae" in m
    assert "mae_reduction_pct" in m
    assert "frozen_directional_acc" in m and "candidate_directional_acc" in m

    # 2. Validate gates structure
    gates = result["gates"]
    assert "mae_beat_5pct" in gates
    assert "event_importance_25pct" in gates
    assert "overall_promotion_decision" in gates
    assert "decision_summary" in gates

    # 3. Check gate evaluation math
    mae_diff_pct = (m["frozen_mae"] - m["candidate_mae"]) / m["frozen_mae"] * 100.0
    assert abs(m["mae_reduction_pct"] - mae_diff_pct) < 0.05

    cand_event_share = result["feature_importance"]["candidate_event_share_pct"]
    assert gates["mae_beat_5pct"]["passed"] == (m["mae_reduction_pct"] > 5.0)
    assert gates["event_importance_25pct"]["passed"] == (cand_event_share > 25.0)

    # If either gate fails, promotion decision must be DO NOT PROMOTE
    if not (gates["mae_beat_5pct"]["passed"] and gates["event_importance_25pct"]["passed"]):
        assert "DO NOT PROMOTE" in gates["overall_promotion_decision"]

    # 4. Verify decision report file created
    report_file = Path(result["report_file"])
    assert report_file.exists(), f"Comparison report file missing: {report_file}"
    with open(report_file, "r", encoding="utf-8") as f:
        rep_content = f.read()
    assert "# Stage 8 Model Comparison & Promotion Review" in rep_content
    assert "Promotion Gate Evaluation" in rep_content
    assert "scenario_models.pkl" in rep_content

    # 5. STRICT GUARANTEE: Frozen model untouched
    frozen_mtime_after = FROZEN_MODEL_PATH.stat().st_mtime
    assert frozen_mtime_before == frozen_mtime_after, "INVARIANT VIOLATION: scenario_models.pkl was modified!"
