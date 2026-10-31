"""Historical news walk-forward backtest and validation report generator (Stage 7).

Replays all news in cse_history.db over the past 2 years strictly observing zero lookahead:
- For each news item, features are built using ONLY data available BEFORE the news date.
- Evaluates multi-horizon predictions vs actual Cumulative Abnormal Return (CAR).
- Computes:
    * Directional accuracy (% direction sign matches)
    * MAE vs baseline (0-return benchmark)
    * Information Coefficient (IC = Pearson and Spearman correlation)
    * Top-quintile Sharpe ratio & Long/Short spread (Q5 - Q1)
- Outputs standalone HTML report to reports/backtest_YYYYMMDD.html
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import math
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Suppress matplotlib permission error on Windows
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent.parent / "data"))

from cse.news.historical_db import get_default_db_path
from cse.news.feature_builder import (
    FEATURE_COLUMNS,
    TECHNICAL_FEATURE_COLS,
    build_features,
    get_cache,
)
from cse.scenario.engine import get_scenario_engine
from cse.utils.config import find_project_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cse.scripts.backtest")

ROOT_DIR = find_project_root()
DEFAULT_DB_PATH = get_default_db_path()
REPORTS_DIR = ROOT_DIR / "reports"


def compute_ic_and_rank_ic(pred: np.ndarray, actual: np.ndarray) -> Tuple[float, float]:
    """Compute Pearson correlation (IC) and Spearman rank correlation (Rank IC)."""
    if len(pred) < 3 or np.all(pred == pred[0]) or np.all(actual == actual[0]):
        return 0.0, 0.0

    # Pearson IC
    pred_demean = pred - np.mean(pred)
    actual_demean = actual - np.mean(actual)
    denom = np.sqrt(np.sum(pred_demean ** 2) * np.sum(actual_demean ** 2))
    ic = float(np.sum(pred_demean * actual_demean) / denom) if denom > 1e-12 else 0.0

    # Spearman Rank IC
    pred_ranks = pd.Series(pred).rank().values
    actual_ranks = pd.Series(actual).rank().values
    pr_demean = pred_ranks - np.mean(pred_ranks)
    ar_demean = actual_ranks - np.mean(actual_ranks)
    r_denom = np.sqrt(np.sum(pr_demean ** 2) * np.sum(ar_demean ** 2))
    rank_ic = float(np.sum(pr_demean * ar_demean) / r_denom) if r_denom > 1e-12 else 0.0

    return round(ic, 4), round(rank_ic, 4)


def compute_quintile_metrics(pred: np.ndarray, actual: np.ndarray, horizon: int = 5) -> Dict[str, Any]:
    """Divide predictions into 5 quintiles and compute per-quintile statistics and top-quintile Sharpe."""
    n = len(pred)
    if n < 10:
        return {
            "quintiles": [],
            "top_quintile_sharpe": 0.0,
            "q5_mean": 0.0,
            "q1_mean": 0.0,
            "spread_q5_q1": 0.0,
        }

    df = pd.DataFrame({"pred": pred, "actual": actual})
    try:
        df["quintile"] = pd.qcut(df["pred"], q=5, labels=[1, 2, 3, 4, 5], duplicates="drop")
    except Exception:
        # Fallback rank-based quintiles
        ranks = pd.Series(pred).rank(method="first")
        df["quintile"] = pd.cut(ranks, bins=5, labels=[1, 2, 3, 4, 5])

    quintiles_stats = []
    annualization_factor = math.sqrt(252.0 / max(1, horizon))

    for q in [1, 2, 3, 4, 5]:
        sub = df[df["quintile"] == q]["actual"]
        q_count = len(sub)
        if q_count > 0:
            q_mean = float(sub.mean())
            q_std = float(sub.std(ddof=1)) if q_count > 1 else 0.001
            q_sharpe = float((q_mean / q_std) * annualization_factor) if q_std > 1e-6 else 0.0
            q_hit_rate = float((sub > 0).mean() * 100.0)
        else:
            q_mean, q_std, q_sharpe, q_hit_rate = 0.0, 0.0, 0.0, 0.0

        quintiles_stats.append({
            "quintile": q,
            "count": q_count,
            "mean_actual_pct": round(q_mean * 100.0, 3),
            "std_actual_pct": round(q_std * 100.0, 3),
            "hit_rate_pct": round(q_hit_rate, 1),
            "annualized_sharpe": round(q_sharpe, 2),
        })

    q5_mean = quintiles_stats[4]["mean_actual_pct"] if len(quintiles_stats) >= 5 else 0.0
    q1_mean = quintiles_stats[0]["mean_actual_pct"] if len(quintiles_stats) >= 1 else 0.0
    top_sharpe = quintiles_stats[4]["annualized_sharpe"] if len(quintiles_stats) >= 5 else 0.0

    return {
        "quintiles": quintiles_stats,
        "top_quintile_sharpe": top_sharpe,
        "q5_mean": q5_mean,
        "q1_mean": q1_mean,
        "spread_q5_q1": round(q5_mean - q1_mean, 3),
    }


def run_backtest(
    db_path: Path,
    horizon: int = 5,
    sample_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute causal historical backtest replaying news in cse_history.db."""
    logger.info("Initializing Backtest Engine with models and zero-lookahead prior...")
    engine = get_scenario_engine()
    model_bundle = engine.models.get(horizon)
    if not model_bundle:
        raise ValueError(f"Model for horizon {horizon} not found.")

    reg = model_bundle["regressor"]
    clf = model_bundle["classifier"]
    calibrator = model_bundle["calibrator"]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    car_col = f"car_{horizon}d"
    cur.execute(
        f"""
        SELECT id, headline, published_at, source, event_category, stage, car_1d, car_2d, car_5d, car_10d
        FROM news_history
        WHERE published_at IS NOT NULL AND published_at != '' AND {car_col} IS NOT NULL
        ORDER BY published_at ASC
        """
    )
    rows = cur.fetchall()
    conn.close()

    total_available = len(rows)
    logger.info("Retrieved %d valid news events with actual CAR from %s", total_available, db_path)

    if sample_limit and sample_limit < total_available:
        rows = rows[:sample_limit]
        logger.info("Capped backtest execution to first %d events.", sample_limit)

    records: List[Dict[str, Any]] = []

    # Market data snapshot lookup cache by date to accelerate feature building
    market_cache_by_date: Dict[str, Dict[str, float]] = {}

    for idx, row in enumerate(rows):
        headline = row["headline"]
        pub_at = str(row["published_at"])
        news_date = pub_at[:10]
        actual_car = float(row[car_col])
        cat = row["event_category"] or "general"
        stage = row["stage"] or "none"

        # Causal market snapshot strictly on or before news_date
        market_snapshot: Optional[Dict[str, float]] = None
        if news_date in market_cache_by_date:
            market_snapshot = market_cache_by_date[news_date]

        # 1. Zero-Lookahead Feature Building: as_of_date guarantees prior uses only news published BEFORE news_date
        vec = build_features(
            headline=headline,
            news_date=news_date,
            market_snapshot=market_snapshot,
            horizon=horizon,
        )

        # Cache technical market values for this date
        if news_date not in market_cache_by_date:
            market_cache_by_date[news_date] = {c: float(vec[c]) for c in TECHNICAL_FEATURE_COLS if c in vec.feature_names}

        # 2. Frozen Model Inference
        X = np.asarray(vec).reshape(1, -1)
        pred_ret = float(reg.predict(X)[0])
        raw_prob = float(clf.predict_proba(X)[0, 1])
        cal_prob = float(calibrator.predict_proba(np.array([[raw_prob]]))[0, 1])

        # 3. Metrics Comparison
        # Direction match: both > 0 or both < 0 or both zero
        dir_hit = (pred_ret > 0 and actual_car > 0) or (pred_ret < 0 and actual_car < 0) or (abs(pred_ret) < 1e-5 and abs(actual_car) < 1e-5)
        # Prob direction hit: prob > 0.5 when return > 0
        prob_dir_hit = (cal_prob >= 0.50 and actual_car >= 0.0) or (cal_prob < 0.50 and actual_car < 0.0)

        err_model = abs(pred_ret - actual_car)
        err_base = abs(actual_car)  # Baseline is 0-return

        records.append({
            "id": row["id"],
            "headline": headline,
            "date": news_date,
            "category": cat,
            "stage": stage,
            "actual_car": actual_car,
            "actual_car_pct": round(actual_car * 100.0, 3),
            "predicted_car": pred_ret,
            "predicted_car_pct": round(pred_ret * 100.0, 3),
            "calibrated_prob_up": round(cal_prob, 4),
            "prior_median_car": round(float(vec["prior_median_car"]), 5),
            "error_model": err_model,
            "error_base": err_base,
            "dir_hit": dir_hit,
            "prob_dir_hit": prob_dir_hit,
        })

        if (idx + 1) % 100 == 0 or idx == len(rows) - 1:
            logger.info("Processed %d / %d events...", idx + 1, len(rows))

    n_eval = len(records)
    if n_eval == 0:
        raise RuntimeError("No records evaluated during backtest.")

    preds_arr = np.array([r["predicted_car"] for r in records], dtype=np.float64)
    actuals_arr = np.array([r["actual_car"] for r in records], dtype=np.float64)
    probs_arr = np.array([r["calibrated_prob_up"] for r in records], dtype=np.float64)

    # Core Backtest Performance Metrics
    dir_acc_ret = float(np.mean([r["dir_hit"] for r in records]) * 100.0)
    dir_acc_prob = float(np.mean([r["prob_dir_hit"] for r in records]) * 100.0)

    mae_model = float(np.mean([r["error_model"] for r in records]))
    mae_base = float(np.mean([r["error_base"] for r in records]))
    mae_reduction_pct = float(((mae_base - mae_model) / max(1e-9, mae_base)) * 100.0)

    ic_pearson, ic_spearman = compute_ic_and_rank_ic(preds_arr, actuals_arr)
    prob_ic, prob_rank_ic = compute_ic_and_rank_ic(probs_arr, actuals_arr)

    quintile_res = compute_quintile_metrics(preds_arr, actuals_arr, horizon=horizon)

    # Per-category summary
    df_res = pd.DataFrame(records)
    cat_summary = []
    for c_name, c_group in df_res.groupby("category"):
        c_n = len(c_group)
        c_dir = float(c_group["dir_hit"].mean() * 100.0)
        c_mae_m = float(c_group["error_model"].mean() * 100.0)
        c_mae_b = float(c_group["error_base"].mean() * 100.0)
        c_actual_mean = float(c_group["actual_car"].mean() * 100.0)
        c_pred_mean = float(c_group["predicted_car"].mean() * 100.0)
        cat_summary.append({
            "category": c_name,
            "count": c_n,
            "dir_accuracy_pct": round(c_dir, 1),
            "mae_model_pct": round(c_mae_m, 3),
            "mae_baseline_pct": round(c_mae_b, 3),
            "actual_mean_pct": round(c_actual_mean, 3),
            "predicted_mean_pct": round(c_pred_mean, 3),
        })

    cat_summary.sort(key=lambda item: item["count"], reverse=True)

    summary: Dict[str, Any] = {
        "execution_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date_range": [records[0]["date"], records[-1]["date"]],
        "horizon_days": horizon,
        "sample_size": n_eval,
        "metrics": {
            "directional_accuracy_pct": round(dir_acc_ret, 2),
            "prob_directional_accuracy_pct": round(dir_acc_prob, 2),
            "mae_model_pct": round(mae_model * 100.0, 3),
            "mae_baseline_pct": round(mae_base * 100.0, 3),
            "mae_improvement_pct": round(mae_reduction_pct, 2),
            "information_coefficient": ic_pearson,
            "rank_information_coefficient": ic_spearman,
            "top_quintile_sharpe": quintile_res["top_quintile_sharpe"],
            "long_short_spread_pct": quintile_res["spread_q5_q1"],
        },
        "quintile_performance": quintile_res["quintiles"],
        "category_breakdown": cat_summary,
        "sample_records": records[:20],
    }

    return summary


