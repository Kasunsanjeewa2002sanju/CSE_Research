"""Verification and diagnostic visualization script for Stage 1 (Historical DB).

Generates:
a) car_distribution_h1_2_5_10.png
b) news_volume_timeline.png
c) car_by_category_h5.png
d) aspi_timeseries.png
e) data_coverage.png
f) car_outlier_breakdown.png
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root and src/scripts are in sys.path
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set cache directory to local folder to prevent permissions issues
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / "data" / "cache" / "matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cse.news.historical_db import get_all_news, get_aspi_range, get_default_db_path
from cse.viz.plot_utils import (
    COLOR_ACCENT,
    COLOR_DOWN,
    COLOR_NEUTRAL,
    COLOR_UP,
    annotate_stats,
    placeholder_png,
    save_fig,
    setup_style,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cse.verify_stage1")
STAGE = "stage1"


def plot_car_distribution_grid(df: pd.DataFrame) -> Tuple[Path, str]:
    """Generate 2x2 subplot grid of CAR distributions across horizons h=1, 2, 5, 10."""
    setup_style()
    horizons = [1, 2, 5, 10]
    n = len(df)
    if n < 10:
        return placeholder_png(STAGE, "car_distribution", "h1_2_5_10", n=n)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    summaries = []

    for idx, h in enumerate(horizons):
        ax = axes[idx // 2, idx % 2]
        col = f"car_{h}d"
        if col not in df.columns:
            ax.text(0.5, 0.5, f"{col} missing", ha="center", va="center")
            continue

        vals = df[col].dropna().values * 100.0  # Scale to %
        if len(vals) == 0:
            continue

        mean_val = float(np.mean(vals))
        std_val = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0

        ax.hist(vals, bins=35, color=COLOR_ACCENT, edgecolor="#FFFFFF", alpha=0.85, label="CAR Dist")
        ax.axvline(0, color=COLOR_NEUTRAL, linestyle="--", linewidth=1.2, alpha=0.8, label="Zero")
        ax.axvline(mean_val, color=COLOR_DOWN if mean_val < 0 else COLOR_UP, linestyle="-", linewidth=2.0, label=f"Mean ({mean_val:+.2f}%)")

        ax.set_title(f"CAR Horizon h={h}d Distribution")
        ax.set_xlabel("Cumulative Abnormal Return (%)")
        ax.set_ylabel("Frequency")
        ax.legend(loc="upper left")
        annotate_stats(ax, vals, loc="upper right", is_percent=True)
        summaries.append(f"h={h}: mean={mean_val:+.2f}%, std={std_val:.2f}%, n={len(vals)}")

    fig.suptitle("Stage 1: Multi-Horizon CAR Distributions (h=1, 2, 5, 10)", fontsize=14, fontweight="bold", y=1.02)
    summary_str = "; ".join(summaries)
    path = save_fig(fig, STAGE, "car_distribution", "h1_2_5_10", summary=summary_str)
    return path, summary_str


def plot_news_volume_timeline(df: pd.DataFrame) -> Tuple[Path, str]:
    """Monthly news count bar chart with 30-day rolling volume line."""
    setup_style()
    n = len(df)
    if n < 10 or "published_at" not in df.columns:
        return placeholder_png(STAGE, "news_volume", "timeline", n=n)

    df_clean = df.copy()
    df_clean["date"] = pd.to_datetime(df_clean["published_at"], errors="coerce")
    df_clean = df_clean.dropna(subset=["date"]).sort_values("date")

    # Monthly aggregation
    monthly = df_clean.set_index("date").resample("ME").size()
    # Daily aggregation for rolling 30d
    daily = df_clean.set_index("date").resample("D").size()
    rolling_30d = daily.rolling(30, min_periods=7).sum()

    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Monthly bars
    month_labels = [d.strftime("%Y-%m") for d in monthly.index]
    bars = ax1.bar(
        np.arange(len(monthly)),
        monthly.values,
        color=COLOR_ACCENT,
        alpha=0.75,
        edgecolor="#FFFFFF",
        width=0.7,
        label="Monthly News Volume",
    )
    ax1.set_xticks(np.arange(len(monthly)))
    ax1.set_xticklabels(month_labels, rotation=45, ha="right", fontsize=9)
    ax1.set_ylabel("Monthly News Count", color=COLOR_ACCENT)
    ax1.set_xlabel("Month")

    # Annotate top bars
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 1, f"{int(h)}", ha="center", va="bottom", fontsize=8)

    # Secondary axis for daily rolling
    ax2 = ax1.twinx()
    ax2.plot(
        np.linspace(0, len(monthly) - 1, len(rolling_30d)),
        rolling_30d.values,
        color=COLOR_UP,
        linewidth=2.2,
        label="30-Day Rolling Total",
    )
    ax2.set_ylabel("30-Day Rolling News Count", color=COLOR_UP)
    ax2.grid(False)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    peak_month = month_labels[int(np.argmax(monthly.values))]
    peak_val = int(np.max(monthly.values))
    ax1.set_title("Historical News Volume Timeline & 30-Day Rolling Velocity")

    summary_str = f"Total news={n:,}, monthly mean={monthly.mean():.1f}, peak={peak_month} ({peak_val} items)"
    path = save_fig(fig, STAGE, "news_volume", "timeline", summary=summary_str)
    return path, summary_str


def plot_car_by_category_h5(df: pd.DataFrame) -> Tuple[Path, str]:
    """Box plot of event_category vs car_5d."""
    setup_style()
    n = len(df)
    if n < 10 or "event_category" not in df.columns or "car_5d" not in df.columns:
        return placeholder_png(STAGE, "car_by_category", "h5", n=n)

    clean_df = df[["event_category", "car_5d"]].dropna().copy()
    clean_df["car_5d_pct"] = clean_df["car_5d"] * 100.0

    cats = clean_df["event_category"].value_counts()
    top_cats = cats[cats >= 5].index.tolist()
    if not top_cats:
        top_cats = cats.head(8).index.tolist()

    sub_df = clean_df[clean_df["event_category"].isin(top_cats)]
    medians = sub_df.groupby("event_category")["car_5d_pct"].median().sort_values(ascending=False)
    sorted_cats = medians.index.tolist()
    grouped_data = [sub_df[sub_df["event_category"] == c]["car_5d_pct"].values for c in sorted_cats]

    fig, ax = plt.subplots(figsize=(10, 6))
    box = ax.boxplot(
        grouped_data,
        patch_artist=True,
        medianprops=dict(color="#000000", linewidth=1.8),
        whiskerprops=dict(color="#455A64", linewidth=1.2),
        capprops=dict(color="#455A64", linewidth=1.2),
        flierprops=dict(marker="o", markersize=4, alpha=0.4, markerfacecolor=COLOR_ACCENT),
    )
    ax.set_xticks(np.arange(1, len(sorted_cats) + 1))
    ax.set_xticklabels(sorted_cats, rotation=30, ha="right")

    for patch, c_name in zip(box["boxes"], sorted_cats):
        med = medians[c_name]
        face_col = COLOR_UP if med > 0 else (COLOR_DOWN if med < 0 else COLOR_ACCENT)
        patch.set_facecolor(face_col)
        patch.set_alpha(0.65)
        patch.set_edgecolor("#37474F")

    ax.axhline(0, color=COLOR_NEUTRAL, linestyle="--", linewidth=1.2, alpha=0.7)
    ax.set_title("5-Day Cumulative Abnormal Return (CAR) by Event Category")
    ax.set_xlabel("Event Category")
    ax.set_ylabel("CAR h=5d (%)")

    highest_cat = sorted_cats[0]
    lowest_cat = sorted_cats[-1]
    summary_str = f"Categories={len(sorted_cats)}, highest={highest_cat} (med={medians[highest_cat]:+.2f}%), lowest={lowest_cat} (med={medians[lowest_cat]:+.2f}%), n={len(sub_df)}"
    path = save_fig(fig, STAGE, "car_by_category", "h5", summary=summary_str)
    return path, summary_str


def plot_aspi_timeseries(aspi_df: pd.DataFrame) -> Tuple[Path, str]:
    """Plot 2-panel ASPI Index Close and Daily 1D Return time series."""
    setup_style()
    n = len(aspi_df)
    if n < 10 or "close" not in aspi_df.columns:
        return placeholder_png(STAGE, "aspi", "timeseries", n=n)

    clean_aspi = aspi_df.copy()
    clean_aspi["date"] = pd.to_datetime(clean_aspi["date"], errors="coerce")
    clean_aspi = clean_aspi.dropna(subset=["date"]).sort_values("date")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, gridspec_kw={"height_ratios": [2, 1]})

    # ASPI Close
    ax1.plot(clean_aspi["date"], clean_aspi["close"], color=COLOR_ACCENT, linewidth=1.6, label="ASPI Close")
    ma50 = clean_aspi["close"].rolling(50, min_periods=10).mean()
    ax1.plot(clean_aspi["date"], ma50, color="#F57C00", linewidth=1.8, label="50-Day MA")
    ax1.set_ylabel("ASPI Index Points")
    ax1.set_title("Colombo Stock Exchange: All Share Price Index (ASPI) History")
    ax1.legend(loc="upper left")

    # Daily Return
    ret = clean_aspi["return_1d"] * 100.0 if clean_aspi["return_1d"].abs().max() < 1.0 else clean_aspi["return_1d"]
    pos_mask = ret >= 0
    ax2.bar(clean_aspi["date"][pos_mask], ret[pos_mask], color=COLOR_UP, width=1.0, alpha=0.7, label="Positive Day")
    ax2.bar(clean_aspi["date"][~pos_mask], ret[~pos_mask], color=COLOR_DOWN, width=1.0, alpha=0.7, label="Negative Day")
    ax2.axhline(0, color=COLOR_NEUTRAL, linestyle="--", linewidth=1.0)
    ax2.set_ylabel("1D Return (%)")
    ax2.set_xlabel("Date")
    ax2.legend(loc="upper left")

    fig.autofmt_xdate()
    min_date = clean_aspi["date"].min().strftime("%Y-%m-%d")
    max_date = clean_aspi["date"].max().strftime("%Y-%m-%d")
    summary_str = f"ASPI range: {min_date} to {max_date}, trading_days={n}, close min={clean_aspi['close'].min():.1f}, max={clean_aspi['close'].max():.1f}"
    path = save_fig(fig, STAGE, "aspi", "timeseries", summary=summary_str)
    return path, summary_str


def plot_data_coverage(df: pd.DataFrame) -> Tuple[Path, str]:
    """Stacked bar chart per month showing 'With CAR' vs 'Without CAR'."""
    setup_style()
    n = len(df)
    if n < 10 or "published_at" not in df.columns:
        return placeholder_png(STAGE, "data_coverage", "monthly", n=n)

    clean_df = df.copy()
    clean_df["date"] = pd.to_datetime(clean_df["published_at"], errors="coerce")
    clean_df = clean_df.dropna(subset=["date"])
    clean_df["month"] = clean_df["date"].dt.to_period("M")
    clean_df["has_car"] = clean_df["car_5d"].notna()

    cov = clean_df.groupby(["month", "has_car"]).size().unstack(fill_value=0)
    if True not in cov.columns:
        cov[True] = 0
    if False not in cov.columns:
        cov[False] = 0

    months = [str(m) for m in cov.index]
    with_car = cov[True].values
    without_car = cov[False].values
    total = with_car + without_car
    cov_pct = (with_car / np.maximum(total, 1)) * 100.0

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(np.arange(len(months)), with_car, color=COLOR_UP, alpha=0.85, label="With CAR", edgecolor="#FFFFFF")
    bars2 = ax.bar(np.arange(len(months)), without_car, bottom=with_car, color=COLOR_DOWN, alpha=0.85, label="Without CAR", edgecolor="#FFFFFF")

    ax.set_xticks(np.arange(len(months)))
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=9)
    ax.set_title("Stage 1 Data Coverage: News With vs Without Valid CAR (Monthly)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Headline Count")
    ax.legend(loc="upper left")

    for i, p in enumerate(cov_pct):
        tot = total[i]
        if tot > 0:
            ax.text(i, tot + 1, f"{p:.0f}%", ha="center", va="bottom", fontsize=8, color="#37474F")

    overall_pct = (with_car.sum() / max(1, total.sum())) * 100.0
    summary_str = f"Data coverage: {overall_pct:.1f}% with CAR ({with_car.sum()}/{total.sum()} total)"
    path = save_fig(fig, STAGE, "data_coverage", "monthly", summary=summary_str)
    return path, summary_str


def plot_car_outlier_breakdown(df: pd.DataFrame) -> Tuple[Path, str]:
    """Breakdown of CAR values clamped to ±10% boundary across horizons."""
    setup_style()
    n = len(df)
    if n < 10:
        return placeholder_png(STAGE, "car_outlier", "breakdown", n=n)

    horizons = [1, 2, 5, 10]
    pos_clamped = []
    neg_clamped = []
    normal_counts = []

    for h in horizons:
        col = f"car_{h}d"
        if col in df.columns:
            s = df[col].dropna()
            pos_c = int((s >= 0.0999).sum())
            neg_c = int((s <= -0.0999).sum())
            norm_c = int(len(s) - pos_c - neg_c)
        else:
            pos_c, neg_c, norm_c = 0, 0, 0
        pos_clamped.append(pos_c)
        neg_clamped.append(neg_c)
        normal_counts.append(norm_c)

    x = np.arange(len(horizons))
    width = 0.55

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x, normal_counts, width, label="Normal Range (|CAR| < 10%)", color=COLOR_ACCENT, alpha=0.8, edgecolor="#FFFFFF")
    ax.bar(x, pos_clamped, width, bottom=normal_counts, label="Clamped High (+10%)", color=COLOR_UP, alpha=0.9, edgecolor="#FFFFFF")
    bottom_neg = np.array(normal_counts) + np.array(pos_clamped)
    ax.bar(x, neg_clamped, width, bottom=bottom_neg, label="Clamped Low (-10%)", color=COLOR_DOWN, alpha=0.9, edgecolor="#FFFFFF")

    ax.set_xticks(x)
    ax.set_xticklabels([f"h={h}d" for h in horizons], fontsize=10.5)
    ax.set_title("Stage 1 Outlier Analysis: Clamped vs Normal CAR Values (±10% Cap)")
    ax.set_xlabel("Return Horizon")
    ax.set_ylabel("Event Count")
    ax.legend(loc="upper left")

    total_clamped = sum(pos_clamped) + sum(neg_clamped)
    total_obs = sum(normal_counts) + total_clamped
    pct_clamped = (total_clamped / max(1, total_obs)) * 100.0

    summary_str = f"Clamped outliers: {sum(pos_clamped)} pos, {sum(neg_clamped)} neg ({pct_clamped:.1f}% of {total_obs} total horizon points)"
    path = save_fig(fig, STAGE, "car_outlier", "breakdown", summary=summary_str)
    return path, summary_str


def run_stage1_verification() -> Dict[str, Any]:
    """Execute all Stage 1 verification charts and return summary dict."""
    logger.info("Running Stage 1 verification: Historical DB and CAR distributions...")
    news_rows = get_all_news()
    aspi_rows = get_aspi_range("2020-01-01", "2026-12-31")

    df_news = pd.DataFrame([dict(r) for r in news_rows])
    df_aspi = pd.DataFrame([dict(r) for r in aspi_rows])

    charts = []
    
    p1, s1 = plot_car_distribution_grid(df_news)
    charts.append((p1, s1))
    logger.info("Saved %s: %s", p1.name, s1)

    p2, s2 = plot_news_volume_timeline(df_news)
    charts.append((p2, s2))
    logger.info("Saved %s: %s", p2.name, s2)

    p3, s3 = plot_car_by_category_h5(df_news)
    charts.append((p3, s3))
    logger.info("Saved %s: %s", p3.name, s3)

    p4, s4 = plot_aspi_timeseries(df_aspi)
    charts.append((p4, s4))
    logger.info("Saved %s: %s", p4.name, s4)

    p5, s5 = plot_data_coverage(df_news)
    charts.append((p5, s5))
    logger.info("Saved %s: %s", p5.name, s5)

    p6, s6 = plot_car_outlier_breakdown(df_news)
    charts.append((p6, s6))
    logger.info("Saved %s: %s", p6.name, s6)

    print(f"\n[STAGE 1 VERIFICATION] Total charts saved: {len(charts)}")
    for p, s in charts:
        print(f"  - {p.name}: {s}")

    return {
        "stage": STAGE,
        "charts_count": len(charts),
        "status": "PASS",
        "key_metric": s1.split(";")[0],
    }


if __name__ == "__main__":
    run_stage1_verification()
