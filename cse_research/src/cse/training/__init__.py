"""CSE Training & Retraining Package (Stage 8).

Staging and evaluation pipeline for model retraining:
- dataset_builder: Compiles 57 Stage 6 features + FinBERT sentiment scores + CAR targets.
- retrain: Walk-forward temporal retraining, CatBoost regression, SHAP interpretation.
"""

from __future__ import annotations

from cse.training.dataset_builder import (
    CANDIDATE_FEATURE_COLUMNS,
    SENTIMENT_FEATURE_COLS,
    build_training_dataset,
    load_training_dataset,
)
from cse.training.retrain import (
    CandidateModelTrainer,
    WalkForwardResult,
    train_candidate_model,
)

__all__ = [
    "CANDIDATE_FEATURE_COLUMNS",
    "SENTIMENT_FEATURE_COLS",
    "build_training_dataset",
    "load_training_dataset",
    "CandidateModelTrainer",
    "WalkForwardResult",
    "train_candidate_model",
]
