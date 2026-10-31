"""
Stage 11 Historical Back-Testing & Validation Suite.

Executes 5 historical back-tests on key Sri Lankan elections:
1. 2015 Presidential Election (2015-01-08)
2. 2015 Parliamentary Election (2015-08-17)
3. 2019 Presidential Election (2019-11-15)
4. 2020 Parliamentary Election (2020-08-05)
5. 2024 Presidential Election (2024-09-20)

Compares predicted directions and conformal ranges against realized historical prices,
recording hits AND misses transparently without cherry-picking (Rule R8).
Generates IEEE publication figure results/figures/fig_stage11_backtests.png
and markdown report results/tables/stage11_backtest_report.md.
"""

import json
import os
import sys
import time
from pathlib import Path

# Set up project root
root_dir = Path(__file__).resolve().parent.parent
os.chdir(str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cse.scenario.engine import ScenarioEngine

HISTORICAL_TEST_CASES = [
    {
        "event_id": "2015_presidential",
        "election_name": "2015 Presidential Election",
        "headline": "Voters head to polls in pivotal presidential contest between Rajapaksa and Sirisena",
        "description": "Polling commences across all electoral districts in high-stakes presidential election amid intense voter interest.",
        "date": "2015-01-08",
    },
    {
        "event_id": "2015_parliamentary",
        "election_name": "2015 Parliamentary Election",
        "headline": "General parliamentary polling underway across all 22 electoral districts",
        "description": "Voters cast ballots to elect 225 members of parliament with major contest between UNF and UPFA alliances.",
        "date": "2015-08-17",
    },
    {
        "event_id": "2019_presidential",
        "election_name": "2019 Presidential Election",
        "headline": "Sri Lanka prepares for presidential election as campaigning concludes nationwide",
        "description": "Election Commission finalizes arrangements for nationwide presidential poll following national security debates.",
        "date": "2019-11-15",
    },
    {
        "event_id": "2020_parliamentary",
        "election_name": "2020 Parliamentary Election",
        "headline": "Voters cast ballots in parliamentary general election under health guidelines",
        "description": "Polling conducted across the island to determine parliamentary configuration following pandemic postponement.",
        "date": "2020-08-05",
    },
    {
        "event_id": "2024_presidential",
        "election_name": "2024 Presidential Election",
        "headline": "Presidential election polling scheduled for Saturday under tight security",
        "description": "First presidential election following economic crisis to be conducted across all nine provinces.",
        "date": "2024-09-20",
    },
]

HORIZONS = [1, 2, 5, 10]


def run_historical_backtests():
    print("=" * 85)
    print("  STAGE 11: 5 HISTORICAL ELECTION BACK-TESTS (HITS & MISSES)")
    print("=" * 85)

    engine = ScenarioEngine()
    df_cse = pd.read_parquet(root_dir / "data" / "processed" / "cse_clean.parquet")
    df_cse["date_str"] = pd.to_datetime(df_cse["date"]).dt.strftime("%Y-%m-%d")

    records = []
    plot_data = []

    for case in HISTORICAL_TEST_CASES:
        t_date = case["date"]
        print(f"\n--- Running Back-Test: {case['election_name']} ({t_date}) ---")
        
        # 1. Run scenario engine
        res = engine.run(
            headline=case["headline"],
            description=case["description"],
            publication_date=t_date,
        )

        aspi_current = res["market_context"]["current_aspi_level"]
        actual_row_idx = df_cse[df_cse["date_str"] <= t_date].index[-1]

        for h in HORIZONS:
            h_str = str(h)
            h_true = res["scenarios"]["TRUE"]["horizons"][h_str]
            pred_ret = h_true["expected_log_return"]
            pred_aspi = h_true["expected_aspi_level"]
            ci80_low = h_true["interval_80"]["aspi_lower"]
            ci80_high = h_true["interval_80"]["aspi_upper"]
            ci95_low = h_true["interval_95"]["aspi_lower"]
            ci95_high = h_true["interval_95"]["aspi_upper"]
            prob_up = h_true["prob_up"]

            # Realized future price at t+h
            target_idx = actual_row_idx + h
            if target_idx < len(df_cse):
                actual_aspi = float(df_cse.loc[target_idx, "aspi"])
                actual_ret = float(np.log(actual_aspi / aspi_current))
                actual_date = str(df_cse.loc[target_idx, "date_str"])
            else:
                actual_aspi = np.nan
                actual_ret = np.nan
                actual_date = "N/A"

            # Hit / Miss Evaluation
            dir_hit = (np.sign(pred_ret) == np.sign(actual_ret)) if not np.isnan(actual_ret) else False
            range_80_hit = (ci80_low <= actual_aspi <= ci80_high) if not np.isnan(actual_aspi) else False
            range_95_hit = (ci95_low <= actual_aspi <= ci95_high) if not np.isnan(actual_aspi) else False

            rec = {
                "event": case["election_name"],
                "as_of_date": t_date,
                "horizon_h": h,
                "target_date": actual_date,
                "aspi_t": aspi_current,
                "actual_aspi": actual_aspi,
                "pred_aspi": pred_aspi,
                "actual_ret_pct": actual_ret * 100 if not np.isnan(actual_ret) else np.nan,
                "pred_ret_pct": pred_ret * 100,
                "prob_up": prob_up,
                "dir_hit": dir_hit,
                "range_80_hit": range_80_hit,
                "range_95_hit": range_95_hit,
                "ci80_low": ci80_low,
                "ci80_high": ci80_high,
                "ci95_low": ci95_low,
                "ci95_high": ci95_high,
            }
            records.append(rec)
            print(f"  h={h:2d} ({actual_date}): Actual={actual_aspi:,.1f} ({actual_ret*100:+.2f}%) | Pred={pred_aspi:,.1f} ({pred_ret*100:+.2f}%) | Dir: {'HIT' if dir_hit else 'MISS'} | 80% Range: {'HIT' if range_80_hit else 'MISS'} | 95% Range: {'HIT' if range_95_hit else 'MISS'}")

        plot_data.append({
            "name": case["election_name"],
            "date": t_date,
            "res": res,
            "actual_idx": actual_row_idx,
        })

    df_results = pd.DataFrame(records)

    # 2. Compute Summary Statistics
    print("\n" + "=" * 85)
    print("  HISTORICAL BACK-TEST PERFORMANCE SUMMARY")
    print("=" * 85)
    
    total_evals = len(df_results)
    dir_acc = df_results["dir_hit"].mean() * 100
    cov_80 = df_results["range_80_hit"].mean() * 100
    cov_95 = df_results["range_95_hit"].mean() * 100

    print(f"Total Evaluated Forecasts: {total_evals} (5 events x 4 horizons)")
    print(f"Overall Directional Accuracy: {dir_acc:.1f}% ({df_results['dir_hit'].sum()}/{total_evals})")
    print(f"80% Conformal Range Coverage: {cov_80:.1f}% ({df_results['range_80_hit'].sum()}/{total_evals})")
    print(f"95% Conformal Range Coverage: {cov_95:.1f}% ({df_results['range_95_hit'].sum()}/{total_evals})")

    # Per-horizon breakdown
    print("\nPer-Horizon Performance:")
    for h in HORIZONS:
        sub = df_results[df_results["horizon_h"] == h]
        print(f"  h={h:2d}: Direction = {sub['dir_hit'].mean()*100:5.1f}% | 80% CI Cov = {sub['range_80_hit'].mean()*100:5.1f}% | 95% CI Cov = {sub['range_95_hit'].mean()*100:5.1f}%")

    # 3. Export Tables
    out_dir = root_dir / "results" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "stage11_backtest_eval.csv"
    md_path = out_dir / "stage11_backtest_report.md"
    df_results.to_csv(csv_path, index=False)

    # Format Markdown Report
    cols_disp = ["event", "as_of_date", "horizon_h", "target_date", "aspi_t", "pred_aspi", "actual_aspi", "pred_ret_pct", "actual_ret_pct", "dir_hit", "range_80_hit", "range_95_hit"]
    header = "| " + " | ".join(cols_disp) + " |"
    sep = "| " + " | ".join(["---"] * len(cols_disp)) + " |"
    rows = []
    for _, r in df_results.iterrows():
        row_str = (
            f"| {r['event']} | {r['as_of_date']} | {r['horizon_h']} | {r['target_date']} | "
            f"{r['aspi_t']:,.1f} | {r['pred_aspi']:,.1f} | {r['actual_aspi']:,.1f} | "
            f"{r['pred_ret_pct']:+.2f}% | {r['actual_ret_pct']:+.2f}% | "
            f"{'**HIT**' if r['dir_hit'] else 'MISS'} | "
            f"{'HIT' if r['range_80_hit'] else 'MISS'} | "
            f"{'HIT' if r['range_95_hit'] else 'MISS'} |"
        )
        rows.append(row_str)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Stage 11 Historical Back-Test Evaluation Report\n\n")
        f.write(f"Executed on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("### Aggregate Metrics (5 Historical Elections x 4 Horizons)\n\n")
        f.write(f"- **Directional Accuracy:** **{dir_acc:.1f}%** ({df_results['dir_hit'].sum()}/{total_evals} hits)\n")
        f.write(f"- **80% Conformal Range Coverage:** **{cov_80:.1f}%** ({df_results['range_80_hit'].sum()}/{total_evals} hits)\n")
        f.write(f"- **95% Conformal Range Coverage:** **{cov_95:.1f}%** ({df_results['range_95_hit'].sum()}/{total_evals} hits)\n\n")
        f.write("### Detailed Forecasts vs Realized Outcomes\n\n")
        f.write("\n".join([header, sep] + rows))
        f.write("\n\n### Econometric Integrity Note\n")
        f.write("- Every back-test inputs only information available strictly on or before the news date (Rule R2 zero-lookahead).\n")
        f.write("- Hits and misses are reported with equal prominence without filtering (Rule R8 honest reporting).\n")

    print(f"\nSaved report to:\n  - {csv_path}\n  - {md_path}")

    # 4. Generate IEEE Publication Figure (5 Panels)
    fig_dir = root_dir / "results" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(5, 1, figsize=(10, 14), dpi=300)

    for idx, case in enumerate(HISTORICAL_TEST_CASES):
        ax = axes[idx]
        sub = df_results[df_results["event"] == case["election_name"]]
        
        hs = sub["horizon_h"].values
        actuals = sub["actual_aspi"].values
        preds = sub["pred_aspi"].values
        ci80_l = sub["ci80_low"].values
        ci80_h = sub["ci80_high"].values
        ci95_l = sub["ci95_low"].values
        ci95_h = sub["ci95_high"].values
        aspi_0 = sub["aspi_t"].iloc[0]

        x_ticks = [0] + list(hs)
        ax.plot([0] + list(hs), [aspi_0] + list(actuals), "ko-", linewidth=2.0, label="Realized ASPI Level")
        ax.plot([0] + list(hs), [aspi_0] + list(preds), "b^--", linewidth=1.5, label="Scenario TRUE Forecast")
        
        ax.fill_between(hs, ci80_l, ci80_h, color="#1f77b4", alpha=0.25, label="80% Conformal Interval")
        ax.fill_between(hs, ci95_l, ci95_h, color="#1f77b4", alpha=0.10, label="95% Conformal Interval")

        ax.set_title(f"{case['election_name']} (As of {case['date']}, Base ASPI: {aspi_0:,.1f})", fontweight="bold", fontsize=10)
        ax.set_ylabel("ASPI Level", fontsize=9)
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f"t (Day 0)"] + [f"+{h}d" for h in hs], fontsize=8.5)
        ax.grid(True, linestyle=":", alpha=0.6)
        if idx == 0:
            ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

    axes[-1].set_xlabel("Forecast Horizon (Trading Days Post-Event)", fontsize=10)
    plt.tight_layout()
    fig_path = fig_dir / "fig_stage11_backtests.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"Saved publication figure to: {fig_path}")


if __name__ == "__main__":
    run_historical_backtests()
