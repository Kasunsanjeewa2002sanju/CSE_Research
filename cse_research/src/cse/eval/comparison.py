"""Model Comparison, Statistical Hypothesis Testing, and Ablation Engine for Stage 9.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead.
- Rule R3: Flag suspicious results (Acc > 60% or R2 > 0.10).
- Rule R5: Uniform protocol across all 5 phases and horizons.
- Rule R6: Full persistence of all tables, metrics, model cards, and figures.
- Rule R7: Pinned seeds and reproducible outputs.
- Rule R8: Honest reporting of negative and null results.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

from cse.eval.tests_stat import (
    binomial_accuracy_test,
    diebold_mariano,
    pesaran_timmermann,
)
from cse.utils.config import find_project_root
from cse.utils.logger import get_logger

logger = get_logger("cse.eval.comparison")


def holm_bonferroni_correction(p_values: np.ndarray) -> np.ndarray:
    """Compute Holm-Bonferroni step-down family-wise error rate (FWER) adjusted p-values."""
    p_vals = np.asarray(p_values, dtype=float)
    n = len(p_vals)
    if n == 0:
        return p_vals

    order = np.argsort(p_vals)
    adj_p = np.zeros(n, dtype=float)
    
    running_max = 0.0
    for rank, idx in enumerate(order):
        multiplier = n - rank
        raw_p = p_vals[idx]
        adj = min(1.0, raw_p * multiplier)
        running_max = max(running_max, adj)
        adj_p[idx] = running_max

    return adj_p


def benjamini_hochberg_correction(p_values: np.ndarray) -> np.ndarray:
    """Compute Benjamini-Hochberg (1995) False Discovery Rate (FDR) adjusted p-values."""
    p_vals = np.asarray(p_values, dtype=float)
    n = len(p_vals)
    if n == 0:
        return p_vals

    order = np.argsort(p_vals)
    adj_p = np.zeros(n, dtype=float)

    running_min = 1.0
    for rank in range(n - 1, -1, -1):
        idx = order[rank]
        multiplier = n / (rank + 1)
        raw_p = p_vals[idx]
        adj = min(1.0, raw_p * multiplier)
        running_min = min(running_min, adj)
        adj_p[idx] = running_min

    return adj_p


def build_master_table(
    metrics_long_df: pd.DataFrame,
    primary_horizon: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Build standardized master table aggregated across the 5 validation phases from metrics_long.csv.
    
    Produces:
    1. df_master: One row per (model, family, feature_set, horizon) with mean, std across phases,
       per-phase breakdown, and family + global ranks.
    2. df_per_phase: Detailed per-phase pivot table.
    """
    logger.info("Building Master Table from %d metric rows...", len(metrics_long_df))
    
    key_metrics = [
        "oos_r2", "accuracy", "balanced_accuracy", "rmse", "mae",
        "theils_u", "level_mae", "level_rmse", "f1", "mcc"
    ]
    
    # Filter to valid metrics and models
    df_clean = metrics_long_df[metrics_long_df["metric"].isin(key_metrics)].copy()
    
    # Grouping keys
    group_cols = ["model", "family", "feature_set", "horizon"]
    
    # Compute per-phase pivots
    pivot_phase = df_clean.pivot_table(
        index=group_cols,
        columns=["metric", "phase"],
        values="value",
        aggfunc="mean",
    )
    
    # Compute mean and std across phases
    stats_rows = []
    unique_groups = df_clean[group_cols].drop_duplicates().values
    
    for row in unique_groups:
        m, fam, fset, h = row
        sub = df_clean[
            (df_clean["model"] == m) &
            (df_clean["family"] == fam) &
            (df_clean["feature_set"] == fset) &
            (df_clean["horizon"] == h)
        ]
        
        entry: Dict[str, Any] = {
            "model": m,
            "family": fam,
            "feature_set": fset,
            "horizon": h,
        }
        
        # Phase count
        phases_present = sub["phase"].unique()
        entry["n_phases"] = len(phases_present)
        
        for met in key_metrics:
            met_sub = sub[sub["metric"] == met]
            if not met_sub.empty:
                entry[f"{met}_mean"] = float(met_sub["value"].mean())
                entry[f"{met}_std"] = float(met_sub["value"].std(ddof=1)) if len(met_sub) > 1 else 0.0
                # per phase values
                for p in ["P1", "P2", "P3", "P4", "P5"]:
                    p_val = met_sub[met_sub["phase"] == p]["value"]
                    if not p_val.empty:
                        entry[f"{met}_{p}"] = float(p_val.iloc[0])
                    else:
                        entry[f"{met}_{p}"] = np.nan
            else:
                entry[f"{met}_mean"] = np.nan
                entry[f"{met}_std"] = np.nan

        # Count phases beating baseline (oos_r2 > 0 and accuracy > 0.50)
        r2_sub = sub[sub["metric"] == "oos_r2"]
        acc_sub = sub[sub["metric"] == "accuracy"]
        entry["phases_beating_r2_zero"] = int((r2_sub["value"] > 0).sum())
        entry["phases_beating_acc_50"] = int((acc_sub["value"] > 0.50).sum())
        
        stats_rows.append(entry)
        
    df_master = pd.DataFrame(stats_rows)
    
    # Add ranks per horizon
    for h in df_master["horizon"].unique():
        h_mask = df_master["horizon"] == h
        # Global rank on oos_r2_mean
        df_master.loc[h_mask, "rank_overall"] = (
            df_master.loc[h_mask, "oos_r2_mean"]
            .rank(ascending=False, method="min")
            .astype(int)
        )
        
        # Family rank
        for fam in df_master["family"].unique():
            fam_h_mask = h_mask & (df_master["family"] == fam)
            if fam_h_mask.any():
                df_master.loc[fam_h_mask, "rank_family"] = (
                    df_master.loc[fam_h_mask, "oos_r2_mean"]
                    .rank(ascending=False, method="min")
                    .astype(int)
                )

    df_master["rank_overall"] = df_master["rank_overall"].astype(int)
    df_master["rank_family"] = df_master["rank_family"].astype(int)
    df_master = df_master.sort_values(["horizon", "rank_overall"]).reset_index(drop=True)
    
    logger.info("Master table assembled: %d unique model configurations.", len(df_master))
    return df_master, pivot_phase


