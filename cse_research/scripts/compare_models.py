"""Model Promotion Gate & Comparative Analysis Script (Stage 8).

Compares the frozen production model against a candidate retrained model on holdout data:
- Frozen Model: models/final/scenario_models.pkl (Horizon 5 CatBoostRegressor, 57 features).
- Candidate Model: models/candidate_YYYYMMDD.cbm (Retrained CatBoostRegressor, 60 features).

Promotion Gate Criteria (Strict):
1. Candidate beats Frozen Model by > 5.0% MAE:
   Delta MAE % = (MAE_frozen - MAE_candidate) / MAE_frozen * 100 > 5.0%
2. Event Feature Importance in Candidate > 25.0%:
   Sum of importances for stage_*, type_*, days_*, in_window_*, prior_*, and sentiment_* > 25.0%

STRICT SAFETY: The frozen model is NEVER overwritten. Human decides whether to promote.
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure 'src' is in sys.path before resolving cse modules
_SCRIPTS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPTS_DIR.parent if _SCRIPTS_DIR.name == "scripts" else _SCRIPTS_DIR
_SRC_DIR = _PROJECT_ROOT / "src"

for _p in [str(_SRC_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from cse.training.dataset_builder import (
    CANDIDATE_FEATURE_COLUMNS,
    DEFAULT_PARQUET_PATH,
    SENTIMENT_FEATURE_COLS,
    TARGET_COLUMN,
    load_training_dataset,
)
from cse.utils.config import find_project_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cse.scripts.compare_models")

ROOT_DIR = find_project_root()
FROZEN_MODEL_PATH = ROOT_DIR / "models" / "final" / "scenario_models.pkl"
FROZEN_COLS_PATH = ROOT_DIR / "models" / "final" / "feature_columns.json"
MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"

EVENT_FEATURE_PREFIXES = ("stage_", "type_", "days_", "in_window_", "prior_")


def find_latest_candidate_model() -> Optional[Path]:
    """Find the most recent candidate model matching models/candidate_*.cbm."""
    pattern = str(MODELS_DIR / "candidate_*.cbm")
    matches = glob.glob(pattern)
    if not matches:
        return None
    matches.sort(reverse=True)
    return Path(matches[0])


def load_frozen_model(horizon: int = 5) -> Tuple[CatBoostRegressor, List[str]]:
    """Load the frozen production model and feature column definitions."""
    if not FROZEN_MODEL_PATH.exists():
        raise FileNotFoundError(f"Frozen model not found at {FROZEN_MODEL_PATH}")

    with open(FROZEN_MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    if horizon not in bundle:
        raise KeyError(f"Horizon {horizon} not found in frozen model bundle.")

    regressor = bundle[horizon]["regressor"]

    with open(FROZEN_COLS_PATH, "r", encoding="utf-8") as f:
        feature_cols: List[str] = json.load(f)

    return regressor, feature_cols


def load_candidate_model(path: Path) -> Tuple[CatBoostRegressor, List[str]]:
    """Load the candidate model and its feature columns."""
    if not path.exists():
        raise FileNotFoundError(f"Candidate model not found at {path}")

    model = CatBoostRegressor()
    model.load_model(str(path))

    # Look for candidate meta file
    meta_path = path.parent / f"{path.stem}_meta.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            feature_cols = meta.get("feature_columns", CANDIDATE_FEATURE_COLUMNS)
        except Exception:
            feature_cols = CANDIDATE_FEATURE_COLUMNS
    else:
        feature_cols = CANDIDATE_FEATURE_COLUMNS

    return model, feature_cols


def compute_event_importance_share(model: CatBoostRegressor, feature_names: List[str]) -> Tuple[float, List[Tuple[str, float]]]:
    """Calculate the percentage of total model feature importance attributed to event and sentiment features."""
    importances = model.get_feature_importance()
    total_imp = float(np.sum(importances)) if np.sum(importances) > 0 else 1.0

    ranked = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    
    event_imp = 0.0
    for name, imp in zip(feature_names, importances):
        if name.startswith(EVENT_FEATURE_PREFIXES) or name in SENTIMENT_FEATURE_COLS:
            event_imp += float(imp)

    event_share_pct = (event_imp / total_imp) * 100.0
    return round(event_share_pct, 2), ranked


def compare_models(
    candidate_path: Optional[Path] = None,
    dataset_path: Optional[Path] = None,
    split: str = "test",
    horizon: int = 5,
    report_output: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run comparative evaluation between frozen model and candidate model.
    
    Parameters
    ----------
    candidate_path : Optional[Path]
        Path to candidate_YYYYMMDD.cbm. If None, auto-selects latest.
    dataset_path : Optional[Path]
        Path to data/training_data.parquet.
    split : str
        Dataset split to evaluate on ('test', 'holdout', 'val', or comma-separated).
    horizon : int
        CAR horizon (default 5).
    report_output : Optional[Path]
        Destination for markdown decision report.

    Returns
    -------
    Dict[str, Any]
        Comparison metrics, gate checks, and promotion recommendation.
    """
    cand_p = candidate_path or find_latest_candidate_model()
    if cand_p is None:
        raise FileNotFoundError("No candidate model found in models/. Run src.cse.training.retrain first.")

    # 1. Load models
    frozen_reg, frozen_cols = load_frozen_model(horizon=horizon)
    cand_reg, cand_cols = load_candidate_model(cand_p)

    # 2. Load evaluation dataset
    df_all = load_training_dataset(dataset_path)
    
    # Filter by split
    requested_splits = [s.strip().lower() for s in split.split(",")]
    if "all" in requested_splits:
        df_eval = df_all.copy()
    else:
        df_eval = df_all[df_all["split"].str.lower().isin(requested_splits)].copy()

    if df_eval.empty:
        df_eval = df_all[df_all["split"].isin(["test", "holdout"])].copy()
        if df_eval.empty:
            df_eval = df_all.iloc[-100:].copy()

    logger.info("Evaluating models on %d samples (split: %s)...", len(df_eval), split)

    # 3. Features & Predictions
    X_frozen = df_eval[frozen_cols].fillna(0.0)
    X_cand = df_eval[cand_cols].fillna(0.0)
    y_actual = df_eval[TARGET_COLUMN].values

    preds_frozen = frozen_reg.predict(X_frozen)
    preds_cand = cand_reg.predict(X_cand)

    # 4. Accuracy & Error Metrics
    frozen_mae = float(np.mean(np.abs(preds_frozen - y_actual)))
    cand_mae = float(np.mean(np.abs(preds_cand - y_actual)))
    mae_diff = frozen_mae - cand_mae
    mae_reduction_pct = (mae_diff / frozen_mae) * 100.0 if frozen_mae > 0 else 0.0

    frozen_rmse = float(np.sqrt(np.mean((preds_frozen - y_actual) ** 2)))
    cand_rmse = float(np.sqrt(np.mean((preds_cand - y_actual) ** 2)))

    # Correlation (IC)
    frozen_ic = float(np.corrcoef(preds_frozen, y_actual)[0, 1]) if np.std(preds_frozen) > 1e-8 else 0.0
    cand_ic = float(np.corrcoef(preds_cand, y_actual)[0, 1]) if np.std(preds_cand) > 1e-8 else 0.0

    # Directional accuracy
    frozen_dir_acc = float(np.mean(np.sign(preds_frozen) == np.sign(y_actual))) * 100.0
    cand_dir_acc = float(np.mean(np.sign(preds_cand) == np.sign(y_actual))) * 100.0

    # Prediction standard deviation (diversity measure)
    frozen_pred_std = float(np.std(preds_frozen))
    cand_pred_std = float(np.std(preds_cand))
    diversity_gain_pct = ((cand_pred_std - frozen_pred_std) / frozen_pred_std) * 100.0 if frozen_pred_std > 0 else 0.0

    # 5. Feature Importance Analysis
    frozen_event_share, frozen_ranked = compute_event_importance_share(frozen_reg, frozen_cols)
    cand_event_share, cand_ranked = compute_event_importance_share(cand_reg, cand_cols)

    cand_imp_dict = dict(cand_ranked)
    sent_imp_total = sum(cand_imp_dict.get(col, 0.0) for col in SENTIMENT_FEATURE_COLS)

    # 6. Promotion Gate Evaluation
    gate_1_passed = mae_reduction_pct > 5.0
    gate_2_passed = cand_event_share > 25.0

    overall_promotable = gate_1_passed and gate_2_passed

    if overall_promotable:
        decision_label = "PROMOTION RECOMMENDED"
        decision_summary = (
            f"Candidate model successfully beats frozen model by {mae_reduction_pct:.2f}% MAE "
            f"(requirement: >5.0%) and achieves {cand_event_share:.2f}% event+sentiment importance "
            f"(requirement: >25.0%)."
        )
    else:
        decision_label = "DO NOT PROMOTE (STAGING ONLY)"
        failed_reasons = []
        if not gate_1_passed:
            failed_reasons.append(f"MAE reduction was {mae_reduction_pct:.2f}% (required: >5.0%)")
        if not gate_2_passed:
            failed_reasons.append(f"Event feature importance was {cand_event_share:.2f}% (required: >25.0%)")
        decision_summary = "Candidate model did not satisfy all promotion gates: " + "; ".join(failed_reasons) + "."

    report_data: Dict[str, Any] = {
        "candidate_model_path": str(cand_p),
        "frozen_model_path": str(FROZEN_MODEL_PATH),
        "evaluated_split": split,
        "n_samples": len(df_eval),
        "evaluation_timestamp": datetime.now().isoformat(),
        "metrics": {
            "frozen_mae": round(frozen_mae, 5),
            "candidate_mae": round(cand_mae, 5),
            "mae_reduction_pct": round(mae_reduction_pct, 2),
            "frozen_rmse": round(frozen_rmse, 5),
            "candidate_rmse": round(cand_rmse, 5),
            "frozen_ic": round(frozen_ic, 4),
            "candidate_ic": round(cand_ic, 4),
            "frozen_directional_acc": round(frozen_dir_acc, 2),
            "candidate_directional_acc": round(cand_dir_acc, 2),
            "frozen_pred_std": round(frozen_pred_std, 5),
            "candidate_pred_std": round(cand_pred_std, 5),
            "diversity_gain_pct": round(diversity_gain_pct, 2),
        },
        "gates": {
            "mae_beat_5pct": {
                "threshold": 5.0,
                "actual": round(mae_reduction_pct, 2),
                "passed": gate_1_passed,
            },
            "event_importance_25pct": {
                "threshold": 25.0,
                "actual": round(cand_event_share, 2),
                "passed": gate_2_passed,
            },
            "overall_promotion_decision": decision_label,
            "decision_summary": decision_summary,
        },
        "feature_importance": {
            "frozen_event_share_pct": frozen_event_share,
            "candidate_event_share_pct": cand_event_share,
            "candidate_sentiment_share_pct": round(sent_imp_total, 2),
            "candidate_top_10": cand_ranked[:10],
            "frozen_top_10": frozen_ranked[:10],
        },
    }

    # Generate Markdown Report
    rep_path = report_output or (REPORTS_DIR / f"model_comparison_{datetime.now().strftime('%Y%m%d')}.md")
    write_comparison_markdown_report(report_data, rep_path)
    report_data["report_file"] = str(rep_path)

    return report_data


