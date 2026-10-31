import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

raw_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
cse_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\processed\cse_clean.parquet")

df_elections = pd.read_csv(raw_path)
df_cse = pd.read_parquet(cse_path)

trading_days = pd.to_datetime(df_cse["date"]).dt.date.sort_values().values
print(f"Total CSE trading days: {len(trading_days)}")
print(f"CSE trading days range: {trading_days[0]} to {trading_days[-1]}")

date_cols = [
    'election_announcement_date',
    'nomination_period_start',
    'nomination_period_end',
    'election_date',
    'election_result_date',
    'government_formation_date'
]

# Check date values in Elections.csv
for col in date_cols:
    val_counts = df_elections[col].apply(lambda x: "Missing" if str(x).strip().lower() in ['not available', 'nan', 'none', ''] else "Valid").value_counts()
    print(f"{col}: {val_counts.to_dict()}")
