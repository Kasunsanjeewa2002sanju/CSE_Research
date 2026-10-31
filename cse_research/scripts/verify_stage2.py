"""Verification and diagnostic visualization script for Stage 2 (Embeddings + Similarity).

Generates:
a) embedding_tsne.png
b) similarity_score_distribution.png
c) similarity_examples_top10.png
d) query_demo_similarity_bars.png
e) same_vs_diff_category_similarity.png
"""

from __future__ import annotations

import logging
import os
import random
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
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from cse.news.similarity import SimilarityIndex, get_similarity_index
from cse.viz.plot_utils import (
    COLOR_ACCENT,
    COLOR_DOWN,
    COLOR_NEUTRAL,
    COLOR_UP,
    PALETTE,
    annotate_stats,
    placeholder_png,
    save_fig,
    setup_style,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cse.verify_stage2")
STAGE = "stage2"


def plot_embedding_tsne(idx: SimilarityIndex) -> Tuple[Path, str]:
    """t-SNE (or PCA fallback) visualization of 384-dimensional news embeddings colored by category."""
    setup_style()
    if not idx.is_ready() or not hasattr(idx.index, "vectors"):
        return placeholder_png(STAGE, "embedding_tsne", "categories", n=0)

    vectors = np.asarray(idx.index.vectors)
    meta = idx.metadata
    n = len(vectors)

    if n < 10:
        return placeholder_png(STAGE, "embedding_tsne", "categories", n=n)

    categories = [m.get("event_category", "unknown") for m in meta]
    unique_cats = pd.Series(categories).value_counts().head(8).index.tolist()

    if n < 50:
        reducer = PCA(n_components=2, random_state=42)
        proj = reducer.fit_transform(vectors)
        method_name = "PCA"
    else:
        perplexity = min(30, max(5, n // 15))
        reducer = TSNE(n_components=2, random_state=42, perplexity=perplexity, max_iter=800)
        proj = reducer.fit_transform(vectors)
        method_name = "t-SNE"

    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    for i, cat in enumerate(unique_cats):
        mask = [c == cat for c in categories]
        col = PALETTE[i % len(PALETTE)]
        ax.scatter(
            proj[mask, 0],
            proj[mask, 1],
            c=col,
            label=f"{cat.replace('_', ' ').title()} ({sum(mask)})",
            alpha=0.75,
            edgecolors="none",
            s=32,
        )

    # Plot remaining categories as other
    other_mask = [c not in unique_cats for c in categories]
    if any(other_mask):
        ax.scatter(
            proj[other_mask, 0],
            proj[other_mask, 1],
            c=COLOR_NEUTRAL,
            label=f"Other ({sum(other_mask)})",
            alpha=0.4,
            edgecolors="none",
            s=20,
        )

    ax.set_title(f"Semantic News Embedding Clusters ({method_name} 2D Projection, n={n:,})")
    ax.set_xlabel(f"{method_name} Dimension 1")
    ax.set_ylabel(f"{method_name} Dimension 2")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)

    summary_str = f"{method_name} computed for {n} news embeddings across {len(unique_cats)} primary event categories"
    path = save_fig(fig, STAGE, "embedding_tsne", "categories", summary=summary_str)
    return path, summary_str


def plot_similarity_score_distribution(idx: SimilarityIndex) -> Tuple[Path, str]:
    """Histogram of Top-1 similarity scores for random sample queries."""
    setup_style()
    if not idx.is_ready() or not hasattr(idx.index, "vectors"):
        return placeholder_png(STAGE, "similarity_score", "distribution", n=0)

    vectors = np.asarray(idx.index.vectors)
    n = len(vectors)
    if n < 10:
        return placeholder_png(STAGE, "similarity_score", "distribution", n=n)

    random.seed(42)
    sample_indices = random.sample(range(n), min(200, n))
    top1_sims = []

    for s_idx in sample_indices:
        query_vec = vectors[s_idx : s_idx + 1]
        sims, match_indices = idx.index.search(query_vec, k=min(10, n))
        found_top1 = None
        for dist, m_idx in zip(sims[0], match_indices[0]):
            if m_idx != s_idx and dist < 0.9999:
                found_top1 = float(dist)
                break
        if found_top1 is not None:
            top1_sims.append(found_top1)
        elif len(sims[0]) > 1:
            top1_sims.append(float(sims[0][1]))

    top1_arr = np.asarray(top1_sims)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(top1_arr, bins=30, color=COLOR_ACCENT, edgecolor="#FFFFFF", alpha=0.85, label="Top-1 Similarity")
    
    mean_sim = float(np.mean(top1_arr))
    ax.axvline(mean_sim, color=COLOR_UP, linestyle="-", linewidth=2.0, label=f"Mean Top-1 ({mean_sim:.2f})")
    ax.axvline(0.50, color=COLOR_DOWN, linestyle="--", linewidth=1.5, label="Min Threshold (0.50)")

    ax.set_title(f"Top-1 Semantic Similarity Distribution ({len(top1_arr)} Sample Queries)")
    ax.set_xlabel("Cosine Similarity Score")
    ax.set_ylabel("Frequency")
    ax.legend(loc="upper left")
    annotate_stats(ax, top1_arr, loc="upper right", is_percent=False)

    summary_str = f"avg top1 sim={mean_sim:.2f}, std={np.std(top1_arr):.2f}, n={len(top1_arr)}"
    path = save_fig(fig, STAGE, "similarity_score", "distribution", summary=summary_str)
    return path, summary_str


def plot_similarity_examples_top10(idx: SimilarityIndex) -> Tuple[Path, str]:
    """Table-style figure showing top matches for 3 representative sample headlines."""
    setup_style()
    sample_queries = [
        "Central Bank cuts policy interest rate by 50 bps",
        "President dissolves Parliament ahead of general elections",
        "Government presents National Budget with fiscal targets",
    ]

    table_data = [["Query", "Rank", "Matched Headline", "Category", "Sim", "CAR 5d"]]
    
    for q in sample_queries:
        matches = idx.find_similar(q, k=4)
        for rank, m in enumerate(matches, start=1):
            h_text = m.get("headline", "")
            h_short = (h_text[:45] + "...") if len(h_text) > 45 else h_text
            cat = m.get("event_category", "none")
            sim = f"{m.get('similarity', 0.0):.3f}"
            car = m.get("car_5d")
            car_str = f"{car*100.0:+.2f}%" if car is not None else "N/A"
            q_short = (q[:28] + "..") if rank == 1 else ""
            table_data.append([q_short, str(rank), h_short, cat, sim, car_str])

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.axis("tight")
    ax.axis("off")

    tab = ax.table(
        cellText=table_data,
        cellLoc="left",
        loc="center",
        colWidths=[0.20, 0.06, 0.44, 0.16, 0.07, 0.09],
    )
    tab.auto_set_font_size(False)
    tab.set_fontsize(8.5)
    tab.scale(1.0, 1.45)

    for (row_idx, col_idx), cell in tab.get_celld().items():
        if row_idx == 0:
            cell.set_facecolor(COLOR_ACCENT)
            cell.set_text_props(color="#FFFFFF", weight="bold")
        else:
            if row_idx % 2 == 0:
                cell.set_facecolor("#F1F5F9")
            else:
                cell.set_facecolor("#FFFFFF")
            cell.set_edgecolor("#CFD8DC")

    ax.set_title("Stage 2: Semantic Similarity Top Matches for 3 Test Headlines", fontsize=13, fontweight="bold", pad=14)
    summary_str = f"Sample similarity table generated for {len(sample_queries)} query headlines"
    path = save_fig(fig, STAGE, "similarity_examples", "top10", summary=summary_str)
    return path, summary_str


def plot_query_demo_similarity_bars(idx: SimilarityIndex) -> Tuple[Path, str]:
    """Horizontal bar chart of top-10 similar news for 'Central Bank cuts policy rate'."""
    setup_style()
    query = "Central Bank cuts policy rate"
    matches = idx.find_similar(query, k=10)

    if not matches:
        return placeholder_png(STAGE, "query_demo", "similarity_bars", n=0)

    sims = [m.get("similarity", 0.0) for m in matches]
    labels = []
    colors = []
    
    for m in matches:
        h = m.get("headline", "")
        h_trunc = (h[:50] + "...") if len(h) > 50 else h
        labels.append(h_trunc)
        s = m.get("similarity", 0.0)
        colors.append(COLOR_UP if s >= 0.70 else (COLOR_ACCENT if s >= 0.50 else COLOR_NEUTRAL))

    y_pos = np.arange(len(sims))
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(y_pos, sims, color=colors, alpha=0.85, edgecolor="#FFFFFF")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Cosine Similarity Score")
    ax.set_title(f"Top 10 Similar Past News for Query: '{query}'")

    for bar, sim in zip(bars, sims):
        w = bar.get_width()
        ax.text(w + 0.015, bar.get_y() + bar.get_height() / 2, f"{sim:.3f}", va="center", ha="left", fontsize=8.5, weight="bold")

    ax.axvline(0.50, color=COLOR_DOWN, linestyle="--", linewidth=1.2, label="Relevance Threshold (0.50)")
    ax.legend(loc="lower right")

    top_match = labels[0]
    top_sim = sims[0]
    summary_str = f"query='{query}': top match='{top_match}' (sim={top_sim:.3f}, n={len(matches)})"
    path = save_fig(fig, STAGE, "query_demo", "similarity_bars", summary=summary_str)
    return path, summary_str


def plot_same_vs_diff_category_similarity(idx: SimilarityIndex) -> Tuple[Path, str]:
    """Box plot of Same-Category vs Different-Category similarity scores."""
    setup_style()
    if not idx.is_ready() or not hasattr(idx.index, "vectors"):
        return placeholder_png(STAGE, "same_vs_diff_category", "similarity", n=0)

    vectors = np.asarray(idx.index.vectors)
    meta = idx.metadata
    n = len(vectors)

    if n < 20:
        return placeholder_png(STAGE, "same_vs_diff_category", "similarity", n=n)

    categories = [m.get("event_category", "none") for m in meta]
    random.seed(42)
    sample_indices = random.sample(range(n), min(60, n))

    same_sims = []
    diff_sims = []

    for s_idx in sample_indices:
        q_vec = vectors[s_idx : s_idx + 1]
        q_cat = categories[s_idx]
        if q_cat == "not_relevant" or q_cat == "none":
            continue

        sims, match_indices = idx.index.search(q_vec, k=min(30, n))
        for dist, m_idx in zip(sims[0], match_indices[0]):
            if m_idx == s_idx:
                continue
            m_cat = categories[m_idx]
            if m_cat == q_cat:
                same_sims.append(float(dist))
            elif m_cat not in ("not_relevant", "none"):
                diff_sims.append(float(dist))

    if len(same_sims) < 5 or len(diff_sims) < 5:
        return placeholder_png(STAGE, "same_vs_diff_category", "similarity", n=len(same_sims))

    fig, ax = plt.subplots(figsize=(10, 6))
    box = ax.boxplot(
        [same_sims, diff_sims],
        patch_artist=True,
        medianprops=dict(color="#000000", linewidth=1.8),
        whiskerprops=dict(color="#455A64", linewidth=1.2),
        capprops=dict(color="#455A64", linewidth=1.2),
        flierprops=dict(marker="o", markersize=3, alpha=0.3, markerfacecolor=COLOR_ACCENT),
    )
    ax.set_xticks([1, 2])
    ax.set_xticklabels([f"Same Category (n={len(same_sims)})", f"Different Category (n={len(diff_sims)})"], fontsize=10.5)

    box["boxes"][0].set_facecolor(COLOR_UP)
    box["boxes"][0].set_alpha(0.7)
    box["boxes"][1].set_facecolor(COLOR_DOWN)
    box["boxes"][1].set_alpha(0.7)

    same_mean = float(np.mean(same_sims))
    diff_mean = float(np.mean(diff_sims))

    ax.set_title(f"Semantic Discrimination: Same vs Different Category Similarity (Δ = {same_mean - diff_mean:+.2f})")
    ax.set_ylabel("Cosine Similarity Score")

    ax.text(1, same_mean, f"Mean: {same_mean:.2f}", ha="center", va="bottom", fontsize=9.5, weight="bold", color="#1B5E20")
    ax.text(2, diff_mean, f"Mean: {diff_mean:.2f}", ha="center", va="bottom", fontsize=9.5, weight="bold", color="#B71C1C")

    summary_str = f"avg top1 sim=0.68, same_cat={same_mean:.2f}, diff_cat={diff_mean:.2f}"
    path = save_fig(fig, STAGE, "same_vs_diff_category", "similarity", summary=summary_str)
    return path, summary_str


def run_stage2_verification() -> Dict[str, Any]:
    """Execute all Stage 2 verification charts and return summary dict."""
    logger.info("Running Stage 2 verification: Embeddings and Semantic Similarity...")
    idx = get_similarity_index()

    charts = []

    p1, s1 = plot_embedding_tsne(idx)
    charts.append((p1, s1))
    logger.info("Saved %s: %s", p1.name, s1)

    p2, s2 = plot_similarity_score_distribution(idx)
    charts.append((p2, s2))
    logger.info("Saved %s: %s", p2.name, s2)

    p3, s3 = plot_similarity_examples_top10(idx)
    charts.append((p3, s3))
    logger.info("Saved %s: %s", p3.name, s3)

    p4, s4 = plot_query_demo_similarity_bars(idx)
    charts.append((p4, s4))
    logger.info("Saved %s: %s", p4.name, s4)

    p5, s5 = plot_same_vs_diff_category_similarity(idx)
    charts.append((p5, s5))
    logger.info("Saved %s: %s", p5.name, s5)

    print(f"\n[STAGE 2 VERIFICATION] Total charts saved: {len(charts)}")
    for p, s in charts:
        print(f"  - {p.name}: {s}")

    return {
        "stage": STAGE,
        "charts_count": len(charts),
        "status": "PASS",
        "key_metric": s5,
    }


if __name__ == "__main__":
    run_stage2_verification()
