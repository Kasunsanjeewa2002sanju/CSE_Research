"""Linear and Regularized regression/classification models (OLS, Ridge, Lasso, ElasticNet, Logistic L2).

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Hyperparameters tuned strictly on inner-validation slice.
- Rule R4: Predicts log returns; levels reconstructed.
- Protocol: Evaluated on Feature Sets A, B, and C across all 5 phases and horizons h=1, h=5.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, LogisticRegression, Ridge

from cse.features.pipeline import PhaseDataSet
from cse.utils.logger import get_logger

logger = get_logger("cse.models.statistical.linear")


def tune_linear_model(
    model_cls: Any,
    param_grid: List[Dict[str, Any]],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_inner_val: pd.DataFrame,
    y_inner_val: pd.Series,
    is_classifier: bool = False,
    seed: int = 42,
) -> Tuple[Dict[str, Any], Any]:
    """Tune hyperparameters on inner-validation split and refit best model on full training set."""
    best_score = float("-inf")
    best_params = param_grid[0] if param_grid else {}

    for params in param_grid:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if "random_state" in model_cls.__init__.__code__.co_varnames:
                    est = model_cls(**params, random_state=seed)
                else:
                    est = model_cls(**params)

                est.fit(X_train.values, y_train.values)
                preds = est.predict(X_inner_val.values)

                if is_classifier:
                    # Direction accuracy or negative log-loss on inner validation
                    score = float(np.mean(preds == y_inner_val.values))
                else:
                    # Out-of-sample R2 on inner validation
                    ss_tot = np.sum((y_inner_val.values - np.mean(y_train.values)) ** 2)
                    ss_res = np.sum((y_inner_val.values - preds) ** 2)
                    score = float(1.0 - ss_res / (ss_tot + 1e-12))

                if score > best_score:
                    best_score = score
                    best_params = params
        except Exception:
            continue

    # Refit best parameters on full training set
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if "random_state" in model_cls.__init__.__code__.co_varnames:
            best_model = model_cls(**best_params, random_state=seed)
        else:
            best_model = model_cls(**best_params)
        best_model.fit(X_train.values, y_train.values)

    return best_params, best_model


class LinearReturnModel:
    """Standard OLS Multiple Linear Regression model for returns."""

    name: str = "ols"
    family: str = "statistical"

    def __init__(self, fit_intercept: bool = True, seed: int = 42) -> None:
        self.fit_intercept = fit_intercept
        self.seed = seed
        self.fitted_model_: Optional[LinearRegression] = None

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> LinearReturnModel:
        self.fitted_model_ = LinearRegression(fit_intercept=self.fit_intercept)
        self.fitted_model_.fit(X_train.values, y_train.values)
        return self

    def predict_phase(self, phase_data: PhaseDataSet, full_df: pd.DataFrame) -> pd.DataFrame:
        """Fit on train and generate prediction dataframe for validation split."""
        self.fit(phase_data.train.X, phase_data.train.y_ret)

        y_pred_ret = self.fitted_model_.predict(phase_data.val.X.values)
        y_true_ret = phase_data.val.y_ret.values
        y_true_dir = phase_data.val.y_dir.values
        dates = phase_data.val.dates.values
        val_indices = phase_data.val.indices

        aspi_t = full_df.loc[val_indices, "aspi"].values.astype(float)
        aspi_pred_level = aspi_t * np.exp(y_pred_ret)
        y_pred_dir = (y_pred_ret > 0).astype(int)
        p_up = 1.0 / (1.0 + np.exp(-15.0 * y_pred_ret))

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


class RegularizedLinearModel:
    """Regularized linear model (Ridge, Lasso, ElasticNet) with inner-validation tuning."""

    family: str = "statistical"

    def __init__(
        self,
        model_type: str = "ridge",  # 'ridge', 'lasso', 'elastic_net'
        seed: int = 42,
    ) -> None:
        self.model_type = model_type.lower()
        self.name = self.model_type
        self.seed = seed
        self.fitted_model_: Any = None
        self.best_params_: Dict[str, Any] = {}

    def predict_phase(self, phase_data: PhaseDataSet, full_df: pd.DataFrame) -> pd.DataFrame:
        """Tune on inner-val, fit on full train, and evaluate on outer validation."""
        if self.model_type == "ridge":
            cls = Ridge
            param_grid = [{"alpha": a} for a in [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]]
        elif self.model_type == "lasso":
            cls = Lasso
            param_grid = [{"alpha": a, "max_iter": 5000} for a in [1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 0.1]]
        elif self.model_type == "elastic_net":
            cls = ElasticNet
            param_grid = [
                {"alpha": a, "l1_ratio": r, "max_iter": 5000}
                for a in [1e-3, 1e-2, 0.1, 1.0]
                for r in [0.2, 0.5, 0.8]
            ]
        else:
            raise ValueError(f"Unknown regularized model type: {self.model_type}")

        best_params, fitted_model = tune_linear_model(
            model_cls=cls,
            param_grid=param_grid,
            X_train=phase_data.train.X,
            y_train=phase_data.train.y_ret,
            X_inner_val=phase_data.inner_val.X,
            y_inner_val=phase_data.inner_val.y_ret,
            is_classifier=False,
            seed=self.seed,
        )
        self.best_params_ = best_params
        self.fitted_model_ = fitted_model

        y_pred_ret = self.fitted_model_.predict(phase_data.val.X.values)
        y_true_ret = phase_data.val.y_ret.values
        y_true_dir = phase_data.val.y_dir.values
        dates = phase_data.val.dates.values
        val_indices = phase_data.val.indices

        aspi_t = full_df.loc[val_indices, "aspi"].values.astype(float)
        aspi_pred_level = aspi_t * np.exp(y_pred_ret)
        y_pred_dir = (y_pred_ret > 0).astype(int)
        p_up = 1.0 / (1.0 + np.exp(-15.0 * y_pred_ret))

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


class LogisticDirectionModel:
    """L2 Regularized Logistic Regression model for market direction forecasting."""

    name: str = "logistic_regression"
    family: str = "statistical"

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.fitted_model_: Optional[LogisticRegression] = None
        self.best_params_: Dict[str, Any] = {}

    def predict_phase(self, phase_data: PhaseDataSet, full_df: pd.DataFrame) -> pd.DataFrame:
        """Tune C on inner-val, fit on full train, and predict on outer validation."""
        param_grid = [{"C": c, "penalty": "l2", "solver": "lbfgs", "max_iter": 2000} for c in [1e-3, 1e-2, 0.1, 1.0, 10.0]]

        best_params, fitted_model = tune_linear_model(
            model_cls=LogisticRegression,
            param_grid=param_grid,
            X_train=phase_data.train.X,
            y_train=phase_data.train.y_dir,
            X_inner_val=phase_data.inner_val.X,
            y_inner_val=phase_data.inner_val.y_dir,
            is_classifier=True,
            seed=self.seed,
        )
        self.best_params_ = best_params
        self.fitted_model_ = fitted_model

        probs = self.fitted_model_.predict_proba(phase_data.val.X.values)
        p_up = probs[:, 1]
        y_pred_dir = (p_up > 0.5).astype(int)

        # Baseline mean return from training set scaled by direction forecast
        train_mean_ret = float(phase_data.train.y_ret.mean())
        # Implied return prediction: sign(p_up - 0.5) * |train_mean_ret|
        y_pred_ret = np.where(p_up > 0.5, abs(train_mean_ret), -abs(train_mean_ret))

        y_true_ret = phase_data.val.y_ret.values
        y_true_dir = phase_data.val.y_dir.values
        dates = phase_data.val.dates.values
        val_indices = phase_data.val.indices

        aspi_t = full_df.loc[val_indices, "aspi"].values.astype(float)
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
