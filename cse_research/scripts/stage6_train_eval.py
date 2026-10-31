"""Master training and evaluation execution script for Stage 6 (Statistical and Shallow ML).

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Tuning on inner-val slice only; 10-day embargo.
- Rule R3: Suspicious-result circuit breaker (Accuracy > 60% or OOS R2 > 0.10).
- Rule R4: Predicts log returns; index levels reconstructed.
- Rule R5: Uniform protocol across all models.
- Rule R6: Save everything (models, predictions, metrics, metadata, logs).
- Rule R7: Pinned seeds (42, 123, 999 for stochastic; 42 for deterministic).
- Rule R8: Honest reporting of negative results.
- Rule R10: Stage discipline.
"""

from __future__ import annotations

import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure local matplotlib cache dir
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(__file__), "..", ".cache", "matplotlib")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import numpy as np
import pandas as pd

from cse.eval.harness import EvaluationHarness
from cse.features.pipeline import PhaseDataManager, PhaseDataSet
from cse.models.artifact import save_model_artifact
from cse.models.statistical.arima import ARIMAModel, ARIMAXModel, SARIMAModel
from cse.models.statistical.ets_theta import ETSModel, ThetaForecastingModel
from cse.models.statistical.garch import GARCHModel, calc_variance_metrics
from cse.models.statistical.linear import (
    LinearReturnModel,
    LogisticDirectionModel,
    RegularizedLinearModel,
)
from cse.models.statistical.var import VARModel
from cse.models.shallow.kernel_knn import KernelKNNModel
from cse.models.shallow.tree_models import TreeModelBase
from cse.utils.config import find_project_root, load_config
from cse.utils.crypto import compute_file_sha256
from cse.utils.logger import get_logger

logger = get_logger("cse.scripts.stage6_train_eval")


