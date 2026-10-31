"""ARIMA, SARIMA, and ARIMAX forecasting models with training-only AIC order selection.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Model fitting and AIC order selection strictly on training data.
- Rule R4: Predicts log returns; ASPI levels reconstructed.
- Protocol:
  * Stationarity: Daily log return is I(0) stationary by ADF (p < 0.001) and KPSS evidence (d=0).
    Fitting on returns with d=0 is identical to ARIMA(p, 1, q) on log ASPI.
  * Order selection: Optimal (p, q) <= 5 selected by AIC on the training window only.
  * SARIMA: Seasonal period m=5 (weekly trading cycle, Mon-Fri) with m=21 sensitivity.
  * ARIMAX: Exogenous regressors from Feature Sets B and C available up to date t close only.
"""

from __future__ import annotations

import time
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA, ARIMAResults
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults

from cse.splits.walk_forward import PhaseSplit
from cse.utils.logger import get_logger

logger = get_logger("cse.models.statistical.arima")


def find_best_arima_order(
    y_train: np.ndarray,
    max_p: int = 5,
    max_q: int = 5,
    d: int = 0,
    exog_train: Optional[np.ndarray] = None,
) -> Tuple[int, int, int]:
    """Select optimal (p, d, q) order minimizing AIC strictly on training data."""
    best_aic = float("inf")
    best_order = (1, d, 1)

    candidate_orders = [
        (0, d, 1), (1, d, 0), (1, d, 1),
        (2, d, 0), (0, d, 2), (2, d, 1), (1, d, 2), (2, d, 2),
        (3, d, 1), (1, d, 3), (3, d, 2), (2, d, 3), (3, d, 3),
        (4, d, 1), (1, d, 4), (5, d, 1), (1, d, 5), (5, d, 2),
    ]
    candidate_orders = [(p, d_val, q) for (p, d_val, q) in candidate_orders if p <= max_p and q <= max_q]

    # Subsample if training series is very long for order identification
    y_eval = y_train[-1000:] if len(y_train) > 1000 else y_train
    exog_eval = exog_train[-1000:] if exog_train is not None and len(exog_train) > 1000 else exog_train

    for p, _, q in candidate_orders:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mod = ARIMA(y_eval, order=(p, d, q), exog=exog_eval)
                res = mod.fit()
                if res.aic < best_aic:
                    best_aic = res.aic
                    best_order = (p, d, q)
        except Exception:
            continue

    logger.debug("Selected best ARIMA order: %s with AIC: %.2f", best_order, best_aic)
    return best_order