def compute_pooled_statistical_tests(
    pred_dir: Path,
    phases: List[str] = ["P1", "P2", "P3", "P4", "P5"],
    horizons: List[int] = [1, 5],
) -> pd.DataFrame:
    """Compute pooled and per-phase statistical tests across all models versus baselines.
    
    Includes:
    - Diebold-Mariano (HLN) vs Random Walk (pooled & per-phase)
    - Diebold-Mariano (HLN) vs Historical Mean (pooled & per-phase)
    - Pesaran-Timmermann direction test (pooled)
    - Binomial direction test vs 50% (pooled)
    - Holm-Bonferroni and Benjamini-Hochberg multiple testing adjustments
    """
    logger.info("Computing pooled statistical tests across all predictions...")
    
    # 1. Load benchmarks
    benchmarks: Dict[Tuple[str, int], Dict[str, pd.DataFrame]] = {}
    for p in phases:
        for h in horizons:
            p_rw = pred_dir / "baseline" / f"random_walk_{p}_h{h}.parquet"
            p_hm = pred_dir / "baseline" / f"historical_mean_{p}_h{h}.parquet"
            benchmarks[(p, h)] = {
                "rw": pd.read_parquet(p_rw),
                "hm": pd.read_parquet(p_hm),
            }

    # 2. Discover all unique model predictions across families
    families = ["baseline", "statistical", "shallow", "deep", "foundation", "hybrid"]
    records = []

    for h in horizons:
        # Build pooled benchmarks for horizon h
        rw_pooled = pd.concat([benchmarks[(p, h)]["rw"] for p in phases], ignore_index=True)
        hm_pooled = pd.concat([benchmarks[(p, h)]["hm"] for p in phases], ignore_index=True)
        e_rw_pooled = rw_pooled["y_true_ret"].values - rw_pooled["y_pred_ret"].values
        e_hm_pooled = hm_pooled["y_true_ret"].values - hm_pooled["y_pred_ret"].values
        y_true_dir_pooled = rw_pooled["y_true_dir"].values

        # Find models with all 5 phases present
        model_map: Dict[str, Tuple[str, List[Path]]] = {}
        for fam in families:
            fam_dir = pred_dir / fam
            if not fam_dir.exists():
                continue
            for p_file in fam_dir.glob(f"*_h{h}.parquet"):
                stem = p_file.stem
                # stem format: {model}_{phase}_h{h}
                parts = stem.rsplit("_", 2)
                if len(parts) == 3 and parts[2] == f"h{h}":
                    m_tag, phase = parts[0], parts[1]
                    if m_tag not in model_map:
                        model_map[m_tag] = (fam, [])
                    model_map[m_tag][1].append(p_file)

        # Evaluate each model
        for m_tag, (fam, file_list) in model_map.items():
            # Only consider models with all 5 phases
            phase_files = {}
            for f in file_list:
                p_match = f.stem.rsplit("_", 2)[1]
                if p_match in phases:
                    phase_files[p_match] = f

            if len(phase_files) < len(phases):
                continue

            # Load and concatenate across phases
            dfs = [pd.read_parquet(phase_files[p]) for p in phases]
            cand_pooled = pd.concat(dfs, ignore_index=True)

            # Align with pooled benchmarks on date
            merged_pooled = pd.merge(
                cand_pooled[["date", "y_true_ret", "y_pred_ret", "y_true_dir", "y_pred_dir"]],
                rw_pooled[["date", "y_pred_ret"]].rename(columns={"y_pred_ret": "y_pred_rw"}),
                on="date",
                how="inner",
            )
            merged_pooled = pd.merge(
                merged_pooled,
                hm_pooled[["date", "y_pred_ret"]].rename(columns={"y_pred_ret": "y_pred_hm"}),
                on="date",
                how="inner",
            )

            if len(merged_pooled) < 100:
                continue

            e_cand_pooled = merged_pooled["y_true_ret"].values - merged_pooled["y_pred_ret"].values
            e_rw_pooled_sub = merged_pooled["y_true_ret"].values - merged_pooled["y_pred_rw"].values
            e_hm_pooled_sub = merged_pooled["y_true_ret"].values - merged_pooled["y_pred_hm"].values
            y_true_dir_pooled_sub = merged_pooled["y_true_dir"].values
            y_pred_dir_pooled_sub = merged_pooled["y_pred_dir"].values

            # Pooled DM vs RW
            dm_rw_res = diebold_mariano(e_cand_pooled, e_rw_pooled_sub, h=h)
            # Pooled DM vs HM
            dm_hm_res = diebold_mariano(e_cand_pooled, e_hm_pooled_sub, h=h)
            # Pooled Pesaran-Timmermann
            pt_res = pesaran_timmermann(y_true_dir_pooled_sub, y_pred_dir_pooled_sub)
            # Pooled Binomial vs 50%
            bin_res = binomial_accuracy_test(y_true_dir_pooled_sub, y_pred_dir_pooled_sub, p_null=0.5)

            # Pooled metrics
            pooled_mse = float(np.mean(e_cand_pooled ** 2))
            pooled_hm_mse = float(np.mean(e_hm_pooled_sub ** 2))
            pooled_oos_r2 = float(1.0 - (pooled_mse / pooled_hm_mse)) if pooled_hm_mse > 0 else 0.0
            pooled_acc = float(np.mean(y_true_dir_pooled_sub == y_pred_dir_pooled_sub))
            pooled_rmse = float(np.sqrt(pooled_mse))
            pooled_mae = float(np.mean(np.abs(e_cand_pooled)))

            # Per-phase DM results
            dm_rw_pvals_per_phase = []
            dm_hm_pvals_per_phase = []
            for p in phases:
                df_p = pd.read_parquet(phase_files[p])
                bench_rw_p = benchmarks[(p, h)]["rw"]
                bench_hm_p = benchmarks[(p, h)]["hm"]
                
                m_p = pd.merge(
                    df_p[["date", "y_true_ret", "y_pred_ret"]],
                    bench_rw_p[["date", "y_pred_ret"]].rename(columns={"y_pred_ret": "y_pred_rw"}),
                    on="date",
                    how="inner",
                )
                m_p = pd.merge(
                    m_p,
                    bench_hm_p[["date", "y_pred_ret"]].rename(columns={"y_pred_ret": "y_pred_hm"}),
                    on="date",
                    how="inner",
                )
                
                e_cand_p = m_p["y_true_ret"].values - m_p["y_pred_ret"].values
                e_rw_p = m_p["y_true_ret"].values - m_p["y_pred_rw"].values
                e_hm_p = m_p["y_true_ret"].values - m_p["y_pred_hm"].values
                
                dm_rw_p = diebold_mariano(e_cand_p, e_rw_p, h=h)["p_value"]
                dm_hm_p = diebold_mariano(e_cand_p, e_hm_p, h=h)["p_value"]
                dm_rw_pvals_per_phase.append(dm_rw_p)
                dm_hm_pvals_per_phase.append(dm_hm_p)

            rec = {
                "model": m_tag,
                "family": fam,
                "horizon": h,
                "n_samples": len(cand_pooled),
                "pooled_oos_r2": pooled_oos_r2,
                "pooled_accuracy": pooled_acc,
                "pooled_rmse": pooled_rmse,
                "pooled_mae": pooled_mae,
                "dm_rw_stat": dm_rw_res["dm_hln_stat"],
                "dm_rw_pval": dm_rw_res["p_value"],
                "dm_hm_stat": dm_hm_res["dm_hln_stat"],
                "dm_hm_pval": dm_hm_res["p_value"],
                "pt_stat": pt_res["pt_stat"],
                "pt_pval": pt_res["p_value"],
                "binom_acc": bin_res["accuracy"],
                "binom_pval": bin_res["p_value"],
                "dm_rw_pval_P1": dm_rw_pvals_per_phase[0],
                "dm_rw_pval_P2": dm_rw_pvals_per_phase[1],
                "dm_rw_pval_P3": dm_rw_pvals_per_phase[2],
                "dm_rw_pval_P4": dm_rw_pvals_per_phase[3],
                "dm_rw_pval_P5": dm_rw_pvals_per_phase[4],
            }
            records.append(rec)

    df_tests = pd.DataFrame(records)

    # 3. Add multiple testing corrections per horizon
    for h in horizons:
        h_mask = df_tests["horizon"] == h
        if not h_mask.any():
            continue
        
        # Adjust dm_rw_pval
        raw_dm_rw = df_tests.loc[h_mask, "dm_rw_pval"].values
        df_tests.loc[h_mask, "dm_rw_pval_holm"] = holm_bonferroni_correction(raw_dm_rw)
        df_tests.loc[h_mask, "dm_rw_pval_bh"] = benjamini_hochberg_correction(raw_dm_rw)

        # Adjust dm_hm_pval
        raw_dm_hm = df_tests.loc[h_mask, "dm_hm_pval"].values
        df_tests.loc[h_mask, "dm_hm_pval_holm"] = holm_bonferroni_correction(raw_dm_hm)
        df_tests.loc[h_mask, "dm_hm_pval_bh"] = benjamini_hochberg_correction(raw_dm_hm)

        # Adjust pt_pval
        raw_pt = df_tests.loc[h_mask, "pt_pval"].values
        df_tests.loc[h_mask, "pt_pval_holm"] = holm_bonferroni_correction(raw_pt)
        df_tests.loc[h_mask, "pt_pval_bh"] = benjamini_hochberg_correction(raw_pt)

    df_tests = df_tests.sort_values(["horizon", "pooled_oos_r2"], ascending=[True, False]).reset_index(drop=True)
    logger.info("Statistical tests completed for %d models across horizons %s.", len(df_tests), horizons)
    return df_tests


