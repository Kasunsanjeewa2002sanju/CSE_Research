"""Evaluation metrics for log returns, reconstructed index levels, and directional classification.

Adheres strictly to:
- Rule R4: Models predict log returns; levels are reconstructed afterwards.
- Protocol: MAE, RMSE, OOS R2 vs historical mean, Theil's U vs random walk;
  level MAE, RMSE, MAPE; direction accuracy, balanced accuracy, precision,
  recall, F1, MCC, ROC-AUC; overlapping vs non-overlapping weekly subsampling.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


def calc_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    mask = ~np.isnan(y_t) & ~np.isnan(y_p)
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs(y_t[mask] - y_p[mask])))


def calc_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    mask = ~np.isnan(y_t) & ~np.isnan(y_p)
    if not np.any(mask):
        return float("nan")
    return float(np.sqrt(np.mean((y_t[mask] - y_p[mask]) ** 2)))


def calc_oos_r2(y_true: np.ndarray, y_pred: np.ndarray, y_benchmark: np.ndarray) -> float:
    """Out-of-sample R-squared (Campbell & Thompson 2008).
    
    R2_OOS = 1 - sum((y - y_pred)^2) / sum((y - y_benchmark)^2)
    Positive value indicates the model forecasts outperform the benchmark forecast.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    y_b = np.asarray(y_benchmark, dtype=float)
    
    mask = ~np.isnan(y_t) & ~np.isnan(y_p) & ~np.isnan(y_b)
    if not np.any(mask):
        return float("nan")
    
    sse_model = np.sum((y_t[mask] - y_p[mask]) ** 2)
    sse_bench = np.sum((y_t[mask] - y_b[mask]) ** 2)
    
    if sse_bench == 0:
        return float("nan")
    return float(1.0 - (sse_model / sse_bench))


def calc_theils_u(y_true: np.ndarray, y_pred: np.ndarray, y_benchmark_rw: Optional[np.ndarray] = None) -> float:
    """Theil's U statistic versus Random Walk (zero return forecast).
    
    Theil's U = RMSE(model) / RMSE(RW)
    A value < 1 indicates superiority over the naive random walk.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    if y_benchmark_rw is None:
        y_b = np.zeros_like(y_t)
    else:
        y_b = np.asarray(y_benchmark_rw, dtype=float)
        
    rmse_model = calc_rmse(y_t, y_p)
    rmse_bench = calc_rmse(y_t, y_b)
    
    if rmse_bench == 0 or np.isnan(rmse_bench):
        return float("nan")
    return float(rmse_model / rmse_bench)


def calc_level_mae(level_true: np.ndarray, level_pred: np.ndarray) -> float:
    """Mean Absolute Error on reconstructed index price levels."""
    return calc_mae(level_true, level_pred)


def calc_level_rmse(level_true: np.ndarray, level_pred: np.ndarray) -> float:
    """Root Mean Squared Error on reconstructed index price levels."""
    return calc_rmse(level_true, level_pred)


def calc_level_mape(level_true: np.ndarray, level_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error on reconstructed price levels (%)."""
    l_t = np.asarray(level_true, dtype=float)
    l_p = np.asarray(level_pred, dtype=float)
    mask = ~np.isnan(l_t) & ~np.isnan(l_p) & (l_t > 0)
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((l_t[mask] - l_p[mask]) / l_t[mask])) * 100.0)


def calc_direction_accuracy(y_true_dir: np.ndarray, y_pred_dir: np.ndarray) -> float:
    """Standard directional accuracy fraction."""
    y_t = np.asarray(y_true_dir, dtype=int)
    y_p = np.asarray(y_pred_dir, dtype=int)
    if len(y_t) == 0:
        return float("nan")
    return float(np.mean(y_t == y_p))


def calc_confusion_matrix(y_true_dir: np.ndarray, y_pred_dir: np.ndarray) -> Dict[str, int]:
    """Compute binary classification confusion matrix components: TP, FP, TN, FN."""
    y_t = np.asarray(y_true_dir, dtype=int)
    y_p = np.asarray(y_pred_dir, dtype=int)
    
    tp = int(np.sum((y_t == 1) & (y_p == 1)))
    fp = int(np.sum((y_t == 0) & (y_p == 1)))
    tn = int(np.sum((y_t == 0) & (y_p == 0)))
    fn = int(np.sum((y_t == 1) & (y_p == 0)))
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def calc_balanced_accuracy(y_true_dir: np.ndarray, y_pred_dir: np.ndarray) -> float:
    """Balanced directional accuracy: (Sensitivity + Specificity) / 2."""
    cm = calc_confusion_matrix(y_true_dir, y_pred_dir)
    tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]
    
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    return float(0.5 * (tpr + tnr))


