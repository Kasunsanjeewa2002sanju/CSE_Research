"""
Stage 11 Model Training & Walk-Forward Conformal Calibration.

1. Fits multi-horizon models (CatBoost/XGBoost regressors & calibrated classifiers)
   for horizons h in {1, 2, 5, 10} on Feature Set C.
2. Conducts 5-phase walk-forward validation (2012-2025) to collect out-of-sample residuals
   both inside event windows and across all trading days.
3. Computes exact split-conformal prediction quantiles (80% and 95% coverage)
   and historical magnitude caps (99.5% quantile).
4. Fits final frozen models on all data (1994-2025) and saves artifacts to models/final/.
"""

import json
import os
import pickle
import sys
import time
from pathlib import Path

# Set up project root
root_dir = Path(__file__).resolve().parent.parent
os.chdir(str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRegressor
from sklearn.linear_model import LogisticRegression

from cse.splits.walk_forward import ExpandingWindowSplitter

HORIZONS = [1, 2, 5, 10]


def run_training_and_calibration():
    print("=" * 80)
    print("  STAGE 11: MULTI-HORIZON TRAINING & CONFORMAL CALIBRATION")
    print("=" * 80)
    t_start = time.time()

    # 1. Load data
    features_path = root_dir / "data" / "processed" / "features_set_c.parquet"
    cse_path = root_dir / "data" / "processed" / "cse_clean.parquet"
    
    df_features = pd.read_parquet(features_path)
    df_cse = pd.read_parquet(cse_path)

    n_samples = len(df_features)
    feature_cols = df_features.columns.tolist()
    print(f"Loaded Feature Set C: {df_features.shape} ({len(feature_cols)} features)")
    print(f"Loaded CSE clean data: {df_cse.shape} ({df_cse['date'].min()} to {df_cse['date'].max()})")

    # 2. Compute targets for h in [1, 2, 5, 10]
    aspi_levels = df_cse["aspi"].values.astype(float)
    targets_dict = {}
    magnitude_caps = {}

    for h in HORIZONS:
        ret_h = np.full(n_samples, np.nan)
        ret_h[:-h] = np.log(aspi_levels[h:] / aspi_levels[:-h])
        dir_h = np.where(np.isnan(ret_h), np.nan, (ret_h > 0).astype(float))
        
        targets_dict[f"y_ret_h{h}"] = ret_h
        targets_dict[f"y_dir_h{h}"] = dir_h

        # Magnitude cap: 99.5th percentile of historical absolute return
        valid_ret = np.abs(ret_h[~np.isnan(ret_h)])
        cap_val = float(np.quantile(valid_ret, 0.995))
        magnitude_caps[str(h)] = cap_val
        print(f"Horizon h={h:2d}: return range [{np.nanmin(ret_h):.4f}, {np.nanmax(ret_h):.4f}], 99.5% Cap = {cap_val:.4f}")

    df_targets = pd.DataFrame(targets_dict)

    # Identify event window mask (active electoral stage)
    # stage_none == 0 means an active stage is present
    if "stage_none" in df_features.columns:
        is_event = (df_features["stage_none"] == 0).values
    elif "in_window_0_7" in df_features.columns:
        is_event = (df_features["in_window_0_7"] == 1).values
    else:
        is_event = np.zeros(n_samples, dtype=bool)

    print(f"Total event-window trading days in sample: {np.sum(is_event)} / {n_samples}")

    os.environ["MPLCONFIGDIR"] = str(root_dir / ".cache" / "matplotlib")
    (root_dir / ".cache" / "matplotlib").mkdir(parents=True, exist_ok=True)

    # 3. Walk-Forward Validation for Conformal Residuals
    splitter = ExpandingWindowSplitter(df=df_cse)
    phases = list(splitter.splits.values())
    print(f"\nRunning 5-Phase Walk-Forward Evaluation across {len(phases)} phases...")

    # Dictionaries to accumulate out-of-sample absolute residuals
    oos_abs_residuals_event = {h: [] for h in HORIZONS}
    oos_abs_residuals_non_event = {h: [] for h in HORIZONS}
    oos_abs_residuals_all = {h: [] for h in HORIZONS}

    X_all = df_features.values

    # Fit hyperparameters matching Stage 9 champion
    cb_params = {
        "iterations": 80,
        "learning_rate": 0.05,
        "depth": 4,
        "random_seed": 42,
        "verbose": 0,
    }

    for phase in phases:
        tr_idx = np.arange(phase.train.start_idx, phase.train.end_idx + 1)
        val_idx = np.arange(phase.val.start_idx, phase.val.end_idx + 1)

        X_tr = X_all[tr_idx]
        X_val = X_all[val_idx]
        val_is_event = is_event[val_idx]

        for h in HORIZONS:
            y_ret_tr = df_targets[f"y_ret_h{h}"].values[tr_idx]
            y_ret_val = df_targets[f"y_ret_h{h}"].values[val_idx]

            # Filter valid (non-NaN)
            valid_tr = ~np.isnan(y_ret_tr)
            valid_val = ~np.isnan(y_ret_val)

            if np.sum(valid_tr) == 0 or np.sum(valid_val) == 0:
                continue

            reg = CatBoostRegressor(**cb_params)
            reg.fit(X_tr[valid_tr], y_ret_tr[valid_tr])
            preds_val = reg.predict(X_val[valid_val])

            actual_val = y_ret_val[valid_val]
            abs_res = np.abs(actual_val - preds_val)
            ev_mask = val_is_event[valid_val]

            oos_abs_residuals_all[h].extend(abs_res.tolist())
            oos_abs_residuals_event[h].extend(abs_res[ev_mask].tolist())
            oos_abs_residuals_non_event[h].extend(abs_res[~ev_mask].tolist())

    # 4. Compute Conformal Prediction Quantiles
    conformal_quantiles = {}
    print("\nConformal Prediction Quantiles (Empirical Out-of-Sample Coverage):")
    for h in HORIZONS:
        res_ev = np.array(oos_abs_residuals_event[h])
        res_non = np.array(oos_abs_residuals_non_event[h])
        res_all = np.array(oos_abs_residuals_all[h])

        # If event sample is small, fall back to pooled
        if len(res_ev) < 30:
            res_ev = res_all

        q80_ev = float(np.quantile(res_ev, 0.80))
        q95_ev = float(np.quantile(res_ev, 0.95))
        q80_non = float(np.quantile(res_non, 0.80))
        q95_non = float(np.quantile(res_non, 0.95))

        conformal_quantiles[str(h)] = {
            "n_event_residuals": len(res_ev),
            "n_non_event_residuals": len(res_non),
            "event": {
                "coverage_80": q80_ev,
                "coverage_95": q95_ev,
            },
            "non_event": {
                "coverage_80": q80_non,
                "coverage_95": q95_non,
            },
        }
        print(f"  h={h:2d} | Event (n={len(res_ev):3d}): 80% = ±{q80_ev*100:.2f}%, 95% = ±{q95_ev*100:.2f}% | Non-Event: 80% = ±{q80_non*100:.2f}%, 95% = ±{q95_non*100:.2f}%")

    # 5. Fit Final Frozen Models on ALL historical data (1994-2025)
    print("\nFitting final frozen multi-horizon models on ALL historical data...")
    final_models = {}

    for h in HORIZONS:
        y_ret = df_targets[f"y_ret_h{h}"].values
        y_dir = df_targets[f"y_dir_h{h}"].values

        valid_mask = ~np.isnan(y_ret) & ~np.isnan(y_dir)
        X_train_final = X_all[valid_mask]
        y_ret_final = y_ret[valid_mask]
        y_dir_final = y_dir[valid_mask]

        # Regressor
        reg = CatBoostRegressor(**cb_params)
        reg.fit(X_train_final, y_ret_final)

        # Classifier for direction probability
        clf = CatBoostClassifier(iterations=80, learning_rate=0.05, depth=4, random_seed=42, verbose=0)
        clf.fit(X_train_final, y_dir_final)

        # Calibrator via logistic regression on predictions
        raw_probs = clf.predict_proba(X_train_final)[:, 1]
        calibrator = LogisticRegression(C=1.0, solver="lbfgs")
        calibrator.fit(raw_probs.reshape(-1, 1), y_dir_final)

        final_models[h] = {
            "regressor": reg,
            "classifier": clf,
            "calibrator": calibrator,
        }

    # 6. Save Artifacts to models/final/
    models_final_dir = root_dir / "models" / "final"
    models_final_dir.mkdir(parents=True, exist_ok=True)

    with open(models_final_dir / "scenario_models.pkl", "wb") as f:
        pickle.dump(final_models, f)

    with open(models_final_dir / "conformal_residuals.json", "w", encoding="utf-8") as f:
        json.dump(conformal_quantiles, f, indent=2)

    with open(models_final_dir / "magnitude_caps.json", "w", encoding="utf-8") as f:
        json.dump(magnitude_caps, f, indent=2)

    with open(models_final_dir / "feature_columns.json", "w", encoding="utf-8") as f:
        json.dump(feature_cols, f, indent=2)

    meta = {
        "stage": "STAGE_11",
        "description": "Multi-horizon scenario forecasting models and conformal residuals",
        "horizons": HORIZONS,
        "n_samples": n_samples,
        "n_features": len(feature_cols),
        "data_range": [str(df_cse["date"].min()), str(df_cse["date"].max())],
        "frozen_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_type": "CatBoost (Regressor + Calibrated Classifier)",
        "hyperparameters": cb_params,
        "elapsed_seconds": round(time.time() - t_start, 2),
    }

    with open(models_final_dir / "scenario_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\nAll Stage 11 model artifacts successfully saved to {models_final_dir}")
    print(f"Elapsed time: {time.time() - t_start:.2f} seconds.")


if __name__ == "__main__":
    run_training_and_calibration()
