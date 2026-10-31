"""Stage 3: Validation Protocol Definition and Shared Evaluation Harness Execution.

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: No lookahead, strict chronological splitting, 10-day embargo.
- Rule R3: Suspicious-result rule. Direction accuracy > 60% or OOS R2 > 0.10 triggers alarm.
- Rule R4: Predict log returns; index levels reconstructed.
- Rule R5: Same protocol for every model.
- Rule R6: Save everything.
- Rule R7: Reproducibility, seed tracking, data hashes.
- Rule R10: Stage discipline, no model training yet (baselines only).
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

from cse.eval.harness import EvaluationHarness
from cse.splits import ExpandingWindowSplitter
from cse.utils.config import find_project_root, load_config
from cse.utils.logger import get_logger

logger = get_logger("cse.stage3")


def run_stage3() -> int:
    """Execute Stage 3 validation protocol, figure generation, and baseline execution."""
    root = find_project_root()
    config = load_config()

    logger.info("=== Starting Stage 3: Validation Protocol & Evaluation Harness ===")

    # 1. Load cleaned CSE data
    proc_data_path = root / config["paths"]["processed_data_dir"] / "cse_clean.parquet"
    if not proc_data_path.exists():
        logger.error("Cleaned CSE data not found at %s. Please run Stage 1 first.", proc_data_path)
        return 1

    df = pd.read_parquet(proc_data_path)
    logger.info("Loaded cleaned CSE data: %d rows (%s to %s)", len(df), df["date"].min(), df["date"].max())

    # 2. Setup Splits and Output Timeline Figure & Table
    val_cfg = config.get("validation_protocol", {})
    splitter = ExpandingWindowSplitter(
        df,
        embargo_days=val_cfg.get("embargo_trading_days", 10),
        inner_tune_ratio=val_cfg.get("inner_tune_ratio", 0.15),
        inner_embargo_days=val_cfg.get("inner_embargo_trading_days", 10),
        phases_config=val_cfg.get("phases", None),
    )

    # Save summary table
    tables_dir = root / config["paths"]["tables_dir"]
    tables_dir.mkdir(parents=True, exist_ok=True)
    split_summary = splitter.summary_table()
    csv_split = tables_dir / "phase_split_counts.csv"
    md_split = tables_dir / "phase_split_counts.md"
    split_summary.to_csv(csv_split, index=False)

    headers = list(split_summary.columns)
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for _, row in split_summary.iterrows():
        lines.append('| ' + ' | '.join(str(val) for val in row.values) + ' |')
    with open(md_split, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    logger.info("Saved phase split table to %s and %s", csv_split, md_split)

    # Save timeline figure
    fig_dir = root / config["paths"]["figures_dir"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_path = fig_dir / "validation_splits_timeline.png"
    splitter.plot_timeline(fig_path)
    logger.info("Saved validation splits timeline figure to %s", fig_path)

    # 3. Initialize Shared Evaluation Harness and Run Baselines
    harness = EvaluationHarness(config=config, data_df=df)
    horizons = val_cfg.get("horizons", [1, 5])
    logger.info("Executing 4 baselines on 5 phases for horizons %s...", horizons)
    df_metrics, df_agg = harness.run_all_baselines(horizons=horizons)

    logger.info("=== Stage 3 Baselines Execution Completed Successfully ===")
    logger.info("Total prediction evaluations: %d", len(df_metrics))
    logger.info("Summary of Baselines across all phases:\n%s",
                df_agg[["model", "horizon", "accuracy_mean", "oos_r2_mean", "theils_u_mean", "mae_mean", "level_mape_mean"]].to_string())

    return 0


if __name__ == "__main__":
    sys.exit(run_stage3())
