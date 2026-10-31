"""Vector Autoregression (VAR) model on (ASPI return, SP20 return, log turnover) for 2012+ period.

Adheres strictly to:
- Rule R1: Real data only. No backfilling SP20 before 2012-06-27 inception.
- Rule R2: Zero lookahead. Fit strictly on post-2012 training slice.
- Rule R4: Predicts log returns; levels reconstructed.
- Protocol: Phases P2-P5 (P1 flagged as not applicable due to pre-2012 SP20 absence).
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

from cse.splits.walk_forward import PhaseSplit
from cse.utils.logger import get_logger

logger = get_logger("cse.models.statistical.var")


class VARModel:
    """Vector Autoregression model on (ASPI return, SP20 return, log turnover)."""

    name: str = "var_aspi_sp20_turnover"
    family: str = "statistical"

    def __init__(self, maxlags: int = 5, seed: int = 42) -> None:
        self.maxlags = maxlags
        self.seed = seed
        self.fitted_model_: Any = None
        self.selected_lag_: int = 1

    def fit(self, df_train_system: pd.DataFrame) -> VARModel:
        """Fit VAR model on training system selecting optimal lag by AIC."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = VAR(df_train_system)
            lag_order = mod.select_order(maxlags=self.maxlags)
            self.selected_lag_ = max(1, lag_order.aic)
            self.fitted_model_ = mod.fit(self.selected_lag_)
        return self

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
        feature_set: str = "none",
    ) -> Optional[pd.DataFrame]:
        """Generate out-of-sample forecasts across the validation block.
        
        Returns None if SP20 is unavailable in the training window (Phase P1).
        """
        # In Phase P1 (train 1994-2011), SP20 did not exist.
        if phase_split.phase == "P1":
            logger.info("Phase P1 training window precedes S&P SL 20 inception (2012-06-27). Skipping VAR.")
            return None

        # Build 3-variable system
        aspi = full_df["aspi"].values.astype(float)
        sp20 = full_df["sp20"].values.astype(float)
        turnover_col = "turnover_equity_mn" if "turnover_equity_mn" in full_df.columns else "turnover"
        turnover = full_df[turnover_col].values.astype(float)

        r_aspi = np.insert(np.log(aspi[1:] / aspi[:-1]), 0, 0.0)
        r_sp20 = np.insert(np.log(sp20[1:] / sp20[:-1]), 0, 0.0)
        ln_turnover = np.log(np.maximum(turnover, 1.0))

        system_df = pd.DataFrame({
            "r_aspi": r_aspi,
            "r_sp20": r_sp20,
            "ln_turnover": ln_turnover,
        })

        train_start = phase_split.train.start_idx
        train_end = phase_split.train.end_idx
        val_start = phase_split.val.start_idx
        val_end = phase_split.val.end_idx
        n_total = len(full_df)

        # SP20 valid index start (post-2012-06-27)
        sp20_valid_indices = np.where(~np.isnan(sp20))[0]
        if len(sp20_valid_indices) == 0:
            return None
        first_valid_sp20 = sp20_valid_indices[0]
        eff_train_start = max(train_start, first_valid_sp20 + 1)

        if eff_train_start >= train_end:
            logger.warning("Insufficient post-2012 training rows in %s for VAR.", phase_split.phase)
            return None

        df_train_slice = system_df.iloc[eff_train_start : train_end + 1].dropna()
        self.fit(df_train_slice)

        hist_mean_train = float(df_train_slice["r_aspi"].mean())

        rows = []
        p_lag = self.selected_lag_

        for t_idx in range(val_start, val_end + 1):
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(aspi[t_idx])
            target_idx = t_idx + horizon

            if target_idx < n_total:
                aspi_future = float(aspi[target_idx])
                y_true_ret = float(np.log(aspi_future / aspi_t))
                y_true_dir = 1 if y_true_ret > 0 else 0
            else:
                y_true_ret = float("nan")
                y_true_dir = -1

            # Available lag state at step t
            lag_state = system_df.iloc[t_idx - p_lag + 1 : t_idx + 1].values
            if len(lag_state) == p_lag and not np.isnan(lag_state).any():
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        fc = self.fitted_model_.forecast(lag_state, steps=horizon)
                        # Column 0 is r_aspi
                        if horizon == 1:
                            y_pred_ret = float(fc[0, 0])
                        else:
                            y_pred_ret = float(np.sum(fc[:, 0]))
                except Exception:
                    y_pred_ret = float(horizon * hist_mean_train)
            else:
                y_pred_ret = float(horizon * hist_mean_train)

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
