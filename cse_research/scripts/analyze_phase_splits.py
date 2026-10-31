import pandas as pd
import numpy as np
from pathlib import Path

cse_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\processed\cse_clean.parquet")
df = pd.read_parquet(cse_path)
df["date"] = pd.to_datetime(df["date"]).dt.date

phases_def = [
    ("P1", "2012-01-01", "2014-12-31"),
    ("P2", "2015-01-01", "2017-12-31"),
    ("P3", "2018-01-01", "2020-12-31"),
    ("P4", "2021-01-01", "2023-12-31"),
    ("P5", "2024-01-01", "2025-12-31"),
]

embargo = 10

print(f"Total rows in cse_clean: {len(df)}")
all_dates = list(df["date"])

for phase_name, val_start_str, val_end_str in phases_def:
    val_start = pd.to_datetime(val_start_str).date()
    val_end = pd.to_datetime(val_end_str).date()
    
    # Validation indices
    val_mask = (df["date"] >= val_start) & (df["date"] <= val_end)
    val_df = df[val_mask]
    val_indices = val_df.index.tolist()
    
    first_val_idx = val_indices[0]
    last_val_idx = val_indices[-1]
    
    # Train indices before val_start, minus embargo
    # Embargo of 10 trading days immediately before first_val_idx
    # So embargo window is [first_val_idx - embargo, first_val_idx - 1]
    # Training window is [0, first_val_idx - embargo - 1]
    train_end_idx = first_val_idx - embargo - 1
    train_indices = list(range(0, train_end_idx + 1))
    embargo_indices = list(range(train_end_idx + 1, first_val_idx))
    
    train_df = df.iloc[train_indices]
    embargo_df = df.iloc[embargo_indices]
    
    # Inner split on train window: last 15% with 10-day embargo
    n_train = len(train_indices)
    n_inner_val = int(np.floor(n_train * 0.15))
    inner_val_start_idx_in_train = n_train - n_inner_val
    inner_train_end_idx_in_train = inner_val_start_idx_in_train - embargo - 1
    
    n_inner_train = inner_train_end_idx_in_train + 1
    n_inner_embargo = embargo
    
    print(f"\n--- {phase_name} ---")
    print(f"Train Date Range: {train_df['date'].min()} to {train_df['date'].max()} ({len(train_df)} rows)")
    print(f"Embargo Date Range: {embargo_df['date'].min()} to {embargo_df['date'].max()} ({len(embargo_df)} rows)")
    print(f"Val Date Range: {val_df['date'].min()} to {val_df['date'].max()} ({len(val_df)} rows)")
    print(f"Inner Tuning: Inner Train={n_inner_train}, Inner Embargo={n_inner_embargo}, Inner Val={n_inner_val} (Total={n_train})")