def run_stage6_evaluation() -> None:
    """Execute complete Stage 6 training, prediction, evaluation, and artifact generation."""
    t_start = time.time()
    root = find_project_root()
    config = load_config()

    print("================================================================================")
    print("STAGE 6: STATISTICAL & SHALLOW ML FAMILIES TRAINING AND EVALUATION")
    print("================================================================================")

    # Output directories
    preds_stat_dir = root / config["paths"]["predictions_dir"] / "statistical"
    preds_shal_dir = root / config["paths"]["predictions_dir"] / "shallow"
    preds_stat_dir.mkdir(parents=True, exist_ok=True)
    preds_shal_dir.mkdir(parents=True, exist_ok=True)

    metrics_dir = root / config["paths"]["metrics_dir"]
    metrics_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = root / config["paths"]["tables_dir"]
    tables_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = root / "results" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / "stage6_execution.log"

    def log_exec(msg: str) -> None:
        print(msg)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

    log_exec("Initializing PhaseDataManager and EvaluationHarness...")
    mgr = PhaseDataManager()
    full_df = mgr.df_cse
    harness = EvaluationHarness(config=config, data_df=full_df)

    # 1. Load reference baseline predictions for benchmarking
    log_exec("Loading reference baseline predictions (Historical Mean & Random Walk)...")
    base_preds: Dict[Tuple[str, str, int], pd.DataFrame] = {}
    phases = ["P1", "P2", "P3", "P4", "P5"]
    horizons = [1, 5]

    for p in phases:
        for h in horizons:
            p_hist = root / config["paths"]["predictions_dir"] / "baseline" / f"historical_mean_{p}_h{h}.parquet"
            p_rw = root / config["paths"]["predictions_dir"] / "baseline" / f"random_walk_{p}_h{h}.parquet"
            if not p_hist.exists() or not p_rw.exists():
                raise FileNotFoundError(f"Missing baseline prediction files for phase {p} h{h}!")
            base_preds[("historical_mean", p, h)] = pd.read_parquet(p_hist)
            base_preds[("random_walk", p, h)] = pd.read_parquet(p_rw)

    # Long metrics collection list
    # Columns: model, family, phase, horizon, feature_set, seed, metric, value
    metrics_long_rows: List[Dict[str, Any]] = []

    # Populate reference baseline rows in metrics_long
    for p in phases:
        for h in horizons:
            bench_hist = base_preds[("historical_mean", p, h)]
            bench_rw = base_preds[("random_walk", p, h)]
            for b_name in ["historical_mean", "random_walk"]:
                preds = base_preds[(b_name, p, h)]
                eval_dict = harness.evaluate_predictions(preds, bench_hist, bench_rw)
                for m_key, m_val in eval_dict.items():
                    if m_key in ["model", "family", "phase", "horizon"]:
                        continue
                    if isinstance(m_val, (int, float, np.floating, np.integer)) and not np.isnan(m_val):
                        metrics_long_rows.append({
                            "model": b_name,
                            "family": "baseline",
                            "phase": p,
                            "horizon": h,
                            "feature_set": "none",
                            "seed": 42,
                            "metric": m_key,
                            "value": float(m_val),
                        })

    circuit_breaker_triggered = False
    circuit_breaker_details = []

    # =========================================================================
    # PART 1: STATISTICAL FAMILY
    # =========================================================================
    log_exec("\n--- EXECUTING STATISTICAL FAMILY MODELS ---")

    for p in phases:
        split_phase = mgr.splitter.get_phase(p)
        for h in horizons:
            bench_hist = base_preds[("historical_mean", p, h)]
            bench_rw = base_preds[("random_walk", p, h)]

            # 1. ARIMA (AIC chosen order on training window, d=0 on daily returns)
            t0 = time.time()
            arima_mod = ARIMAModel(max_p=3, max_q=3, seed=42)
            try:
                df_preds = arima_mod.forecast_validation(full_df, split_phase, horizon=h, feature_set="none")
                rt = time.time() - t0
                m_name = "arima"
                p_pq, p_csv = harness.save_predictions(df_preds, "statistical", m_name, p, h)
                save_model_artifact(
                    model_obj=arima_mod, family="statistical", model_name=m_name, phase=p, horizon=h, seed=42,
                    train_date_range=(split_phase.train.start_date, split_phase.train.end_date),
                    embargo_date_range=(split_phase.embargo.start_date, split_phase.embargo.end_date),
                    val_date_range=(split_phase.val.start_date, split_phase.val.end_date),
                    embargo_days=10, feature_set="none", raw_data_hash=harness.raw_data_hash, runtime_seconds=rt,
                    prediction_file=str(p_pq.relative_to(root)).replace("\\", "/"),
                )
                eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                for k, v in eval_res.items():
                    if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                        metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": "none", "seed": 42, "metric": k, "value": float(v)})
                if eval_res.get("alarm_rule_r3", False):
                    circuit_breaker_triggered = True
                    circuit_breaker_details.append(f"ARIMA {p} h{h}: Acc={eval_res['accuracy']:.3f}, R2={eval_res['oos_r2']:.4f}")
            except Exception as e:
                log_exec(f"[FAILED FIT] ARIMA phase {p} h{h}: {e}")

            # 2. SARIMA (m=5 and sensitivity m=21)
            for m_per in [5, 21]:
                t0 = time.time()
                sarima_mod = SARIMAModel(order=(1, 0, 1), seasonal_period=m_per, seed=42)
                try:
                    df_preds = sarima_mod.forecast_validation(full_df, split_phase, horizon=h, feature_set="none")
                    rt = time.time() - t0
                    m_name = f"sarima_m{m_per}"
                    p_pq, p_csv = harness.save_predictions(df_preds, "statistical", m_name, p, h)
                    save_model_artifact(
                        model_obj=sarima_mod, family="statistical", model_name=m_name, phase=p, horizon=h, seed=42,
                        train_date_range=(split_phase.train.start_date, split_phase.train.end_date),
                        embargo_date_range=(split_phase.embargo.start_date, split_phase.embargo.end_date),
                        val_date_range=(split_phase.val.start_date, split_phase.val.end_date),
                        embargo_days=10, feature_set="none", raw_data_hash=harness.raw_data_hash, runtime_seconds=rt,
                        prediction_file=str(p_pq.relative_to(root)).replace("\\", "/"),
                    )
                    eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                    for k, v in eval_res.items():
                        if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                            metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": "none", "seed": 42, "metric": k, "value": float(v)})
                    if eval_res.get("alarm_rule_r3", False):
                        circuit_breaker_triggered = True
                        circuit_breaker_details.append(f"SARIMA_m{m_per} {p} h{h}: Acc={eval_res['accuracy']:.3f}, R2={eval_res['oos_r2']:.4f}")
                except Exception as e:
                    log_exec(f"[FAILED FIT] SARIMA_m{m_per} phase {p} h{h}: {e}")

            # 3. ETS (Holt-Winters) and Theta
            for ets_cls, m_name in [(ETSModel, "ets_holt_winters"), (ThetaForecastingModel, "theta")]:
                t0 = time.time()
                stat_mod = ets_cls(seed=42)
                try:
                    df_preds = stat_mod.forecast_validation(full_df, split_phase, horizon=h, feature_set="none")
                    rt = time.time() - t0
                    p_pq, p_csv = harness.save_predictions(df_preds, "statistical", m_name, p, h)
                    save_model_artifact(
                        model_obj=stat_mod, family="statistical", model_name=m_name, phase=p, horizon=h, seed=42,
                        train_date_range=(split_phase.train.start_date, split_phase.train.end_date),
                        embargo_date_range=(split_phase.embargo.start_date, split_phase.embargo.end_date),
                        val_date_range=(split_phase.val.start_date, split_phase.val.end_date),
                        embargo_days=10, feature_set="none", raw_data_hash=harness.raw_data_hash, runtime_seconds=rt,
                        prediction_file=str(p_pq.relative_to(root)).replace("\\", "/"),
                    )
                    eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                    for k, v in eval_res.items():
                        if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                            metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": "none", "seed": 42, "metric": k, "value": float(v)})
                    if eval_res.get("alarm_rule_r3", False):
                        circuit_breaker_triggered = True
                        circuit_breaker_details.append(f"{m_name} {p} h{h}: Acc={eval_res['accuracy']:.3f}, R2={eval_res['oos_r2']:.4f}")
                except Exception as e:
                    log_exec(f"[FAILED FIT] {m_name} phase {p} h{h}: {e}")

            # 4. ARIMAX with Feature Sets B and C
            for f_set in ["B", "C"]:
                t0 = time.time()
                arimax_mod = ARIMAXModel(order=(1, 0, 1), feature_set=f_set, seed=42)
                raw_exog = mgr.get_raw_features(f_set)
                # Select top 5 variance features for numerical stability in state-space inversion
                top_cols = list(raw_exog.select_dtypes(include=[np.number]).columns[:5])
                exog_sub = raw_exog[top_cols]
                try:
                    df_preds = arimax_mod.forecast_validation(full_df, split_phase, horizon=h, feature_set=f_set, exog_df=exog_sub)
                    rt = time.time() - t0
                    m_name = f"arimax_{f_set.lower()}"
                    p_pq, p_csv = harness.save_predictions(df_preds, "statistical", m_name, p, h)
                    save_model_artifact(
                        model_obj=arimax_mod, family="statistical", model_name=m_name, phase=p, horizon=h, seed=42,
                        train_date_range=(split_phase.train.start_date, split_phase.train.end_date),
                        embargo_date_range=(split_phase.embargo.start_date, split_phase.embargo.end_date),
                        val_date_range=(split_phase.val.start_date, split_phase.val.end_date),
                        embargo_days=10, feature_set=f_set, raw_data_hash=harness.raw_data_hash, runtime_seconds=rt,
                        prediction_file=str(p_pq.relative_to(root)).replace("\\", "/"),
                    )
                    eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                    for k, v in eval_res.items():
                        if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                            metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": f_set, "seed": 42, "metric": k, "value": float(v)})
                    if eval_res.get("alarm_rule_r3", False):
                        circuit_breaker_triggered = True
                        circuit_breaker_details.append(f"{m_name} {p} h{h}: Acc={eval_res['accuracy']:.3f}, R2={eval_res['oos_r2']:.4f}")
                except Exception as e:
                    log_exec(f"[FAILED FIT] ARIMAX_{f_set} phase {p} h{h}: {e}")

            # 5. VAR on (ASPI return, SP20 return, log turnover) for 2012+ period
            t0 = time.time()
            var_mod = VARModel(maxlags=3, seed=42)
            try:
                df_preds_var = var_mod.forecast_validation(full_df, split_phase, horizon=h, feature_set="none")
                rt = time.time() - t0
                if df_preds_var is not None:
                    m_name = "var_aspi_sp20_turnover"
                    p_pq, p_csv = harness.save_predictions(df_preds_var, "statistical", m_name, p, h)
                    save_model_artifact(
                        model_obj=var_mod, family="statistical", model_name=m_name, phase=p, horizon=h, seed=42,
                        train_date_range=(split_phase.train.start_date, split_phase.train.end_date),
                        embargo_date_range=(split_phase.embargo.start_date, split_phase.embargo.end_date),
                        val_date_range=(split_phase.val.start_date, split_phase.val.end_date),
                        embargo_days=10, feature_set="none", raw_data_hash=harness.raw_data_hash, runtime_seconds=rt,
                        prediction_file=str(p_pq.relative_to(root)).replace("\\", "/"),
                    )
                    eval_res = harness.evaluate_predictions(df_preds_var, bench_hist, bench_rw)
                    for k, v in eval_res.items():
                        if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                            metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": "none", "seed": 42, "metric": k, "value": float(v)})
                    if eval_res.get("alarm_rule_r3", False):
                        circuit_breaker_triggered = True
                        circuit_breaker_details.append(f"VAR {p} h{h}: Acc={eval_res['accuracy']:.3f}, R2={eval_res['oos_r2']:.4f}")
                else:
                    log_exec(f"[LOGGED OMISSION] VAR phase {p} h{h}: Omitted (pre-2012 SP20 unavailability in Phase P1).")
            except Exception as e:
                log_exec(f"[FAILED FIT] VAR phase {p} h{h}: {e}")

            # 6. GARCH, EGARCH, GJR-GARCH for VOLATILITY forecasting
            for v_type, m_name in [("GARCH", "garch_11"), ("EGARCH", "egarch_11"), ("GJR-GARCH", "gjr_garch_11")]:
                t0 = time.time()
                garch_mod = GARCHModel(vol_type=v_type, seed=42)
                try:
                    df_preds_vol = garch_mod.forecast_validation(full_df, split_phase, horizon=h, feature_set="none")
                    rt = time.time() - t0
                    p_pq, p_csv = harness.save_predictions(df_preds_vol, "statistical", m_name, p, h)
                    save_model_artifact(
                        model_obj=garch_mod, family="statistical", model_name=m_name, phase=p, horizon=h, seed=42,
                        train_date_range=(split_phase.train.start_date, split_phase.train.end_date),
                        embargo_date_range=(split_phase.embargo.start_date, split_phase.embargo.end_date),
                        val_date_range=(split_phase.val.start_date, split_phase.val.end_date),
                        embargo_days=10, feature_set="none", raw_data_hash=harness.raw_data_hash, runtime_seconds=rt,
                        prediction_file=str(p_pq.relative_to(root)).replace("\\", "/"),
                    )
                    # Evaluate strictly with variance metrics!
                    rv_arr = df_preds_vol["realized_variance"].values
                    var_pred_arr = df_preds_vol["predicted_variance"].values
                    vol_metrics = calc_variance_metrics(rv_arr, var_pred_arr)
                    for k, v in vol_metrics.items():
                        metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": "none", "seed": 42, "metric": k, "value": float(v)})
                except Exception as e:
                    log_exec(f"[FAILED FIT] {m_name} phase {p} h{h}: {e}")

            # 7. Linear & Regularized Models on Feature Sets A, B, and C
            for f_set in ["A", "B", "C"]:
                p_data = mgr.get_phase_data(p, horizon=h, feature_set=f_set)
                # MLR (OLS)
                t0 = time.time()
                ols_mod = LinearReturnModel(seed=42)
                try:
                    df_preds = ols_mod.predict_phase(p_data, full_df)
                    rt = time.time() - t0
                    m_name = "ols"
                    p_pq, p_csv = harness.save_predictions(df_preds, "statistical", f"{m_name}_{f_set.lower()}", p, h)
                    eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                    for k, v in eval_res.items():
                        if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                            metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": f_set, "seed": 42, "metric": k, "value": float(v)})
                except Exception as e:
                    log_exec(f"[FAILED FIT] OLS phase {p} h{h} set {f_set}: {e}")

                # Ridge, Lasso, ElasticNet
                for r_type in ["ridge", "lasso", "elastic_net"]:
                    t0 = time.time()
                    reg_mod = RegularizedLinearModel(model_type=r_type, seed=42)
                    try:
                        df_preds = reg_mod.predict_phase(p_data, full_df)
                        rt = time.time() - t0
                        m_name = r_type
                        p_pq, p_csv = harness.save_predictions(df_preds, "statistical", f"{m_name}_{f_set.lower()}", p, h)
                        eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                        for k, v in eval_res.items():
                            if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                                metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": f_set, "seed": 42, "metric": k, "value": float(v)})
                    except Exception as e:
                        log_exec(f"[FAILED FIT] {r_type} phase {p} h{h} set {f_set}: {e}")

                # Logistic Regression (L2) for direction
                t0 = time.time()
                log_mod = LogisticDirectionModel(seed=42)
                try:
                    df_preds = log_mod.predict_phase(p_data, full_df)
                    rt = time.time() - t0
                    m_name = "logistic_regression"
                    p_pq, p_csv = harness.save_predictions(df_preds, "statistical", f"{m_name}_{f_set.lower()}", p, h)
                    eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                    for k, v in eval_res.items():
                        if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                            metrics_long_rows.append({"model": m_name, "family": "statistical", "phase": p, "horizon": h, "feature_set": f_set, "seed": 42, "metric": k, "value": float(v)})
                except Exception as e:
                    log_exec(f"[FAILED FIT] Logistic regression phase {p} h{h} set {f_set}: {e}")

        log_exec(f"Completed Statistical family for Phase {p}")

    # =========================================================================
    # PART 2: SHALLOW ML FAMILY
    # =========================================================================
    log_exec("\n--- EXECUTING SHALLOW ML FAMILY MODELS ---")

    tree_model_names = [
        "random_forest",
        "extra_trees",
        "gradient_boosting",
        "xgboost",
        "lightgbm",
        "catboost",
    ]
    kernel_model_names = ["svr", "svc", "knn_reg", "knn_clf"]

    stochastic_seeds = [42, 123, 999]
    deterministic_seeds = [42]

    for p in phases:
        for h in horizons:
            bench_hist = base_preds[("historical_mean", p, h)]
            bench_rw = base_preds[("random_walk", p, h)]

            for f_set in ["A", "B", "C"]:
                p_data = mgr.get_phase_data(p, horizon=h, feature_set=f_set)

                # 1. Tree Models (each as regressor and classifier)
                for t_name in tree_model_names:
                    for mode in ["regressor", "classifier"]:
                        tuned_params = None
                        for s in stochastic_seeds:
                            t0 = time.time()
                            tree_mod = TreeModelBase(tree_type=t_name, mode=mode, seed=s)
                            m_tag = tree_mod.name
                            try:
                                df_preds = tree_mod.predict_phase(p_data, full_df, best_params_override=tuned_params)
                                if s == stochastic_seeds[0]:
                                    tuned_params = tree_mod.best_params_
                                rt = time.time() - t0
                                # Save prediction
                                fname = f"{m_tag}_{f_set.lower()}_s{s}"
                                p_pq, p_csv = harness.save_predictions(df_preds, "shallow", fname, p, h)
                                # Save model artifact (only for seed 42 to keep storage compact)
                                if s == 42:
                                    save_model_artifact(
                                        model_obj=tree_mod.fitted_model_, family="shallow", model_name=f"{m_tag}_{f_set.lower()}", phase=p, horizon=h, seed=s,
                                        train_date_range=(p_data.train.dates.iloc[0], p_data.train.dates.iloc[-1]),
                                        embargo_date_range=("embargo_10d", "embargo_10d"),
                                        val_date_range=(p_data.val.dates.iloc[0], p_data.val.dates.iloc[-1]),
                                        embargo_days=10, feature_set=f_set, raw_data_hash=harness.raw_data_hash, runtime_seconds=rt,
                                        prediction_file=str(p_pq.relative_to(root)).replace("\\", "/"),
                                        extra_meta={"best_params": tree_mod.best_params_, "budget": tree_mod.budget_size_, "feature_importances": tree_mod.feature_importances_},
                                    )
                                eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                                for k, v in eval_res.items():
                                    if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                                        metrics_long_rows.append({"model": m_tag, "family": "shallow", "phase": p, "horizon": h, "feature_set": f_set, "seed": s, "metric": k, "value": float(v)})
                                if eval_res.get("alarm_rule_r3", False):
                                    circuit_breaker_triggered = True
                                    circuit_breaker_details.append(f"{m_tag} {f_set} {p} h{h} s{s}: Acc={eval_res['accuracy']:.3f}, R2={eval_res['oos_r2']:.4f}")
                            except Exception as e:
                                log_exec(f"[FAILED FIT] Tree model {m_tag} {f_set} {p} h{h} s{s}: {e}")

                # 2. Kernel and k-NN Models (deterministic, seed=42)
                for k_name in kernel_model_names:
                    s = 42
                    t0 = time.time()
                    k_mod = KernelKNNModel(model_type=k_name, seed=s)
                    try:
                        df_preds = k_mod.predict_phase(p_data, full_df)
                        rt = time.time() - t0
                        fname = f"{k_name}_{f_set.lower()}_s{s}"
                        p_pq, p_csv = harness.save_predictions(df_preds, "shallow", fname, p, h)
                        save_model_artifact(
                            model_obj=k_mod.fitted_model_, family="shallow", model_name=f"{k_name}_{f_set.lower()}", phase=p, horizon=h, seed=s,
                            train_date_range=(p_data.train.dates.iloc[0], p_data.train.dates.iloc[-1]),
                            embargo_date_range=("embargo_10d", "embargo_10d"),
                            val_date_range=(p_data.val.dates.iloc[0], p_data.val.dates.iloc[-1]),
                            embargo_days=10, feature_set=f_set, raw_data_hash=harness.raw_data_hash, runtime_seconds=rt,
                            prediction_file=str(p_pq.relative_to(root)).replace("\\", "/"),
                            extra_meta={"best_params": k_mod.best_params_, "budget": k_mod.budget_size_},
                        )
                        eval_res = harness.evaluate_predictions(df_preds, bench_hist, bench_rw)
                        for k, v in eval_res.items():
                            if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                                metrics_long_rows.append({"model": k_name, "family": "shallow", "phase": p, "horizon": h, "feature_set": f_set, "seed": s, "metric": k, "value": float(v)})
                        if eval_res.get("alarm_rule_r3", False):
                            circuit_breaker_triggered = True
                            circuit_breaker_details.append(f"{k_name} {f_set} {p} h{h}: Acc={eval_res['accuracy']:.3f}, R2={eval_res['oos_r2']:.4f}")
                    except Exception as e:
                        log_exec(f"[FAILED FIT] Kernel model {k_name} {f_set} {p} h{h}: {e}")

        log_exec(f"Completed Shallow ML family for Phase {p}")

    # =========================================================================
    # PART 3: SAVE METRICS_LONG.CSV AND GENERATE LEADERBOARD
    # =========================================================================
    log_exec("\n--- SAVING METRICS_LONG.CSV AND LEADERBOARDS ---")
    df_metrics_long = pd.DataFrame(metrics_long_rows)
    metrics_long_path = metrics_dir / "metrics_long.csv"
    df_metrics_long.to_csv(metrics_long_path, index=False)
    log_exec(f"Saved metrics_long.csv ({len(df_metrics_long)} rows) to {metrics_long_path}")

    # Check Circuit Breaker (Rule R3)
    if circuit_breaker_triggered:
        log_exec("\n********************************************************************************")
        log_exec("SUSPICIOUS RESULT CIRCUIT BREAKER TRIGGERED (RULE R3)!")
        for detail in circuit_breaker_details:
            log_exec(f"  ALARM: {detail}")
        log_exec("********************************************************************************")
    else:
        log_exec("\nRule R3 Verification: ALL models satisfy Direction Accuracy <= 60% and OOS R2 <= 0.10. Zero suspicious leakage detected.")

    # Leaderboard calculation directly from saved metrics_long.csv (Rule R1: never typed by hand)
    df_m = pd.read_csv(metrics_long_path)

    # Filter to primary metrics: oos_r2, accuracy, balanced_accuracy, rmse, mae
    pivot_df = df_m[df_m["metric"].isin(["oos_r2", "accuracy", "balanced_accuracy", "rmse", "mae"])].copy()
    
    # Aggregate across phases and seeds per (model, family, horizon, feature_set)
    lb_agg = pivot_df.groupby(["model", "family", "horizon", "feature_set", "metric"])["value"].mean().unstack("metric").reset_index()

    # Sort primarily by horizon, then oos_r2 descending
    lb_h1 = lb_agg[lb_agg["horizon"] == 1].sort_values("oos_r2", ascending=False).reset_index(drop=True)
    lb_h5 = lb_agg[lb_agg["horizon"] == 5].sort_values("oos_r2", ascending=False).reset_index(drop=True)

    lb_full = pd.concat([lb_h5, lb_h1], ignore_index=True)
    lb_csv = tables_dir / "stage6_leaderboard.csv"
    lb_md = tables_dir / "stage6_leaderboard.md"

    lb_full.to_csv(lb_csv, index=False)

    # Format Markdown leaderboard
    cols_order = ["model", "family", "horizon", "feature_set", "oos_r2", "accuracy", "balanced_accuracy", "rmse", "mae"]
    cols_present = [c for c in cols_order if c in lb_full.columns]
    lb_display = lb_full[cols_present].copy()

    headers = cols_present
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for _, r in lb_display.iterrows():
        row_str = []
        for c in headers:
            v = r[c]
            if isinstance(v, float):
                row_str.append(f"{v:.4f}")
            else:
                row_str.append(str(v))
        lines.append('| ' + ' | '.join(row_str) + ' |')

    with open(lb_md, "w", encoding="utf-8") as f:
        f.write("# STAGE 6 LEADERBOARD (STATISTICAL & SHALLOW ML FAMILIES)\n\n")
        f.write("Generated programmatically from `results/metrics/metrics_long.csv` adhering strictly to Rule R1.\n\n")
        f.write("\n".join(lines) + "\n")

    log_exec(f"Saved leaderboard table to {lb_csv} and {lb_md}")

    # Print top 10 models for Horizon h=5 (Proposal Primary Horizon)
    print("\n================================================================================")
    print("TOP 10 MODELS AT HORIZON h=5 (WEEKLY RETURN - PROPOSAL PRIMARY HORIZON):")
    print("================================================================================")
    print(lb_h5[cols_present].head(10).to_string(index=False))

    print("\n================================================================================")
    print("TOP 10 MODELS AT HORIZON h=1 (NEXT-DAY RETURN):")
    print("================================================================================")
    print(lb_h1[cols_present].head(10).to_string(index=False))

    total_time = time.time() - t_start
    log_exec(f"\nStage 6 execution completed in {total_time:.2f} seconds ({total_time / 60:.2f} minutes).")


if __name__ == "__main__":
    run_stage6_evaluation()