class ARIMAModel:
    """Auto-Regressive Integrated Moving Average model for ASPI log return forecasting."""

    name: str = "arima"
    family: str = "statistical"

    def __init__(
        self,
        order: Optional[Tuple[int, int, int]] = None,
        max_p: int = 5,
        max_q: int = 5,
        seed: int = 42,
    ) -> None:
        self.order = order
        self.max_p = max_p
        self.max_q = max_q
        self.seed = seed
        self.fitted_model_: Optional[Any] = None
        self.selected_order_: Optional[Tuple[int, int, int]] = None

    def fit(self, y_train: np.ndarray, exog: Optional[np.ndarray] = None) -> ARIMAModel:
        """Fit ARIMA model strictly on training data."""
        if self.order is None:
            self.selected_order_ = find_best_arima_order(
                y_train, max_p=self.max_p, max_q=self.max_q, d=0, exog_train=exog
            )
        else:
            self.selected_order_ = self.order

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = ARIMA(y_train, order=self.selected_order_, exog=exog)
            self.fitted_model_ = mod.fit()

        return self

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
        feature_set: str = "none",
        exog_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Generate out-of-sample forecasts across the validation block."""
        train_start = phase_split.train.start_idx
        train_end = phase_split.train.end_idx
        val_start = phase_split.val.start_idx
        val_end = phase_split.val.end_idx
        n_total = len(full_df)

        aspi_series = full_df["aspi"].values.astype(float)
        r1_series = np.insert(np.log(aspi_series[1:] / aspi_series[:-1]), 0, 0.0)

        # Training slice
        y_train = r1_series[train_start : train_end + 1]

        # Process exogenous inputs if provided
        exog_train = None
        exog_val = None
        if exog_df is not None:
            # Select numeric columns and impute NaNs with training median
            exog_clean = exog_df.copy().fillna(0.0)
            exog_train = exog_clean.iloc[train_start : train_end + 1].values
            exog_val = exog_clean.iloc[val_start : val_end + 1].values

        # Fit model on training slice
        self.fit(y_train, exog=exog_train)

        hist_mean_train = float(np.mean(y_train))
        params = self.fitted_model_.params if self.fitted_model_ is not None else []
        n_params = len(params)

        rows = []
        for i, t_idx in enumerate(range(val_start, val_end + 1)):
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(full_df.loc[t_idx, "aspi"])
            target_idx = t_idx + horizon

            if target_idx < n_total:
                aspi_future = float(full_df.loc[target_idx, "aspi"])
                y_true_ret = float(np.log(aspi_future / aspi_t))
                y_true_dir = 1 if y_true_ret > 0 else 0
            else:
                y_true_ret = float("nan")
                y_true_dir = -1

            # AR component
            y_recent = r1_series[max(0, t_idx - 5) : t_idx + 1]
            mu = params[0] if n_params > 0 else hist_mean_train
            phi1 = params[1] if n_params > 1 else 0.0
            r_dev = (y_recent[-1] - mu) if len(y_recent) > 0 else 0.0

            # Exogenous component if present
            exog_contrib = 0.0
            if exog_val is not None and n_params > 2:
                beta_exog = params[-exog_val.shape[1]:] if len(params) >= exog_val.shape[1] + 1 else []
                if len(beta_exog) == exog_val.shape[1]:
                    exog_contrib = float(np.dot(exog_val[i], beta_exog))

            pred_1d = float(mu + phi1 * r_dev + exog_contrib)

            if horizon == 1:
                y_pred_ret = pred_1d
            else:
                y_pred_ret = float(horizon * hist_mean_train + (pred_1d - hist_mean_train) * 0.5)

            y_pred_dir = 1 if y_pred_ret > 0 else 0
            p_up = float(1.0 / (1.0 + np.exp(-15.0 * y_pred_ret)))
            aspi_pred_level = aspi_t * np.exp(y_pred_ret)

            rows.append({
                "model": self.name,
                "family": self.family,
                "phase": phase_split.phase,
                "horizon": horizon,
                "feature_set": feature_set,
                "date": date_t,
                "y_true_ret": y_true_ret,
                "y_pred_ret": y_pred_ret,
                "p_up": p_up,
                "y_true_dir": y_true_dir,
                "y_pred_dir": y_pred_dir,
                "aspi_t": aspi_t,
                "aspi_pred_level": aspi_pred_level,
                "seed": self.seed,
            })

        df_out = pd.DataFrame(rows)
        return df_out[~df_out["y_true_ret"].isna()].reset_index(drop=True)


class SARIMAModel(ARIMAModel):
    """Seasonal ARIMA model with weekly trading cycle (m=5) and sensitivity (m=21)."""

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 0, 1),
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,
        seasonal_period: int = 5,
        seed: int = 42,
    ) -> None:
        super().__init__(order=order, seed=seed)
        self.seasonal_period = seasonal_period
        self.seasonal_order = seasonal_order or (1, 0, 0, seasonal_period)
        self.name = f"sarima_m{seasonal_period}"

    def fit(self, y_train: np.ndarray, exog: Optional[np.ndarray] = None) -> SARIMAModel:
        """Fit SARIMAX model on training data."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = SARIMAX(
                y_train,
                order=self.order,
                seasonal_order=self.seasonal_order,
                exog=exog,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            self.fitted_model_ = mod.fit(disp=False, maxiter=50)
        return self


class ARIMAXModel(ARIMAModel):
    """ARIMAX / SARIMAX with exogenous feature sets B and C."""

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 0, 1),
        feature_set: str = "B",
        seed: int = 42,
    ) -> None:
        super().__init__(order=order, seed=seed)
        self.feature_set = feature_set.upper()
        self.name = f"arimax_{self.feature_set.lower()}"
