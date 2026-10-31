"""Tree-based Shallow ML models (Random Forest, Extra Trees, Gradient Boosting, XGBoost, LightGBM, CatBoost).

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Tuning on inner-val slice, calibrator on inner-val slice, feature importances from train only.
- Rule R4: Predicts log returns; levels reconstructed.
- Rule R7: Fixed seeds (42, 123, 999 for stochastic models).
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRegressor
import lightgbm as lgb
from sklearn.ensemble import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
import xgboost as xgb

from cse.features.pipeline import PhaseDataSet
from cse.models.shallow.calibrator import InnerSliceCalibrator
from cse.models.shallow.tuner import tune_model_on_inner_val
from cse.utils.logger import get_logger

logger = get_logger("cse.models.shallow.tree_models")


class TreeModelBase:
    """Base class for tree-based ensemble models with tuning, calibration, and feature importances."""

    family: str = "shallow"

    def __init__(
        self,
        tree_type: str = "random_forest",  # 'random_forest', 'extra_trees', 'gradient_boosting', 'xgboost', 'lightgbm', 'catboost'
        mode: str = "regressor",          # 'regressor' (y_ret) or 'classifier' (y_dir)
        seed: int = 42,
    ) -> None:
        self.tree_type = tree_type.lower()
        self.mode = mode.lower()
        self.seed = seed
        self.name = f"{self.tree_type}_{'reg' if self.mode == 'regressor' else 'clf'}"
        self.fitted_model_: Any = None
        self.best_params_: Dict[str, Any] = {}
        self.budget_size_: int = 0
        self.calibrator_: Optional[InnerSliceCalibrator] = None
        self.feature_importances_: Dict[str, float] = {}

    def _get_regressor(self, params: Dict[str, Any], seed: int) -> Any:
        if self.tree_type == "random_forest":
            return RandomForestRegressor(**params, random_state=seed, n_jobs=1)
        elif self.tree_type == "extra_trees":
            return ExtraTreesRegressor(**params, random_state=seed, n_jobs=1)
        elif self.tree_type == "gradient_boosting":
            return GradientBoostingRegressor(**params, random_state=seed)
        elif self.tree_type == "xgboost":
            return xgb.XGBRegressor(**params, random_state=seed, n_jobs=1, verbosity=0)
        elif self.tree_type == "lightgbm":
            return lgb.LGBMRegressor(**params, random_state=seed, n_jobs=1, verbose=-1)
        elif self.tree_type == "catboost":
            return CatBoostRegressor(**params, random_seed=seed, verbose=0, thread_count=1, allow_writing_files=False)
        raise ValueError(f"Unknown tree type: {self.tree_type}")

    def _get_classifier(self, params: Dict[str, Any], seed: int) -> Any:
        if self.tree_type == "random_forest":
            return RandomForestClassifier(**params, random_state=seed, n_jobs=1)
        elif self.tree_type == "extra_trees":
            return ExtraTreesClassifier(**params, random_state=seed, n_jobs=1)
        elif self.tree_type == "gradient_boosting":
            return GradientBoostingClassifier(**params, random_state=seed)
        elif self.tree_type == "xgboost":
            return xgb.XGBClassifier(**params, random_state=seed, n_jobs=1, verbosity=0, eval_metric="logloss")
        elif self.tree_type == "lightgbm":
            return lgb.LGBMClassifier(**params, random_state=seed, n_jobs=1, verbose=-1)
        elif self.tree_type == "catboost":
            return CatBoostClassifier(**params, random_seed=seed, verbose=0, thread_count=1, allow_writing_files=False)
        raise ValueError(f"Unknown tree type: {self.tree_type}")

    def _extract_feature_importances(self, feature_names: List[str]) -> Dict[str, float]:
        """Extract feature importances from fitted model on training data only."""
        if hasattr(self.fitted_model_, "feature_importances_"):
            imps = self.fitted_model_.feature_importances_
            total = float(np.sum(imps))
            norm_imps = imps / (total + 1e-12)
            return {name: float(imp) for name, imp in zip(feature_names, norm_imps)}
        return {}

    def predict_phase(
        self,
        phase_data: PhaseDataSet,
        full_df: pd.DataFrame,
        best_params_override: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Run inner-validation tuning, fit on full training set, calibrate if classifier, predict on val."""
        is_clf = (self.mode == "classifier")
        factory = (lambda p, seed: self._get_classifier(p, seed)) if is_clf else (lambda p, seed: self._get_regressor(p, seed))

        X_train_arr = phase_data.train.X.values
        y_train_arr = phase_data.train.y_dir.values if is_clf else phase_data.train.y_ret.values

        X_inval_arr = phase_data.inner_val.X.values
        y_inval_arr = phase_data.inner_val.y_dir.values if is_clf else phase_data.inner_val.y_ret.values

        # 1. Inner validation tuning with fixed budget (or reuse tuned params from primary seed)
        if best_params_override is not None:
            self.best_params_ = best_params_override
            self.budget_size_ = 3
        else:
            budget_name = self.tree_type
            best_params, budget_size = tune_model_on_inner_val(
                model_factory=factory,
                budget_name=budget_name,
                X_train=X_train_arr,
                y_train=y_train_arr,
                X_inner_val=X_inval_arr,
                y_inner_val=y_inval_arr,
                is_classifier=is_clf,
                seed=self.seed,
            )
            self.best_params_ = best_params
            self.budget_size_ = budget_size

        # 2. Refit best model on full training set
        self.fitted_model_ = factory(self.best_params_, seed=self.seed)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fitted_model_.fit(X_train_arr, y_train_arr)

        # 3. Extract training-only feature importances
        self.feature_importances_ = self._extract_feature_importances(phase_data.feature_names)

        # 4. For classifiers, fit probability calibrator on inner-validation slice (Platt sigmoid)
        if is_clf:
            self.calibrator_ = InnerSliceCalibrator(method="sigmoid")
            self.calibrator_.fit_calibration(
                base_clf=self.fitted_model_,
                X_inner_val=X_inval_arr,
                y_inner_val=phase_data.inner_val.y_dir.values,
            )

        # 5. Out-of-sample prediction on outer validation slice
        X_val_arr = phase_data.val.X.values
        y_true_ret = phase_data.val.y_ret.values
        y_true_dir = phase_data.val.y_dir.values
        dates = phase_data.val.dates.values
        val_indices = phase_data.val.indices
        aspi_t = full_df.loc[val_indices, "aspi"].values.astype(float)

        if is_clf:
            # Predict calibrated probability
            probs = self.calibrator_.predict_proba(self.fitted_model_, X_val_arr)
            p_up = probs[:, 1]
            y_pred_dir = (p_up > 0.5).astype(int)
            train_mean_ret = float(phase_data.train.y_ret.mean())
            y_pred_ret = np.where(p_up > 0.5, abs(train_mean_ret), -abs(train_mean_ret))
        else:
            y_pred_ret = self.fitted_model_.predict(X_val_arr)
            y_pred_dir = (y_pred_ret > 0).astype(int)
            p_up = 1.0 / (1.0 + np.exp(-15.0 * y_pred_ret))

        aspi_pred_level = aspi_t * np.exp(y_pred_ret)

        df_out = pd.DataFrame({
            "model": self.name,
            "family": self.family,
            "phase": phase_data.phase,
            "horizon": phase_data.horizon,
            "feature_set": phase_data.feature_set,
            "date": dates,
            "y_true_ret": y_true_ret,
            "y_pred_ret": y_pred_ret,
            "p_up": p_up,
            "y_true_dir": y_true_dir,
            "y_pred_dir": y_pred_dir,
            "aspi_t": aspi_t,
            "aspi_pred_level": aspi_pred_level,
            "seed": self.seed,
        })
        return df_out