def write_comparison_markdown_report(data: Dict[str, Any], output_path: Path) -> None:
    """Write comprehensive markdown comparison report for human review."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    m = data["metrics"]
    g = data["gates"]
    fi = data["feature_importance"]

    g1_icon = "PASSED" if g["mae_beat_5pct"]["passed"] else "FAILED"
    g2_icon = "PASSED" if g["event_importance_25pct"]["passed"] else "FAILED"

    md = f"""# Stage 8 Model Comparison & Promotion Review

- **Candidate Model**: `{Path(data['candidate_model_path']).name}`
- **Frozen Model**: `scenario_models.pkl` (Protected - Read Only)
- **Evaluation Period**: Split `{data['evaluated_split']}` (N = {data['n_samples']} news events)
- **Report Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Final Decision**: **{g['overall_promotion_decision']}**

---

## 1. Promotion Gate Evaluation

| Criterion | Requirement | Candidate Result | Gate Status |
|:---|:---:|:---:|:---:|
| **MAE Reduction** | Candidate beats Frozen by **> 5.0%** | **{m['mae_reduction_pct']:+.2f}%** | **{g1_icon}** |
| **Event Feature Share** | Event + Sentiment importance **> 25.0%** | **{fi['candidate_event_share_pct']:.2f}%** | **{g2_icon}** |

