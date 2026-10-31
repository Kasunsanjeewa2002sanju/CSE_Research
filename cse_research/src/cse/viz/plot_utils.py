"""Plotting utilities and standardized styling for CSE verification diagnostics."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# Set cache directory to prevent permission issues on Windows
_DATA_CACHE = Path(__file__).resolve().parents[3] / "data" / "cache" / "matplotlib"
_DATA_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_DATA_CACHE))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cse.utils.config import find_project_root

logger = logging.getLogger("cse.viz.plot_utils")

# Standardized Color Palette
COLOR_UP = "#2E7D32"        # Green (Positive / Up)
COLOR_DOWN = "#C62828"      # Red (Negative / Down)
COLOR_NEUTRAL = "#616161"   # Neutral Gray
COLOR_ACCENT = "#1565C0"    # Primary Blue Accent
COLOR_LIGHT_BG = "#F8F9FA"

PALETTE = [
    COLOR_ACCENT,
    COLOR_UP,
    COLOR_DOWN,
    "#F57C00",  # Orange
    "#7B1FA2",  # Purple
    "#00838F",  # Teal
    COLOR_NEUTRAL,
    "#C2185B",  # Pink
    "#5D4037",  # Brown
    "#455A64",  # Blue-grey
]


def setup_style() -> None:
    """Configure matplotlib rcParams for consistent, high-DPI diagnostic publication charts."""
    plt.style.use("default")
    matplotlib.use("Agg")
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "figure.figsize": (10, 6),
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial", "sans-serif"],
        "font.family": "sans-serif",
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.labelweight": "normal",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "grid.color": "#B0BEC5",
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 9.5,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "#CFD8DC",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#78909C",
        "figure.autolayout": False,
    })


def get_verification_root() -> Path:
    """Return the base output path for reports/verification."""
    root = find_project_root()
    out_dir = root / "reports" / "verification"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _clean_token(text: Any) -> str:
    """Sanitize string to lowercase alphanumeric and underscores only."""
    clean = re.sub(r"[^a-z0-9_]+", "_", str(text).lower()).strip("_")
    return clean or "default"


def _format_stage_name(stage: Union[str, int]) -> str:
    """Format stage string cleanly into stage1..stage8."""
    st = str(stage).lower().strip()
    match = re.search(r"\d+", st)
    if match:
        return f"stage{match.group(0)}"
    return _clean_token(st)


def parse_path_args(path_args: Union[Dict[str, Any], Sequence[Any], str]) -> Tuple[str, str, str]:
    """Parse path args into (stage, topic, detail)."""
    if isinstance(path_args, dict):
        stage = path_args.get("stage", "stage1")
        topic = path_args.get("topic", "chart")
        detail = path_args.get("detail", "overview")
        return str(stage), str(topic), str(detail)
    elif isinstance(path_args, (list, tuple)):
        if len(path_args) == 3:
            return str(path_args[0]), str(path_args[1]), str(path_args[2])
        elif len(path_args) == 2:
            return str(path_args[0]), str(path_args[1]), "overview"
        elif len(path_args) == 1:
            return str(path_args[0]), "chart", "overview"
    return "stage1", "chart", str(path_args)


def save_fig(
    fig: plt.Figure,
    stage: Union[str, int],
    topic: str,
    detail: str,
    summary: Optional[str] = None,
) -> Path:
    """Construct filename, save figure to reports/verification/{stage}/, and update manifest.json.
    
    All filenames follow: {stage}_{topic}_{detail}_{YYYYMMDD_HHMMSS}.png
    Regex guarantee: ^stage\\d+_[a-z0-9_]+_\\d{8}_\\d{6}\\.png$
    """
    stage_key = _format_stage_name(stage)
    clean_topic = _clean_token(topic)
    clean_detail = _clean_token(detail)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{stage_key}_{clean_topic}_{clean_detail}_{timestamp}.png"
    stage_dir = get_verification_root() / stage_key
    stage_dir.mkdir(parents=True, exist_ok=True)
    out_path = stage_dir / filename

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Manifest update
    manifest_path = stage_dir / "manifest.json"
    manifest: List[Dict[str, Any]] = []
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    manifest = loaded
        except Exception as e:
            logger.warning("Could not read existing manifest at %s: %s", manifest_path, e)

    manifest_entry = {
        "filename": filename,
        "topic": clean_topic,
        "detail": clean_detail,
        "summary": summary or f"{clean_topic} {clean_detail}",
        "timestamp": timestamp,
        "stage": stage_key,
        "path": str(out_path.resolve()),
    }
    manifest.append(manifest_entry)

    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    except Exception as e:
        logger.error("Failed to write manifest at %s: %s", manifest_path, e)

    # Brief sleep to avoid exact timestamp collision on next immediate call
    time.sleep(0.02)
    return out_path


def annotate_stats(
    ax: plt.Axes,
    series: Union[pd.Series, np.ndarray, Sequence[float]],
    loc: str = "upper right",
    is_percent: bool = True,
    extra_text: Optional[str] = None,
) -> None:
    """Add standardized mean, std, n statistical annotation box to ax."""
    arr = np.asarray(series)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    if n == 0:
        return

    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    med_val = float(np.median(arr))

    if is_percent:
        scale = 100.0 if abs(mean_val) < 1.0 and abs(std_val) < 1.0 else 1.0
        text = (
            f"n = {n:,}\n"
            f"Mean = {mean_val * scale:+.2f}%\n"
            f"Std  = {std_val * scale:.2f}%\n"
            f"Med  = {med_val * scale:+.2f}%"
        )
    else:
        text = (
            f"n = {n:,}\n"
            f"Mean = {mean_val:.3f}\n"
            f"Std  = {std_val:.3f}\n"
            f"Med  = {med_val:.3f}"
        )

    if extra_text:
        text += f"\n{extra_text}"

    coords = {
        "upper right": (0.97, 0.95, "top", "right"),
        "upper left": (0.03, 0.95, "top", "left"),
        "lower right": (0.97, 0.05, "bottom", "right"),
        "lower left": (0.03, 0.05, "bottom", "left"),
    }
    x_pos, y_pos, va, ha = coords.get(loc, (0.97, 0.95, "top", "right"))

    ax.text(
        x_pos,
        y_pos,
        text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment=va,
        horizontalalignment=ha,
        bbox=dict(
            boxstyle="round,pad=0.4",
            facecolor="#FFFFFF",
            alpha=0.9,
            edgecolor="#90A4AE",
            linewidth=1.0,
        ),
    )


def placeholder_png(
    stage: Union[str, int],
    topic: str,
    detail: str,
    n: int = 0,
    reason: str = "INSUFFICIENT DATA",
) -> Tuple[Path, str]:
    """Generate and save an informative placeholder image when data rows < 10."""
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    stage_key = _format_stage_name(stage)
    topic_clean = _clean_token(topic)
    detail_clean = _clean_token(detail)
    
    ax.set_facecolor("#ECEFF1")
    ax.text(
        0.5,
        0.55,
        f"{reason.upper()} (n={n})",
        fontsize=18,
        fontweight="bold",
        color=COLOR_DOWN,
        ha="center",
        va="center",
    )
    ax.text(
        0.5,
        0.42,
        f"Stage: {stage_key.upper()} | Topic: {topic_clean} | Detail: {detail_clean}",
        fontsize=11,
        color=COLOR_NEUTRAL,
        ha="center",
        va="center",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"{stage_key.upper()} - {topic_clean.replace('_', ' ').title()}", fontsize=14, pad=12)
    ax.grid(False)
    
    summary = f"{stage_key} {topic_clean}_{detail_clean}: {reason} (n={n})"
    path = save_fig(fig, stage_key, topic_clean, detail_clean, summary=summary)
    return path, summary


def plot_histogram(
    series: Union[pd.Series, np.ndarray, Sequence[float]],
    title: str,
    xlabel: str,
    path_args: Union[Dict[str, Any], Sequence[Any], str],
    bins: int = 30,
    color: str = COLOR_ACCENT,
    vlines: Optional[List[float]] = None,
    is_percent: bool = True,
    ylabel: str = "Count",
    summary_metric: Optional[str] = None,
) -> Tuple[Path, str]:
    """Plot distribution histogram with vertical reference lines and statistics box."""
    setup_style()
    stage, topic, detail = parse_path_args(path_args)
    arr = np.asarray(series)
    arr = arr[~np.isnan(arr)]
    n = len(arr)

    if n < 10:
        return placeholder_png(stage, topic, detail, n=n)

    fig, ax = plt.subplots(figsize=(10, 6))
    scale = 100.0 if is_percent and abs(np.nanmean(arr)) < 1.0 and abs(np.nanstd(arr)) < 1.0 else 1.0
    scaled_arr = arr * scale

    ax.hist(scaled_arr, bins=bins, color=color, edgecolor="#FFFFFF", alpha=0.85, label="Data")
    
    # Vertical line at 0 if within range
    if scaled_arr.min() <= 0 <= scaled_arr.max():
        ax.axvline(0, color=COLOR_NEUTRAL, linestyle="--", linewidth=1.2, alpha=0.8, label="Zero")

    # Mean line
    mean_val = float(np.mean(scaled_arr))
    ax.axvline(mean_val, color=COLOR_DOWN if mean_val < 0 else COLOR_UP, linestyle="-", linewidth=2.0, label=f"Mean ({mean_val:+.2f}%)")

    if vlines:
        for vl in vlines:
            ax.axvline(vl * scale, color="#F57C00", linestyle=":", linewidth=1.5, alpha=0.8)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="upper left")
    annotate_stats(ax, arr, loc="upper right", is_percent=is_percent)

    unit = "%" if is_percent else ""
    summary = summary_metric or (
        f"{title}: mean={np.mean(arr)*scale:.2f}{unit}, std={np.std(arr)*scale:.2f}{unit}, n={n}"
    )
    path = save_fig(fig, stage, topic, detail, summary=summary)
    return path, summary


def plot_timeseries(
    series: Union[pd.Series, Dict[str, Any]],
    title: str,
    ylabel: str,
    path_args: Union[Dict[str, Any], Sequence[Any], str],
    dates: Optional[Sequence[Any]] = None,
    rolling_window: Optional[int] = None,
    color: str = COLOR_ACCENT,
    baseline: Optional[float] = None,
) -> Tuple[Path, str]:
    """Plot time-series with optional rolling average trend."""
    setup_style()
    stage, topic, detail = parse_path_args(path_args)

    if isinstance(series, pd.Series):
        s = series.dropna()
        x_vals = s.index
        y_vals = s.values
    else:
        y_vals = np.asarray(series)
        x_vals = dates if dates is not None else np.arange(len(y_vals))

    n = len(y_vals)
    if n < 10:
        return placeholder_png(stage, topic, detail, n=n)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x_vals, y_vals, color=color, linewidth=1.6, alpha=0.85, label="Observed")

    if rolling_window and n >= rolling_window:
        roll = pd.Series(y_vals).rolling(rolling_window, min_periods=max(1, rolling_window // 2)).mean()
        ax.plot(x_vals, roll.values, color=COLOR_UP, linewidth=2.2, label=f"{rolling_window}-Period MA")

    if baseline is not None:
        ax.axhline(baseline, color=COLOR_NEUTRAL, linestyle="--", linewidth=1.2, label=f"Baseline ({baseline})")

    ax.set_title(title)
    ax.set_xlabel("Time / Date")
    ax.set_ylabel(ylabel)
    ax.legend(loc="best")
    fig.autofmt_xdate()

    summary = f"{title}: latest={y_vals[-1]:.3f}, mean={np.mean(y_vals):.3f}, n={n}"
    path = save_fig(fig, stage, topic, detail, summary=summary)
    return path, summary


def plot_box_by_category(
    df: pd.DataFrame,
    cat_col: str,
    val_col: str,
    title: str,
    path_args: Union[Dict[str, Any], Sequence[Any], str],
    is_percent: bool = True,
    ylabel: Optional[str] = None,
    max_categories: int = 12,
) -> Tuple[Path, str]:
    """Plot categorized box plot sorted by median value."""
    setup_style()
    stage, topic, detail = parse_path_args(path_args)

    clean_df = df[[cat_col, val_col]].dropna().copy()
    n = len(clean_df)
    if n < 10:
        return placeholder_png(stage, topic, detail, n=n)

    scale = 100.0 if is_percent and clean_df[val_col].abs().max() < 1.0 else 1.0
    clean_df["scaled_val"] = clean_df[val_col] * scale

    # Keep top categories by frequency
    top_cats = clean_df[cat_col].value_counts().head(max_categories).index.tolist()
    sub_df = clean_df[clean_df[cat_col].isin(top_cats)].copy()

    # Sort categories by median
    cat_medians = sub_df.groupby(cat_col)["scaled_val"].median().sort_values(ascending=False)
    sorted_cats = cat_medians.index.tolist()
    grouped_data = [sub_df[sub_df[cat_col] == c]["scaled_val"].values for c in sorted_cats]

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
        med = cat_medians[c_name]
        face_col = COLOR_UP if med > 0 else (COLOR_DOWN if med < 0 else COLOR_ACCENT)
        patch.set_facecolor(face_col)
        patch.set_alpha(0.65)
        patch.set_edgecolor("#37474F")

    ax.axhline(0, color=COLOR_NEUTRAL, linestyle="--", linewidth=1.2, alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel(cat_col.replace("_", " ").title())
    ax.set_ylabel(ylabel or (f"{val_col} (%)" if is_percent else val_col))

    highest_cat = sorted_cats[0]
    lowest_cat = sorted_cats[-1]
    unit = "%" if is_percent else ""
    summary = (
        f"{title}: highest={highest_cat} (med={cat_medians[highest_cat]:+.2f}{unit}), "
        f"lowest={lowest_cat} (med={cat_medians[lowest_cat]:+.2f}{unit}), n={n}"
    )
    path = save_fig(fig, stage, topic, detail, summary=summary)
    return path, summary


def plot_scatter(
    x: Union[pd.Series, np.ndarray, Sequence[float]],
    y: Union[pd.Series, np.ndarray, Sequence[float]],
    title: str,
    xlabel: str,
    ylabel: str,
    path_args: Union[Dict[str, Any], Sequence[Any], str],
    fit_line: bool = True,
    color: str = COLOR_ACCENT,
    alpha: float = 0.65,
) -> Tuple[Path, str]:
    """Plot scatter plot with regression fit, Spearman rank correlation, and Pearson IC."""
    setup_style()
    stage, topic, detail = parse_path_args(path_args)

    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
    x_arr = x_arr[mask]
    y_arr = y_arr[mask]
    n = len(x_arr)

    if n < 10:
        return placeholder_png(stage, topic, detail, n=n)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(x_arr, y_arr, color=color, alpha=alpha, edgecolors="none", s=28, label="Observations")

    r_squared = 0.0
    r_val = 0.0
    if fit_line and n > 2 and np.std(x_arr) > 1e-9:
        slope, intercept = np.polyfit(x_arr, y_arr, 1)
        x_vals = np.linspace(x_arr.min(), x_arr.max(), 100)
        y_vals = slope * x_vals + intercept
        ax.plot(x_vals, y_vals, color=COLOR_DOWN, linewidth=2.0, label=f"Fit (slope={slope:.3f})")

        # Pearson and Spearman
        mean_x, mean_y = np.mean(x_arr), np.mean(y_arr)
        denom = np.sqrt(np.sum((x_arr - mean_x) ** 2) * np.sum((y_arr - mean_y) ** 2))
        r_val = float(np.sum((x_arr - mean_x) * (y_arr - mean_y)) / denom) if denom > 1e-12 else 0.0
        r_squared = r_val ** 2

    # Rank correlation
    s_x = pd.Series(x_arr).rank()
    s_y = pd.Series(y_arr).rank()
    spearman = float(s_x.corr(s_y)) if n > 2 else 0.0

    ax.set_title(f"{title} (R²={r_squared:.3f}, Pearson IC={r_val:+.3f}, Spearman={spearman:+.3f})")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="upper left")

    summary = f"{title}: IC={r_val:.2f}, Rank IC={spearman:.2f}, R²={r_squared:.2f}, n={n}"
    path = save_fig(fig, stage, topic, detail, summary=summary)
    return path, summary


def plot_heatmap(
    matrix: Union[pd.DataFrame, np.ndarray],
    labels_x: Sequence[str],
    labels_y: Sequence[str],
    title: str,
    path_args: Union[Dict[str, Any], Sequence[Any], str],
    cmap: str = "Blues",
    fmt: str = ".2f",
    annotate: bool = True,
    xlabel: str = "",
    ylabel: str = "",
) -> Tuple[Path, str]:
    """Plot structured 2D heatmap matrix with cell values."""
    setup_style()
    stage, topic, detail = parse_path_args(path_args)

    mat = np.asarray(matrix, dtype=np.float64)
    rows, cols = mat.shape

    if rows == 0 or cols == 0:
        return placeholder_png(stage, topic, detail, n=0)

    fig_w = max(9.0, min(14.0, cols * 0.8 + 3.0))
    fig_h = max(6.0, min(12.0, rows * 0.6 + 2.5))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    cax = ax.imshow(mat, cmap=cmap, aspect="auto", interpolation="nearest")
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(np.arange(cols))
    ax.set_yticks(np.arange(rows))
    ax.set_xticklabels(labels_x, rotation=35, ha="right", fontsize=9)
    ax.set_yticklabels(labels_y, fontsize=9.5)

    if annotate and (rows * cols <= 250):
        thresh = (np.nanmax(mat) + np.nanmin(mat)) / 2.0
        for i in range(rows):
            for j in range(cols):
                val = mat[i, j]
                if not np.isnan(val):
                    text_col = "#FFFFFF" if val > thresh else "#000000"
                    ax.text(j, i, f"{val:{fmt}}", ha="center", va="center", color=text_col, fontsize=8.5)

    ax.set_title(title, pad=12)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(False)

    summary = f"{title}: matrix shape ({rows}x{cols}), min={np.nanmin(mat):.2f}, max={np.nanmax(mat):.2f}"
    path = save_fig(fig, stage, topic, detail, summary=summary)
    return path, summary


def plot_bar(
    values: Sequence[float],
    labels: Sequence[str],
    title: str,
    path_args: Union[Dict[str, Any], Sequence[Any], str],
    xlabel: str = "",
    ylabel: str = "",
    orientation: str = "vertical",
    color: Union[str, Sequence[str]] = COLOR_ACCENT,
    baseline: Optional[float] = None,
    value_labels: bool = True,
    fmt: str = ".1f",
) -> Tuple[Path, str]:
    """Plot vertical or horizontal bar chart with value callouts."""
    setup_style()
    stage, topic, detail = parse_path_args(path_args)

    val_arr = np.asarray(values, dtype=np.float64)
    lbl_arr = list(labels)
    n = len(val_arr)

    if n == 0:
        return placeholder_png(stage, topic, detail, n=0)

    fig, ax = plt.subplots(figsize=(10, 6))

    if orientation == "horizontal":
        bars = ax.barh(np.arange(n), val_arr, color=color, alpha=0.85, edgecolor="#FFFFFF")
        ax.set_yticks(np.arange(n))
        ax.set_yticklabels(lbl_arr, fontsize=9.5)
        ax.invert_yaxis()
        ax.set_xlabel(xlabel or "Value")
        ax.set_ylabel(ylabel)

        if baseline is not None:
            ax.axvline(baseline, color=COLOR_DOWN, linestyle="--", linewidth=1.5, label=f"Baseline ({baseline})")
            ax.legend(loc="lower right")

        if value_labels:
            for bar in bars:
                w = bar.get_width()
                offset = (np.nanmax(val_arr) - np.nanmin(val_arr)) * 0.015 if np.nanmax(val_arr) != np.nanmin(val_arr) else 0.1
                ha = "left" if w >= 0 else "right"
                ax.text(w + (offset if w >= 0 else -offset), bar.get_y() + bar.get_height() / 2, f"{w:{fmt}}", va="center", ha=ha, fontsize=8.5)
    else:
        bars = ax.bar(np.arange(n), val_arr, color=color, alpha=0.85, edgecolor="#FFFFFF")
        ax.set_xticks(np.arange(n))
        ax.set_xticklabels(lbl_arr, rotation=35, ha="right", fontsize=9.5)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel or "Value")

        if baseline is not None:
            ax.axhline(baseline, color=COLOR_DOWN, linestyle="--", linewidth=1.5, label=f"Baseline ({baseline})")
            ax.legend(loc="upper right")

        if value_labels:
            for bar in bars:
                h = bar.get_height()
                offset = (np.nanmax(val_arr) - np.nanmin(val_arr)) * 0.015 if np.nanmax(val_arr) != np.nanmin(val_arr) else 0.1
                va = "bottom" if h >= 0 else "top"
                ax.text(bar.get_x() + bar.get_width() / 2, h + (offset if h >= 0 else -offset), f"{h:{fmt}}", ha="center", va=va, fontsize=8.5)

    ax.set_title(title, pad=12)

    summary = f"{title}: items={n}, mean={np.nanmean(val_arr):.2f}, max={np.nanmax(val_arr):.2f}"
    path = save_fig(fig, stage, topic, detail, summary=summary)
    return path, summary
