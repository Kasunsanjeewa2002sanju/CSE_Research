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

# # 06 - Statistical Models: Evaluation, Diagnostics, and Volatility Forecasting
# Quantitative ML Research - Colombo Stock Exchange (CSE) ASPI Project
# Strictly following Rules R1, R2, R3, R4, R5, R6, R7, R8, R10.

# +
import sys
import os
from pathlib import Path

# Set local matplotlib cache directory
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(__file__), "..", ".cache", "matplotlib")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf

import cse
from cse.utils.config import load_config
from cse.models.statistical.garch import calc_variance_metrics

print(f"CSE Package Version: {cse.__version__}")
config = load_config()

fig_dir = root_dir / "results" / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)
# -

# ## 1. Load Clean Panel & Statistical Predictions

# +
preds_dir = root_dir / "results" / "predictions" / "statistical"
phases = ["P1", "P2", "P3", "P4", "P5"]
horizons = [1, 5]

print("Available statistical prediction files in results/predictions/statistical:")
stat_files = sorted(list(preds_dir.glob("*.parquet")))
print(f"Found {len(stat_files)} statistical prediction files.")
# -

# ## 2. Forecast vs Actual Plots across Validation Phases (ARIMA, SARIMA, ETS)

# +
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, axes = plt.subplots(len(phases), 2, figsize=(16, 20), sharex=False)

for i, p in enumerate(phases):
    for j, h in enumerate(horizons):
        ax = axes[i, j]
        # Load ARIMA predictions
        f_arima = preds_dir / f"arima_{p}_h{h}.parquet"
        f_sarima = preds_dir / f"sarima_m5_{p}_h{h}.parquet"
        f_ets = preds_dir / f"ets_holt_winters_{p}_h{h}.parquet"

        if f_arima.exists():
            df_arima = pd.read_parquet(f_arima)
            dates = pd.to_datetime(df_arima["date"])
            ax.plot(dates, df_arima["y_true_ret"], label="Actual Realized", color="black", alpha=0.4, lw=1.0)
            ax.plot(dates, df_arima["y_pred_ret"], label="ARIMA Forecast", color="tab:blue", lw=1.5)

            if f_sarima.exists():
                df_sarima = pd.read_parquet(f_sarima)
                ax.plot(dates, df_sarima["y_pred_ret"], label="SARIMA (m=5)", color="tab:orange", lw=1.2, ls="--")

            if f_ets.exists():
                df_ets = pd.read_parquet(f_ets)
                ax.plot(dates, df_ets["y_pred_ret"], label="ETS (Holt-Winters)", color="tab:green", lw=1.2, ls=":")

        ax.set_title(f"Phase {p} (Horizon h={h}) - Return Forecast vs Actual", fontsize=11, fontweight="bold")
        ax.set_ylabel("Log Return")
        if i == len(phases) - 1:
            ax.set_xlabel("Date")
        if i == 0 and j == 0:
            ax.legend(loc="upper right", fontsize=9)

plt.tight_layout()
fig_path = fig_dir / "fig_statistical_forecast_vs_actual.png"
plt.savefig(fig_path, dpi=150)
plt.close()
print(f"Saved forecast-versus-actual comparison plot to: {fig_path}")
# -

# ## 3. Residual Diagnostics for ARIMA and SARIMA (Ljung-Box Test)

# +
diagnostic_records = []

for p in phases:
    for h in [1]:
        f_arima = preds_dir / f"arima_{p}_h{h}.parquet"
        f_sarima_5 = preds_dir / f"sarima_m5_{p}_h{h}.parquet"
        f_sarima_21 = preds_dir / f"sarima_m21_{p}_h{h}.parquet"

        for label, f_path in [("ARIMA", f_arima), ("SARIMA_m5", f_sarima_5), ("SARIMA_m21", f_sarima_21)]:
            if f_path.exists():
                df_p = pd.read_parquet(f_path)
                residuals = df_p["y_true_ret"].values - df_p["y_pred_ret"].values
                # Ljung-Box test at lags 5, 10, 20
                lb_res = acorr_ljungbox(residuals, lags=[5, 10, 20], return_df=True)
                
                lb_stat_5 = lb_res.loc[5, "lb_stat"]
                lb_pval_5 = lb_res.loc[5, "lb_pvalue"]
                lb_pval_10 = lb_res.loc[10, "lb_pvalue"]
                lb_pval_20 = lb_res.loc[20, "lb_pvalue"]

                diagnostic_records.append({
                    "phase": p,
                    "model": label,
                    "n_obs": len(residuals),
                    "mean_resid": np.mean(residuals),
                    "std_resid": np.std(residuals),
                    "lb_stat_lag5": lb_stat_5,
                    "lb_pval_lag5": lb_pval_5,
                    "lb_pval_lag10": lb_pval_10,
                    "lb_pval_lag20": lb_pval_20,
                    "white_noise_at_5pct": "Yes" if lb_pval_5 > 0.05 else "No (Autocorrelated)",
                })

df_diag = pd.DataFrame(diagnostic_records)
print("\n--- RESIDUAL DIAGNOSTICS: LJUNG-BOX TEST RESULTS ---")
print(df_diag.to_string(index=False))

diag_csv = root_dir / "results" / "tables" / "statistical_residual_diagnostics.csv"
df_diag.to_csv(diag_csv, index=False)
print(f"Saved residual diagnostics to: {diag_csv}")
# -

# ## 4. Ljung-Box Autocorrelation Function (ACF) Diagnostic Plot

# +
fig, axes = plt.subplots(len(phases), 2, figsize=(14, 15))