> **Decision Summary**:  
> {g['decision_summary']}

---

## 2. Comparative Performance Metrics

| Metric | Frozen Model (57 feats) | Candidate Model (60 feats) | Delta (Improvement) |
|:---|:---:|:---:|:---:|
| **Mean Absolute Error (MAE)** | `{m['frozen_mae']:.4f}` | `{m['candidate_mae']:.4f}` | `{m['mae_reduction_pct']:+.2f}%` |
| **Root Mean Squared Error (RMSE)** | `{m['frozen_rmse']:.4f}` | `{m['candidate_rmse']:.4f}` | `{((m['frozen_rmse'] - m['candidate_rmse'])/m['frozen_rmse']*100):+.2f}%` |
| **Information Coefficient (IC / r)** | `{m['frozen_ic']:+.4f}` | `{m['candidate_ic']:+.4f}` | `{m['candidate_ic'] - m['frozen_ic']:+.4f}` |
| **Directional Hit Rate** | `{m['frozen_directional_acc']:.1f}%` | `{m['candidate_directional_acc']:.1f}%` | `{m['candidate_directional_acc'] - m['frozen_directional_acc']:+.1f}%` |
| **Prediction Diversity (Std Dev)** | `{m['frozen_pred_std']:.4f}` | `{m['candidate_pred_std']:.4f}` | `{m['diversity_gain_pct']:+.2f}%` |

