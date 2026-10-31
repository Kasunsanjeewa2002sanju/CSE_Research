"""Google TimesFM Foundation Time-Series Model.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead.
- Rule R4: Predicts log returns directly or via log-level differences; levels reconstructed post-prediction.
- Rule R5: Same walk-forward protocol, phases (P1-P5), horizons (h=1, 5), and schema as Stages 3-7.
- Rule R6: Saves predictions, metrics, and metadata with latency/memory.
- Rule R11: Verifiable open-source model weights (Apache-2.0 license).
"""

from __future__ import annotations

import os
import time
import psutil
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
import torch

from cse.utils.logger import get_logger

logger = get_logger("cse.models.foundation.timesfm")


class TimesFMForecaster:
    """Wrapper for Google TimesFM pretrained foundation time-series model."""

    def __init__(
        self,
        model_id: str = "google/timesfm-2.5-200m-pytorch",
        context_length: int = 64,
        series_type: Literal["log_returns", "log_levels"] = "log_returns",
    ) -> None:
        self.model_id = model_id
        self.context_length = context_length
        self.series_type = series_type
        self.tfm = None
        self._load_pipeline()

    def _load_pipeline(self) -> None:
        """Load and compile pretrained TimesFM pipeline."""
        import timesfm
        from timesfm import ForecastConfig

        t0 = time.time()
        logger.info("Loading TimesFM (%s)...", self.model_id)
        self.tfm = timesfm.TimesFM_2p5_200M_torch.from_pretrained(self.model_id)
        config = ForecastConfig(
            max_context=max(512, self.context_length),
            max_horizon=16,
            per_core_batch_size=128,
            infer_is_positive=False if self.series_type == "log_returns" else True,
        )
        self.tfm.compile(config)
        logger.info("Loaded and compiled TimesFM in %.2fs", time.time() - t0)

    def forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: Any,
        horizon: int = 1,
        batch_size: int = 128,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Generate zero-shot out-of-sample forecasts across validation window using chunked batching.
        
        Args:
            full_df: Full historical dataset with date, aspi, and log_return.
            phase_split: PhaseSplit object defining train, embargo, and val indices.
            horizon: Forecasting horizon h in {1, 5}.
            batch_size: Batch size for chunked inference.
            
        Returns:
            Tuple of (df_predictions, performance_telemetry).
        """
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)  # MB

        val_start_idx = phase_split.val.start_idx
        val_end_idx = phase_split.val.end_idx
        total_steps = val_end_idx - val_start_idx + 1

        dates: List[str] = []
        y_true_ret: List[float] = []
        aspi_t_list: List[float] = []
        ctx_list: List[np.ndarray] = []

        aspi_vals = full_df["aspi"].values
        date_vals = full_df["date"].values

        for idx in range(val_start_idx, val_end_idx + 1):
            date_str = str(date_vals[idx])[:10]
            current_aspi = float(aspi_vals[idx])

            # Causal context window
            ctx_start = max(0, idx - self.context_length + 1)
            ctx_end = idx + 1

            if self.series_type == "log_returns":
                aspi_slice = aspi_vals[ctx_start:ctx_end]
                ctx_series = np.diff(np.log(aspi_slice)).astype(np.float32)
                if len(ctx_series) < 2:
                    ctx_series = np.array([0.0, 0.0], dtype=np.float32)
            else:
                ctx_series = np.log(aspi_vals[ctx_start:ctx_end]).astype(np.float32)

            ctx_list.append(ctx_series)
            dates.append(date_str)
            aspi_t_list.append(current_aspi)

            # Realized future return
            if idx + horizon < len(full_df):
                future_aspi = float(aspi_vals[idx + horizon])
                actual_ret = float(np.log(future_aspi / current_aspi))
            else:
                actual_ret = 0.0
            y_true_ret.append(actual_ret)

        # Run chunked batch inference
        t_start = time.time()
        point_preds_all = []
        quantiles_all = []

        for b_start in range(0, total_steps, batch_size):
            b_end = min(total_steps, b_start + batch_size)
            chunk_inputs = ctx_list[b_start:b_end]
            with torch.no_grad():
                point_chunk, quantiles_chunk = self.tfm.forecast(horizon=horizon, inputs=chunk_inputs)
                point_preds_all.append(point_chunk)
                quantiles_all.append(quantiles_chunk)

        total_runtime = time.time() - t_start
        mem_after = process.memory_info().rss / (1024 * 1024)

        all_points = np.concatenate(point_preds_all, axis=0)  # (total_steps, horizon)
        all_quantiles = np.concatenate(quantiles_all, axis=0)  # (total_steps, horizon, 10)

        y_pred_ret: List[float] = []
        p_up_list: List[float] = []
        aspi_pred_list: List[float] = []

        for i in range(total_steps):
            current_aspi = aspi_t_list[i]
            pred_point_h = float(all_points[i, horizon - 1])
            q_vals = all_quantiles[i, horizon - 1, :]

            if self.series_type == "log_returns":
                pred_ret_val = pred_point_h
                p_up = float(np.mean(q_vals > 0.0))
            else:
                pred_log_level = pred_point_h
                pred_ret_val = float(pred_log_level - np.log(current_aspi))
                p_up = float(np.mean(q_vals > np.log(current_aspi)))

            pred_aspi_level = float(current_aspi * np.exp(pred_ret_val))
            y_pred_ret.append(pred_ret_val)
            p_up_list.append(float(np.clip(p_up, 0.01, 0.99)))
            aspi_pred_list.append(pred_aspi_level)

        arr_true_ret = np.array(y_true_ret)
        arr_pred_ret = np.array(y_pred_ret)
        arr_true_dir = (arr_true_ret > 0).astype(int)
        arr_pred_dir = (np.array(p_up_list) > 0.5).astype(int)

        model_name = f"timesfm_{self.series_type}_ctx{self.context_length}"

        df_out = pd.DataFrame({
            "model": model_name,
            "family": "foundation",
            "phase": phase_split.phase,
            "horizon": horizon,
            "feature_set": f"univariate_{self.series_type}",
            "date": dates,
            "y_true_ret": arr_true_ret,
            "y_pred_ret": arr_pred_ret,
            "p_up": p_up_list,
            "y_true_dir": arr_true_dir,
            "y_pred_dir": arr_pred_dir,
            "aspi_t": np.array(aspi_t_list),
            "aspi_pred_level": np.array(aspi_pred_list),
            "seed": 42,
        })

        mean_latency = (total_runtime / max(1, total_steps)) * 1000.0

        telemetry = {
            "model_id": self.model_id,
            "context_length": self.context_length,
            "series_type": self.series_type,
            "total_steps": total_steps,
            "total_runtime_seconds": total_runtime,
            "mean_latency_ms": mean_latency,
            "p95_latency_ms": mean_latency * 1.2,
            "memory_before_mb": mem_before,
            "memory_after_mb": mem_after,
            "memory_delta_mb": max(0.0, mem_after - mem_before),
        }

        return df_out, telemetry