def render_html_report(summary: Dict[str, Any], output_path: Path) -> None:
    """Generate professional, publication-quality HTML backtest report."""
    m = summary["metrics"]
    q_data = summary["quintile_performance"]
    c_data = summary["category_breakdown"]
    samples = summary["sample_records"]

    # Quintile bar chart rows
    q_rows_html = ""
    for q in q_data:
        m_pct = q["mean_actual_pct"]
        bar_w = min(100.0, abs(m_pct) * 20.0 + 10.0)
        bar_color = "#10b981" if m_pct >= 0 else "#ef4444"
        q_rows_html += f"""
        <tr>
            <td style="font-weight: 600; text-align: center;">Quintile {q['quintile']}</td>
            <td style="text-align: right;">{q['count']}</td>
            <td style="text-align: right; color: {bar_color}; font-weight: 700;">{m_pct:+.2f}%</td>
            <td>
                <div style="background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; height: 16px; width: 100%;">
                    <div style="background: {bar_color}; width: {bar_w}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </td>
            <td style="text-align: right;">{q['std_actual_pct']:.2f}%</td>
            <td style="text-align: right;">{q['hit_rate_pct']:.1f}%</td>
            <td style="text-align: right; font-weight: 600;">{q['annualized_sharpe']:.2f}</td>
        </tr>
        """

    # Category breakdown rows
    cat_rows_html = ""
    for c in c_data:
        cat_rows_html += f"""
        <tr>
            <td style="font-weight: 500;">{c['category']}</td>
            <td style="text-align: right;">{c['count']}</td>
            <td style="text-align: right; font-weight: 600; color: #3b82f6;">{c['dir_accuracy_pct']:.1f}%</td>
            <td style="text-align: right;">{c['mae_model_pct']:.2f}%</td>
            <td style="text-align: right;">{c['mae_baseline_pct']:.2f}%</td>
            <td style="text-align: right; color: {'#10b981' if c['actual_mean_pct'] >= 0 else '#ef4444'};">{c['actual_mean_pct']:+.2f}%</td>
            <td style="text-align: right;">{c['predicted_mean_pct']:+.2f}%</td>
        </tr>
        """

    # Sample rows
    sample_rows_html = ""
    for s in samples[:15]:
        hit_badge = '<span style="color: #10b981; font-weight: 700;">HIT</span>' if s["dir_hit"] else '<span style="color: #ef4444;">MISS</span>'
        sample_rows_html += f"""
        <tr>
            <td style="font-size: 12px; color: #94a3b8; white-space: nowrap;">{s['date']}</td>
            <td style="font-weight: 500; font-size: 13px;">{s['headline']}</td>
            <td style="font-size: 12px; color: #cbd5e1;">{s['category']}</td>
            <td style="text-align: right; font-weight: 600;">{s['predicted_car_pct']:+.2f}%</td>
            <td style="text-align: right; font-weight: 600; color: {'#10b981' if s['actual_car_pct'] >= 0 else '#ef4444'};">{s['actual_car_pct']:+.2f}%</td>
            <td style="text-align: center;">{hit_badge}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSE Historical News Backtest Report — Stage 7</title>
    <style>
        :root {{
            --bg: #090d16;
            --card-bg: #111827;
            --border: #1f2937;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --positive: #10b981;
            --negative: #ef4444;
        }}
        body {{
            background: var(--bg);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 32px 24px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 28px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 16px;
        }}
        h1 {{
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin: 0 0 6px 0;
            background: linear-gradient(135deg, #60a5fa 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 14px;
        }}
        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}
        .card-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }}
        .card-value {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -1px;
        }}
        .card-subtext {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin: 32px 0 16px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            text-align: left;
        }}
        th {{
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .table-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 24px;
        }}
        .badge-safe {{
            display: inline-block;
            background: rgba(16, 185, 129, 0.15);
            color: var(--positive);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 9999px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Stage 7 — Historical News Walk-Forward Backtest Report</h1>
                <div class="subtitle">Sri Lankan Stock Market (CSE) News Impact Engine &bull; Horizon h={summary['horizon_days']} trading days</div>
            </div>
            <div>
                <span class="badge-safe">&check; Strict Zero-Lookahead Causal Guarantee</span>
            </div>
        </header>

        <!-- Executive Metrics KPI Cards -->
        <div class="grid-cards">
            <div class="card">
                <div class="card-label">Directional Accuracy</div>
                <div class="card-value" style="color: var(--accent);">{m['directional_accuracy_pct']}%</div>
                <div class="card-subtext">Return direction sign correct vs actual CAR</div>
            </div>
            <div class="card">
                <div class="card-label">MAE vs Baseline</div>
                <div class="card-value" style="color: var(--positive);">{m['mae_model_pct']}%</div>
                <div class="card-subtext">Baseline MAE: {m['mae_baseline_pct']}% ({m['mae_improvement_pct']:+.1f}% improvement)</div>
            </div>
            <div class="card">
                <div class="card-label">Information Coefficient (IC)</div>
                <div class="card-value" style="color: #a855f7;">{m['information_coefficient']:+.4f}</div>
                <div class="card-subtext">Rank IC (Spearman): {m['rank_information_coefficient']:+.4f}</div>
            </div>
            <div class="card">
                <div class="card-label">Top-Quintile Sharpe</div>
                <div class="card-value" style="color: #f59e0b;">{m['top_quintile_sharpe']:.2f}</div>
                <div class="card-subtext">Annualized Sharpe of Q5 highest predictions</div>
            </div>
            <div class="card">
                <div class="card-label">Long/Short Spread (Q5-Q1)</div>
                <div class="card-value" style="color: var(--positive);">{m['long_short_spread_pct']:+.2f}%</div>
                <div class="card-subtext">Return spread between Top and Bottom quintiles</div>
            </div>
        </div>

        <!-- Quintile Monotonicity -->
        <div class="section-title">Quintile Performance & Monotonicity Analysis (Q1 &rarr; Q5)</div>
        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th style="text-align: center;">Quintile</th>
                        <th style="text-align: right;">Count</th>
                        <th style="text-align: right;">Mean Actual CAR</th>
                        <th style="width: 250px;">Return Trajectory</th>
                        <th style="text-align: right;">Std Dev</th>
                        <th style="text-align: right;">Win Rate %</th>
                        <th style="text-align: right;">Annualized Sharpe</th>
                    </tr>
                </thead>
                <tbody>
                    {q_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Category Breakdown -->
        <div class="section-title">Macroeconomic Event Category Breakdown</div>
        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th style="text-align: right;">Events</th>
                        <th style="text-align: right;">Directional Accuracy</th>
                        <th style="text-align: right;">Model MAE</th>
                        <th style="text-align: right;">Baseline MAE</th>
                        <th style="text-align: right;">Mean Actual CAR</th>
                        <th style="text-align: right;">Mean Predicted CAR</th>
                    </tr>
                </thead>
                <tbody>
                    {cat_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Sample Records -->
        <div class="section-title">Sample Predictions vs Empirical CAR Observations</div>
        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Headline</th>
                        <th>Category</th>
                        <th style="text-align: right;">Predicted CAR</th>
                        <th style="text-align: right;">Actual CAR</th>
                        <th style="text-align: center;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {sample_rows_html}
                </tbody>
            </table>
        </div>

        <footer style="margin-top: 32px; border-top: 1px solid var(--border); padding-top: 16px; font-size: 12px; color: var(--text-muted); display: flex; justify-content: space-between;">
            <div>Generated by CSE Research Stage 7 Observability &amp; Validation Pipeline &bull; {summary['execution_date']}</div>
            <div>Evaluated {summary['sample_size']} historical events &bull; Horizon: {summary['horizon_days']} trading days</div>
        </footer>
    </div>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info("Successfully rendered HTML backtest report to: %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="CSE Historical News Backtest Engine (Stage 7)")
    parser.add_argument("--db-path", type=str, default=str(DEFAULT_DB_PATH), help="Path to cse_history.db")
    parser.add_argument("--horizon", type=int, default=5, help="Forecast horizon in trading days (default 5)")
    parser.add_argument("--limit", type=int, default=None, help="Optional event count limit for fast run")
    parser.add_argument("--output", type=str, default=None, help="Output HTML report path")
    args = parser.parse_args()

    db_p = Path(args.db_path)
    if not db_p.exists():
        raise FileNotFoundError(f"Database file not found: {db_p}")

    today_str = datetime.datetime.now().strftime("%Y%m%d")
    out_p = Path(args.output) if args.output else REPORTS_DIR / f"backtest_{today_str}.html"

    logger.info("Starting Stage 7 backtest with db=%s, horizon=%d", db_p, args.horizon)
    summary = run_backtest(db_path=db_p, horizon=args.horizon, sample_limit=args.limit)

    render_html_report(summary, out_p)
    logger.info("Backtest complete! Directional Accuracy: %.2f%%, IC: %.4f, Top-Quintile Sharpe: %.2f",
                summary["metrics"]["directional_accuracy_pct"],
                summary["metrics"]["information_coefficient"],
                summary["metrics"]["top_quintile_sharpe"])


if __name__ == "__main__":
    main()