def compute_feature_set_ablation(
    pred_dir: Path,
    phases: List[str] = ["P1", "P2", "P3", "P4", "P5"],
    horizons: List[int] = [1, 5],
) -> pd.DataFrame:
    """Ablation Study: Compare Feature Set C vs B vs A across all compatible model architectures.
    
    Tests whether political event features (Set C) improve forecast accuracy over Set B and Set A.
    Uses paired t-tests and Wilcoxon signed-rank tests on loss differentials.
    """
    logger.info("Computing Feature Set Ablation (Set C vs Set B vs Set A)...")
    
    # Candidate architectures that were trained on all 3 sets
    architectures = [
        "catboost_reg", "extra_trees_reg", "random_forest_reg", "gradient_boosting_reg",
        "xgboost_reg", "lightgbm_reg", "ridge", "lasso", "elastic_net", "mlp", "linear_regression"
    ]
    
    ablation_rows = []
    
    for h in horizons:
        for arch in architectures:
            # Check availability of Set A, B, C
            # Model file stems: {arch}_{set}_s42_{phase}_h{h}.parquet or {arch}_{set}_{phase}_h{h}.parquet
            for fam in ["shallow", "statistical", "deep"]:
                fam_dir = pred_dir / fam
                if not fam_dir.exists():
                    continue

                def load_pooled(letter: str) -> Optional[pd.DataFrame]:
                    pats = [
                        f"{arch}_{letter}_s42", f"{arch}_{letter}", f"{arch}_{letter.lower()}", f"{arch}_{letter.upper()}"
                    ]
                    dfs = []
                    for p in phases:
                        found = None
                        for pat in pats:
                            cand = fam_dir / f"{pat}_{p}_h{h}.parquet"
                            if cand.exists():
                                found = cand
                                break
                        if found:
                            dfs.append(pd.read_parquet(found))
                    if len(dfs) == len(phases):
                        return pd.concat(dfs, ignore_index=True)
                    return None

                df_a = load_pooled("a")
                df_b = load_pooled("b")
                df_c = load_pooled("c")

                if df_a is not None and df_b is not None and df_c is not None:
                    # Compare C vs B
                    e_a = df_a["y_true_ret"].values - df_a["y_pred_ret"].values
                    e_b = df_b["y_true_ret"].values - df_b["y_pred_ret"].values
                    e_c = df_c["y_true_ret"].values - df_c["y_pred_ret"].values

                    loss_a = e_a ** 2
                    loss_b = e_b ** 2
                    loss_c = e_c ** 2

                    diff_cb = loss_c - loss_b
                    diff_ca = loss_c - loss_a
                    diff_ba = loss_b - loss_a

                    # Paired t-tests
                    t_stat_cb, p_val_cb = stats.ttest_rel(loss_c, loss_b)
                    t_stat_ca, p_val_ca = stats.ttest_rel(loss_c, loss_a)
                    t_stat_ba, p_val_ba = stats.ttest_rel(loss_b, loss_a)

                    # Wilcoxon signed rank tests
                    try:
                        w_stat_cb, w_pval_cb = stats.wilcoxon(loss_c, loss_b)
                    except Exception:
                        w_stat_cb, w_pval_cb = np.nan, np.nan

                    r2_a = 1.0 - (np.mean(loss_a) / np.var(df_a["y_true_ret"].values))
                    r2_b = 1.0 - (np.mean(loss_b) / np.var(df_b["y_true_ret"].values))
                    r2_c = 1.0 - (np.mean(loss_c) / np.var(df_c["y_true_ret"].values))

                    acc_a = float(np.mean(df_a["y_true_dir"].values == df_a["y_pred_dir"].values))
                    acc_b = float(np.mean(df_b["y_true_dir"].values == df_b["y_pred_dir"].values))
                    acc_c = float(np.mean(df_c["y_true_dir"].values == df_c["y_pred_dir"].values))

                    ablation_rows.append({
                        "architecture": arch,
                        "family": fam,
                        "horizon": h,
                        "n_samples": len(df_c),
                        "r2_set_a": r2_a,
                        "r2_set_b": r2_b,
                        "r2_set_c": r2_c,
                        "delta_r2_c_minus_b": r2_c - r2_b,
                        "delta_r2_c_minus_a": r2_c - r2_a,
                        "acc_set_a": acc_a,
                        "acc_set_b": acc_b,
                        "acc_set_c": acc_c,
                        "delta_acc_c_minus_b": acc_c - acc_b,
                        "delta_acc_c_minus_a": acc_c - acc_a,
                        "mean_loss_diff_c_minus_b": float(np.mean(diff_cb)),
                        "t_stat_c_vs_b": float(t_stat_cb),
                        "p_val_c_vs_b": float(p_val_cb),
                        "wilcoxon_pval_c_vs_b": float(w_pval_cb),
                        "t_stat_c_vs_a": float(t_stat_ca),
                        "p_val_c_vs_a": float(p_val_ca),
                    })
                    break

    df_ablation = pd.DataFrame(ablation_rows)
    logger.info("Feature set ablation completed: %d architectures analyzed.", len(df_ablation))
    return df_ablation


