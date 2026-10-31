"""Statistical hypothesis testing for predictive superiority and directional accuracy.

Implements:
1. Diebold-Mariano test with Harvey-Leybourne-Newbold (HLN 1997) finite-sample correction.
2. Binomial test of directional accuracy vs 50% and vs majority-class benchmark.
3. Pesaran-Timmermann (1992) non-parametric test of directional predictability.
4. Newey-West HAC standard errors for overlapping multi-step returns.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
from scipy import stats


def newey_west_variance(d: np.ndarray, max_lags: int) -> float:
    """Compute Newey-West HAC variance of the sample mean of series d."""
    T = len(d)
    if T <= 1:
        return float("nan")
        
    d_centered = d - np.mean(d)
    gamma_0 = float(np.sum(d_centered ** 2) / T)
    
    if max_lags <= 0:
        return gamma_0
        
    v = gamma_0
    for lag in range(1, max_lags + 1):
        weight = 1.0 - (lag / (max_lags + 1))  # Bartlett kernel
        gamma_lag = float(np.sum(d_centered[lag:] * d_centered[:-lag]) / T)
        v += 2.0 * weight * gamma_lag
        
    return max(v, 1e-12)


def diebold_mariano(
    e_candidate: np.ndarray,
    e_benchmark: np.ndarray,
    h: int = 1,
    power: int = 2,
    alternative: str = "two-sided",
) -> Dict[str, Any]:
    """Diebold-Mariano test with Harvey, Leybourne & Newbold (HLN 1997) correction.
    
    Args:
        e_candidate: Prediction errors of candidate model (y_true - y_pred).
        e_benchmark: Prediction errors of benchmark model (e.g. Random Walk or Historical Mean).
        h: Forecast horizon in trading days (default: 1).
        power: Loss power (2 for MSE, 1 for MAE).
        alternative: 'two-sided', 'less' (candidate model loss < benchmark), or 'greater'.
        
    Returns:
        Dict with 'dm_stat', 'dm_hln_stat', 'p_value', 'mean_loss_diff', 'df'.
    """
    e1 = np.asarray(e_candidate, dtype=float)
    e2 = np.asarray(e_benchmark, dtype=float)
    
    mask = ~np.isnan(e1) & ~np.isnan(e2)
    e1 = e1[mask]
    e2 = e2[mask]
    
    T = len(e1)
    if T <= (h + 1):
        return {
            "dm_stat": float("nan"),
            "dm_hln_stat": float("nan"),
            "p_value": float("nan"),
            "mean_loss_diff": float("nan"),
            "df": 0,
        }
        
    # Loss differential: d_t = L(e1_t) - L(e2_t)
    if power == 2:
        d = (e1 ** 2) - (e2 ** 2)
    elif power == 1:
        d = np.abs(e1) - np.abs(e2)
    else:
        d = (np.abs(e1) ** power) - (np.abs(e2) ** power)
        
    d_bar = float(np.mean(d))
    
    # Autocovariances up to lag h - 1
    d_centered = d - d_bar
    gamma_0 = float(np.sum(d_centered ** 2) / T)
    
    long_run_var = gamma_0
    if h > 1:
        for lag in range(1, h):
            gamma_lag = float(np.sum(d_centered[lag:] * d_centered[:-lag]) / T)
            long_run_var += 2.0 * gamma_lag
            
    # Guarantee positive variance using Bartlett fallback if negative
    if long_run_var <= 0:
        long_run_var = newey_west_variance(d, max_lags=h - 1)
        
    var_d_bar = long_run_var / T
    if var_d_bar <= 0:
        dm_stat = 0.0
    else:
        dm_stat = d_bar / np.sqrt(var_d_bar)
        
    # Harvey-Leybourne-Newbold (HLN 1997) finite-sample correction
    # Correction factor = sqrt((T + 1 - 2*h + h*(h - 1)/T) / T)
    hln_term = (T + 1.0 - 2.0 * h + (h * (h - 1.0) / T)) / T
    hln_factor = np.sqrt(max(hln_term, 1e-12))
    dm_hln_stat = dm_stat * hln_factor
    
    df = T - 1
    if alternative == "two-sided":
        p_val = 2.0 * (1.0 - stats.t.cdf(np.abs(dm_hln_stat), df=df))
    elif alternative == "less":
        # Candidate is better (loss diff < 0)
        p_val = stats.t.cdf(dm_hln_stat, df=df)
    elif alternative == "greater":
        p_val = 1.0 - stats.t.cdf(dm_hln_stat, df=df)
    else:
        raise ValueError(f"Unknown alternative: {alternative}")
        
    return {
        "dm_stat": float(dm_stat),
        "dm_hln_stat": float(dm_hln_stat),
        "p_value": float(p_val),
        "mean_loss_diff": float(d_bar),
        "df": int(df),
    }


def binomial_accuracy_test(
    y_true_dir: np.ndarray,
    y_pred_dir: np.ndarray,
    p_null: float = 0.5,
    alternative: str = "greater",
) -> Dict[str, Any]:
    """Exact binomial test of directional classification accuracy against a null rate.
    
    Args:
        y_true_dir: Realized binary directions (0 or 1).
        y_pred_dir: Predicted binary directions (0 or 1).
        p_null: Null success probability (0.5 for random coin-flip; or majority class proportion).
        alternative: 'greater', 'two-sided', or 'less'.
        
    Returns:
        Dict with 'successes', 'total', 'accuracy', 'p_null', 'p_value'.
    """
    y_t = np.asarray(y_true_dir, dtype=int)
    y_p = np.asarray(y_pred_dir, dtype=int)
    
    mask = ~np.isnan(y_t) & ~np.isnan(y_p)
    y_t = y_t[mask]
    y_p = y_p[mask]
    
    n_total = len(y_t)
    if n_total == 0:
        return {
            "successes": 0,
            "total": 0,
            "accuracy": float("nan"),
            "p_null": p_null,
            "p_value": float("nan"),
        }
        
    k_success = int(np.sum(y_t == y_p))
    acc = k_success / n_total
    
    res = stats.binomtest(k=k_success, n=n_total, p=p_null, alternative=alternative)
    return {
        "successes": k_success,
        "total": n_total,
        "accuracy": float(acc),
        "p_null": float(p_null),
        "p_value": float(res.pvalue),
    }


def pesaran_timmermann(y_true_dir: np.ndarray, y_pred_dir: np.ndarray) -> Dict[str, Any]:
    """Pesaran and Timmermann (1992) non-parametric test of directional predictability.
    
    H0: Realized direction and predicted direction are statistically independent.
    Under H0, the PT test statistic is asymptotically standard normal N(0, 1).
    """
    y_t = np.asarray(y_true_dir, dtype=int)
    y_p = np.asarray(y_pred_dir, dtype=int)
    
    mask = ~np.isnan(y_t) & ~np.isnan(y_p)
    y_t = y_t[mask]
    y_p = y_p[mask]
    
    T = len(y_t)
    if T <= 2:
        return {
            "pt_stat": float("nan"),
            "p_value": float("nan"),
            "success_rate": float("nan"),
            "expected_rate": float("nan"),
        }
        
    # Success rate
    P = np.mean(y_t == y_p)
    
    # Marginal probabilities
    P_y = np.mean(y_t)
    P_y_hat = np.mean(y_p)
    
    # Expected success rate under independence
    P_star = (P_y * P_y_hat) + ((1.0 - P_y) * (1.0 - P_y_hat))
    
    # Variances under independence
    var_P = (P_star * (1.0 - P_star)) / T
    
    term1 = ((2.0 * P_y - 1.0) ** 2) * (P_y_hat * (1.0 - P_y_hat)) / T
    term2 = ((2.0 * P_y_hat - 1.0) ** 2) * (P_y * (1.0 - P_y)) / T
    term3 = (4.0 * P_y * P_y_hat * (1.0 - P_y) * (1.0 - P_y_hat)) / (T ** 2)
    var_P_star = term1 + term2 + term3
    
    denom = var_P - var_P_star
    if denom <= 0:
        # Edge case: degenerate predictions
        pt_stat = 0.0
        p_val = 1.0
    else:
        pt_stat = float((P - P_star) / np.sqrt(denom))
        p_val = float(2.0 * (1.0 - stats.norm.cdf(np.abs(pt_stat))))
        
    return {
        "pt_stat": float(pt_stat),
        "p_value": float(p_val),
        "success_rate": float(P),
        "expected_rate": float(P_star),
    }
