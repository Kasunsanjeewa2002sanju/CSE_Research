import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
stock_file = os.path.join(base_dir, "data", "processed", "cleaned_stock_data.csv")
aligned_file = os.path.join(base_dir, "data", "processed", "aligned_policy_stock_data.csv")
reports_dir = os.path.join(base_dir, "reports", "phases", "phase_02")
os.makedirs(reports_dir, exist_ok=True)

df_stock = pd.read_csv(stock_file)
df_stock["Date_dt"] = pd.to_datetime(df_stock["Date"])
df_stock = df_stock.sort_values("Date_dt").reset_index(drop=True)
df_stock["MA_20"] = df_stock["ASPI"].rolling(20).mean()
df_stock["MA_50"] = df_stock["ASPI"].rolling(50).mean()

df_focus = df_stock[(df_stock["Date_dt"] >= "2020-01-01") & (df_stock["Date_dt"] <= "2025-12-31")].copy()

df_aligned = pd.read_csv(aligned_file)
date_col = "Aligned_Trading_Date" if "Aligned_Trading_Date" in df_aligned.columns else "Effective_Trading_Date"
df_aligned["Aligned_Date_dt"] = pd.to_datetime(df_aligned[date_col])
if "Return_Post_1d" not in df_aligned.columns and "Immediate_Event_Return" in df_aligned.columns:
    df_aligned["Return_Post_1d"] = df_aligned["Immediate_Event_Return"]
policies_focus = df_aligned[(df_aligned["Aligned_Date_dt"] >= "2020-01-01") & (df_aligned["Aligned_Date_dt"] <= "2025-12-31")].copy()

# Figure 1: 2020-2025 ASPI with Policy Overlay
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8), dpi=150, sharex=True, gridspec_kw={'height_ratios': [3.5, 1]})
ax1.plot(df_focus["Date_dt"], df_focus["ASPI"], color="#059669", linewidth=1.8, label="ASPI Index Close")
ax1.plot(df_focus["Date_dt"], df_focus["MA_20"], color="#0284c7", linewidth=1.2, linestyle="--", alpha=0.8, label="20-Day MA")
ax1.plot(df_focus["Date_dt"], df_focus["MA_50"], color="#9333ea", linewidth=1.2, linestyle=":", alpha=0.8, label="50-Day MA")

colors = {"Fiscal Policy": "#f59e0b", "Emergency Economic Policy": "#ef4444", "Tax Policy": "#8b5cf6", "Foreign Exchange Policy": "#ec4899"}
for _, pol in policies_focus.iterrows():
    p_date = pol["Aligned_Date_dt"]
    p_close = pol["ASPI_Event_Close"]
    c = colors.get(pol["Policy_Type"], "#eab308")
    ax1.scatter(p_date, p_close, color=c, s=55, zorder=5, edgecolor="black", linewidth=0.8)

ax1.set_title("Colombo Stock Exchange — ASPI 2020–2025 Timeline with Government Policy Interventions", fontsize=12, fontweight="bold")
ax1.set_ylabel("Index Level (LKR)")
ax1.grid(True, linestyle="--", alpha=0.4)
ax1.legend(loc="upper left", framealpha=0.9)

ax2.bar(df_focus["Date_dt"], df_focus["Turnover_Equity_Mn"], color="#0284c7", alpha=0.6, width=1.0)
ax2.set_ylabel("Turnover (Mn)")
ax2.set_xlabel("Timeline (2020–2025)")
ax2.grid(True, linestyle="--", alpha=0.3)

plt.tight_layout()
fig1_path = os.path.join(reports_dir, "aspi_2020_2025_with_policies.png")
plt.savefig(fig1_path)
plt.close()
print("Saved Figure 1:", fig1_path)

# Figure 2: Return Horizons Distribution Boxplot
plt.figure(figsize=(10, 5), dpi=150)
ret_data = []
for horizon in ["Return_Post_1d", "Return_Post_3d", "Return_Post_5d"]:
    vals = df_aligned[horizon].dropna() * 100
    for v in vals:
        ret_data.append({"Horizon": horizon.replace("Return_Post_", "").replace("d", " Trading Days"), "Cumulative Return (%)": v})

df_ret = pd.DataFrame(ret_data)
sns.boxplot(x="Horizon", y="Cumulative Return (%)", data=df_ret, palette=["#10b981", "#38bdf8", "#a855f7"], width=0.4)
plt.axhline(0, color="gray", linestyle="--", linewidth=0.8)
plt.title("Distribution of CSE ASPI Cumulative Returns Across Post-Policy Horizons (2000–2025)", fontsize=11, fontweight="bold")
plt.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
fig2_path = os.path.join(reports_dir, "policy_impact_distribution_horizons.png")
plt.savefig(fig2_path)
plt.close()
print("Saved Figure 2:", fig2_path)

# Stats JSON
stats = {
    "timeline_scope": "2020-2025 Primary Evaluation Horizon",
    "total_trading_days": int(len(df_focus)),
    "starting_close": float(df_focus["ASPI"].iloc[0]),
    "ending_close": float(df_focus["ASPI"].iloc[-1]),
    "period_net_return_pct": round(float(((df_focus["ASPI"].iloc[-1] - df_focus["ASPI"].iloc[0]) / df_focus["ASPI"].iloc[0]) * 100), 2),
    "period_high": float(df_focus["ASPI"].max()),
    "period_low": float(df_focus["ASPI"].min()),
    "annualized_volatility": round(float(df_focus["ASPI"].pct_change().std() * np.sqrt(252) * 100), 2),
    "policy_count_focus": int(len(policies_focus)),
    "mean_immediate_1d_reaction_pct": round(float(df_aligned["Return_Post_1d"].dropna().mean() * 100), 2),
    "mean_3d_reaction_pct": round(float(df_aligned["Return_Post_3d"].dropna().mean() * 100), 2),
    "mean_5d_reaction_pct": round(float(df_aligned["Return_Post_5d"].dropna().mean() * 100), 2)
}
json_path = os.path.join(reports_dir, "timeline_descriptive_stats.json")
with open(json_path, "w") as f:
    json.dump(stats, f, indent=2)
print("Saved Stats JSON:", json_path)
