"""ARIMA + LSTM on Residuals Hybrid Forecaster.

Architecture:
1. Linear/econometric backbone: ARIMA fitted on the training window log returns.
2. Non-linear ML residual corrector: PyTorch LSTM trained strictly on the ARIMA in-sample
   residuals, with early stopping on an inner validation split.
3. Out-of-sample forecast: y_hat = y_hat_arima + e_hat_lstm.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead (LSTM trained only on train window residuals).
- Rule R4: Predicts log returns; levels reconstructed post-prediction.
- Rule R5: Same walk-forward protocol, phases (P1-P5), horizons (h=1, 5), and schema.
- Rule R6: Saves predictions, metrics, and metadata with latency/memory.
"""

from __future__ import annotations

import os
import time
import psutil
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from statsmodels.tsa.arima.model import ARIMA

from cse.utils.logger import get_logger

logger = get_logger("cse.models.hybrid.arima_lstm")


class ResidualLSTM(nn.Module):
    """Lightweight LSTM for forecasting ARIMA residual sequences."""

    def __init__(self, lookback: int = 20, hidden_dim: int = 32, num_layers: int = 1, dropout: float = 0.1) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=1,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch_size, lookback, 1)
        out, _ = self.lstm(x)
        # Take last time step
        pred = self.fc(out[:, -1, :])
        return pred.squeeze(-1)


