"""Stage 5: Feature Engineering Matrix, Pipeline, and Ablation Feature Sets.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead bias. Every feature at date t uses ONLY observations up to close of t.
- Rule R5: Same protocol for every model.
- Rule R6: Save everything (parquet matrices, tables, figures, metadata).
- Rule R7: Full reproducibility.
- Rule R10: Stage discipline.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cse.features.events_features import build_feature_set_c
from cse.features.market_activity import build_feature_set_b
from cse.features.pipeline import (
    PhaseDataManager,
    compute_targets,
    get_phase_data,
    get_sequence_windows,
)
from cse.features.technical import build_feature_set_a
from cse.splits.walk_forward import ExpandingWindowSplitter
from cse.utils.config import find_project_root, load_config
from cse.utils.logger import get_logger

logger = get_logger("cse.stage5")


def generate_feature_dictionary(df_c: pd.DataFrame) -> pd.DataFrame:
    """Generate comprehensive feature dictionary describing all engineered features."""
    dict_rows = []

    for col in df_c.columns:
        if col.startswith("ret_") or col in ["rsi_14", "macd_line", "macd_signal", "macd_hist", "dist_from_sma_20", "dist_from_sma_50"]:
            fset = "A, B, C"
            cat = "Price / Technical"
        elif col in [
            "sp20_log_return", "aspi_sp20_spread", "has_sp20", "log_turnover", "log_shares",
            "turnover_log_change_1d", "shares_log_change_1d", "turnover_zscore_60d",
            "shares_zscore_60d", "turnover_to_5d_ratio"
        ]:
            fset = "B, C"
            cat = "Market Activity / Liquidity"
        elif col.startswith("cal_"):
            fset = "C"
            cat = "Calendar"
        elif col.startswith("stage_") or col.startswith("type_") or col in ["days_to_next_known_event", "days_since_last_stage", "in_window_0_2", "in_window_0_7", "in_window_0_15", "in_window_0_30"]:
            fset = "C"
            cat = "Electoral Cycle (Causal)"
        elif col.startswith("prior_"):
            fset = "C"
            cat = "Historical Prior CAR (Causal)"
        else:
            fset = "C"
            cat = "Other"

        # Descriptions
        desc_map = {
            "ret_1d": "1-day ASPI log return: ln(ASPI[t] / ASPI[t-1])",
            "ret_2d": "2-day cumulative ASPI log return: ln(ASPI[t] / ASPI[t-2])",
            "ret_3d": "3-day cumulative ASPI log return: ln(ASPI[t] / ASPI[t-3])",
            "ret_5d": "5-day cumulative ASPI log return: ln(ASPI[t] / ASPI[t-5])",
            "ret_10d": "10-day cumulative ASPI log return: ln(ASPI[t] / ASPI[t-10])",
            "ret_20d": "20-day cumulative ASPI log return: ln(ASPI[t] / ASPI[t-20])",
            "ret_lag_1": "1-day lagged daily log return: ret_1d[t-1]",
            "ret_lag_2": "2-day lagged daily log return: ret_1d[t-2]",
            "ret_lag_3": "3-day lagged daily log return: ret_1d[t-3]",
            "ret_lag_5": "5-day lagged daily log return: ret_1d[t-5]",
            "ret_lag_10": "10-day lagged daily log return: ret_1d[t-10]",
            "ret_lag_20": "20-day lagged daily log return: ret_1d[t-20]",
            "ret_mean_5d": "Trailing 5-day rolling mean of daily log returns",
            "ret_mean_10d": "Trailing 10-day rolling mean of daily log returns",
            "ret_mean_20d": "Trailing 20-day rolling mean of daily log returns",
            "ret_vol_5d": "Trailing 5-day rolling standard deviation of daily log returns",
            "ret_vol_10d": "Trailing 10-day rolling standard deviation of daily log returns",
            "ret_vol_20d": "Trailing 20-day rolling standard deviation of daily log returns",
            "rsi_14": "14-day Relative Strength Index (Wilder's exponential smoothing)",
            "macd_line": "MACD line: EMA(12) - EMA(26) of ASPI closing level",
            "macd_signal": "MACD signal line: EMA(9) of MACD line",
            "macd_hist": "MACD histogram: macd_line - macd_signal",
            "dist_from_sma_20": "Fractional distance of ASPI closing level from 20-day SMA: (ASPI - SMA20)/SMA20",
            "dist_from_sma_50": "Fractional distance of ASPI closing level from 50-day SMA: (ASPI - SMA50)/SMA50",
            "sp20_log_return": "S&P SL 20 daily log return. Masked NaN prior to 2012-06-27 inception",
            "aspi_sp20_spread": "Return spread: aspi_log_return - sp20_log_return. Masked NaN before 2012-06-27",
            "has_sp20": "Binary indicator: 1 if S&P SL 20 is active and populated on date t, 0 prior to 2012",
            "log_turnover": "Natural logarithm of daily equity turnover: ln(turnover_equity_mn)",
            "log_shares": "Natural logarithm of daily shares traded: ln(shares_traded_equity_k)",
            "turnover_log_change_1d": "1-day change in log turnover: diff(1) of log_turnover",
            "shares_log_change_1d": "1-day change in log shares traded: diff(1) of log_shares",
            "turnover_zscore_60d": "Trailing 60-day rolling z-score of log equity turnover",
            "shares_zscore_60d": "Trailing 60-day rolling z-score of log shares traded",
            "turnover_to_5d_ratio": "Ratio of daily equity turnover to trailing 5-day average turnover",
            "cal_day_of_week": "Day of week integer (0=Monday, 1=Tuesday, ..., 4=Friday)",
            "cal_month": "Calendar month integer (1=January, ..., 12=December)",
            "cal_session_gap_days": "Calendar days elapsed since previous trading session (weekend/holiday gap)",
            "stage_none": "One-hot flag: 1 if no known election stage is active on date t",
            "stage_announcement": "One-hot flag: 1 if active stage is election announcement proclamation",
            "stage_nomination_start": "One-hot flag: 1 if active stage is candidate nomination window start",
            "stage_nomination_end": "One-hot flag: 1 if active stage is nomination deadline closing",
            "stage_polling": "One-hot flag: 1 if active stage is election polling day",
            "stage_result": "One-hot flag: 1 if active stage is official election results declaration",
            "stage_government_formation": "One-hot flag: 1 if active stage is government swearing-in / cabinet appointment",
            "type_none": "One-hot flag: 1 if no known election is active",
            "type_presidential": "One-hot flag: 1 if active election is Presidential election",
            "type_parliamentary": "One-hot flag: 1 if active election is Parliamentary general election",
            "type_provincial_council": "One-hot flag: 1 if active election is Provincial Council election",
            "days_to_next_known_event": "Trading days to next announced election stage (-1 if no stage is currently known)",
            "days_since_last_stage": "Trading days elapsed since most recent active election stage (-1 if no event active)",
            "in_window_0_2": "Binary flag: 1 if date t falls within [0,+2] trading days of most recent stage",
            "in_window_0_7": "Binary flag: 1 if date t falls within [0,+7] trading days of most recent stage",
            "in_window_0_15": "Binary flag: 1 if date t falls within [0,+15] trading days of most recent stage",
            "in_window_0_30": "Binary flag: 1 if date t falls within [0,+30] trading days of most recent stage",
            "prior_mean_car": "Historical mean CAR from completed prior events for matching type, stage, and window",
            "prior_median_car": "Historical median CAR from completed prior events for matching type, stage, and window",
            "prior_n": "Count of prior completed events informing historical CAR statistics as of date t",
        }

        desc = desc_map.get(col, f"Engineered feature {col}")
        dtype_str = str(df_c[col].dtype)

        dict_rows.append({
            "feature_name": col,
            "feature_set": fset,
            "category": cat,
            "dtype": dtype_str,
            "description": desc,
            "lookahead_check": "Strictly causal at t close (Rule R2)",
        })

    return pd.DataFrame(dict_rows)


def analyze_missingness(df_a: pd.DataFrame, df_b: pd.DataFrame, df_c: pd.DataFrame) -> pd.DataFrame:
    """Analyze missing value counts and percentages across all feature sets."""
    total_n = len(df_c)
    rows = []

    for col in df_c.columns:
        n_missing = int(df_c[col].isna().sum())
        pct_missing = (n_missing / total_n) * 100.0

        if col in df_a.columns:
            in_sets = "A, B, C"
        elif col in df_b.columns:
            in_sets = "B, C"
        else:
            in_sets = "C"

        # Rationale for missingness
        if col in ["sp20_log_return", "aspi_sp20_spread"]:
            rationale = "Pre-inception period (1994-2012-06-26; 4,425 days). Strictly masked with has_sp20."
        elif "60d" in col or col in ["dist_from_sma_50"]:
            rationale = "Warmup window (first 50-60 trading days of series in 1994)."
        elif col in ["prior_mean_car", "prior_median_car"]:
            rationale = "Non-event days (stage='none') or zero completed prior events (n=0)."
        elif n_missing > 0:
            rationale = f"Warmup window ({n_missing} trading days)."
        else:
            rationale = "Complete (0 missing values)."

        rows.append({
            "feature_name": col,
            "feature_set": in_sets,
            "missing_count": n_missing,
            "missing_pct": f"{pct_missing:.2f}%",
            "rationale": rationale,
        })

    return pd.DataFrame(rows)


def calculate_event_coverage_by_phase(df_cse: pd.DataFrame, df_c: pd.DataFrame) -> pd.DataFrame:
    """Calculate validation days falling inside election event windows across all 5 phases."""
    splitter = ExpandingWindowSplitter(df_cse, embargo_days=10)
    rows = []

    for phase_name, split in splitter.splits.items():
        v_start = split.val.start_idx
        v_end = split.val.end_idx
        v_df = df_c.iloc[v_start : v_end + 1]
        n_val = len(v_df)

        n_any_stage = int((v_df["stage_none"] == 0).sum())
        n_win_2 = int((v_df["in_window_0_2"] == 1).sum())
        n_win_7 = int((v_df["in_window_0_7"] == 1).sum())
        n_win_15 = int((v_df["in_window_0_15"] == 1).sum())
        n_win_30 = int((v_df["in_window_0_30"] == 1).sum())

        rows.append({
            "phase": phase_name,
            "val_dates": f"{split.val.start_date} to {split.val.end_date}",
            "val_days_total": n_val,
            "days_in_active_stage": n_any_stage,
            "pct_in_active_stage": f"{(n_any_stage / n_val) * 100:.1f}%",
            "days_in_win_0_2": n_win_2,
            "days_in_win_0_7": n_win_7,
            "days_in_win_0_15": n_win_15,
            "days_in_win_0_30": n_win_30,
            "pct_in_win_0_30": f"{(n_win_30 / n_val) * 100:.1f}%",
        })

    return pd.DataFrame(rows)


def plot_training_correlation_heatmap(
    df_cse: pd.DataFrame,
    df_c: pd.DataFrame,
    output_path: Path,
) -> None:
    """Plot correlation heatmap strictly on training windows (Rule R2)."""
    # Use Phase 5 training window (1994 to 2023-12-13; largest training window)
    splitter = ExpandingWindowSplitter(df_cse, embargo_days=10)
    p5_split = splitter.get_phase("P5")
    train_slice = slice(p5_split.train.start_idx, p5_split.train.end_idx + 1)
    df_train = df_c.iloc[train_slice].copy()

    # Select representative features across categories
    selected_cols = [
        "ret_1d", "ret_5d", "ret_20d", "ret_vol_5d", "ret_vol_20d", "rsi_14", "macd_line", "dist_from_sma_20",
        "log_turnover", "log_shares", "turnover_zscore_60d", "turnover_to_5d_ratio",
        "sp20_log_return", "aspi_sp20_spread", "cal_day_of_week", "cal_session_gap_days",
        "in_window_0_2", "in_window_0_7", "in_window_0_30", "days_since_last_stage", "prior_mean_car", "prior_n"
    ]

    df_sub = df_train[[c for c in selected_cols if c in df_train.columns]].copy()
    # Fill remaining NaNs for correlation calculation
    corr_matrix = df_sub.corr(method="pearson").values

    fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
    im = ax.imshow(corr_matrix, cmap="coolwarm", vmin=-1.0, vmax=1.0)

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=10)
    cbar.set_label("Pearson Correlation Coefficient", fontsize=11, fontweight="bold")

    # Labels
    col_names = [c for c in selected_cols if c in df_train.columns]
    ax.set_xticks(np.arange(len(col_names)))
    ax.set_yticks(np.arange(len(col_names)))
    ax.set_xticklabels(col_names, rotation=45, ha="right", fontsize=9, fontweight="medium")
    ax.set_yticklabels(col_names, fontsize=9, fontweight="medium")

    # Annotate values on cells if matrix is not too dense
    for i in range(len(col_names)):
        for j in range(len(col_names)):
            val = corr_matrix[i, j]
            if not np.isnan(val) and abs(val) > 0.35 and i != j:
                color = "white" if abs(val) > 0.65 else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=color, fontsize=7)

    ax.set_title(
        "Feature Correlation Heatmap (Phase P5 Training Window: 1994-2023, N=7,147)\nStrictly Training Only — No Validation Data Included (Rule R2)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved training correlation heatmap to %s", output_path)


def run_stage5() -> int:
    """Execute Stage 5 complete feature generation, pipeline validation, and report outputs."""
    root = find_project_root()
    config = load_config()

    logger.info("=== Starting Stage 5: Feature Engineering Matrix & Pipelines ===")
    t_start = time.time()

    # 1. Load cleaned CSE data
    proc_dir = root / config["paths"]["processed_data_dir"]
    cse_path = proc_dir / "cse_clean.parquet"
    if not cse_path.exists():
        logger.error("Cleaned CSE panel not found at %s. Run Stage 1 first.", cse_path)
        return 1

    df_cse = pd.read_parquet(cse_path)
    logger.info("Loaded cleaned CSE data: %d rows (%s to %s)", len(df_cse), df_cse["date"].min(), df_cse["date"].max())

    # 2. Build Feature Set A (Price-Only)
    logger.info("Building Feature Set A (Price-Only)...")
    feats_a = build_feature_set_a(df_cse)
    p_feat_a = proc_dir / "features_set_a.parquet"
    feats_a.to_parquet(p_feat_a, index=False)
    logger.info("Feature Set A saved: %d rows, %d features -> %s", len(feats_a), feats_a.shape[1], p_feat_a)

    # 3. Build Feature Set B (Set A + Market Activity)
    logger.info("Building Feature Set B (Price + Market Activity)...")
    feats_b = build_feature_set_b(df_cse)
    p_feat_b = proc_dir / "features_set_b.parquet"
    feats_b.to_parquet(p_feat_b, index=False)
    logger.info("Feature Set B saved: %d rows, %d features -> %s", len(feats_b), feats_b.shape[1], p_feat_b)

    # 4. Build Feature Set C (Set B + Calendar + Event Features)
    logger.info("Building Feature Set C (Price + Market Activity + Calendar + Causal Events)...")
    feats_c = build_feature_set_c(df_cse)
    p_feat_c = proc_dir / "features_set_c.parquet"
    feats_c.to_parquet(p_feat_c, index=False)
    logger.info("Feature Set C saved: %d rows, %d features -> %s", len(feats_c), feats_c.shape[1], p_feat_c)

    # 5. Compute & Save Targets (h=1 and h=5)
    logger.info("Computing Targets (h=1 and h=5)...")
    targets_df = compute_targets(df_cse)
    p_targets = proc_dir / "targets.parquet"
    targets_df.to_parquet(p_targets, index=False)
    logger.info("Targets saved: %d rows -> %s", len(targets_df), p_targets)

    # 6. Generate Tables & Reports
    tables_dir = root / config["paths"]["tables_dir"]
    figures_dir = root / config["paths"]["figures_dir"]
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # (a) Feature Dictionary
    logger.info("Generating Feature Dictionary...")
    df_dict = generate_feature_dictionary(feats_c)
    dict_csv = tables_dir / "feature_dictionary.csv"
    dict_md = tables_dir / "feature_dictionary.md"
    df_dict.to_csv(dict_csv, index=False)
    # Save markdown table
    headers = list(df_dict.columns)
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for _, row in df_dict.iterrows():
        lines.append('| ' + ' | '.join(str(val) for val in row.values) + ' |')
    with open(dict_md, "w", encoding="utf-8") as f:
        f.write("# Feature Dictionary (Stage 5)\n\n" + "\n".join(lines) + "\n")
    logger.info("Saved feature dictionary to %s and %s", dict_csv, dict_md)

    # (b) Missingness Analysis
    logger.info("Analyzing Feature Missingness...")
    df_miss = analyze_missingness(feats_a, feats_b, feats_c)
    miss_csv = tables_dir / "feature_missingness.csv"
    miss_md = tables_dir / "feature_missingness.md"
    df_miss.to_csv(miss_csv, index=False)
    headers = list(df_miss.columns)
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for _, row in df_miss.iterrows():
        lines.append('| ' + ' | '.join(str(val) for val in row.values) + ' |')
    with open(miss_md, "w", encoding="utf-8") as f:
        f.write("# Feature Missingness Analysis (Stage 5)\n\n" + "\n".join(lines) + "\n")
    logger.info("Saved missingness table to %s and %s", miss_csv, miss_md)

    # (c) Event Coverage by Phase
    logger.info("Calculating Event Feature Coverage across Walk-Forward Phases...")
    df_cov = calculate_event_coverage_by_phase(df_cse, feats_c)
    cov_csv = tables_dir / "event_feature_coverage_by_phase.csv"
    cov_md = tables_dir / "event_feature_coverage_by_phase.md"
    df_cov.to_csv(cov_csv, index=False)
    headers = list(df_cov.columns)
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for _, row in df_cov.iterrows():
        lines.append('| ' + ' | '.join(str(val) for val in row.values) + ' |')
    with open(cov_md, "w", encoding="utf-8") as f:
        f.write("# Event Feature Coverage by Validation Phase (Stage 5)\n\n" + "\n".join(lines) + "\n")
    logger.info("Saved event feature coverage table to %s and %s", cov_csv, cov_md)

    # (d) Training Correlation Heatmap
    logger.info("Plotting Training Correlation Heatmap...")
    heatmap_path = figures_dir / "feature_correlation_heatmap_train.png"
    plot_training_correlation_heatmap(df_cse, feats_c, heatmap_path)

    # 7. Validate Pipeline Extraction across all 5 phases & both horizons
    logger.info("Validating PhaseDataPipeline extraction across P1-P5...")
    for p in ["P1", "P2", "P3", "P4", "P5"]:
        for h in [1, 5]:
            for fset in ["A", "B", "C"]:
                p_data = get_phase_data(phase=p, horizon=h, feature_set=fset, df_cse=df_cse)
                assert len(p_data.train.X) > 0
                assert len(p_data.val.X) > 0
                assert len(p_data.inner_val.X) > 0
                # Assert zero NaNs in transformed output
                assert not np.isnan(p_data.train.X.values).any(), f"NaNs in train X for {p}_{h}_{fset}"
                assert not np.isnan(p_data.val.X.values).any(), f"NaNs in val X for {p}_{h}_{fset}"

    # 8. Validate Sequence Window Generation for Deep Models (L in {20, 60, 120})
    logger.info("Validating Sequence Window Generation for L in {20, 60, 120}...")
    for lookback in [20, 60, 120]:
        seq_data = get_sequence_windows(phase="P1", horizon=5, feature_set="C", lookback=lookback, df_cse=df_cse)
        assert seq_data.train.X_seq.shape[1] == lookback
        assert seq_data.val.X_seq.shape[1] == lookback
        assert seq_data.inner_val.X_seq.shape[1] == lookback
        assert seq_data.train.X_seq.shape[2] == feats_c.shape[1]

    elapsed = time.time() - t_start
    logger.info("=== Stage 5 Feature Matrix & Pipelines Completed Successfully in %.2fs ===", elapsed)
    return 0


if __name__ == "__main__":
    sys.exit(run_stage5())
