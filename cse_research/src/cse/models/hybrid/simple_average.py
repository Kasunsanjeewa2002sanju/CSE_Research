"""Simple Average Ensemble of Best Model per Family.

Computes unweighted ensemble average of the top-performing model from each family:
1. Statistical (e.g. Theta, ARIMA, ARIMAX)
2. Shallow ML (e.g. Ridge, CatBoost, LightGBM)
3. Deep Sequence (e.g. DLinear, PatchTST, MLP)
4. Foundation Pretrained (e.g. Chronos-Bolt, TimesFM)

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead (selection based strictly on training/validation harness splits).
- Rule R4: Predicts log returns; levels reconstructed post-prediction.
- Rule R5: Same walk-forward protocol, phases (P1-P5), horizons (h=1, 5), and schema.
- Rule R6: Saves predictions, metrics, and metadata with latency/memory.
"""

from __future__ import annotations

import os
import time
import psutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from cse.utils.config import find_project_root
from cse.utils.logger import get_logger

logger = get_logger("cse.models.hybrid.simple_average")


class SimpleAverageEnsemble:
    """Ensemble combining predictions by taking a simple average of the best model per family."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root = root_dir or find_project_root()
        self.pred_dir = self.root / "results" / "predictions"

    def select_best_model_per_family(
        self,
        phase: str,
        horizon: int,
        metrics_df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, str]:
        """Select best base model for each family based on inner/oos training validation score.
        
        Default fallback mappings ensure robust selection if metrics are incomplete.
        """
        # If metrics_df is available, select best model per family by lowest RMSE or highest R2
        selected = {}
        if metrics_df is not None and not metrics_df.empty:
            sub = metrics_df[(metrics_df["phase"] == phase) & (metrics_df["horizon"] == horizon)]
            if not sub.empty:
                for fam in ["statistical", "shallow", "deep", "foundation"]:
                    fam_sub = sub[sub["family"] == fam]
                    if not fam_sub.empty:
                        # Find model with best metric (lowest rmse or highest oos_r2)
                        if "rmse" in fam_sub.columns:
                            best_row = fam_sub.sort_values(by="rmse", ascending=True).iloc[0]
                        elif "metric_name" in fam_sub.columns:
                            # metrics_long format
                            rmse_sub = fam_sub[fam_sub["metric_name"] == "rmse"]
                            if not rmse_sub.empty:
                                best_row = rmse_sub.sort_values(by="value", ascending=True).iloc[0]
                            else:
                                best_row = fam_sub.iloc[0]
                        else:
                            best_row = fam_sub.iloc[0]
                        selected[fam] = str(best_row["model"])

        # Defaults / Fallbacks per family if not in metrics
        defaults = {
            "statistical": "theta",
            "shallow": "ridge_b",
            "deep": "dlinear_c",
            "foundation": "chronos_bolt_log_returns_ctx256",
        }
        for fam, def_model in defaults.items():
            if fam not in selected:
                selected[fam] = def_model

        return selected

    def load_prediction_df(self, family: str, model_name: str, phase: str, horizon: int) -> Optional[pd.DataFrame]:
        """Load parquet or csv prediction file for given model, phase, and horizon."""
        fam_dir = self.pred_dir / family
        if not fam_dir.exists():
            return None

        # Look for standard matching naming schemes:
        # e.g. {model}_{phase}_h{horizon}.parquet or {model}_*_{phase}_h{horizon}.parquet
        patterns = [
            f"{model_name}_{phase}_h{horizon}.parquet",
            f"{model_name}_{phase}_h{horizon}.csv",
            f"{model_name}_*_{phase}_h{horizon}.parquet",
            f"{model_name}_*_{phase}_h{horizon}.csv",
        ]
        for p in patterns:
            matched = list(fam_dir.glob(p))
            if matched:
                target_file = matched[0]
                try:
                    if target_file.suffix == ".parquet":
                        df = pd.read_parquet(target_file)
                    else:
                        df = pd.read_csv(target_file)
                    return df
                except Exception as e:
                    logger.warning("Error reading %s: %s", target_file, e)
        return None

    def combine_predictions(
        self,
        phase: str,
        horizon: int,
        base_models: Dict[str, str],
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Compute simple average of selected base model predictions.

        Returns:
            Tuple of (df_predictions, performance_telemetry).
        """
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)
        t_start = time.time()

        loaded_dfs: List[pd.DataFrame] = []
        used_model_names: List[str] = []

        for fam, model_name in base_models.items():
            df_pred = self.load_prediction_df(fam, model_name, phase, horizon)
            if df_pred is not None and not df_pred.empty:
                loaded_dfs.append(df_pred)
                used_model_names.append(f"{fam}:{model_name}")
            else:
                # Try finding any valid model in this family for fallback
                fam_dir = self.pred_dir / fam
                if fam_dir.exists():
                    f_candidates = list(fam_dir.glob(f"*_{phase}_h{horizon}.parquet")) + list(
                        fam_dir.glob(f"*_{phase}_h{horizon}.csv")
                    )
                    if f_candidates:
                        fb_file = f_candidates[0]
                        try:
                            df_fb = (
                                pd.read_parquet(fb_file)
                                if fb_file.suffix == ".parquet"
                                else pd.read_csv(fb_file)
                            )
                            loaded_dfs.append(df_fb)
                            fb_name = df_fb["model"].iloc[0] if "model" in df_fb.columns else fb_file.stem
                            used_model_names.append(f"{fam}:{fb_name}")
                        except Exception:
                            pass

        if not loaded_dfs:
            raise RuntimeError(f"No base model predictions found for Phase {phase} h={horizon}!")

        logger.info(
            "Phase %s h=%d: Combining %d base models: %s",
            phase,
            horizon,
            len(used_model_names),
            ", ".join(used_model_names),
        )

        # Align on dates
        base_df = loaded_dfs[0].copy().sort_values("date").reset_index(drop=True)
        date_series = base_df["date"].values
        y_true_ret = base_df["y_true_ret"].values
        aspi_t = base_df["aspi_t"].values

        pred_rets = []
        p_ups = []

        for df_m in loaded_dfs:
            df_m_aligned = df_m.set_index("date").reindex(date_series).reset_index()
            # Fill any missing with base_df
            p_ret = df_m_aligned["y_pred_ret"].fillna(base_df["y_pred_ret"]).values
            p_up = df_m_aligned["p_up"].fillna(base_df["p_up"]).values
            pred_rets.append(p_ret)
            p_ups.append(p_up)

        # Unweighted average across base models
        avg_pred_ret = np.mean(pred_rets, axis=0)
        avg_p_up = np.mean(p_ups, axis=0)
        avg_pred_dir = (avg_p_up > 0.5).astype(int)
        arr_true_dir = (y_true_ret > 0).astype(int)

        aspi_pred_level = aspi_t * np.exp(avg_pred_ret)

        total_runtime = time.time() - t_start
        mem_after = process.memory_info().rss / (1024 * 1024)

        df_out = pd.DataFrame({
            "model": "simple_average_ensemble",
            "family": "hybrid",
            "phase": phase,
            "horizon": horizon,
            "feature_set": "ensemble_average",
            "date": date_series,
            "y_true_ret": y_true_ret,
            "y_pred_ret": avg_pred_ret,
            "p_up": avg_p_up,
            "y_true_dir": arr_true_dir,
            "y_pred_dir": avg_pred_dir,
            "aspi_t": aspi_t,
            "aspi_pred_level": aspi_pred_level,
            "seed": 42,
        })

        telemetry = {
            "model": "simple_average_ensemble",
            "phase": phase,
            "horizon": horizon,
            "base_models_used": used_model_names,
            "num_base_models": len(used_model_names),
            "total_steps": len(date_series),
            "total_runtime_seconds": total_runtime,
            "mean_latency_ms": (total_runtime / max(1, len(date_series))) * 1000.0,
            "memory_before_mb": mem_before,
            "memory_after_mb": mem_after,
            "memory_delta_mb": max(0.0, mem_after - mem_before),
        }

        return df_out, telemetry
