"""Inner chronological validation tuner with fixed budget.

Adheres strictly to:
- Rule R2: Zero lookahead. Tuning evaluates exclusively on the inner validation split.
- Protocol: Fixed budget documented and recorded in metadata.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from cse.utils.logger import get_logger

logger = get_logger("cse.models.shallow.tuner")

# Fixed hyperparameter search budget (3 principled candidate configurations per model family)
# Balances regularization vs capacity for noisy financial returns while maintaining execution speed.
HYPERPARAM_BUDGETS: Dict[str, List[Dict[str, Any]]] = {
    "random_forest": [
        {"n_estimators": 50, "max_depth": 3, "min_samples_leaf": 10},
        {"n_estimators": 50, "max_depth": 5, "min_samples_leaf": 10},
        {"n_estimators": 80, "max_depth": 5, "min_samples_leaf": 20},
    ],
    "extra_trees": [
        {"n_estimators": 50, "max_depth": 3, "min_samples_leaf": 10},
        {"n_estimators": 50, "max_depth": 5, "min_samples_leaf": 10},
        {"n_estimators": 80, "max_depth": 5, "min_samples_leaf": 20},
    ],
    "gradient_boosting": [
        {"n_estimators": 40, "learning_rate": 0.02, "max_depth": 2},
        {"n_estimators": 60, "learning_rate": 0.05, "max_depth": 3},
        {"n_estimators": 80, "learning_rate": 0.05, "max_depth": 3},
    ],
    "xgboost": [
        {"n_estimators": 40, "learning_rate": 0.02, "max_depth": 2, "subsample": 0.8},
        {"n_estimators": 60, "learning_rate": 0.05, "max_depth": 3, "subsample": 0.8},
        {"n_estimators": 80, "learning_rate": 0.05, "max_depth": 3, "subsample": 0.8},
    ],
    "lightgbm": [
        {"n_estimators": 40, "learning_rate": 0.02, "max_depth": 3, "num_leaves": 7},
        {"n_estimators": 60, "learning_rate": 0.05, "max_depth": 4, "num_leaves": 15},
        {"n_estimators": 80, "learning_rate": 0.05, "max_depth": 4, "num_leaves": 15},
    ],
    "catboost": [
        {"iterations": 40, "learning_rate": 0.03, "depth": 3},
        {"iterations": 60, "learning_rate": 0.05, "depth": 4},
        {"iterations": 80, "learning_rate": 0.05, "depth": 4},
    ],
    "svr_svc": [
        {"C": 0.1, "gamma": "scale"},
        {"C": 1.0, "gamma": "scale"},
        {"C": 10.0, "gamma": "scale"},
    ],
    "knn": [
        {"n_neighbors": 10},
        {"n_neighbors": 25},
        {"n_neighbors": 50},
    ],
}


def tune_model_on_inner_val(
    model_factory: Any,
    budget_name: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_inner_val: np.ndarray,
    y_inner_val: np.ndarray,
    is_classifier: bool = False,
    seed: int = 42,
) -> Tuple[Dict[str, Any], int]:
    """Execute fixed budget tuning on inner validation slice.
    
    Returns:
        (best_params, total_budget)
    """
    candidates = HYPERPARAM_BUDGETS.get(budget_name, [{}])
    best_score = float("-inf")
    best_params = candidates[0]

    for params in candidates:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = model_factory(params, seed=seed)
                model.fit(X_train, y_train)

                preds = model.predict(X_inner_val)
                if is_classifier:
                    acc = float(np.mean(preds == y_inner_val))
                    score = acc
                else:
                    mse = float(np.mean((preds - y_inner_val) ** 2))
                    score = -mse

                if score > best_score:
                    best_score = score
                    best_params = params
        except Exception:
            continue

    return best_params, len(candidates)
