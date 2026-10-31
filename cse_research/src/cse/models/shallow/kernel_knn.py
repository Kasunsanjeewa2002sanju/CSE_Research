"""Kernel and distance-based Shallow ML models (SVR, SVC with RBF, and k-NN).

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Tuning on inner-val slice, calibrator on inner-val slice.
- Rule R4: Predicts log returns; levels reconstructed.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC, SVR

from cse.features.pipeline import PhaseDataSet
from cse.models.shallow.calibrator import InnerSliceCalibrator
from cse.models.shallow.tuner import tune_model_on_inner_val
from cse.utils.logger import get_logger

logger = get_logger("cse.models.shallow.kernel_knn")


class KernelKNNModel:
    """Kernel SVM (SVR/SVC) and k-Nearest Neighbors models."""

    family: str = "shallow"

    def __init__(
        self,
        model_type: str = "svr",  # 'svr', 'svc', 'knn_reg', 'knn_clf'
        seed: int = 42,
    ) -> None:
        self.model_type = model_type.lower()
        self.seed = seed
        self.name = self.model_type
        self.fitted_model_: Any = None
        self.best_params_: Dict[str, Any] = {}
        self.budget_size_: int = 0
        self.calibrator_: Optional[InnerSliceCalibrator] = None

        if "clf" in self.model_type or self.model_type == "svc":
            self.mode = "classifier"
        else:
            self.mode = "regressor"

    def _get_estimator(self, params: Dict[str, Any], seed: int) -> Any:
        if self.model_type == "svr":
            return SVR(**params, kernel="rbf")
        elif self.model_type == "svc":
            return SVC(**params, kernel="rbf", probability=False, random_state=seed)
        elif self.model_type == "knn_reg":
            return KNeighborsRegressor(**params, n_jobs=1)
        elif self.model_type == "knn_clf":
            return KNeighborsClassifier(**params, n_jobs=1)
        raise ValueError(f"Unknown kernel/knn model type: {self.model_type}")

    def predict_phase(self, phase_data: PhaseDataSet, full_df: pd.DataFrame) -> pd.DataFrame:
        """Run inner-validation tuning, fit on full training set, calibrate if classifier, predict on val."""
        is_clf = (self.mode == "classifier")
        factory = lambda p, seed: self._get_estimator(p, seed)

        X_train_arr = phase_data.train.X.values
        y_train_arr = phase_data.train.y_dir.values if is_clf else phase_data.train.y_ret.values

        X_inval_arr = phase_data.inner_val.X.values
        y_inval_arr = phase_data.inner_val.y_dir.values if is_clf else phase_data.inner_val.y_ret.values

        # Subsample training data if very large for SVR/SVC quadratic memory
        if "sv" in self.model_type and len(X_train_arr) > 2500:
            sub_idx = np.arange(len(X_train_arr) - 2500, len(X_train_arr))
            X_train_fit = X_train_arr[sub_idx]
            y_train_fit = y_train_arr[sub_idx]
        else:
            X_train_fit = X_train_arr
            y_train_fit = y_train_arr

        # 1. Inner validation tuning with fixed budget
        budget_name = "knn" if "knn" in self.model_type else "svr_svc"
        best_params, budget_size = tune_model_on_inner_val(
            model_factory=factory,
            budget_name=budget_name,
            X_train=X_train_fit,
            y_train=y_train_fit,
            X_inner_val=X_inval_arr,
            y_inner_val=y_inval_arr,
            is_classifier=is_clf,
            seed=self.seed,
        )
        self.best_params_ = best_params
        self.budget_size_ = budget_size

        # 2. Refit best model on training set
        self.fitted_model_ = factory(self.best_params_, seed=self.seed)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fitted_model_.fit(X_train_fit, y_train_fit)

        # 3. For classifiers, fit probability calibrator on inner-validation slice (Platt scaling)
        if is_clf:
            self.calibrator_ = InnerSliceCalibrator(method="sigmoid")
            self.calibrator_.fit_calibration(
                base_clf=self.fitted_model_,
                X_inner_val=X_inval_arr,
                y_inner_val=phase_data.inner_val.y_dir.values,
            )

        # 4. Out-of-sample prediction on outer validation slice
        X_val_arr = phase_data.val.X.values
        y_true_ret = phase_data.val.y_ret.values
        y_true_dir = phase_data.val.y_dir.values
        dates = phase_data.val.dates.values
        val_indices = phase_data.val.indices
        aspi_t = full_df.loc[val_indices, "aspi"].values.astype(float)

        if is_clf:
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