for i, p in enumerate(phases):
    f_arima = preds_dir / f"arima_{p}_h1.parquet"
    f_sarima = preds_dir / f"sarima_m5_{p}_h1.parquet"

    if f_arima.exists():
        res_arima = pd.read_parquet(f_arima)["y_true_ret"].values - pd.read_parquet(f_arima)["y_pred_ret"].values
        acf_arima = acf(res_arima, nlags=20, fft=True)
        axes[i, 0].stem(range(len(acf_arima)), acf_arima)
        axes[i, 0].axhline(y=1.96 / np.sqrt(len(res_arima)), ls="--", color="red", alpha=0.6)
        axes[i, 0].axhline(y=-1.96 / np.sqrt(len(res_arima)), ls="--", color="red", alpha=0.6)
        axes[i, 0].set_title(f"Phase {p} - ARIMA Residual ACF", fontsize=10, fontweight="bold")
        axes[i, 0].set_ylabel("ACF")

    if f_sarima.exists():
        res_sarima = pd.read_parquet(f_sarima)["y_true_ret"].values - pd.read_parquet(f_sarima)["y_pred_ret"].values
        acf_sarima = acf(res_sarima, nlags=20, fft=True)
        axes[i, 1].stem(range(len(acf_sarima)), acf_sarima)
        axes[i, 1].axhline(y=1.96 / np.sqrt(len(res_sarima)), ls="--", color="red", alpha=0.6)
        axes[i, 1].axhline(y=-1.96 / np.sqrt(len(res_sarima)), ls="--", color="red", alpha=0.6)
        axes[i, 1].set_title(f"Phase {p} - SARIMA (m=5) Residual ACF", fontsize=10, fontweight="bold")
        axes[i, 1].set_ylabel("ACF")

axes[-1, 0].set_xlabel("Lag (Trading Days)")
axes[-1, 1].set_xlabel("Lag (Trading Days)")
plt.tight_layout()
fig_acf_path = fig_dir / "fig_arima_sarima_residual_acf.png"
plt.savefig(fig_acf_path, dpi=150)
plt.close()
print(f"Saved residual ACF diagnostics to: {fig_acf_path}")
# -

# ## 5. GARCH Volatility Forecasting Evaluation (QLIKE & Realized Variance MSE)

# +
garch_eval_records = []

for p in phases:
    for h in horizons:
        for m_name in ["garch_11", "egarch_11", "gjr_garch_11"]:
            f_vol = preds_dir / f"{m_name}_{p}_h{h}.parquet"
            if f_vol.exists():
                df_vol = pd.read_parquet(f_vol)
                rv = df_vol["realized_variance"].values
                pv = df_vol["predicted_variance"].values
                v_metrics = calc_variance_metrics(rv, pv)
                garch_eval_records.append({
                    "model": m_name,
                    "phase": p,
                    "horizon": h,
                    "n_obs": len(df_vol),
                    "mean_realized_vol": float(np.mean(df_vol["realized_volatility"])),
                    "mean_predicted_vol": float(np.mean(df_vol["predicted_volatility"])),
                    "qlike": v_metrics["qlike"],
                    "mse_variance": v_metrics["mse_realized_variance"],
                    "mae_volatility": v_metrics["mae_realized_volatility"],
                    "mz_r2": v_metrics["mincer_zarnowitz_r2"],
                })

df_garch_eval = pd.DataFrame(garch_eval_records)
print("\n--- GARCH CONDITIONAL VOLATILITY FORECASTING PERFORMANCE ---")
print(df_garch_eval.head(15).to_string(index=False))

vol_csv = root_dir / "results" / "tables" / "garch_volatility_evaluation.csv"
df_garch_eval.to_csv(vol_csv, index=False)
print(f"Saved volatility evaluation table to: {vol_csv}")
# -

# ## 6. Volatility Forecast vs Realized Variance Plot

# +
fig, axes = plt.subplots(len(phases), 1, figsize=(14, 18), sharex=False)

for i, p in enumerate(phases):
    ax = axes[i]
    f_garch = preds_dir / f"garch_11_{p}_h1.parquet"
    f_egarch = preds_dir / f"egarch_11_{p}_h1.parquet"
    f_gjr = preds_dir / f"gjr_garch_11_{p}_h1.parquet"

    if f_garch.exists():
        df_g = pd.read_parquet(f_garch)
        dates = pd.to_datetime(df_g["date"])
        ax.plot(dates, df_g["realized_volatility"], label="Realized Volatility (|r| proxy)", color="black", alpha=0.35, lw=1.0)
        ax.plot(dates, df_g["predicted_volatility"], label="GARCH(1,1)", color="tab:blue", lw=1.5)

        if f_egarch.exists():
            df_eg = pd.read_parquet(f_egarch)
            ax.plot(dates, df_eg["predicted_volatility"], label="EGARCH(1,1)", color="tab:red", lw=1.2, ls="--")

        if f_gjr.exists():
            df_gjr = pd.read_parquet(f_gjr)
            ax.plot(dates, df_gjr["predicted_volatility"], label="GJR-GARCH(1,1)", color="tab:purple", lw=1.2, ls=":")

    ax.set_title(f"Phase {p} - Conditional Volatility Forecasts vs Realized Volatility", fontsize=11, fontweight="bold")
    ax.set_ylabel("Volatility (sigma)")
    if i == 0:
        ax.legend(loc="upper right", fontsize=9)
    if i == len(phases) - 1:
        ax.set_xlabel("Date")

plt.tight_layout()
fig_vol_path = fig_dir / "fig_garch_volatility_forecasting.png"
plt.savefig(fig_vol_path, dpi=150)
plt.close()
print(f"Saved conditional volatility comparison plot to: {fig_vol_path}")
print("Statistical notebook execution completed successfully.")
# -