def compute_event_window_ablation(
    pred_dir: Path,
    events_calendar_path: Path,
    top_models: List[Tuple[str, str]],  # (family, model_tag)
    phases: List[str] = ["P1", "P2", "P3", "P4", "P5"],
    horizons: List[int] = [1, 5],
    event_window_days: int = 20,
) -> pd.DataFrame:
    """Ablation Study: Compare Model Performance INSIDE vs OUTSIDE Electoral Event Windows.
    
    Evaluates whether models exhibit superior directional edge or return variance explanation
    during politically volatile event periods versus normal market regimes.
    """
    logger.info("Computing Event Window Ablation (Inside vs Outside +/- %d trading days)...", event_window_days)
    
    # 1. Load event calendar
    cal_df = pd.read_csv(events_calendar_path)
    event_dates = set(pd.to_datetime(cal_df["mapped_date"]).dt.strftime("%Y-%m-%d").unique())

    # Load baseline dates to get full trading day calendar
    ref_file = pred_dir / "baseline" / "random_walk_P1_h1.parquet"
    all_dates_list = []
    for p in phases:
        f_p = pred_dir / "baseline" / f"random_walk_{p}_h1.parquet"
        all_dates_list.extend(pd.read_parquet(f_p)["date"].tolist())
    all_dates = sorted(list(set(all_dates_list)))
        
    date_to_idx = {d: i for i, d in enumerate(all_dates)}

    # Mark trading days within event_window_days of any event date
    is_event_window = np.zeros(len(all_dates), dtype=bool)
    for ed in event_dates:
        if ed in date_to_idx:
            idx = date_to_idx[ed]
            start_idx = max(0, idx - event_window_days)
            end_idx = min(len(all_dates) - 1, idx + event_window_days)
            is_event_window[start_idx : end_idx + 1] = True

    event_date_mask = {all_dates[i]: is_event_window[i] for i in range(len(all_dates))}

    event_records = []

    for h in horizons:
        for fam, m_tag in top_models:
            fam_dir = pred_dir / fam
            if not fam_dir.exists():
                continue

            # Load across phases
            dfs = []
            for p in phases:
                # Find matching file
                candidates = list(fam_dir.glob(f"*{m_tag}*_{p}_h{h}.parquet"))
                if not candidates:
                    candidates = list(fam_dir.glob(f"{m_tag}_{p}_h{h}.parquet"))
                if candidates:
                    dfs.append((p, pd.read_parquet(candidates[0])))

            if len(dfs) < len(phases):
                continue

            # Evaluate per-phase and pooled
            for p, df_p in dfs + [("POOLED", pd.concat([d[1] for d in dfs], ignore_index=True))]:
                df_p = df_p.copy()
                df_p["in_event_window"] = df_p["date"].map(lambda d: event_date_mask.get(str(d)[:10], False))

                df_in = df_p[df_p["in_event_window"]]
                df_out = df_p[~df_p["in_event_window"]]

                n_in = len(df_in)
                n_out = len(df_out)

                if n_in < 5 or n_out < 5:
                    continue

                # In-window metrics
                e_in = df_in["y_true_ret"].values - df_in["y_pred_ret"].values
                mse_in = float(np.mean(e_in ** 2))
                var_in = float(np.var(df_in["y_true_ret"].values))
                r2_in = 1.0 - (mse_in / var_in) if var_in > 0 else 0.0
                acc_in = float(np.mean(df_in["y_true_dir"].values == df_in["y_pred_dir"].values))
                rmse_in = float(np.sqrt(mse_in))
                mae_in = float(np.mean(np.abs(e_in)))

                # Out-window metrics
                e_out = df_out["y_true_ret"].values - df_out["y_pred_ret"].values
                mse_out = float(np.mean(e_out ** 2))
                var_out = float(np.var(df_out["y_true_ret"].values))
                r2_out = 1.0 - (mse_out / var_out) if var_out > 0 else 0.0
                acc_out = float(np.mean(df_out["y_true_dir"].values == df_out["y_pred_dir"].values))
                rmse_out = float(np.sqrt(mse_out))
                mae_out = float(np.mean(np.abs(e_out)))

                # Direction test in-window
                pt_in = pesaran_timmermann(df_in["y_true_dir"].values, df_in["y_pred_dir"].values)

                event_records.append({
                    "model": m_tag,
                    "family": fam,
                    "horizon": h,
                    "phase": p,
                    "n_inside_events": n_in,
                    "n_outside_events": n_out,
                    "r2_inside": r2_in,
                    "r2_outside": r2_out,
                    "delta_r2_in_minus_out": r2_in - r2_out,
                    "acc_inside": acc_in,
                    "acc_outside": acc_out,
                    "delta_acc_in_minus_out": acc_in - acc_out,
                    "rmse_inside": rmse_in,
                    "rmse_outside": rmse_out,
                    "pt_pval_inside": pt_in["p_value"],
                })

    df_event_ablation = pd.DataFrame(event_records)
    logger.info("Event window ablation completed: %d rows generated.", len(df_event_ablation))
    return df_event_ablation


