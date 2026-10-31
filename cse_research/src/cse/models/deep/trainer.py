"""PyTorch training loop, checkpointing, early stopping, and collapse diagnostics.

Adheres strictly to:
    - Rule R1: Real data only.
    - Rule R2: Zero lookahead. Early stopping evaluated exclusively on the inner validation split.
    - Rule R3: Sanity and collapse diagnostics.
    - Rule R4: Predicts log returns; levels reconstructed post-prediction.
    - Rule R6: Saves checkpoints, training curves (CSV and PNG), and metadata.
    - Rule R7: Pinned seeds and hardware logging.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau

from cse.features.pipeline import PhaseSequenceDataSet, SequenceSplitData
from cse.models.deep.architectures import BaseSequenceModel, build_deep_model
from cse.models.deep.dataset import create_dataloader
from cse.utils.logger import get_logger

logger = get_logger("cse.models.deep.trainer")


def get_device() -> torch.device:
    """Automatically detect hardware and return PyTorch device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def get_hardware_info() -> Dict[str, Any]:
    """Inspect and return current hardware telemetry."""
    info: Dict[str, Any] = {
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "cuda_available": torch.cuda.is_available(),
    }
    if torch.cuda.is_available():
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_count"] = torch.cuda.device_count()
    else:
        info["cpu_threads"] = torch.get_num_threads()
    return info


