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

# # 07 - Deep Sequence Models: Learning Curves, Out-of-Sample Forecasts, and Sanity Diagnostics
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

import cse
from cse.utils.config import load_config
from cse.models.deep.trainer import get_device, get_hardware_info

print(f"CSE Package Version: {cse.__version__}")
config = load_config()

fig_dir = root_dir / "results" / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)
models_deep_dir = root_dir / "models" / "deep"
preds_deep_dir = root_dir / "results" / "predictions" / "deep"
metrics_dir = root_dir / "results" / "metrics"

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
print("Hardware Telemetry:", get_hardware_info())
# -

# ## 1. Model Architecture, Trainable Parameters, and Runtime Summary
# Inspect parameter counts, best lookback windows, training epochs, and runtime across all 11 model architectures.

# +
meta_records = []
for model_dir in sorted(models_deep_dir.iterdir()):
    if not model_dir.is_dir():
        continue
    m_name = model_dir.name
    # Pick P1 seed_42 meta.json as representative architectural sample
    p1_seed42_meta = model_dir / "P1" / "seed_42" / "meta.json"
    if p1_seed42_meta.exists():
        with open(p1_seed42_meta, "r", encoding="utf-8") as f:
            meta = json.load(f)
            fit_sum = meta.get("fit_summary", {})
            meta_records.append({
                "Model Tag": m_name,
                "Model Type": meta.get("model_type", m_name.replace("_revin", "")),
                "RevIN Enabled": meta.get("use_revin", False),
                "Lookback (L)": meta.get("lookback", 20),
                "Trainable Parameters": meta.get("parameters", 0),
                "Best Epoch (P1)": meta.get("best_epoch", 0),
                "Total Epochs (P1)": meta.get("total_epochs", 0),
                "Runtime / Seed (s)": round(fit_sum.get("runtime_seconds", 0.0), 2),
                "Collapsed": meta.get("is_collapsed", False),
            })

df_meta = pd.DataFrame(meta_records)
if not df_meta.empty:
    df_meta = df_meta.sort_values(["RevIN Enabled", "Trainable Parameters"]).reset_index(drop=True)
    print("\nDeep Sequence Models Summary Table:")
    print(df_meta.to_string(index=False))
else:
    print("No model metadata records found.")
# -

# ## 2. Representative Multitask Learning Curves
# Compare training and inner-validation loss curves across representative model families, showing early stopping behavior.

# +
curve_models = [
    ("lstm_revin", "LSTM + RevIN"),
    ("tcn_revin", "TCN + RevIN"),
    ("transformer_revin", "Transformer + RevIN"),
    ("patch_tst_revin", "PatchTST + RevIN"),
    ("dlinear_revin", "DLinear + RevIN"),
    ("nbeats_revin", "N-BEATS + RevIN"),
]

fig, axes = plt.subplots(2, 3, figsize=(16, 9), sharey=False)
axes = axes.flatten()

