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

# # 01 - Stage 1 Data Ingestion & Audit
# Quantitative ML Research - Colombo Stock Exchange (CSE) ASPI Project
# Strictly following Rules R1, R2, R4, R6, R7, R12.

# +
import sys
from pathlib import Path

# Anchor workspace and package path
root_dir = Path("..").resolve() if Path("..").resolve().name == "cse_research" else Path(".").resolve()
sys.path.insert(0, str(root_dir / "src"))

import pandas as pd
import numpy as np

import cse
from cse.data.ingest import ingest_cse_raw, compute_file_sha256
from cse.data.audit import (
    compute_calendar_gaps,
    compute_trading_days_per_year,
    compute_missingness_by_year,
    compute_column_summaries,
    investigate_large_returns,
    check_consistency_and_outliers,
    run_stationarity_tests,
    generate_figures,
)
from cse.utils.logger import get_logger

logger = get_logger("notebook.stage1")
print(f"CSE Package Version: {cse.__version__}")
# -

# ## 1. Raw Data Ingestion & Hash Tracking (Rule R1, R7)

# +
raw_path = root_dir / "data" / "raw" / "CSE_data.csv"
if not raw_path.exists():
    raw_path = Path("D:/SLIIT/YEAR 04/Research/NEW Dev/CSE_data.csv")

raw_hash = compute_file_sha256(raw_path)
print(f"Raw File Path: {raw_path}")
print(f"Raw File SHA-256: {raw_hash}")

records = ingest_cse_raw(raw_path)
df = pd.DataFrame(records)
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

print(f"Total Rows Ingested: {len(df):,}")
print(f"Trading Date Range: {df['date'].min()} to {df['date'].max()}")
df.head(10)
# -

# ## 2. Column Distribution Summaries

# +
summary_df = compute_column_summaries(df)
summary_df
# -

# ## 3. Large Return Shocks Investigation (|r_t| > 8%)

# +
large_moves = investigate_large_returns(df, threshold=0.08)
large_moves
# -

# ## 4. Market Volume & Consistency Diagnostics

# +
consistency_dict = check_consistency_and_outliers(df)
for k, v in consistency_dict.items():
    print(f"{k}: {v}")
# -

# ## 5. Stationarity Diagnostics (ADF & KPSS)

# +
stationarity_df = run_stationarity_tests(df)
stationarity_df
# -

# ## 6. Calendar Gaps & Annual Trading Days

# +
gaps_df = compute_calendar_gaps(df, max_gap_days=5)
print(f"Total Calendar Gaps > 5 Days: {len(gaps_df)}")
gaps_df.head(10)
# -

# +
trading_days_df = compute_trading_days_per_year(df)
trading_days_df[trading_days_df["is_anomalous_low"]]
# -

# ## 7. Diagnostic Figures

# +
fig_dir = root_dir / "results" / "figures"
fig_paths = generate_figures(df, fig_dir)
print(f"Generated {len(fig_paths)} audit figures:")
for p in fig_paths:
    print(f"  - {p.name}")
# -

# ## 8. Processed Dataset Persistence (Rule R6)

# +
proc_dir = root_dir / "data" / "processed"
proc_dir.mkdir(parents=True, exist_ok=True)

clean_csv_path = proc_dir / "cse_clean.csv"
df.to_csv(clean_csv_path, index=False)
print(f"Saved CSV: {clean_csv_path} ({clean_csv_path.stat().st_size:,} bytes)")

clean_parquet_path = proc_dir / "cse_clean.parquet"
try:
    df.to_parquet(clean_parquet_path, index=False)
    print(f"Saved Parquet: {clean_parquet_path} ({clean_parquet_path.stat().st_size:,} bytes)")
except Exception as e:
    print(f"Parquet export notice: {e}")
# -