---

## 3. Feature Importance & News Sensitivity

- **Frozen Model Event Feature Share**: `{fi['frozen_event_share_pct']:.2f}%`
- **Candidate Model Event Feature Share**: `{fi['candidate_event_share_pct']:.2f}%`
  * Includes FinBERT Sentiment Share: `{fi['candidate_sentiment_share_pct']:.2f}%`

### Top 10 Features Comparison

| Rank | Frozen Model Top Features | Candidate Model Top Features | Candidate Category |
|:---:|:---|:---|:---:|
"""
    for i in range(10):
        f_feat, f_imp = fi["frozen_top_10"][i] if i < len(fi["frozen_top_10"]) else ("-", 0.0)
        c_feat, c_imp = fi["candidate_top_10"][i] if i < len(fi["candidate_top_10"]) else ("-", 0.0)
        
        c_cat = "Sentiment" if c_feat in SENTIMENT_FEATURE_COLS else ("Event" if c_feat.startswith(EVENT_FEATURE_PREFIXES) else "Technical")
        md += f"| #{i+1} | `{f_feat}` ({f_imp:.1f}%) | `{c_feat}` ({c_imp:.1f}%) | **{c_cat}** |\n"

    md += f"""
---

## 4. Operational Safety Invariant

> [!IMPORTANT]
> **Frozen Model Preservation**:  
> The frozen production model at `models/final/scenario_models.pkl` was **NOT modified** during this evaluation.
> Stage 8 is an isolated staging area. Any promotion to production requires deliberate operator approval.
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info("Saved comparison decision report to %s", output_path)