def calc_precision(y_true_dir: np.ndarray, y_pred_dir: np.ndarray) -> float:
    """Direction precision: TP / (TP + FP)."""
    cm = calc_confusion_matrix(y_true_dir, y_pred_dir)
    denom = cm["tp"] + cm["fp"]
    return float(cm["tp"] / denom) if denom > 0 else 0.0


def calc_recall(y_true_dir: np.ndarray, y_pred_dir: np.ndarray) -> float:
    """Direction recall / sensitivity: TP / (TP + FN)."""
    cm = calc_confusion_matrix(y_true_dir, y_pred_dir)
    denom = cm["tp"] + cm["fn"]
    return float(cm["tp"] / denom) if denom > 0 else 0.0


def calc_f1(y_true_dir: np.ndarray, y_pred_dir: np.ndarray) -> float:
    """Direction F1 score."""
    p = calc_precision(y_true_dir, y_pred_dir)
    r = calc_recall(y_true_dir, y_pred_dir)
    if (p + r) == 0:
        return 0.0
    return float(2.0 * p * r / (p + r))


def calc_mcc(y_true_dir: np.ndarray, y_pred_dir: np.ndarray) -> float:
    """Matthews Correlation Coefficient for directional predictions."""
    cm = calc_confusion_matrix(y_true_dir, y_pred_dir)
    tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]
    
    numerator = (tp * tn) - (fp * fn)
    denominator = np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def calc_roc_auc(y_true_dir: np.ndarray, p_up: Optional[np.ndarray]) -> Optional[float]:
    """Compute Area Under the ROC Curve if probabilities exist."""
    if p_up is None:
        return None
    y_t = np.asarray(y_true_dir, dtype=int)
    p = np.asarray(p_up, dtype=float)
    
    mask = ~np.isnan(p)
    y_t = y_t[mask]
    p = p[mask]
    
    # Must have both positive and negative cases
    n_pos = np.sum(y_t == 1)
    n_neg = np.sum(y_t == 0)
    if n_pos == 0 or n_neg == 0 or len(y_t) == 0:
        return None
        
    # Mann-Whitney U formula for ROC AUC
    # Ranks of positive cases
    ranks = stats.rankdata(p)
    sum_ranks_pos = np.sum(ranks[y_t == 1])
    u_stat = sum_ranks_pos - (n_pos * (n_pos + 1) / 2.0)
    return float(u_stat / (n_pos * n_neg))


def get_non_overlapping_indices(n_total: int, step: int = 5) -> np.ndarray:
    """Return indices for non-overlapping evaluation subsamples (e.g. every 5th day)."""
    return np.arange(0, n_total, step)


def calc_all_metrics(
    y_true_ret: np.ndarray,
    y_pred_ret: np.ndarray,
    y_benchmark_ret: np.ndarray,
    y_true_dir: np.ndarray,
    y_pred_dir: np.ndarray,
    aspi_true_level: np.ndarray,
    aspi_pred_level: np.ndarray,
    p_up: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Calculate the complete battery of evaluation metrics for a single prediction set."""
    metrics = {
        "mae": calc_mae(y_true_ret, y_pred_ret),
        "rmse": calc_rmse(y_true_ret, y_pred_ret),
        "oos_r2": calc_oos_r2(y_true_ret, y_pred_ret, y_benchmark_ret),
        "theils_u": calc_theils_u(y_true_ret, y_pred_ret),
        "level_mae": calc_level_mae(aspi_true_level, aspi_pred_level),
        "level_rmse": calc_level_rmse(aspi_true_level, aspi_pred_level),
        "level_mape": calc_level_mape(aspi_true_level, aspi_pred_level),
        "accuracy": calc_direction_accuracy(y_true_dir, y_pred_dir),
        "balanced_accuracy": calc_balanced_accuracy(y_true_dir, y_pred_dir),
        "precision": calc_precision(y_true_dir, y_pred_dir),
        "recall": calc_recall(y_true_dir, y_pred_dir),
        "f1": calc_f1(y_true_dir, y_pred_dir),
        "mcc": calc_mcc(y_true_dir, y_pred_dir),
        "roc_auc": calc_roc_auc(y_true_dir, p_up),
    }
    return metrics
