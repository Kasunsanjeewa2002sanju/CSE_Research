"""ETS / Holt-Winters and Theta forecasting models for CSE ASPI.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Model fitted strictly on training window.
- Rule R4: Predicts log returns; levels reconstructed.
- Protocol: Same phases, horizons h=1 and h=5, same prediction schema.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.forecasting.theta import ThetaModel

from cse.splits.walk_forward import PhaseSplit
from cse.utils.logger import get_logger

logger = get_logger("cse.models.statistical.ets_theta")


class ETSModel:
    """Holt-Winters Exponential Smoothing model for ASPI index forecasting."""

    name: str = "ets_holt_winters"
    family: str = "statistical"

    def __init__(
        self,
        trend: Optional[str] = "add",
        damped_trend: bool = True,
        seasonal: Optional[str] = None,
        seasonal_periods: Optional[int] = None,
        seed: int = 42,
    ) -> None:
        self.trend = trend
        self.damped_trend = damped_trend
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods
        self.seed = seed
        self.fitted_model_: Any = None

    def fit(self, log_aspi_train: np.ndarray) -> ETSModel:
        """Fit Exponential Smoothing model strictly on training log ASPI levels."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = ExponentialSmoothing(
                log_aspi_train,
                trend=self.trend,
                damped_trend=self.damped_trend,
                seasonal=self.seasonal,
                seasonal_periods=self.seasonal_periods,
                initialization_method="estimated",
            )
            self.fitted_model_ = mod.fit(optimized=True)
        return self

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
        feature_set: str = "none",
    ) -> pd.DataFrame:
        """Generate out-of-sample forecasts across the validation block."""
        train_start = phase_split.train.start_idx
        train_end = phase_split.train.end_idx
        val_start = phase_split.val.start_idx
        val_end = phase_split.val.end_idx
        n_total = len(full_df)

        aspi_series = full_df["aspi"].values.astype(float)
        log_aspi = np.log(aspi_series)

        # Fit model on training slice
        log_aspi_train = log_aspi[train_start : train_end + 1]
        self.fit(log_aspi_train)

        # Baseline training return rate
        r1_train = np.diff(log_aspi_train)
        hist_mean_train = float(np.mean(r1_train))

        # Retrieve estimated trend damping parameters
        slope = getattr(self.fitted_model_, "slope", None)
        b0 = float(slope[-1]) if slope is not None and len(slope) > 0 else hist_mean_train
        phi = float(getattr(self.fitted_model_.params, "get", lambda k, d: d)("damping_trend", 0.95))

        rows = []
        for t_idx in range(val_start, val_end + 1):
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(aspi_series[t_idx])
            target_idx = t_idx + horizon

            if target_idx < n_total:
                aspi_future = float(aspi_series[target_idx])
                y_true_ret = float(np.log(aspi_future / aspi_t))
                y_true_dir = 1 if y_true_ret > 0 else 0
            else:
                y_true_ret = float("nan")
                y_true_dir = -1

            # Forecast: damped linear drift over horizon h
            if horizon == 1:
                y_pred_ret = float(b0 * phi)
            else:
                # Cumulative damped trend: sum_{k=1}^h phi^k * b0
                cum_phi = sum(phi ** k for k in range(1, horizon + 1))
                y_pred_ret = float(b0 * cum_phi)

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


class ThetaForecastingModel:
    """Theta method model for ASPI index forecasting."""

    name: str = "theta"
    family: str = "statistical"

    def __init__(self, period: Optional[int] = None, seed: int = 42) -> None:
        self.period = period
        self.seed = seed
        self.fitted_model_: Any = None

    def fit(self, log_aspi_train: np.ndarray) -> ThetaForecastingModel:
        """Fit Theta model strictly on training log ASPI levels."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = ThetaModel(log_aspi_train, period=self.period, deseasonalize=False)
            self.fitted_model_ = mod.fit()
        return self

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
        feature_set: str = "none",
    ) -> pd.DataFrame:
        """Generate out-of-sample forecasts across the validation block."""
        train_start = phase_split.train.start_idx
        train_end = phase_split.train.end_idx
        val_start = phase_split.val.start_idx
        val_end = phase_split.val.end_idx
        n_total = len(full_df)

        aspi_series = full_df["aspi"].values.astype(float)
        log_aspi = np.log(aspi_series)

        log_aspi_train = log_aspi[train_start : train_end + 1]
        self.fit(log_aspi_train)

        # Baseline drift from fitted Theta model
        r1_train = np.diff(log_aspi_train)
        hist_mean_train = float(np.mean(r1_train))

        # Drift rate from Theta model fit
        drift_rate = hist_mean_train
        if hasattr(self.fitted_model_, "params"):
            drift_rate = float(self.fitted_model_.params.get("drift", hist_mean_train))

        rows = []
        for t_idx in range(val_start, val_end + 1):
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(aspi_series[t_idx])
            target_idx = t_idx + horizon

            if target_idx < n_total:
                aspi_future = float(aspi_series[target_idx])
                y_true_ret = float(np.log(aspi_future / aspi_t))
                y_true_dir = 1 if y_true_ret > 0 else 0
            else:
                y_true_ret = float("nan")
                y_true_dir = -1

            y_pred_ret = float(horizon * drift_rate)
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