def print_cli_report(res: Dict[str, Any]) -> None:
    """Print readable formatted decision report to terminal."""
    m = res["metrics"]
    g = res["gates"]
    fi = res["feature_importance"]

    print("\n" + "=" * 70)
    print("       CSE MODEL RETRAINING PROMOTION DECISION REPORT (STAGE 8)      ")
    print("=" * 70)
    print(f"Candidate: {Path(res['candidate_model_path']).name}")
    print(f"Holdout:   Split '{res['evaluated_split']}' (N={res['n_samples']} headlines)")
    print("-" * 70)
    print("PROMOTION GATE EVALUATION:")
    g1_status = "[PASSED]" if g["mae_beat_5pct"]["passed"] else "[FAILED]"
    g2_status = "[PASSED]" if g["event_importance_25pct"]["passed"] else "[FAILED]"
    print(f" 1. MAE Beat > 5.0%:        {g1_status} (Actual: {m['mae_reduction_pct']:+.2f}%)")
    print(f" 2. Event Importance > 25%: {g2_status} (Actual: {fi['candidate_event_share_pct']:.2f}%)")
    print(f"\nDECISION: >>> {g['overall_promotion_decision']} <<<")
    print(f"Summary:  {g['decision_summary']}")
    print("-" * 70)
    print("METRICS COMPARISON:")
    print(f"  MAE:          Frozen = {m['frozen_mae']:.4f}  | Candidate = {m['candidate_mae']:.4f} ({m['mae_reduction_pct']:+.1f}%)")
    print(f"  RMSE:         Frozen = {m['frozen_rmse']:.4f}  | Candidate = {m['candidate_rmse']:.4f}")
    print(f"  Directional:  Frozen = {m['frozen_directional_acc']:.1f}%   | Candidate = {m['candidate_directional_acc']:.1f}%")
    print(f"  Pred Std Dev: Frozen = {m['frozen_pred_std']:.4f}  | Candidate = {m['candidate_pred_std']:.4f} (Diversity {m['diversity_gain_pct']:+.1f}%)")
    print(f"  Event Share:  Frozen = {fi['frozen_event_share_pct']:.1f}%   | Candidate = {fi['candidate_event_share_pct']:.1f}% (Sent: {fi['candidate_sentiment_share_pct']:.1f}%)")
    print("-" * 70)
    print(f"Report File: {res['report_file']}")
    print("SAFEGUARD: Frozen model (scenario_models.pkl) remains intact.")
    print("=" * 70 + "\n")


def main() -> None:
    """CLI entry point for model comparison."""
    parser = argparse.ArgumentParser(description="Compare Frozen vs Candidate Model for Promotion Gate")
    parser.add_argument("--candidate", type=str, default=None, help="Path to candidate .cbm model")
    parser.add_argument("--dataset", type=str, default=str(DEFAULT_PARQUET_PATH), help="Path to training_data.parquet")
    parser.add_argument("--split", type=str, default="test", help="Evaluation split (test, holdout, val, or all)")
    parser.add_argument("--horizon", type=int, default=5, help="CAR horizon to evaluate (default 5)")
    parser.add_argument("--report", type=str, default=None, help="Path to output markdown report")
    args = parser.parse_args()

    cand_path = Path(args.candidate) if args.candidate else None
    data_path = Path(args.dataset) if args.dataset else None
    rep_path = Path(args.report) if args.report else None

    result = compare_models(
        candidate_path=cand_path,
        dataset_path=data_path,
        split=args.split,
        horizon=args.horizon,
        report_output=rep_path,
    )
    print_cli_report(result)


if __name__ == "__main__":
    main()