def compute_pairwise_dm_matrix(
    pred_dir: Path,
    candidate_models: List[Tuple[str, str, str]],  # (family, model_tag, label)
    phases: List[str] = ["P1", "P2", "P3", "P4", "P5"],
    horizon: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute Pairwise Diebold-Mariano Matrix with Holm-Bonferroni correction among top candidates.
    
    Identifies whether the top-ranked model is statistically indistinguishable from other top-tier models
    (Model Confidence Set approximation).
    """
    n_models = len(candidate_models)
    labels = [c[2] for c in candidate_models]
    
    # Load pooled predictions
    df_dict: Dict[str, pd.DataFrame] = {}
    for fam, m_tag, lbl in candidate_models:
        fam_dir = pred_dir / fam
        dfs = []
        for p in phases:
            candidates = list(fam_dir.glob(f"*{m_tag}*_{p}_h{horizon}.parquet"))
            if not candidates:
                candidates = list(fam_dir.glob(f"{m_tag}_{p}_h{horizon}.parquet"))
            if candidates:
                dfs.append(pd.read_parquet(candidates[0]))
        if len(dfs) == len(phases):
            pooled_df = pd.concat(dfs, ignore_index=True)
            df_dict[lbl] = pooled_df[["date", "y_true_ret", "y_pred_ret"]].copy()
        else:
            raise ValueError(f"Missing phases for {lbl} in {fam_dir}")

    stat_mat = np.zeros((n_models, n_models))
    pval_mat = np.zeros((n_models, n_models))
    raw_pvals = []
    pairs = []

    for i in range(n_models):
        for j in range(n_models):
            if i == j:
                stat_mat[i, j] = 0.0
                pval_mat[i, j] = 1.0
            else:
                m1, m2 = labels[i], labels[j]
                m_pair = pd.merge(df_dict[m1], df_dict[m2], on="date", suffixes=("_1", "_2"), how="inner")
                e1 = m_pair["y_true_ret_1"].values - m_pair["y_pred_ret_1"].values
                e2 = m_pair["y_true_ret_2"].values - m_pair["y_pred_ret_2"].values
                dm_res = diebold_mariano(e1, e2, h=horizon)
                stat_mat[i, j] = dm_res["dm_hln_stat"]
                pval_mat[i, j] = dm_res["p_value"]
                if i < j:
                    raw_pvals.append(dm_res["p_value"])
                    pairs.append((i, j))

    # Apply Holm correction to upper triangle pairs
    adj_pvals = holm_bonferroni_correction(np.array(raw_pvals))
    adj_pval_mat = np.copy(pval_mat)
    for idx, (i, j) in enumerate(pairs):
        adj_pval_mat[i, j] = adj_pvals[idx]
        adj_pval_mat[j, i] = adj_pvals[idx]

    df_stat = pd.DataFrame(stat_mat, index=labels, columns=labels)
    df_adj_pval = pd.DataFrame(adj_pval_mat, index=labels, columns=labels)
    
    return df_stat, df_adj_pval


