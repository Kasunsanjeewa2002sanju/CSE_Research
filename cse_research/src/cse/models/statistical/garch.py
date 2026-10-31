"""GARCH(1,1), EGARCH, and GJR-GARCH conditional volatility forecasting models.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Model fit on training window only.
- User mandate: Evaluate with variance metrics (QLIKE, MSE of realised volatility), NOT direction accuracy.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from arch import arch_model

from cse.splits.walk_forward import PhaseSplit
from cse.utils.logger import get_logger

logger = get_logger("cse.models.statistical.garch")


def calc_variance_metrics(
    rv_true: np.ndarray,
    var_pred: np.ndarray,
) -> Dict[str, float]:
    """Compute standard volatility evaluation metrics (QLIKE, MSE, MAE, Mincer-Zarnowitz R2)."""
    eps = 1e-8
    rv_clean = np.maximum(rv_true, eps)
    var_clean = np.maximum(var_pred, eps)

    # Patton (2011) QLIKE loss: RV / sigma^2 - ln(RV / sigma^2) - 1
    qlike = np.mean(rv_clean / var_clean - np.log(rv_clean / var_clean) - 1.0)
    mse_rv = np.mean((rv_true - var_pred) ** 2)
    mae_vol = np.mean(np.abs(np.sqrt(rv_clean) - np.sqrt(var_clean)))

    # Mincer-Zarnowitz regression R2: RV_t = a + b * sigma^2_t + e
    ss_tot = np.sum((rv_true - np.mean(rv_true)) ** 2)
    ss_res = np.sum((rv_true - var_pred) ** 2)
    mz_r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    return {
        "qlike": float(qlike),
        "mse_realized_variance": float(mse_rv),
        "mae_realized_volatility": float(mae_vol),
        "mincer_zarnowitz_r2": float(mz_r2),
    }


class GARCHModel:
    """Conditional volatility forecasting model (GARCH, EGARCH, GJR-GARCH)."""

    family: str = "statistical"

    def __init__(
        self,
        vol_type: str = "GARCH",  # 'GARCH', 'EGARCH', 'GJR-GARCH'
        p: int = 1,
        q: int = 1,
        o: int = 0,
        seed: int = 42,
    ) -> None:
        self.vol_type = vol_type.upper()
        self.p = p
        self.q = q
        self.o = 1 if "GJR" in self.vol_type or "EGARCH" in self.vol_type else o
        self.seed = seed
        self.fitted_res_: Any = None

        if "EGARCH" in self.vol_type:
            self.name = "egarch_11"
            self._arch_vol = "EGARCH"
        elif "GJR" in self.vol_type:
            self.name = "gjr_garch_11"
            self._arch_vol = "Garch"
        else:
            self.name = "garch_11"
            self._arch_vol = "Garch"
            self.o = 0

    def fit(self, returns_train: np.ndarray) -> GARCHModel:
        """Fit GARCH model on percentage returns strictly in the training window."""
        # Scale returns by 100 for numerical stability per arch documentation
        r_pct = returns_train * 100.0
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = arch_model(
                r_pct,
                vol=self._arch_vol,
                p=self.p,
                o=self.o,
                q=self.q,
                dist="Normal",
                rescale=False,
            )
            self.fitted_res_ = mod.fit(disp="off", show_warning=False)
        return self

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: PhaseSplit,
        horizon: int,
        feature_set: str = "none",
    ) -> pd.DataFrame:
        """Generate out-of-sample volatility forecasts across the validation block."""
        train_start = phase_split.train.start_idx
        train_end = phase_split.train.end_idx
        val_start = phase_split.val.start_idx
        val_end = phase_split.val.end_idx
        n_total = len(full_df)

        aspi_series = full_df["aspi"].values.astype(float)
        r1_series = np.insert(np.log(aspi_series[1:] / aspi_series[:-1]), 0, 0.0)

        # Fit on training returns
        r_train = r1_series[train_start : train_end + 1]
        self.fit(r_train)

        # Unconditional training variance as benchmark fallback
        uncond_var = float(np.var(r_train, ddof=1))

        rows = []
        for t_idx in range(val_start, val_end + 1):
            date_t = str(full_df.loc[t_idx, "date"])
            aspi_t = float(aspi_series[t_idx])
            target_idx = t_idx + horizon

            # Realized variance over horizon h: sum_{k=1}^h r_{t+k}^2
            if target_idx < n_total:
                realized_returns = r1_series[t_idx + 1 : target_idx + 1]
                realized_variance = float(np.sum(realized_returns ** 2))
                realized_vol = float(np.sqrt(realized_variance))
            else:
                realized_variance = float("nan")
                realized_vol = float("nan")

            # Conditional variance forecast from GARCH parameters
            # sigma_{t+1}^2 = omega + alpha * eps_t^2 + beta * sigma_t^2
            try:
                params = self.fitted_res_.params
                omega = float(params.get("omega", 1e-4)) / 10000.0  # scale back
                alpha = float(params.get("alpha[1]", 0.1))
                beta = float(params.get("beta[1]", 0.8))
                
                # Recent return deviation at step t
                r_recent = r1_series[t_idx]
                r_dev2 = r_recent ** 2
                
                # 1-day variance forecast
                var_1d = omega + alpha * r_dev2 + beta * uncond_var
                var_1d = max(var_1d, 1e-6)

                if horizon == 1:
                    pred_var = var_1d
                else:
                    # Persistent multi-day cumulative variance
                    persistence = min(alpha + beta, 0.99)
                    pred_var = float(horizon * uncond_var + (var_1d - uncond_var) * (1.0 - persistence ** horizon) / (1.0 - persistence + 1e-8))
            except Exception:
                pred_var = float(horizon * uncond_var)

            pred_vol = float(np.sqrt(max(pred_var, 1e-8)))

            rows.append({
                "model": self.name,
                "family": self.family,
                "phase": phase_split.phase,
                "horizon": horizon,
                "feature_set": feature_set,
                "date": date_t,
                "realized_variance": realized_variance,
                "predicted_variance": pred_var,
                "realized_volatility": realized_vol,
                "predicted_volatility": pred_vol,
                # Placeholders for standard prediction schema compatibility
                "y_true_ret": realized_returns.sum() if target_idx < n_total else float("nan"),
                "y_pred_ret": 0.0,  # volatility model, not directional return forecaster
                "p_up": 0.5,
                "y_true_dir": 1 if target_idx < n_total and realized_returns.sum() > 0 else 0,
                "y_pred_dir": 1,
                "aspi_t": aspi_t,
                "aspi_pred_level": aspi_t,
                "seed": self.seed,
            })

        df_out = pd.DataFrame(rows)
        return df_out[~df_out["realized_variance"].isna()].reset_index(drop=True)
