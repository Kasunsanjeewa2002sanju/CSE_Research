"""Baseline models for Colombo Stock Exchange ASPI forecasting.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: No lookahead bias. At step t, uses only observations up to t.
- Rule R4: Predicts log returns; index levels are reconstructed afterwards.
- Protocol: 4 standard baselines:
  1. Random Walk (zero return)
  2. Expanding Historical Mean
  3. Majority-Class Direction
  4. Previous-Direction / Return Momentum
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from cse.splits.walk_forward import PhaseSplit


class BaseBaselineModel:
    """Base class for baseline forecasting models."""
    name: str = "base_baseline"
    family: str = "baseline"

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
    ) -> pd.DataFrame:
        """Run step-by-step out-of-sample forecasting across the validation block."""
        raise NotImplementedError


class RandomWalkBaseline(BaseBaselineModel):
    """Random Walk baseline forecasting zero future log return (no price change).
    
    y_pred_ret = 0.0
    y_pred_dir = 0
    aspi_pred_level = aspi_t
    """
    name: str = "random_walk"

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
    ) -> pd.DataFrame:
        val_start_idx = phase_split.val.start_idx
        val_end_idx = phase_split.val.end_idx
        n_total = len(full_df)

        rows = []
        for t_idx in range(val_start_idx, val_end_idx + 1):
            target_idx = t_idx + horizon
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(full_df.loc[t_idx, "aspi"])

            # Check if forward target is within dataset bounds
            if target_idx < n_total:
                aspi_future = float(full_df.loc[target_idx, "aspi"])
                y_true_ret = float(np.log(aspi_future / aspi_t))
                y_true_dir = 1 if y_true_ret > 0 else 0
            else:
                y_true_ret = float("nan")
                y_true_dir = -1

            y_pred_ret = 0.0
            y_pred_dir = 0
            p_up = None
            aspi_pred_level = aspi_t * np.exp(y_pred_ret)

            rows.append({
                "model": self.name,
                "family": self.family,
                "phase": phase_split.phase,
                "horizon": horizon,
                "feature_set": "none",
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
        # Filter out rows where future target is beyond dataset end
        return df_out[~df_out["y_true_ret"].isna()].reset_index(drop=True)


class HistoricalMeanBaseline(BaseBaselineModel):
    """Expanding historical mean baseline.
    
    Forecasts the expanding historical mean of all h-day log returns observed up to day t.
    y_pred_ret = mean(r_{k-h, k}) for all k <= t.
    """
    name: str = "historical_mean"

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
    ) -> pd.DataFrame:
        val_start_idx = phase_split.val.start_idx
        val_end_idx = phase_split.val.end_idx
        n_total = len(full_df)

        aspi_series = full_df["aspi"].values
        # Precompute realized h-day returns for each index k: log(aspi[k] / aspi[k-h])
        past_returns_h = np.full(n_total, np.nan)
        for k in range(horizon, n_total):
            past_returns_h[k] = np.log(aspi_series[k] / aspi_series[k - horizon])

        rows = []
        for t_idx in range(val_start_idx, val_end_idx + 1):
            target_idx = t_idx + horizon
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(aspi_series[t_idx])

            # Forward target
            if target_idx < n_total:
                aspi_future = float(aspi_series[target_idx])
                y_true_ret = float(np.log(aspi_future / aspi_t))
                y_true_dir = 1 if y_true_ret > 0 else 0
            else:
                y_true_ret = float("nan")
                y_true_dir = -1

            # Available historical returns observed at close of day t
            # Any return settled at or before day t is known
            # Realized h-day returns up to t_idx: past_returns_h[horizon : t_idx + 1]
            valid_hist = past_returns_h[horizon : t_idx + 1]
            valid_hist = valid_hist[~np.isnan(valid_hist)]
            y_pred_ret = float(np.mean(valid_hist)) if len(valid_hist) > 0 else 0.0

            y_pred_dir = 1 if y_pred_ret > 0 else 0
            p_up = None
            aspi_pred_level = aspi_t * np.exp(y_pred_ret)

            rows.append({
                "model": self.name,
                "family": self.family,
                "phase": phase_split.phase,
                "horizon": horizon,
                "feature_set": "none",
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


class MajorityClassBaseline(BaseBaselineModel):
    """Majority-class directional baseline.
    
    Predicts the majority direction observed historically up to date t.
    p_up = proportion of positive returns observed up to t.
    y_pred_dir = 1 if p_up >= 0.5 else 0.
    """
    name: str = "majority_class"

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
    ) -> pd.DataFrame:
        val_start_idx = phase_split.val.start_idx
        val_end_idx = phase_split.val.end_idx
        n_total = len(full_df)

        aspi_series = full_df["aspi"].values
        past_returns_h = np.full(n_total, np.nan)
        for k in range(horizon, n_total):
            past_returns_h[k] = np.log(aspi_series[k] / aspi_series[k - horizon])

        rows = []
        for t_idx in range(val_start_idx, val_end_idx + 1):
            target_idx = t_idx + horizon
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(aspi_series[t_idx])

            if target_idx < n_total:
                aspi_future = float(aspi_series[target_idx])
                y_true_ret = float(np.log(aspi_future / aspi_t))
                y_true_dir = 1 if y_true_ret > 0 else 0
            else:
                y_true_ret = float("nan")
                y_true_dir = -1

            valid_hist = past_returns_h[horizon : t_idx + 1]
            valid_hist = valid_hist[~np.isnan(valid_hist)]
            if len(valid_hist) > 0:
                p_up = float(np.mean(valid_hist > 0))
                y_pred_ret = float(np.mean(valid_hist))
            else:
                p_up = 0.5
                y_pred_ret = 0.0

            y_pred_dir = 1 if p_up >= 0.5 else 0
            aspi_pred_level = aspi_t * np.exp(y_pred_ret)

            rows.append({
                "model": self.name,
                "family": self.family,
                "phase": phase_split.phase,
                "horizon": horizon,
                "feature_set": "none",
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


class MomentumBaseline(BaseBaselineModel):
    """Previous-direction / return momentum baseline.
    
    Forecasts that the forward h-day return will equal the most recently observed h-day return.
    y_pred_ret = ln(ASPI_t / ASPI_{t-h})
    """
    name: str = "momentum"

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
    ) -> pd.DataFrame:
        val_start_idx = phase_split.val.start_idx
        val_end_idx = phase_split.val.end_idx
        n_total = len(full_df)

        aspi_series = full_df["aspi"].values

        rows = []
        for t_idx in range(val_start_idx, val_end_idx + 1):
            target_idx = t_idx + horizon
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(aspi_series[t_idx])

            if target_idx < n_total:
                aspi_future = float(aspi_series[target_idx])
                y_true_ret = float(np.log(aspi_future / aspi_t))
                y_true_dir = 1 if y_true_ret > 0 else 0
            else:
                y_true_ret = float("nan")
                y_true_dir = -1

            # Return observed over the previous h trading days ending at day t
            prev_idx = t_idx - horizon
            if prev_idx >= 0:
                aspi_prev = float(aspi_series[prev_idx])
                y_pred_ret = float(np.log(aspi_t / aspi_prev))
            else:
                y_pred_ret = 0.0

            y_pred_dir = 1 if y_pred_ret > 0 else 0
            p_up = None
            aspi_pred_level = aspi_t * np.exp(y_pred_ret)

            rows.append({
                "model": self.name,
                "family": self.family,
                "phase": phase_split.phase,
                "horizon": horizon,
                "feature_set": "none",
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