class ARIMALSTMHybridForecaster:
    """Hybrid forecaster combining ARIMA linear mean dynamics with LSTM residual corrections."""

    def __init__(
        self,
        arima_order: Tuple[int, int, int] = (1, 0, 1),
        lookback: int = 20,
        hidden_dim: int = 32,
        epochs: int = 25,
        lr: float = 0.005,
        device: str = "cpu",
        seed: int = 42,
    ) -> None:
        self.arima_order = arima_order
        self.lookback = lookback
        self.hidden_dim = hidden_dim
        self.epochs = epochs
        self.lr = lr
        self.device = device
        self.seed = seed

    def _create_residual_windows(
        self, residuals: np.ndarray, horizon: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create lookback windows and forward residual targets."""
        X, y = [], []
        n = len(residuals)
        for i in range(self.lookback, n - horizon + 1):
            X.append(residuals[i - self.lookback : i])
            # For horizon h, the residual target is residuals[i + horizon - 1]
            y.append(residuals[i + horizon - 1])
        if len(X) == 0:
            return np.empty((0, self.lookback)), np.empty(0)
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def fit_and_forecast_validation(
        self,
        full_df: pd.DataFrame,
        phase_split: Any,
        horizon: int = 1,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fit ARIMA + LSTM on training window and forecast validation window.

        Args:
            full_df: DataFrame containing date, aspi, and log_return.
            phase_split: PhaseSplit object defining train, embargo, and val indices.
            horizon: Forecasting horizon h in {1, 5}.

        Returns:
            Tuple of (df_predictions, performance_telemetry).
        """
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)

        t_start = time.time()

        train_start = phase_split.train.start_idx
        train_end = phase_split.train.end_idx
        val_start = phase_split.val.start_idx
        val_end = phase_split.val.end_idx

        # Extract returns
        aspi_all = full_df["aspi"].values
        # Compute forward h-day returns: log(aspi_{t+h} / aspi_t)
        # Realized forward return for each day t
        n_total = len(full_df)
        fwd_ret = np.zeros(n_total)
        for i in range(n_total):
            if i + horizon < n_total:
                fwd_ret[i] = np.log(aspi_all[i + horizon] / aspi_all[i])
            else:
                fwd_ret[i] = 0.0

        # Step 1: Fit ARIMA on 1-day returns in training window
        daily_ret_all = np.zeros(n_total)
        daily_ret_all[1:] = np.diff(np.log(aspi_all))
        train_daily_ret = daily_ret_all[train_start : train_end + 1]

        logger.info(
            "Fitting ARIMA%s on Phase %s train window (%d samples)...",
            self.arima_order,
            phase_split.phase,
            len(train_daily_ret),
        )
        try:
            arima_model = ARIMA(train_daily_ret, order=self.arima_order).fit()
            train_arima_fitted = arima_model.fittedvalues
            train_residuals = train_daily_ret - train_arima_fitted
        except Exception as e:
            logger.warning("ARIMA fit failed (%s), falling back to mean: %s", self.arima_order, e)
            mean_ret = np.mean(train_daily_ret)
            train_arima_fitted = np.full_like(train_daily_ret, mean_ret)
            train_residuals = train_daily_ret - mean_ret

        # Step 2: Inner chronological split inside train window for LSTM early stopping
        # Last 15% of train window is inner validation
        n_train = len(train_residuals)
        n_inner_val = max(30, int(n_train * 0.15))
        n_inner_train = n_train - n_inner_val

        inner_train_res = train_residuals[:n_inner_train]
        inner_val_res = train_residuals[n_inner_train:]

        X_train_res, y_train_res = self._create_residual_windows(inner_train_res, horizon)
        X_val_res, y_val_res = self._create_residual_windows(inner_val_res, horizon)

        lstm_model = ResidualLSTM(
            lookback=self.lookback,
            hidden_dim=self.hidden_dim,
            num_layers=1,
            dropout=0.1,
        ).to(self.device)

        if len(X_train_res) > 0:
            train_dataset = TensorDataset(
                torch.tensor(X_train_res).unsqueeze(-1),
                torch.tensor(y_train_res),
            )
            train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
            optimizer = torch.optim.Adam(lstm_model.parameters(), lr=self.lr, weight_decay=1e-4)
            criterion = nn.MSELoss()

            best_val_loss = float("inf")
            best_state = None

            for ep in range(self.epochs):
                lstm_model.train()
                for bx, by in train_loader:
                    bx, by = bx.to(self.device), by.to(self.device)
                    optimizer.zero_grad()
                    out = lstm_model(bx)
                    loss = criterion(out, by)
                    loss.backward()
                    optimizer.step()

                if len(X_val_res) > 0:
                    lstm_model.eval()
                    with torch.no_grad():
                        vx = torch.tensor(X_val_res).unsqueeze(-1).to(self.device)
                        vy = torch.tensor(y_val_res).to(self.device)
                        val_loss = criterion(lstm_model(vx), vy).item()
                        if val_loss < best_val_loss:
                            best_val_loss = val_loss
                            best_state = {k: v.cpu().clone() for k, v in lstm_model.state_dict().items()}

            if best_state is not None:
                lstm_model.load_state_dict(best_state)

        lstm_model.eval()

        # Step 3: Out-of-sample forecast generation across validation window
        dates: List[str] = []
        y_true_ret: List[float] = []
        y_pred_ret: List[float] = []
        p_up_list: List[float] = []
        aspi_t_list: List[float] = []
        aspi_pred_list: List[float] = []
        step_latencies: List[float] = []

        std_ret = float(np.std(train_daily_ret)) if np.std(train_daily_ret) > 0 else 0.01

        # We maintain running daily residuals
        all_residuals = list(train_residuals)

        # ARIMA forecast over h steps (constant across fixed-parameter validation window)
        try:
            arima_fc = arima_model.forecast(steps=horizon)
            arima_pred = float(np.sum(arima_fc))
        except Exception:
            arima_pred = float(np.mean(train_daily_ret) * horizon)

        for idx in range(val_start, val_end + 1):
            t_step0 = time.time()
            date_str = str(full_df["date"].iloc[idx])[:10]
            current_aspi = float(aspi_all[idx])
            actual_fwd_ret = float(fwd_ret[idx])

            # LSTM correction on recent residual window
            recent_res = np.array(all_residuals[-self.lookback:], dtype=np.float32)
            if len(recent_res) < self.lookback:
                recent_res = np.pad(recent_res, (self.lookback - len(recent_res), 0))

            with torch.no_grad():
                res_tensor = torch.tensor(recent_res).unsqueeze(0).unsqueeze(-1).to(self.device)
                lstm_correction = float(lstm_model(res_tensor).item())

            # Combined hybrid forecast
            pred_hybrid_ret = arima_pred + lstm_correction

            # Directional probability p_up via logistic sigmoid
            scaled_z = pred_hybrid_ret / (std_ret * np.sqrt(horizon))
            p_up = 1.0 / (1.0 + np.exp(-np.clip(scaled_z, -10.0, 10.0)))

            pred_aspi_level = float(current_aspi * np.exp(pred_hybrid_ret))

            dates.append(date_str)
            y_true_ret.append(actual_fwd_ret)
            y_pred_ret.append(pred_hybrid_ret)
            p_up_list.append(float(np.clip(p_up, 0.01, 0.99)))
            aspi_t_list.append(current_aspi)
            aspi_pred_list.append(pred_aspi_level)

            # Update running residuals causally with realized day idx return
            realized_day_ret = daily_ret_all[idx]
            step_res = realized_day_ret - (arima_pred / horizon)
            all_residuals.append(step_res)

            step_latencies.append((time.time() - t_step0) * 1000.0)

        total_runtime = time.time() - t_start
        mem_after = process.memory_info().rss / (1024 * 1024)

        arr_true_ret = np.array(y_true_ret)
        arr_pred_ret = np.array(y_pred_ret)
        arr_true_dir = (arr_true_ret > 0).astype(int)
        arr_pred_dir = (np.array(p_up_list) > 0.5).astype(int)

        df_out = pd.DataFrame({
            "model": "arima_lstm_residuals",
            "family": "hybrid",
            "phase": phase_split.phase,
            "horizon": horizon,
            "feature_set": "returns_residuals",
            "date": dates,
            "y_true_ret": arr_true_ret,
            "y_pred_ret": arr_pred_ret,
            "p_up": p_up_list,
            "y_true_dir": arr_true_dir,
            "y_pred_dir": arr_pred_dir,
            "aspi_t": np.array(aspi_t_list),
            "aspi_pred_level": np.array(aspi_pred_list),
            "seed": self.seed,
        })

        telemetry = {
            "model": "arima_lstm_residuals",
            "phase": phase_split.phase,
            "horizon": horizon,
            "total_steps": len(dates),
            "total_runtime_seconds": total_runtime,
            "mean_latency_ms": float(np.mean(step_latencies)),
            "p95_latency_ms": float(np.percentile(step_latencies, 95)),
            "memory_before_mb": mem_before,
            "memory_after_mb": mem_after,
            "memory_delta_mb": max(0.0, mem_after - mem_before),
            "arima_order": self.arima_order,
            "lookback": self.lookback,
        }

        return df_out, telemetry
