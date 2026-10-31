"""Master training and evaluation execution script for Stage 7 (Deep Sequence Models).

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Lookback L in {20, 60, 120} chosen exclusively on inner-val slice.
- Rule R3: Sanity and collapse diagnostics (accuracy > 60%, OOS R2 > 0.10, or constant output).
- Rule R4: Predicts log returns; levels reconstructed post-prediction.
- Rule R5: Same walk-forward protocol, phases (P1-P5), horizons (h=1, 5), and schema as Stages 3-6.
- Rule R6: Save everything: checkpoints, curves (CSV & PNG), meta.json, predictions, and metrics.
- Rule R7: Pinned seeds (42, 123, 999, 2024, 777), hardware logging, and raw data hash.
- Rule R8: Honest reporting of negative and collapsed results.
- Rule R10: Stage discipline.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Set local matplotlib cache directory
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(__file__), "..", ".cache", "matplotlib")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import numpy as np
import pandas as pd
import torch

from cse.eval.harness import EvaluationHarness
from cse.features.pipeline import PhaseDataManager
from cse.models.deep.architectures import build_deep_model, MODEL_REGISTRY
from cse.models.deep.trainer import DeepSequenceTrainer, get_device, get_hardware_info
from cse.models.deep.tuner import select_best_lookback
from cse.utils.config import find_project_root, load_config
from cse.utils.logger import get_logger

logger = get_logger("cse.scripts.stage7_deep_train_eval")


def run_stage7_evaluation() -> None:
    """Execute complete Stage 7 deep sequence models training, prediction, and evaluation."""
    t_start = time.time()
    root = find_project_root()
    config = load_config()

    print("=" * 80)
    print("STAGE 7: DEEP SEQUENCE MODELS TRAINING AND EVALUATION")
    print("=" * 80)

    # Directories
    preds_deep_dir = root / config["paths"]["predictions_dir"] / "deep"
    preds_deep_dir.mkdir(parents=True, exist_ok=True)

    models_deep_root = root / "models" / "deep"
    models_deep_root.mkdir(parents=True, exist_ok=True)

    metrics_dir = root / config["paths"]["metrics_dir"]
    metrics_dir.mkdir(parents=True, exist_ok=True)

    tables_dir = root / config["paths"]["tables_dir"]
    tables_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = root / "results" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / "stage7_execution.log"

    def log_exec(msg: str) -> None:
        print(msg, flush=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

    device = get_device()
    hw_info = get_hardware_info()
    log_exec(f"Detected Hardware: {hw_info}")

    log_exec("Initializing PhaseDataManager and EvaluationHarness...")
    mgr = PhaseDataManager()
    full_df = mgr.df_cse
    harness = EvaluationHarness(config=config, data_df=full_df)

    phases = ["P1", "P2", "P3", "P4", "P5"]
    horizons = [1, 5]
    seeds = [42, 123, 999, 2024, 777]

    # Load baseline reference predictions
    log_exec("Loading baseline reference predictions for benchmark comparison...")
    base_preds: Dict[Tuple[str, str, int], pd.DataFrame] = {}
    for p in phases:
        for h in horizons:
            p_hist = root / config["paths"]["predictions_dir"] / "baseline" / f"historical_mean_{p}_h{h}.parquet"
            p_rw = root / config["paths"]["predictions_dir"] / "baseline" / f"random_walk_{p}_h{h}.parquet"
            if not p_hist.exists() or not p_rw.exists():
                raise FileNotFoundError(f"Missing baseline prediction files for phase {p} h{h}!")
            base_preds[("historical_mean", p, h)] = pd.read_parquet(p_hist)
            base_preds[("random_walk", p, h)] = pd.read_parquet(p_rw)

    # All 11 models required by prompt
    all_model_types = [
        "mlp",
        "lstm",
        "gru",
        "bilstm",
        "cnn1d",
        "tcn",
        "cnn_lstm",
        "transformer",
        "patch_tst",
        "dlinear",
        "nbeats",
    ]

    # Model specifications to run:
    # 1. Base models without RevIN on Feature Set C
    # 2. RevIN models (with RevIN) on Feature Set C
    # 3. Feature ablation across Feature Sets A, B, and C on representative architectures
    model_configs: List[Dict[str, Any]] = []

    # All 11 models with and without RevIN on primary Feature Set C
    for m in all_model_types:
        model_configs.append({"model_type": m, "use_revin": False, "feature_set": "C", "tag": m})
        model_configs.append({"model_type": m, "use_revin": True, "feature_set": "C", "tag": f"{m}_revin"})

    # Feature ablation on Sets A and B for representative models (MLP, LSTM, CNN1D, Transformer, DLinear)
    ablation_reps = ["mlp", "lstm", "cnn1d", "transformer", "dlinear"]
    for m in ablation_reps:
        for f_set in ["A", "B"]:
            model_configs.append({"model_type": m, "use_revin": True, "feature_set": f_set, "tag": f"{m}_revin"})

    log_exec(f"Configured {len(model_configs)} deep sequence model specifications.")

    # Storage for all new metric rows
    new_metrics_rows: List[Dict[str, Any]] = []
    collapse_flags: List[Dict[str, Any]] = []
    circuit_breaker_triggered = False
    circuit_breaker_details: List[str] = []

    # Cache for lookback selection: (phase, horizon, f_set, model_type, use_revin) -> best_L
    lookback_cache: Dict[Tuple[str, int, str, str, bool], int] = {}

    total_runs = len(phases) * len(horizons) * len(model_configs)
    run_idx = 0

    log_exec(f"Starting execution across {len(phases)} phases, {len(horizons)} horizons, {len(seeds)} seeds...")

    for p in phases:
        for h in horizons:
            bench_hist = base_preds[("historical_mean", p, h)]
            bench_rw = base_preds[("random_walk", p, h)]

            for m_cfg in model_configs:
                run_idx += 1
                m_type = m_cfg["model_type"]
                use_revin = m_cfg["use_revin"]
                f_set = m_cfg["feature_set"]
                m_tag = m_cfg["tag"]

                # 1. Select optimal lookback L in {20, 60, 120} strictly on inner-val split (Rule R2)
                cache_key = (p, h, m_type)
                if cache_key not in lookback_cache:
                    best_l, _ = select_best_lookback(
                        mgr=mgr,
                        phase=p,
                        horizon=h,
                        feature_set="C",
                        model_type=m_type,
                        use_revin=True,
                        device=device,
                        seed=42,
                    )
                    lookback_cache[cache_key] = best_l
                best_lookback = lookback_cache[cache_key]

                # 2. Extract sequence windows for chosen lookback L
                try:
                    seq_data = mgr.get_sequence_windows(
                        phase=p,
                        horizon=h,
                        feature_set=f_set,
                        lookback=best_lookback,
                    )
                except Exception as e:
                    log_exec(f"[ERROR] Window extraction failed for {m_tag} {p} h{h} set {f_set}: {e}")
                    continue

                in_features = seq_data.train.X_seq.shape[2]

                seed_predictions: List[pd.DataFrame] = []
                seed_runtimes: List[float] = []

                # 3. Train from scratch per phase across 5 seeds
                for s in seeds:
                    t0 = time.time()
                    try:
                        model = build_deep_model(
                            model_type=m_type,
                            in_features=in_features,
                            lookback=best_lookback,
                            use_revin=use_revin,
                        )

                        trainer = DeepSequenceTrainer(
                            model=model,
                            device=device,
                            lr=1e-3,
                            weight_decay=1e-4,
                            huber_delta=0.01,
                            dir_loss_weight=0.5,
                            grad_clip=1.0,
                            patience=3,
                            max_epochs=12,
                            time_budget_seconds=5.0,
                            seed=s,
                        )

                        fit_res = trainer.fit(
                            train_data=seq_data.train,
                            inner_val_data=seq_data.inner_val,
                            batch_size=128,
                        )

                        rt = time.time() - t0
                        seed_runtimes.append(rt)

                        # Generate out-of-sample predictions on outer validation window
                        df_pred_s, is_collapsed, diag = trainer.predict(
                            val_data=seq_data.val,
                            full_df=full_df,
                            model_name=m_tag,
                            phase=p,
                            horizon=h,
                            feature_set=f_set,
                        )
                        seed_predictions.append(df_pred_s)

                        # Save individual seed model artifacts
                        artifact_dir = models_deep_root / m_tag / p / f"seed_{s}"
                        trainer.save_artifacts(
                            artifact_dir=artifact_dir,
                            extra_meta={
                                "model_type": m_type,
                                "model_tag": m_tag,
                                "feature_set": f_set,
                                "horizon": h,
                                "lookback": best_lookback,
                                "use_revin": use_revin,
                                "fit_summary": fit_res,
                                "diagnostics": diag,
                            },
                        )

                        # Save individual seed prediction parquet
                        seed_pq = preds_deep_dir / f"{m_tag}_{f_set.lower()}_{p}_h{h}_s{s}.parquet"
                        df_pred_s.to_parquet(seed_pq, index=False)

                        # Evaluate individual seed predictions against aligned baselines
                        eval_res = harness.evaluate_predictions(df_pred_s, bench_hist, bench_rw)

                        # Record per-seed metrics
                        for k, v in eval_res.items():
                            if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                                new_metrics_rows.append({
                                    "model": m_tag,
                                    "family": "deep",
                                    "phase": p,
                                    "horizon": h,
                                    "feature_set": f_set,
                                    "seed": s,
                                    "metric": k,
                                    "value": float(v),
                                })

                        # Collapse tracking
                        if is_collapsed:
                            collapse_flags.append({
                                "model": m_tag,
                                "phase": p,
                                "horizon": h,
                                "feature_set": f_set,
                                "seed": s,
                                "pred_std": diag["pred_ret_std"],
                                "dir_mean": diag["pred_dir_mean"],
                            })

                        # Check Rule R3 circuit breaker
                        if eval_res.get("alarm_rule_r3", False):
                            circuit_breaker_triggered = True
                            circuit_breaker_details.append(
                                f"{m_tag} {p} h{h} s{s}: Acc={eval_res['accuracy']:.3f}, R2={eval_res['oos_r2']:.4f}"
                            )

                    except Exception as e:
                        log_exec(f"[ERROR FIT] {m_tag} {p} h{h} s{s}: {e}")

                # 4. Average seeds for headline row and headline prediction parquet
                if len(seed_predictions) == len(seeds):
                    # Average continuous predicted log returns and probabilities across seeds
                    avg_y_pred_ret = np.mean([df["y_pred_ret"].values for df in seed_predictions], axis=0)
                    avg_p_up = np.mean([df["p_up"].values for df in seed_predictions], axis=0)
                    avg_y_pred_dir = (avg_p_up > 0.5).astype(int)

                    base_df = seed_predictions[0].copy()
                    aspi_t = base_df["aspi_t"].values
                    aspi_pred_level = aspi_t * np.exp(avg_y_pred_ret)

                    df_avg = pd.DataFrame({
                        "model": m_tag,
                        "family": "deep",
                        "phase": p,
                        "horizon": h,
                        "feature_set": f_set,
                        "date": base_df["date"].values,
                        "y_true_ret": base_df["y_true_ret"].values,
                        "y_pred_ret": avg_y_pred_ret,
                        "p_up": avg_p_up,
                        "y_true_dir": base_df["y_true_dir"].values,
                        "y_pred_dir": avg_y_pred_dir,
                        "aspi_t": aspi_t,
                        "aspi_pred_level": aspi_pred_level,
                        "seed": -1,  # -1 represents averaged headline ensemble
                    })

                    # Save headline averaged predictions
                    harness.save_predictions(
                        df_preds=df_avg,
                        family="deep",
                        model=f"{m_tag}_{f_set.lower()}",
                        phase=p,
                        horizon=h,
                    )

                    # Evaluate headline predictions
                    eval_headline = harness.evaluate_predictions(df_avg, bench_hist, bench_rw)
                    for k, v in eval_headline.items():
                        if k not in ["model", "family", "phase", "horizon"] and isinstance(v, (int, float, np.floating, np.integer)):
                            new_metrics_rows.append({
                                "model": m_tag,
                                "family": "deep",
                                "phase": p,
                                "horizon": h,
                                "feature_set": f_set,
                                "seed": "ensemble",
                                "metric": k,
                                "value": float(v),
                            })

                log_exec(
                    f"[{run_idx}/{total_runs}] Done: {m_tag:<18} Phase={p} h={h} Set={f_set} L={best_lookback} (mean time: {np.mean(seed_runtimes):.2f}s/seed)"
                )

        log_exec(f"Completed Phase {p} across all deep models.")

    # =========================================================================
    # PART 2: APPEND METRICS TO METRICS_LONG.CSV AND BUILD LEADERBOARDS
    # =========================================================================
    log_exec("\n--- UPDATING METRICS_LONG.CSV AND GENERATING LEADERBOARD ---")

    metrics_long_path = metrics_dir / "metrics_long.csv"
    if metrics_long_path.exists():
        df_old_metrics = pd.read_csv(metrics_long_path)
        # Drop previous deep rows if any exist to prevent duplicate accumulation
        df_old_non_deep = df_old_metrics[df_old_metrics["family"] != "deep"]
        df_metrics_all = pd.concat([df_old_non_deep, pd.DataFrame(new_metrics_rows)], ignore_index=True)
    else:
        df_metrics_all = pd.DataFrame(new_metrics_rows)

    df_metrics_all.to_csv(metrics_long_path, index=False)
    log_exec(f"Saved updated metrics_long.csv ({len(df_metrics_all)} total rows) to {metrics_long_path}")

    # Report Collapsed Models
    log_exec("\n" + "=" * 80)
    log_exec("COLLAPSE SANITY DIAGNOSTICS (Rule R3 / Constant Predictor Check):")
    log_exec("=" * 80)
    if collapse_flags:
        log_exec(f"Identified {len(collapse_flags)} collapsed model runs (outputs trivially near-constant):")
        df_col = pd.DataFrame(collapse_flags)
        col_summary = df_col.groupby(["model", "phase", "horizon"])["seed"].count().reset_index()
        for _, r in col_summary.iterrows():
            log_exec(f"  FLAG: Model {r['model']} in {r['phase']} h{r['horizon']} had {r['seed']}/5 seeds collapsed.")
    else:
        log_exec("No model exhibited trivial output collapse. All return std >= 1e-4 and direction means in (0.02, 0.98).")

    # Check Circuit Breaker
    if circuit_breaker_triggered:
        log_exec("\n********************************************************************************")
        log_exec("RULE R3 CIRCUIT BREAKER ALARM TRIGGERED (Direction Acc > 60% or OOS R2 > 0.10):")
        for detail in circuit_breaker_details[:10]:
            log_exec(f"  ALARM: {detail}")
        if len(circuit_breaker_details) > 10:
            log_exec(f"  ... and {len(circuit_breaker_details) - 10} more occurrences.")
        log_exec("********************************************************************************")
    else:
        log_exec("\nRule R3 Verification: ALL deep models satisfy Direction Accuracy <= 60% and OOS R2 <= 0.10.")

    # Leaderboard Generation directly from saved metrics_long.csv (Rule R1)
    df_deep_m = df_metrics_all[df_metrics_all["family"] == "deep"].copy()
    headline_deep_m = df_deep_m[df_deep_m["seed"] == "ensemble"].copy()

    primary_metrics = ["oos_r2", "accuracy", "balanced_accuracy", "rmse", "mae"]
    pivot_deep = headline_deep_m[headline_deep_m["metric"].isin(primary_metrics)].copy()
    lb_deep_agg = pivot_deep.groupby(["model", "horizon", "feature_set", "metric"])["value"].mean().unstack("metric").reset_index()

    lb_deep_h5 = lb_deep_agg[lb_deep_agg["horizon"] == 5].sort_values("oos_r2", ascending=False).reset_index(drop=True)
    lb_deep_h1 = lb_deep_agg[lb_deep_agg["horizon"] == 1].sort_values("oos_r2", ascending=False).reset_index(drop=True)
    lb_deep_full = pd.concat([lb_deep_h5, lb_deep_h1], ignore_index=True)

    lb_deep_csv = tables_dir / "stage7_deep_leaderboard.csv"
    lb_deep_md = tables_dir / "stage7_deep_leaderboard.md"
    lb_deep_full.to_csv(lb_deep_csv, index=False)

    # Format Markdown
    cols = ["model", "horizon", "feature_set", "oos_r2", "accuracy", "balanced_accuracy", "rmse", "mae"]
    cols_present = [c for c in cols if c in lb_deep_full.columns]
    lines = ['| ' + ' | '.join(cols_present) + ' |', '| ' + ' | '.join(['---'] * len(cols_present)) + ' |']
    for _, r in lb_deep_full[cols_present].iterrows():
        row_str = []
        for c in cols_present:
            v = r[c]
            row_str.append(f"{v:.4f}" if isinstance(v, float) else str(v))
        lines.append('| ' + ' | '.join(row_str) + ' |')

    with open(lb_deep_md, "w", encoding="utf-8") as f:
        f.write("# STAGE 7 DEEP SEQUENCE MODELS LEADERBOARD\n\n")
        f.write("Generated programmatically from `results/metrics/metrics_long.csv` adhering strictly to Rule R1.\n\n")
        f.write("\n".join(lines) + "\n")

    log_exec(f"Saved Stage 7 leaderboard to {lb_deep_csv} and {lb_deep_md}")

    # Print top models
    print("\n" + "=" * 80)
    print("TOP 10 DEEP MODELS AT HORIZON h=5 (WEEKLY RETURN - PROPOSAL PRIMARY HORIZON):")
    print("=" * 80)
    print(lb_deep_h5[cols_present].head(10).to_string(index=False))

    print("\n" + "=" * 80)
    print("TOP 10 DEEP MODELS AT HORIZON h=1 (DAILY RETURN):")
    print("=" * 80)
    print(lb_deep_h1[cols_present].head(10).to_string(index=False))

    total_time = time.time() - t_start
    log_exec(f"\nStage 7 execution completed in {total_time:.2f} seconds ({total_time / 60:.2f} minutes).")


if __name__ == "__main__":
    run_stage7_evaluation()