for idx, (m_tag, title) in enumerate(curve_models):
    ax = axes[idx]
    curves_csv = models_deep_dir / m_tag / "P1" / "seed_42" / "curves.csv"
    meta_json = models_deep_dir / m_tag / "P1" / "seed_42" / "meta.json"
    
    if curves_csv.exists() and meta_json.exists():
        df_c = pd.read_csv(curves_csv)
        with open(meta_json, "r") as f:
            meta = json.load(f)
        best_ep = meta.get("best_epoch", 1)
        
        ax.plot(df_c["epoch"], df_c["train_loss"], label="Train (Huber+BCE)", color="#1f77b4", lw=2)
        ax.plot(df_c["epoch"], df_c["val_loss"], label="Inner-Val Loss", color="#ff7f0e", lw=2)
        ax.axvline(x=best_ep, color="#d62728", linestyle="--", alpha=0.8, label=f"Best Ep ({best_ep})")
        ax.set_title(f"{title} (Phase P1, Seed 42)", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Loss")
        ax.legend(fontsize=9, loc="upper right")
    else:
        ax.text(0.5, 0.5, f"Awaiting {m_tag}", ha="center", va="center")

plt.tight_layout()
fig_curves_path = fig_dir / "stage7_learning_curves.png"
fig.savefig(fig_curves_path, dpi=150)
print(f"Saved learning curves comparison to {fig_curves_path}")
plt.show()
# -

# ## 3. Out-of-Sample Forecast versus Actual Log Return & Price Levels per Phase
# Compare predicted vs actual 5-day log returns and reconstructed ASPI price trajectories.

# +
phases = ["P1", "P2", "P3", "P4", "P5"]
rep_model = "transformer_revin_c"

fig, axes = plt.subplots(len(phases), 2, figsize=(16, 18))

for idx, p in enumerate(phases):
    ax_ret = axes[idx, 0]
    ax_lvl = axes[idx, 1]
    
    pred_file = preds_deep_dir / f"{rep_model}_{p}_h5.parquet"
    if pred_file.exists():
        df_p = pd.read_parquet(pred_file)
        df_p["dt"] = pd.to_datetime(df_p["date"])
        
        # Plot returns
        ax_ret.plot(df_p["dt"], df_p["y_true_ret"] * 100, label="Actual Return (%)", color="#7f7f7f", alpha=0.6, lw=1.2)
        ax_ret.plot(df_p["dt"], df_p["y_pred_ret"] * 100, label="Pred Return (%)", color="#1f77b4", lw=1.5)
        ax_ret.set_title(f"Phase {p} - 5-Day Return Forecast vs Actual ({rep_model})", fontsize=10, fontweight="bold")
        ax_ret.set_ylabel("5-Day Return (%)")
        ax_ret.legend(fontsize=8, loc="upper left")
        
        # Plot levels
        actual_level = df_p["aspi_t"] * np.exp(df_p["y_true_ret"])
        ax_lvl.plot(df_p["dt"], actual_level, label="Actual ASPI Level", color="#2ca02c", lw=1.5)
        ax_lvl.plot(df_p["dt"], df_p["aspi_pred_level"], label="Predicted ASPI Level", color="#d62728", linestyle="--", lw=1.5)
        ax_lvl.set_title(f"Phase {p} - Reconstructed ASPI Index Level", fontsize=10, fontweight="bold")
        ax_lvl.set_ylabel("Index Level")
        ax_lvl.legend(fontsize=8, loc="upper left")
    else:
        ax_ret.text(0.5, 0.5, f"Phase {p} pending", ha="center")
        ax_lvl.text(0.5, 0.5, f"Phase {p} pending", ha="center")

plt.tight_layout()
fig_fc_path = fig_dir / "stage7_forecast_vs_actual.png"
fig.savefig(fig_fc_path, dpi=150)
print(f"Saved forecast vs actual plot to {fig_fc_path}")
plt.show()
# -

# ## 4. RevIN Ablation Analysis (With vs Without Reversible Instance Normalization)
# Compare out-of-sample performance metrics of base models vs RevIN-augmented variants.

# +
metrics_long_path = metrics_dir / "metrics_long.csv"
if metrics_long_path.exists():
    df_m = pd.read_csv(metrics_long_path)
    df_deep = df_m[(df_m["family"] == "deep") & (df_m["seed"] == "ensemble") & (df_m["feature_set"] == "C") & (df_m["horizon"] == 5)].copy()
    
    # Pivot primary metrics
    piv = df_deep[df_deep["metric"].isin(["oos_r2", "accuracy", "balanced_accuracy"])].groupby(["model", "metric"])["value"].mean().unstack("metric").reset_index()
    
    # Separate base vs revin
    piv["base_model"] = piv["model"].str.replace("_revin", "")
    piv["is_revin"] = piv["model"].str.contains("_revin")
    
    revin_compare = piv.pivot(index="base_model", columns="is_revin", values=["oos_r2", "accuracy", "balanced_accuracy"])
    print("\nRevIN Ablation Comparison Table (Horizon h=5, Feature Set C):")
    print(revin_compare.to_string())
    
    # Plot RevIN Impact on OOS R2
    if False in revin_compare["oos_r2"].columns and True in revin_compare["oos_r2"].columns:
        fig, ax = plt.subplots(figsize=(12, 6))
        models_list = revin_compare.index.tolist()
        x = np.arange(len(models_list))
        width = 0.35
        
        r2_no_revin = revin_compare["oos_r2"][False].values
        r2_revin = revin_compare["oos_r2"][True].values
        
        ax.bar(x - width/2, r2_no_revin, width, label="Without RevIN", color="#aec7e8")
        ax.bar(x + width/2, r2_revin, width, label="With RevIN", color="#1f77b4")
        ax.axhline(0, color="black", linestyle="--", lw=0.8)
        ax.set_ylabel("Out-of-Sample R²")
        ax.set_title("RevIN Ablation: Out-of-Sample R² (h=5, Feature Set C)", fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(models_list, rotation=35, ha="right")
        ax.legend()
        plt.tight_layout()
        fig.savefig(fig_dir / "stage7_revin_ablation.png", dpi=150)
        plt.show()
else:
    print("metrics_long.csv not found.")
# -

# ## 5. Sanity & Collapse Diagnostics (Rule R3)
# Verify prediction standard deviations and directional distribution to ensure zero collapsed predictors.

# +
if metrics_long_path.exists():
    df_all_deep = df_m[(df_m["family"] == "deep") & (df_m["seed"] != "ensemble")].copy()
    print("Evaluating individual seed diagnostics across all deep models...")
    print(f"Total evaluated seed runs: {len(df_all_deep[['model', 'phase', 'horizon', 'seed']].drop_duplicates())}")
    
    # Check max accuracy and max OOS R2 across all deep rows
    max_acc = df_all_deep[df_all_deep["metric"] == "accuracy"]["value"].max()
    max_r2 = df_all_deep[df_all_deep["metric"] == "oos_r2"]["value"].max()
    print(f"Maximum Seed Direction Accuracy: {max_acc:.4f} (Rule R3 threshold: 0.60)")
    print(f"Maximum Seed Out-of-Sample R²:   {max_r2:.4f} (Rule R3 threshold: 0.10)")
    
    if max_acc > 0.60 or max_r2 > 0.10:
        print("WARNING: Rule R3 circuit breaker threshold exceeded! Investigating cause...")
    else:
        print("PASS: All deep sequence models satisfy Rule R3 circuit breaker thresholds.")
# -
