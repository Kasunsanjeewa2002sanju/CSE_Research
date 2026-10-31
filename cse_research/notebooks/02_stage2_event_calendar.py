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

# # 02 - Stage 2: Election Event Calendar & Trading Day Alignment
# Quantitative ML Research - Colombo Stock Exchange (CSE) ASPI Project
# Strictly following Rules R1, R2, R6, R7, R11, R12.

# +
import sys
from pathlib import Path

# Anchor workspace and package path
root_dir = Path("..").resolve() if Path("..").resolve().name == "cse_research" else Path(".").resolve()
sys.path.insert(0, str(root_dir / "src"))

import pandas as pd
import numpy as np

import cse
from cse.data.events import (
    parse_elections_raw,
    build_event_level_table,
    build_stage_level_table,
    build_event_calendar,
    generate_election_figures,
    load_and_merge_events,
)
from cse.data.ingest import compute_file_sha256
from cse.utils.logger import get_logger

logger = get_logger("notebook.stage2")
print(f"CSE Package Version: {cse.__version__}")
# -

# ## 1. Ingest Raw Elections Data & Hash Verification (Rule R1, R7)

# +
raw_elections_path = root_dir / "data" / "raw" / "Elections.csv"
if not raw_elections_path.exists():
    raw_elections_path = Path("D:/SLIIT/YEAR 04/Research/NEW Dev/Elections.csv")

elections_hash = compute_file_sha256(raw_elections_path)
print(f"Raw Elections Path: {raw_elections_path}")
print(f"Raw Elections SHA-256: {elections_hash}")

df_raw = parse_elections_raw(raw_elections_path)
print(f"Parsed {len(df_raw)} records across columns: {list(df_raw.columns)}")
df_raw.head()
# -

# ## 2. Load Processed CSE Daily Trading Data

# +
cse_clean_path = root_dir / "data" / "processed" / "cse_clean.parquet"
df_cse = pd.read_parquet(cse_clean_path)
print(f"CSE Clean Panel: {len(df_cse)} trading days ({df_cse['date'].min()} to {df_cse['date'].max()})")
df_cse.head()
# -

# ## 3. Construct Event-Level Table (Distinct Elections)

# +
df_events = build_event_level_table(df_raw, df_cse)
print(f"Total distinct election events: {len(df_events)}")
print("\nBreakdown by election type:")
print(df_events["election_type"].value_counts())
print("\nProposal Sample Period (2009-2025) count:")
print(df_events["sample_2009_2025"].value_counts())

df_events[[
    "event_id", "election_type", "n_provinces", "province",
    "polling_date_raw", "polling_date_mapped", "polling_gap_days",
    "sample_2009_2025", "has_overlap_poll_30td"
]]
# -

# ## 4. Construct Event-Stage Table & Master Calendar

# +
df_stages = build_stage_level_table(df_raw, df_cse)
print(f"Total stage observations: {len(df_stages)}")
print("\nStage breakdown (available dates):")
print(df_stages[df_stages["mapped_date"].notna()]["stage"].value_counts())

df_calendar = build_event_calendar(df_stages)
print(f"Master Event Calendar rows: {len(df_calendar)}")
df_calendar.head(15)
# -

# ## 5. Market Reaction Gap Distribution (Trading Day Alignment)

# +
print("Calendar gap distribution between raw date and open CSE trading day:")
print(df_stages["gap_days"].value_counts().sort_index())
# -

# ## 6. Visualizations

# +
figs_dir = root_dir / "results" / "figures"
figs = generate_election_figures(df_cse, df_events, df_stages, figs_dir)
print(f"Generated {len(figs)} figures:")
for f in figs:
    print(f" - {f.name}")
# -