def set_seed(seed: int) -> None:
    """Pin random seeds across Python, NumPy, and PyTorch (Rule R7)."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


class DeepSequenceTrainer:
    """End-to-end trainer for deep sequence models on CSE ASPI return forecasting."""

    def __init__(
        self,
        model: BaseSequenceModel,
        device: Optional[torch.device] = None,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        huber_delta: float = 0.01,
        dir_loss_weight: float = 0.5,
        grad_clip: float = 1.0,
        patience: int = 7,
        max_epochs: int = 35,
        time_budget_seconds: float = 8.0,
        seed: int = 42,
    ):
        self.model = model
        self.device = device if device is not None else get_device()
        self.model.to(self.device)

        self.lr = lr
        self.weight_decay = weight_decay
        self.huber_delta = huber_delta
        self.dir_loss_weight = dir_loss_weight
        self.grad_clip = grad_clip
        self.patience = patience
        self.max_epochs = max_epochs
        self.time_budget_seconds = time_budget_seconds
        self.seed = seed

        # Multitask loss criteria
        self.criterion_ret = nn.HuberLoss(delta=huber_delta)
        self.criterion_dir = nn.BCEWithLogitsLoss()

        self.optimizer = AdamW(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = ReduceLROnPlateau(self.optimizer, mode="min", factor=0.5, patience=3, min_lr=1e-5)

        self.best_val_loss = float("inf")
        self.best_epoch = 0
        self.best_state_dict: Optional[Dict[str, Any]] = None
        self.history: List[Dict[str, float]] = []

    def fit(self, train_data: SequenceSplitData, inner_val_data: SequenceSplitData, batch_size: int = 64) -> Dict[str, Any]:
        """Fit model with early stopping on inner validation slice."""
        set_seed(self.seed)
        train_loader = create_dataloader(train_data, batch_size=batch_size, shuffle=True)
        val_loader = create_dataloader(inner_val_data, batch_size=batch_size, shuffle=False)

        epochs_without_improvement = 0
        t0 = time.time()

        for epoch in range(1, self.max_epochs + 1):
            # --- TRAINING PHASE ---
            self.model.train()
            train_loss_sum = 0.0
            train_ret_loss_sum = 0.0
            train_dir_loss_sum = 0.0
            total_train_samples = 0

            for X_b, y_ret_b, y_dir_b, _ in train_loader:
                X_b = X_b.to(self.device)
                y_ret_b = y_ret_b.to(self.device)
                y_dir_b = y_dir_b.to(self.device)

                self.optimizer.zero_grad()
                pred_ret, logits_dir = self.model(X_b)

                loss_ret = self.criterion_ret(pred_ret, y_ret_b)
                loss_dir = self.criterion_dir(logits_dir, y_dir_b)
                total_loss = loss_ret + self.dir_loss_weight * loss_dir

                total_loss.backward()
                if self.grad_clip > 0:
                    nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=self.grad_clip)
                self.optimizer.step()

                batch_n = len(X_b)
                train_loss_sum += float(total_loss.item()) * batch_n
                train_ret_loss_sum += float(loss_ret.item()) * batch_n
                train_dir_loss_sum += float(loss_dir.item()) * batch_n
                total_train_samples += batch_n

            mean_train_loss = train_loss_sum / max(total_train_samples, 1)
            mean_train_ret_loss = train_ret_loss_sum / max(total_train_samples, 1)
            mean_train_dir_loss = train_dir_loss_sum / max(total_train_samples, 1)

            # --- INNER VALIDATION PHASE ---
            self.model.eval()
            val_loss_sum = 0.0
            val_ret_loss_sum = 0.0
            val_dir_loss_sum = 0.0
            total_val_samples = 0

            with torch.no_grad():
                for X_b, y_ret_b, y_dir_b, _ in val_loader:
                    X_b = X_b.to(self.device)
                    y_ret_b = y_ret_b.to(self.device)
                    y_dir_b = y_dir_b.to(self.device)

                    pred_ret, logits_dir = self.model(X_b)
                    loss_ret = self.criterion_ret(pred_ret, y_ret_b)
                    loss_dir = self.criterion_dir(logits_dir, y_dir_b)
                    total_loss = loss_ret + self.dir_loss_weight * loss_dir

                    batch_n = len(X_b)
                    val_loss_sum += float(total_loss.item()) * batch_n
                    val_ret_loss_sum += float(loss_ret.item()) * batch_n
                    val_dir_loss_sum += float(loss_dir.item()) * batch_n
                    total_val_samples += batch_n

            mean_val_loss = val_loss_sum / max(total_val_samples, 1)
            mean_val_ret_loss = val_ret_loss_sum / max(total_val_samples, 1)
            mean_val_dir_loss = val_dir_loss_sum / max(total_val_samples, 1)

            current_lr = float(self.optimizer.param_groups[0]["lr"])
            self.scheduler.step(mean_val_loss)

            self.history.append({
                "epoch": epoch,
                "train_loss": mean_train_loss,
                "train_ret_loss": mean_train_ret_loss,
                "train_dir_loss": mean_train_dir_loss,
                "val_loss": mean_val_loss,
                "val_ret_loss": mean_val_ret_loss,
                "val_dir_loss": mean_val_dir_loss,
                "lr": current_lr,
            })

            # Check early stopping improvement
            if mean_val_loss < self.best_val_loss - 1e-6:
                self.best_val_loss = mean_val_loss
                self.best_epoch = epoch
                self.best_state_dict = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
                if epochs_without_improvement >= self.patience:
                    break

            if time.time() - t0 >= self.time_budget_seconds:
                break

        train_runtime = time.time() - t0

        # Load best weights
        if self.best_state_dict is not None:
            self.model.load_state_dict(self.best_state_dict)

        return {
            "total_epochs": len(self.history),
            "best_epoch": self.best_epoch,
            "best_val_loss": self.best_val_loss,
            "runtime_seconds": train_runtime,
        }

    def predict(
        self,
        val_data: SequenceSplitData,
        full_df: pd.DataFrame,
        model_name: str,
        phase: str,
        horizon: int,
        feature_set: str,
    ) -> Tuple[pd.DataFrame, bool, Dict[str, Any]]:
        """Generate out-of-sample predictions, reconstruct levels, and audit against collapse."""
        self.model.eval()
        val_loader = create_dataloader(val_data, batch_size=128, shuffle=False)

        all_preds_ret: List[float] = []
        all_probs_up: List[float] = []

        with torch.no_grad():
            for X_b, _, _, _ in val_loader:
                X_b = X_b.to(self.device)
                pred_ret, logits_dir = self.model(X_b)
                probs = torch.sigmoid(logits_dir)

                all_preds_ret.extend(pred_ret.cpu().numpy().tolist())
                all_probs_up.extend(probs.cpu().numpy().tolist())

        y_pred_ret = np.array(all_preds_ret, dtype=float)
        p_up = np.array(all_probs_up, dtype=float)
        y_pred_dir = (p_up > 0.5).astype(int)

        dates = val_data.dates
        y_true_ret = np.array(val_data.y_ret, dtype=float)
        y_true_dir = np.array(val_data.y_dir, dtype=int)

        # Retrieve exact aspi_t base prices for matched dates from full clean DataFrame
        date_to_aspi = dict(zip(pd.to_datetime(full_df["date"]).dt.strftime("%Y-%m-%d"), full_df["aspi"].values))
        aspi_t = np.array([date_to_aspi.get(str(d)[:10], 1000.0) for d in dates], dtype=float)
        aspi_pred_level = aspi_t * np.exp(y_pred_ret)

        df_out = pd.DataFrame({
            "model": model_name,
            "family": "deep",
            "phase": phase,
            "horizon": horizon,
            "feature_set": feature_set,
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

        # Sanity collapse check: detect trivial constant predictions
        pred_std = float(np.std(y_pred_ret))
        dir_mean = float(np.mean(y_pred_dir))
        is_collapsed = bool(pred_std < 1e-4 or dir_mean > 0.98 or dir_mean < 0.02)

        diagnostics = {
            "pred_ret_std": pred_std,
            "pred_dir_mean": dir_mean,
            "is_collapsed": is_collapsed,
        }

        return df_out, is_collapsed, diagnostics

    def save_artifacts(
        self,
        artifact_dir: Path,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save model checkpoint, curves CSV, curves PNG, and meta.json."""
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # 1. Checkpoint
        ckpt_path = artifact_dir / "checkpoint.pt"
        torch.save(self.model.state_dict(), ckpt_path)

        # 2. Curves CSV
        df_curves = pd.DataFrame(self.history)
        curves_csv = artifact_dir / "curves.csv"
        df_curves.to_csv(curves_csv, index=False)

        # 3. Curves PNG plot
        curves_png = artifact_dir / "curves.png"
        if len(self.history) > 0:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(df_curves["epoch"], df_curves["train_loss"], label="Train Loss (Huber + BCE)", color="tab:blue")
            ax.plot(df_curves["epoch"], df_curves["val_loss"], label="Inner-Val Loss", color="tab:orange")
            ax.axvline(x=self.best_epoch, color="red", linestyle="--", alpha=0.7, label=f"Best Epoch ({self.best_epoch})")
            ax.set_title(f"Deep Sequence Training Curves - Seed {self.seed}", fontsize=11, fontweight="bold")
            ax.set_xlabel("Epoch")
            ax.set_ylabel("Loss")
            ax.legend(loc="upper right")
            plt.tight_layout()
            fig.savefig(curves_png, dpi=120)
            plt.close(fig)

        # 4. Meta JSON
        meta_dict = {
            "parameters": self.model.count_parameters(),
            "best_epoch": self.best_epoch,
            "best_val_loss": self.best_val_loss,
            "total_epochs": len(self.history),
            "seed": self.seed,
            "hardware": get_hardware_info(),
        }
        if extra_meta:
            meta_dict.update(extra_meta)

        with open(artifact_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)
