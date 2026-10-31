"""Shared Evaluation Harness for model forecasting, prediction validation, and metric aggregation.

Adheres strictly to:
- Rule R3: Suspicious-result rule. Direction accuracy > 60% or OOS R2 > 0.10 triggers alarm.
- Rule R5: Same protocol for every model: same phases, horizons, metrics, and schema.
- Rule R6: Save everything (models, predictions, metrics, configs).
- Rule R7: Reproducibility: seeds, library versions, hardware, data hash.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from cse.eval.metrics import (
    calc_all_metrics,
    get_non_overlapping_indices,
)
from cse.eval.tests_stat import (
    binomial_accuracy_test,
    diebold_mariano,
    pesaran_timmermann,
)
from cse.models.artifact import save_model_artifact
from cse.models.baselines import (
    HistoricalMeanBaseline,
    MajorityClassBaseline,
    MomentumBaseline,
    RandomWalkBaseline,
)
from cse.splits.walk_forward import ExpandingWindowSplitter, PhaseSplit
from cse.utils.config import find_project_root, load_config
from cse.utils.crypto import compute_file_sha256
from cse.utils.logger import get_logger

logger = get_logger("cse.eval.harness")

PREDICTION_SCHEMA = [
    "model",
    "family",
    "phase",
    "horizon",
    "feature_set",
    "date",
    "y_true_ret",
    "y_pred_ret",
    "p_up",
    "y_true_dir",
    "y_pred_dir",
    "aspi_t",
    "aspi_pred_level",
    "seed",
]


class EvaluationHarness:
    """Shared evaluation harness executing models and calculating metrics according to protocol."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        data_df: Optional[pd.DataFrame] = None,
    ) -> None:
        self.config = config or load_config()
        self.root = find_project_root()
        
        # Load processed data if not passed
        if data_df is None:
            proc_path = self.root / self.config["paths"]["processed_data_dir"] / "cse_clean.parquet"
            self.df = pd.read_parquet(proc_path)
        else:
            self.df = data_df.copy()
            
        self.df["date"] = pd.to_datetime(self.df["date"]).dt.strftime("%Y-%m-%d")

        # Initialize splitter
        val_cfg = self.config.get("validation_protocol", {})
        embargo_days = val_cfg.get("embargo_trading_days", 10)
        inner_tune_ratio = val_cfg.get("inner_tune_ratio", 0.15)
        inner_embargo_days = val_cfg.get("inner_embargo_trading_days", 10)
        phases_dict = val_cfg.get("phases", None)

        self.splitter = ExpandingWindowSplitter(
            self.df,
            embargo_days=embargo_days,
            inner_tune_ratio=inner_tune_ratio,
            inner_embargo_days=inner_embargo_days,
            phases_config=phases_dict,
        )

        # Raw data hash for reproducibility (Rule R7)
        raw_path = self.root / self.config["paths"]["raw_data_dir"] / self.config["inputs"]["cse_data_file"]
        self.raw_data_hash = compute_file_sha256(raw_path) if raw_path.exists() else "unknown"

    def validate_prediction_schema(self, df_preds: pd.DataFrame) -> None:
        """Enforce strict prediction DataFrame schema."""
        missing = [col for col in PREDICTION_SCHEMA if col not in df_preds.columns]
        if missing:
            raise ValueError(f"Prediction DataFrame is missing required schema columns: {missing}")

        # Check required non-null fields
        for col in ["model", "family", "phase", "horizon", "date", "y_true_ret", "y_pred_ret", "y_true_dir", "y_pred_dir", "aspi_t", "aspi_pred_level"]:
            if df_preds[col].isna().any():
                raise ValueError(f"Prediction DataFrame contains unexpected NaNs in required column: {col}")

    def save_predictions(
        self,
        df_preds: pd.DataFrame,
        family: str,
        model: str,
        phase: str,
        horizon: int,
    ) -> Tuple[Path, Path]:
        """Save predictions to parquet and csv adhering to protocol directory structure."""
        self.validate_prediction_schema(df_preds)
        
        preds_dir = self.root / self.config["paths"]["predictions_dir"] / family
        preds_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{model}_{phase}_h{horizon}"
        parquet_path = preds_dir / f"{base_name}.parquet"
        csv_path = preds_dir / f"{base_name}.csv"

        df_preds.to_parquet(parquet_path, index=False)
        df_preds.to_csv(csv_path, index=False)

        logger.info("Saved predictions to %s and %s (%d rows)", parquet_path, csv_path, len(df_preds))
        return parquet_path, csv_path

    def evaluate_predictions(
        self,
        df_preds: pd.DataFrame,
        df_benchmark_hist_mean: pd.DataFrame,
        df_benchmark_rw: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Compute full suite of metrics and hypothesis tests on a prediction dataframe."""
        self.validate_prediction_schema(df_preds)

        y_true_ret = df_preds["y_true_ret"].values
        y_pred_ret = df_preds["y_pred_ret"].values
        y_true_dir = df_preds["y_true_dir"].values
        y_pred_dir = df_preds["y_pred_dir"].values
        aspi_true_level = df_preds["aspi_t"].values * np.exp(y_true_ret)
        aspi_pred_level = df_preds["aspi_pred_level"].values
        p_up = df_preds["p_up"].values if "p_up" in df_preds.columns else None

        # Align benchmarks by date
        if "date" in df_preds.columns and "date" in df_benchmark_hist_mean.columns:
            date_to_hist = dict(zip(df_benchmark_hist_mean["date"].values, df_benchmark_hist_mean["y_pred_ret"].values))
            date_to_rw = dict(zip(df_benchmark_rw["date"].values, df_benchmark_rw["y_pred_ret"].values))
            y_bench_ret = np.array([date_to_hist.get(d, 0.0) for d in df_preds["date"].values], dtype=float)
            y_rw_ret = np.array([date_to_rw.get(d, 0.0) for d in df_preds["date"].values], dtype=float)
        else:
            y_bench_ret = df_benchmark_hist_mean["y_pred_ret"].values
            y_rw_ret = df_benchmark_rw["y_pred_ret"].values

        # Base metrics
        metrics = calc_all_metrics(
            y_true_ret=y_true_ret,
            y_pred_ret=y_pred_ret,
            y_benchmark_ret=y_bench_ret,
            y_true_dir=y_true_dir,
            y_pred_dir=y_pred_dir,
            aspi_true_level=aspi_true_level,
            aspi_pred_level=aspi_pred_level,
            p_up=p_up,
        )

        horizon = int(df_preds["horizon"].iloc[0])

        # Hypothesis tests
        e_model = y_true_ret - y_pred_ret
        e_rw = y_true_ret - y_rw_ret
        e_hist = y_true_ret - y_bench_ret

        dm_rw = diebold_mariano(e_model, e_rw, h=horizon, power=2, alternative="two-sided")
        dm_hist = diebold_mariano(e_model, e_hist, h=horizon, power=2, alternative="two-sided")

        # Binomial test vs 50% and majority class
        maj_prop = float(np.mean(y_true_dir == 1))
        p_null_maj = max(maj_prop, 1.0 - maj_prop)
        binom_50 = binomial_accuracy_test(y_true_dir, y_pred_dir, p_null=0.5, alternative="greater")
        binom_maj = binomial_accuracy_test(y_true_dir, y_pred_dir, p_null=p_null_maj, alternative="greater")

        pt_test = pesaran_timmermann(y_true_dir, y_pred_dir)

        # Non-overlapping evaluation if horizon > 1
        non_ov_metrics = {}
        if horizon > 1:
            step = horizon
            idx_sub = get_non_overlapping_indices(len(df_preds), step=step)
            non_ov_metrics = {
                "non_ov_n": len(idx_sub),
                "non_ov_mae": float(np.mean(np.abs(y_true_ret[idx_sub] - y_pred_ret[idx_sub]))),
                "non_ov_rmse": float(np.sqrt(np.mean((y_true_ret[idx_sub] - y_pred_ret[idx_sub]) ** 2))),
                "non_ov_accuracy": float(np.mean(y_true_dir[idx_sub] == y_pred_dir[idx_sub])),
            }

        # Check Suspicious Result Circuit Breaker (Rule R3)
        acc = metrics["accuracy"]
        r2 = metrics["oos_r2"]
        if acc > 0.60 or r2 > 0.10:
            logger.warning(
                "SUSPICIOUS RESULT ALARM (Rule R3): Direction accuracy=%.3f (>0.60) or OOS R2=%.4f (>0.10) for model %s phase %s h%d!",
                acc, r2, df_preds["model"].iloc[0], df_preds["phase"].iloc[0], horizon
            )
            metrics["alarm_rule_r3"] = True
        else:
            metrics["alarm_rule_r3"] = False

        # Compile combined results
        results = {
            "model": str(df_preds["model"].iloc[0]),
            "family": str(df_preds["family"].iloc[0]),
            "phase": str(df_preds["phase"].iloc[0]),
            "horizon": horizon,
            "n_samples": len(df_preds),
            **metrics,
            "dm_rw_stat": dm_rw["dm_hln_stat"],
            "dm_rw_pval": dm_rw["p_value"],
            "dm_hist_stat": dm_hist["dm_hln_stat"],
            "dm_hist_pval": dm_hist["p_value"],
            "binom_50_pval": binom_50["p_value"],
            "binom_maj_pval": binom_maj["p_value"],
            "pt_stat": pt_test["pt_stat"],
            "pt_pval": pt_test["p_value"],
            **non_ov_metrics,
        }
        return results

    def run_all_baselines(
        self,
        horizons: Optional[List[int]] = None,
        refit_interval: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Execute all 4 baseline models across all 5 phases for given horizons.
        
        Args:
            horizons: List of forecast horizons in trading days (default [1, 5]).
            refit_interval: Optional sensitivity protocol refit frequency in trading days (e.g. 63).
        """
        if horizons is None:
            horizons = [1, 5]

        models = [
            RandomWalkBaseline(seed=self.config["seed"]),
            HistoricalMeanBaseline(seed=self.config["seed"]),
            MajorityClassBaseline(seed=self.config["seed"]),
            MomentumBaseline(seed=self.config["seed"]),
        ]

        all_predictions: Dict[Tuple[str, str, int], pd.DataFrame] = {}

        # 1. Generate predictions for all models, phases, and horizons
        for phase_name in self.splitter.splits.keys():
            phase_split = self.splitter.get_phase(phase_name)
            for h in horizons:
                for model in models:
                    t0 = time.time()
                    df_preds = model.forecast_validation(self.df, phase_split, horizon=h)
                    runtime = time.time() - t0

                    # Save predictions
                    parquet_p, csv_p = self.save_predictions(
                        df_preds=df_preds,
                        family=model.family,
                        model=model.name,
                        phase=phase_name,
                        horizon=h,
                    )
                    all_predictions[(model.name, phase_name, h)] = df_preds

                    # Save artifact
                    save_model_artifact(
                        model_obj=model,
                        family=model.family,
                        model_name=model.name,
                        phase=phase_name,
                        horizon=h,
                        seed=self.config["seed"],
                        train_date_range=(phase_split.train.start_date, phase_split.train.end_date),
                        embargo_date_range=(phase_split.embargo.start_date, phase_split.embargo.end_date),
                        val_date_range=(phase_split.val.start_date, phase_split.val.end_date),
                        embargo_days=phase_split.embargo.n_days,
                        feature_set="none",
                        raw_data_hash=self.raw_data_hash,
                        runtime_seconds=runtime,
                        prediction_file=str(parquet_p.relative_to(self.root)).replace("\\", "/"),
                    )

        # 2. Evaluate all predictions against benchmarks
        eval_rows = []
        for phase_name in self.splitter.splits.keys():
            for h in horizons:
                bench_hist = all_predictions[("historical_mean", phase_name, h)]
                bench_rw = all_predictions[("random_walk", phase_name, h)]

                for model in models:
                    preds = all_predictions[(model.name, phase_name, h)]
                    row_metrics = self.evaluate_predictions(preds, bench_hist, bench_rw)
                    eval_rows.append(row_metrics)

        df_metrics = pd.DataFrame(eval_rows)

        # 3. Aggregate across phases (mean and std per model-horizon)
        numeric_cols = [
            "mae", "rmse", "oos_r2", "theils_u", "level_mae", "level_rmse", "level_mape",
            "accuracy", "balanced_accuracy", "precision", "recall", "f1", "mcc",
            "dm_rw_stat", "dm_rw_pval", "pt_stat", "pt_pval"
        ]
        agg_rows = []
        for (model_name, h), group in df_metrics.groupby(["model", "horizon"]):
            agg_entry = {
                "model": model_name,
                "horizon": h,
                "n_phases": len(group),
            }
            for col in numeric_cols:
                if col in group.columns:
                    agg_entry[f"{col}_mean"] = float(group[col].mean())
                    agg_entry[f"{col}_std"] = float(group[col].std())
            agg_rows.append(agg_entry)

        df_agg = pd.DataFrame(agg_rows)

        # Save summary tables
        tables_dir = self.root / self.config["paths"]["tables_dir"]
        tables_dir.mkdir(parents=True, exist_ok=True)

        metrics_csv = tables_dir / "baseline_metrics_summary.csv"
        metrics_md = tables_dir / "baseline_metrics_summary.md"
        df_metrics.to_csv(metrics_csv, index=False)

        headers = list(df_metrics.columns)
        lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
        for _, r in df_metrics.iterrows():
            lines.append('| ' + ' | '.join(f"{val:.5f}" if isinstance(val, float) else str(val) for val in r.values) + ' |')
        with open(metrics_md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        agg_csv = tables_dir / "baseline_metrics_aggregated.csv"
        df_agg.to_csv(agg_csv, index=False)

        logger.info("Baseline execution complete. Metrics saved to %s and %s", metrics_csv, agg_csv)
        return df_metrics, df_agg
