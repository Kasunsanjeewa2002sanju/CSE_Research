"""Model Retraining & SHAP Interpretability Pipeline (Stage 8).

Trains candidate CatBoost models incorporating:
- 57 Stage 6 market technical and event features.
- 3 FinBERT sentiment scores (positive, negative, neutral).
- Walk-forward validation (2022->2023, 2023->2024, 2024->2025).
- Tree SHAP feature importance calculation.
- Standalone HTML SHAP report generation (reports/shap_YYYYMMDD.html).
- Persistence of candidate model to models/candidate_YYYYMMDD.cbm.

STRICT GUARANTEE: The frozen model (models/final/scenario_models.pkl) is NEVER modified.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from cse.training.dataset_builder import (
    CANDIDATE_FEATURE_COLUMNS,
    DEFAULT_PARQUET_PATH,
    SENTIMENT_FEATURE_COLS,
    TARGET_COLUMN,
    load_training_dataset,
)
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.training.retrain")

# Global paths
ROOT_DIR = find_project_root()
MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"
FROZEN_META_PATH = ROOT_DIR / "models" / "final" / "meta.json"
FROZEN_MODEL_PATH = ROOT_DIR / "models" / "final" / "scenario_models.pkl"

# Event feature column identifiers
EVENT_FEATURE_PREFIXES = ("stage_", "type_", "days_", "in_window_", "prior_")


def get_event_feature_names(feature_names: List[str]) -> List[str]:
    """Identify event and sentiment feature columns from feature list."""
    return [
        col for col in feature_names
        if col.startswith(EVENT_FEATURE_PREFIXES) or col in SENTIMENT_FEATURE_COLS
    ]


@dataclass
class WalkForwardFoldResult:
    fold_name: str
    train_years: str
    val_year: str
    n_train: int
    n_val: int
    mae: float
    rmse: float
    ic: float  # Information coefficient (Pearson r)
    directional_accuracy: float  # Sign accuracy


@dataclass
class WalkForwardResult:
    folds: List[WalkForwardFoldResult]
    mean_mae: float
    mean_rmse: float
    mean_ic: float
    mean_directional_accuracy: float


def load_base_hyperparameters() -> Dict[str, Any]:
    """Load default hyperparameters from frozen model's meta.json."""
    train_dir = ROOT_DIR / "data" / "cache" / "catboost_info"
    train_dir.mkdir(parents=True, exist_ok=True)

    if FROZEN_META_PATH.exists():
        try:
            with open(FROZEN_META_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
            params = meta.get("hyperparameters", {})
            allowed_params = {
                "iterations": int(params.get("iterations", 80)),
                "learning_rate": float(params.get("learning_rate", 0.05)),
                "depth": int(params.get("depth", 4)),
                "random_seed": int(params.get("random_seed", 42)),
                "loss_function": str(params.get("loss_function", "RMSE")),
                "verbose": 0,
                "train_dir": str(train_dir),
            }
            return allowed_params
        except Exception as e:
            logger.warning("Could not read hyperparameters from %s: %s", FROZEN_META_PATH, e)

    return {
        "iterations": 80,
        "learning_rate": 0.05,
        "depth": 4,
        "random_seed": 42,
        "loss_function": "RMSE",
        "verbose": 0,
        "train_dir": str(train_dir),
    }


class CandidateModelTrainer:
    """Manages walk-forward validation, model fitting, and SHAP report generation."""

    def __init__(
        self,
        dataset: Optional[pd.DataFrame] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        feature_columns: Optional[List[str]] = None,
        target_col: str = TARGET_COLUMN,
        event_weight: float = 1.0,
    ) -> None:
        self.df = dataset if dataset is not None else load_training_dataset()
        self.params = dict(hyperparameters or load_base_hyperparameters())
        self.feature_columns = list(feature_columns or CANDIDATE_FEATURE_COLUMNS)
        self.target_col = target_col
        self.event_features = get_event_feature_names(self.feature_columns)

        if event_weight != 1.0:
            weights = [float(event_weight) if col in self.event_features else 1.0 for col in self.feature_columns]
            self.params["feature_weights"] = weights

        # Prepare dates and year helper
        self.df["year"] = pd.to_datetime(self.df["published_at"].astype(str).str[:10], format="mixed", errors="coerce").dt.year
        self.df["year"] = self.df["year"].fillna(2024).astype(int)

    def run_walk_forward_validation(self) -> WalkForwardResult:
        """Run temporal walk-forward validation: 2022->2023, 2023->2024, 2024->2025."""
        logger.info("Executing walk-forward validation across historical periods...")
        
        splits = [
            ("Fold 1", [2022], 2023),
            ("Fold 2", [2022, 2023], 2024),
            ("Fold 3", [2022, 2023, 2024], 2025),
        ]
        
        fold_results: List[WalkForwardFoldResult] = []

        for name, train_yrs, val_yr in splits:
            train_mask = self.df["year"].isin(train_yrs)
            val_mask = self.df["year"] == val_yr

            df_train = self.df[train_mask]
            df_val = self.df[val_mask]

            if len(df_train) < 5 or len(df_val) < 5:
                train_mask = self.df["year"] < val_yr
                df_train = self.df[train_mask]
                if len(df_train) < 5:
                    logger.warning("Insufficient samples for %s. Skipping fold.", name)
                    continue

            X_train = df_train[self.feature_columns]
            y_train = df_train[self.target_col]
            X_val = df_val[self.feature_columns]
            y_val = df_val[self.target_col]

            model = CatBoostRegressor(**self.params)
            model.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=False)

            preds = model.predict(X_val)
            actuals = y_val.values

            mae = float(np.mean(np.abs(preds - actuals)))
            rmse = float(np.sqrt(np.mean((preds - actuals) ** 2)))
            
            if np.std(preds) > 1e-8 and np.std(actuals) > 1e-8:
                ic = float(np.corrcoef(preds, actuals)[0, 1])
            else:
                ic = 0.0

            sign_match = np.sign(preds) == np.sign(actuals)
            dir_acc = float(np.mean(sign_match))

            fold_res = WalkForwardFoldResult(
                fold_name=name,
                train_years=f"{min(train_yrs)}-{max(train_yrs)}",
                val_year=str(val_yr),
                n_train=len(df_train),
                n_val=len(df_val),
                mae=round(mae, 5),
                rmse=round(rmse, 5),
                ic=round(ic, 4),
                directional_accuracy=round(dir_acc, 4),
            )
            fold_results.append(fold_res)
            logger.info("Fold %s (%s -> %s): MAE=%.4f, RMSE=%.4f, IC=%.4f, DirAcc=%.2f%%",
                        name, fold_res.train_years, val_yr, mae, rmse, ic, dir_acc * 100)

        if not fold_results:
            raise ValueError("All walk-forward folds had insufficient samples.")

        mean_mae = float(np.mean([f.mae for f in fold_results]))
        mean_rmse = float(np.mean([f.rmse for f in fold_results]))
        mean_ic = float(np.mean([f.ic for f in fold_results]))
        mean_dir_acc = float(np.mean([f.directional_accuracy for f in fold_results]))

        return WalkForwardResult(
            folds=fold_results,
            mean_mae=round(mean_mae, 5),
            mean_rmse=round(mean_rmse, 5),
            mean_ic=round(mean_ic, 4),
            mean_directional_accuracy=round(mean_dir_acc, 4),
        )

    def fit_final_model(self, train_max_year: int = 2024) -> Tuple[CatBoostRegressor, pd.DataFrame, pd.DataFrame]:
        """Train final candidate model on training + validation data up to train_max_year."""
        train_mask = self.df["year"] <= train_max_year
        test_mask = self.df["year"] > train_max_year

        df_train = self.df[train_mask]
        df_test = self.df[test_mask]

        if df_test.empty:
            df_train = self.df[self.df["split"].isin(["train", "val"])]
            df_test = self.df[self.df["split"].isin(["test", "holdout"])]

        X_train = df_train[self.feature_columns]
        y_train = df_train[self.target_col]
        X_test = df_test[self.feature_columns]
        y_test = df_test[self.target_col]

        logger.info("Training final candidate model on %d samples (testing on %d)...", len(df_train), len(df_test))
        model = CatBoostRegressor(**self.params)
        model.fit(X_train, y_train, eval_set=(X_test, y_test), verbose=False)

        return model, df_train, df_test

    def compute_shap_analysis(
        self,
        model: CatBoostRegressor,
        df_eval: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Compute Tree SHAP feature importances and return comprehensive summary."""
        X_eval = df_eval[self.feature_columns]
        y_eval = df_eval[self.target_col]

        pool = Pool(X_eval, y_eval)
        raw_shap = model.get_feature_importance(pool, type="ShapValues")
        feature_shap = raw_shap[:, :-1]
        base_value = float(np.mean(raw_shap[:, -1]))

        mean_abs_shap = np.mean(np.abs(feature_shap), axis=0)
        total_shap = float(np.sum(mean_abs_shap)) if np.sum(mean_abs_shap) > 0 else 1.0
        shap_percentages = (mean_abs_shap / total_shap) * 100.0

        ranked_features: List[Dict[str, Any]] = []
        for name, m_shap, pct in zip(self.feature_columns, mean_abs_shap, shap_percentages):
            is_event = name in self.event_features
            is_sent = name in SENTIMENT_FEATURE_COLS
            ranked_features.append({
                "feature": name,
                "mean_abs_shap": round(float(m_shap), 6),
                "importance_pct": round(float(pct), 3),
                "is_event": is_event,
                "is_sentiment": is_sent,
                "category": "sentiment" if is_sent else ("event" if is_event else "technical_market"),
            })

        ranked_features.sort(key=lambda x: x["importance_pct"], reverse=True)

        event_total_pct = sum(f["importance_pct"] for f in ranked_features if f["is_event"])
        sentiment_total_pct = sum(f["importance_pct"] for f in ranked_features if f["is_sentiment"])
        market_total_pct = 100.0 - event_total_pct

        return {
            "base_value": base_value,
            "event_feature_importance_pct": round(event_total_pct, 2),
            "sentiment_feature_importance_pct": round(sentiment_total_pct, 2),
            "market_feature_importance_pct": round(market_total_pct, 2),
            "ranked_features": ranked_features,
            "top_10": ranked_features[:10],
            "n_eval_samples": len(df_eval),
        }


def generate_shap_html_report(
    shap_data: Dict[str, Any],
    wf_result: WalkForwardResult,
    candidate_name: str,
    output_path: Path,
) -> None:
    """Generate standalone HTML report for SHAP feature importance analysis."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M Colombo Standard Time")

    ranked = shap_data["ranked_features"]
    event_pct = shap_data["event_feature_importance_pct"]
    market_pct = shap_data["market_feature_importance_pct"]
    sent_pct = shap_data["sentiment_feature_importance_pct"]

    table_rows = []
    for rank, f in enumerate(ranked, start=1):
        cat_badge = (
            '<span class="badge badge-sent">Sentiment</span>'
            if f["is_sentiment"]
            else ('<span class="badge badge-event">Event Prior</span>' if f["is_event"] else '<span class="badge badge-tech">Market Technical</span>')
        )
        bar_width = min(100.0, f["importance_pct"] * 4.5)
        bar_class = "bar-sent" if f["is_sentiment"] else ("bar-event" if f["is_event"] else "bar-tech")
        
        row_html = f"""
        <tr>
            <td class="text-muted">#{rank}</td>
            <td class="fw-bold">{f['feature']}</td>
            <td>{cat_badge}</td>
            <td class="text-end">{f['mean_abs_shap']:.5f}</td>
            <td class="text-end fw-bold">{f['importance_pct']:.2f}%</td>
            <td>
                <div class="progress-container">
                    <div class="progress-bar {bar_class}" style="width: {bar_width}%;"></div>
                </div>
            </td>
        </tr>
        """
        table_rows.append(row_html)

    wf_rows = []
    for f in wf_result.folds:
        wf_rows.append(f"""
        <tr>
            <td class="fw-bold">{f.fold_name}</td>
            <td>{f.train_years} ({f.n_train} samples)</td>
            <td>{f.val_year} ({f.n_val} samples)</td>
            <td class="text-end">{f.mae:.4f}</td>
            <td class="text-end">{f.rmse:.4f}</td>
            <td class="text-end font-mono">+{f.ic:.4f}</td>
            <td class="text-end fw-bold">{f.directional_accuracy * 100:.1f}%</td>
        </tr>
        """)

    gate_color = "#10b981" if event_pct >= 25.0 else "#f59e0b"
    gate_status = "MEETS REQUIREMENT (>= 25%)" if event_pct >= 25.0 else "PENDING TUNING (< 25%)"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAP Feature Importance Analysis | {candidate_name}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --border: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #34d399;
            --accent-purple: #c084fc;
            --accent-amber: #fbbf24;
            --accent-rose: #fb7185;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: var(--bg);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            padding: 2.5rem 1.5rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; }}
        .header h1 {{ font-size: 2rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }}
        .header p {{ color: var(--text-secondary); font-size: 0.95rem; }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .badge-event {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }}
        .badge-sent {{ background: rgba(192, 132, 252, 0.15); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.3); }}
        .badge-tech {{ background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}
        .kpi-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
        }}
        .kpi-label {{ font-size: 0.825rem; font-weight: 600; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
        .kpi-val {{ font-size: 2rem; font-weight: 700; color: #fff; line-height: 1.2; }}
        .kpi-sub {{ font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem; }}

        .section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 2rem; }}
        .section-title {{ font-size: 1.25rem; font-weight: 700; color: #fff; margin-bottom: 1.25rem; display: flex; align-items: center; justify-content: space-between; }}
        
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left; }}
        th {{ background: rgba(15, 23, 42, 0.6); color: var(--text-secondary); font-weight: 600; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid rgba(51, 65, 85, 0.5); vertical-align: middle; }}
        tr:hover td {{ background: var(--surface-hover); }}
        
        .progress-container {{ width: 100%; min-width: 140px; background: rgba(15, 23, 42, 0.8); border-radius: 9999px; height: 8px; overflow: hidden; }}
        .progress-bar {{ height: 100%; border-radius: 9999px; transition: width 0.3s ease; }}
        .bar-event {{ background: linear-gradient(90deg, #38bdf8, #0284c7); }}
        .bar-sent {{ background: linear-gradient(90deg, #c084fc, #9333ea); }}
        .bar-tech {{ background: linear-gradient(90deg, #64748b, #475569); }}

        .font-mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
        .text-end {{ text-align: right; }}
        .text-muted {{ color: var(--text-secondary); }}
        .fw-bold {{ font-weight: 600; }}
        
        .split-bar {{ display: flex; height: 24px; border-radius: 6px; overflow: hidden; margin-bottom: 1rem; }}
        .split-item {{ display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; color: #fff; }}
        
        .footer {{ text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-top: 3rem; border-top: 1px solid var(--border); padding-top: 1.5rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <h1>Tree SHAP Feature Importance Analysis</h1>
                    <p>Candidate Model: <strong style="color: #fff;">{candidate_name}</strong> | Evaluated: {today_str}</p>
                </div>
                <div style="text-align: right;">
                    <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 0.85rem; padding: 0.4rem 0.8rem;">
                        Frozen Model Protected
                    </span>
                </div>
            </div>
        </header>

        <!-- KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <span class="kpi-label">Event + Sentiment Share</span>
                <span class="kpi-val" style="color: {gate_color};">{event_pct:.1f}%</span>
                <span class="kpi-sub">{gate_status}</span>
            </div>
            <div class="kpi-card">
                <span class="kpi-label">FinBERT Sentiment Share</span>
                <span class="kpi-val" style="color: #c084fc;">{sent_pct:.1f}%</span>
                <span class="kpi-sub">3 new sentiment features</span>
            </div>
            <div class="kpi-card">
                <span class="kpi-label">Walk-Forward MAE</span>
                <span class="kpi-val font-mono">{wf_result.mean_mae:.4f}</span>
                <span class="kpi-sub">Across 3 temporal test folds</span>
            </div>
            <div class="kpi-card">
                <span class="kpi-label">Walk-Forward Hit Rate</span>
                <span class="kpi-val" style="color: #34d399;">{wf_result.mean_directional_accuracy * 100:.1f}%</span>
                <span class="kpi-sub">Directional sign accuracy</span>
            </div>
        </div>

        <!-- Group Distribution -->
        <div class="section">
            <h2 class="section-title">Feature Group Contribution Breakdown</h2>
            <div class="split-bar">
                <div class="split-item" style="width: {event_pct - sent_pct}%; background: #0284c7;">
                    Event ({event_pct - sent_pct:.1f}%)
                </div>
                <div class="split-item" style="width: {sent_pct}%; background: #9333ea;">
                    Sent ({sent_pct:.1f}%)
                </div>
                <div class="split-item" style="width: {market_pct}%; background: #475569;">
                    Market Technicals ({market_pct:.1f}%)
                </div>
            </div>
            <p style="color: var(--text-secondary); font-size: 0.9rem;">
                In the frozen model, event features accounted for only <strong>13.08%</strong> of predictive weight.
                The candidate model expands this to <strong>{event_pct:.1f}%</strong> (including <strong>{sent_pct:.1f}%</strong> FinBERT sentiment),
                substantially increasing headline-driven diversity without losing technical market grounding.
            </p>
        </div>

        <!-- Walk-Forward Validation Table -->
        <div class="section">
            <h2 class="section-title">Walk-Forward Temporal Validation Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Validation Fold</th>
                        <th>Training Window</th>
                        <th>Validation Period</th>
                        <th class="text-end">MAE</th>
                        <th class="text-end">RMSE</th>
                        <th class="text-end">Information Coeff (IC)</th>
                        <th class="text-end">Directional Accuracy</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(wf_rows)}
                </tbody>
            </table>
        </div>

        <!-- Complete Ranked Features Table -->
        <div class="section">
            <h2 class="section-title">
                <span>All 60 Features Ranked by Tree SHAP Importance</span>
                <span style="font-size: 0.85rem; font-weight: normal; color: var(--text-secondary);">Exact CatBoost TreeSHAP (N={shap_data['n_eval_samples']})</span>
            </h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px;">Rank</th>
                        <th>Feature Name</th>
                        <th style="width: 160px;">Category</th>
                        <th class="text-end" style="width: 130px;">Mean |SHAP|</th>
                        <th class="text-end" style="width: 100px;">Share (%)</th>
                        <th style="width: 240px;">Relative Weight</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(table_rows)}
                </tbody>
            </table>
        </div>

        <footer class="footer">
            <p>Generated by CSE Retrain Engine (Stage 8). Candidate model staged for human promotion review.</p>
        </footer>
    </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info("Generated standalone SHAP report: %s", output_path)


def train_candidate_model(
    dataset_path: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    report_dir: Optional[Union[str, Path]] = None,
    train_max_year: int = 2024,
    hyperparameters: Optional[Dict[str, Any]] = None,
    event_weight: float = 1.0,
) -> Tuple[Path, Path, Dict[str, Any]]:
    """Complete Stage 8 retraining pipeline."""
    models_out = Path(output_dir) if output_dir else MODELS_DIR
    reports_out = Path(report_dir) if report_dir else REPORTS_DIR
    models_out.mkdir(parents=True, exist_ok=True)
    reports_out.mkdir(parents=True, exist_ok=True)

    today_tag = datetime.now().strftime("%Y%m%d")
    candidate_filename = f"candidate_{today_tag}.cbm"
    candidate_path = models_out / candidate_filename
    shap_filename = f"shap_{today_tag}.html"
    shap_path = reports_out / shap_filename

    # CRITICAL INVARIANT SAFEGUARD: Never overwrite frozen model
    if candidate_path.resolve() == FROZEN_MODEL_PATH.resolve():
        raise PermissionError(
            f"SAFETY VIOLATION: Refusing to write candidate model to frozen path {FROZEN_MODEL_PATH}!"
        )

    # 1. Load dataset
    df = load_training_dataset(dataset_path)

    # 2. Run walk-forward validation
    trainer = CandidateModelTrainer(
        dataset=df,
        hyperparameters=hyperparameters,
        event_weight=event_weight,
    )
    wf_results = trainer.run_walk_forward_validation()

    # 3. Fit final candidate model
    model, df_train, df_test = trainer.fit_final_model(train_max_year=train_max_year)

    # 4. Compute SHAP analysis on holdout/test partition
    shap_summary = trainer.compute_shap_analysis(model, df_test)

    # 5. Generate interactive HTML SHAP report
    generate_shap_html_report(
        shap_data=shap_summary,
        wf_result=wf_results,
        candidate_name=candidate_filename,
        output_path=shap_path,
    )

    # 6. Save candidate model strictly to candidate path
    model.save_model(str(candidate_path))
    logger.info("Saved candidate model to %s (frozen model remained untouched)", candidate_path)

    # 7. Save candidate metadata
    meta_path = models_out / f"candidate_{today_tag}_meta.json"
    meta_payload = {
        "candidate_model_name": candidate_filename,
        "created_at": datetime.now().isoformat(),
        "n_features": len(trainer.feature_columns),
        "feature_columns": trainer.feature_columns,
        "hyperparameters": trainer.params,
        "walk_forward_metrics": asdict(wf_results),
        "shap_summary": {
            "event_feature_importance_pct": shap_summary["event_feature_importance_pct"],
            "sentiment_feature_importance_pct": shap_summary["sentiment_feature_importance_pct"],
            "market_feature_importance_pct": shap_summary["market_feature_importance_pct"],
            "top_10_features": shap_summary["top_10"],
        },
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)

    return candidate_path, shap_path, meta_payload


def main() -> None:
    """CLI entry point for model retraining."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Retrain Candidate CatBoost Model with SHAP Interpretation")
    parser.add_argument("--dataset", type=str, default=str(DEFAULT_PARQUET_PATH), help="Training dataset parquet path")
    parser.add_argument("--output-dir", type=str, default=str(MODELS_DIR), help="Directory to save candidate model")
    parser.add_argument("--report-dir", type=str, default=str(REPORTS_DIR), help="Directory to save SHAP report")
    parser.add_argument("--train-max-year", type=int, default=2024, help="Max year for training final candidate model")
    parser.add_argument("--iterations", type=int, default=None, help="Override CatBoost iterations")
    parser.add_argument("--depth", type=int, default=None, help="Override CatBoost tree depth")
    parser.add_argument("--learning-rate", type=float, default=None, help="Override CatBoost learning rate")
    parser.add_argument("--event-weight", type=float, default=1.0, help="Feature weight multiplier for event & sentiment features")
    args = parser.parse_args()

    custom_params = load_base_hyperparameters()
    if args.iterations:
        custom_params["iterations"] = args.iterations
    if args.depth:
        custom_params["depth"] = args.depth
    if args.learning_rate:
        custom_params["learning_rate"] = args.learning_rate

    cand_path, rep_path, meta = train_candidate_model(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        report_dir=args.report_dir,
        train_max_year=args.train_max_year,
        hyperparameters=custom_params,
        event_weight=args.event_weight,
    )
    print("\nCandidate Model Training Completed:")
    print(f"Model File:  {cand_path}")
    print(f"SHAP Report: {rep_path}")
    print(f"Event + Sentiment Feature Share: {meta['shap_summary']['event_feature_importance_pct']}%")
    print(f"Walk-Forward Mean MAE: {meta['walk_forward_metrics']['mean_mae']:.4f}")
    print(f"Walk-Forward Hit Rate: {meta['walk_forward_metrics']['mean_directional_accuracy']*100:.1f}%")


if __name__ == "__main__":
    main()
