# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # 06 - Shallow ML Models: Training-Only Feature Importances, Calibration, and Performance
# Quantitative ML Research - Colombo Stock Exchange (CSE) ASPI Project
# Strictly following Rules R1, R2, R3, R4, R5, R6, R7, R8, R10.

# +
import sys
import os
import json
from pathlib import Path

# Configure local matplotlib cache directory
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(__file__), "..", ".cache", "matplotlib")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve

import cse
from cse.utils.config import load_config

print(f"CSE Package Version: {cse.__version__}")
config = load_config()

fig_dir = root_dir / "results" / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)
models_shallow_dir = root_dir / "models" / "shallow"
preds_shallow_dir = root_dir / "results" / "predictions" / "shallow"
# -

# ## 1. Training-Only Feature Importances (Tree Models)
# Rule R2: Feature importances extracted strictly from fitted training models, never from validation data.

# +
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

tree_families = ["random_forest_reg", "gradient_boosting_reg", "xgboost_reg", "lightgbm_reg"]
feature_sets = ["a", "b", "c"]
phases = ["P1", "P3", "P5"]

fig, axes = plt.subplots(len(tree_families), len(phases), figsize=(18, 16), sharey=False)

for i, t_fam in enumerate(tree_families):
    for j, p in enumerate(phases):
        ax = axes[i, j]
        # Look for model artifact in models/shallow/{t_fam}_c/{p} or {t_fam}_b/{p}
        meta_file = models_shallow_dir / f"{t_fam}_c" / p / "meta.json"
        if not meta_file.exists():
            meta_file = models_shallow_dir / f"{t_fam}_b" / p / "meta.json"
        if not meta_file.exists():
            meta_file = models_shallow_dir / f"{t_fam}_a" / p / "meta.json"

        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            extra = meta.get("extra_meta", {})
            importances = extra.get("feature_importances", {})

            if importances:
                # Sort top 10 features
                top_items = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]
                feat_names = [x[0] for x in top_items][::-1]
                feat_vals = [x[1] for x in top_items][::-1]

                ax.barh(range(len(feat_names)), feat_vals, color="steelblue", alpha=0.85)
                ax.set_yticks(range(len(feat_names)))
                ax.set_yticklabels(feat_names, fontsize=8)
                ax.set_xlabel("Relative Importance (Training Data Only)")
        
        ax.set_title(f"{t_fam.replace('_', ' ').title()} - Phase {p}", fontsize=10, fontweight="bold")

plt.tight_layout()
fig_imp_path = fig_dir / "fig_tree_feature_importances_training_only.png"
plt.savefig(fig_imp_path, dpi=150)
plt.close()
print(f"Saved training-only feature importances plot to: {fig_imp_path}")
# -

# ## 2. Probability Calibration Curves (Reliability Diagrams)
# Evaluates whether predicted Pr(y > 0) matches actual realized positive return frequencies.

# +
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

models_to_plot = ["random_forest_clf", "gradient_boosting_clf", "xgboost_clf", "lightgbm_clf", "logistic_regression"]

for h_idx, h in enumerate([1, 5]):
    ax = axes[h_idx]
    ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")

    for m_name in models_to_plot:
        all_true = []
        all_prob = []

        for p in ["P1", "P2", "P3", "P4", "P5"]:
            f_p = preds_shallow_dir / f"{m_name}_c_s42_{p}_h{h}.parquet"
            if not f_p.exists():
                f_p = preds_shallow_dir / f"{m_name}_b_s42_{p}_h{h}.parquet"
            if not f_p.exists():
                # check statistical for logistic regression
                f_p = root_dir / "results" / "predictions" / "statistical" / f"{m_name}_c_{p}_h{h}.parquet"

            if f_p.exists():
                df_preds = pd.read_parquet(f_p)
                all_true.extend(df_preds["y_true_dir"].values)
                all_prob.extend(df_preds["p_up"].values)

        if len(all_true) > 0:
            prob_true, prob_pred = calibration_curve(all_true, all_prob, n_bins=8, strategy="uniform")
            ax.plot(prob_pred, prob_true, marker="o", label=m_name.replace("_", " ").title())

    ax.set_title(f"Reliability Diagram (Calibration Curve) - Horizon h={h}", fontsize=11, fontweight="bold")
    ax.set_xlabel("Mean Predicted Probability P(Up)")
    ax.set_ylabel("Empirical Frequency of Positive Return")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.0])

plt.tight_layout()
fig_cal_path = fig_dir / "fig_shallow_calibration_curves.png"
plt.savefig(fig_cal_path, dpi=150)
plt.close()
print(f"Saved calibration reliability curves to: {fig_cal_path}")
# -

# ## 3. Out-of-Sample Return Forecast vs Actual Across Phases (RF, XGB, LGBM)

# +
fig, axes = plt.subplots(5, 2, figsize=(16, 20), sharex=False)

for i, p in enumerate(["P1", "P2", "P3", "P4", "P5"]):
    for j, h in enumerate([1, 5]):
        ax = axes[i, j]

        f_rf = preds_shallow_dir / f"random_forest_reg_c_s42_{p}_h{h}.parquet"
        f_xgb = preds_shallow_dir / f"xgboost_reg_c_s42_{p}_h{h}.parquet"
        f_lgb = preds_shallow_dir / f"lightgbm_reg_c_s42_{p}_h{h}.parquet"

        if f_rf.exists():
            df_rf = pd.read_parquet(f_rf)
            dates = pd.to_datetime(df_rf["date"])
            ax.plot(dates, df_rf["y_true_ret"], label="Actual Realized", color="black", alpha=0.35, lw=1.0)
            ax.plot(dates, df_rf["y_pred_ret"], label="Random Forest (Set C)", color="tab:blue", lw=1.4)

            if f_xgb.exists():
                df_xgb = pd.read_parquet(f_xgb)
                ax.plot(dates, df_xgb["y_pred_ret"], label="XGBoost (Set C)", color="tab:red", lw=1.2, ls="--")

            if f_lgb.exists():
                df_lgb = pd.read_parquet(f_lgb)
                ax.plot(dates, df_lgb["y_pred_ret"], label="LightGBM (Set C)", color="tab:green", lw=1.2, ls=":")

        ax.set_title(f"Phase {p} (Horizon h={h}) - Shallow ML Forecast vs Actual", fontsize=11, fontweight="bold")
        ax.set_ylabel("Log Return")
        if i == 0 and j == 0:
            ax.legend(loc="upper right", fontsize=9)
        if i == 4:
            ax.set_xlabel("Date")

plt.tight_layout()
fig_sh_path = fig_dir / "fig_shallow_forecast_vs_actual.png"
plt.savefig(fig_sh_path, dpi=150)
plt.close()
print(f"Saved shallow ML forecast comparison plot to: {fig_sh_path}")
print("Shallow notebook execution completed successfully.")
# -
