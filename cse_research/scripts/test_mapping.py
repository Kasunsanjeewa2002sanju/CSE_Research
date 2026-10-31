import pandas as pd
import numpy as np
from pathlib import Path

raw_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
cse_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\processed\cse_clean.parquet")

df = pd.read_csv(raw_path)
df_cse = pd.read_parquet(cse_path)

trading_days = pd.to_datetime(df_cse["date"]).dt.date.sort_values().values

def map_to_trading_day(dt):
    if pd.isna(dt):
        return None, None
    d = dt.date() if isinstance(dt, pd.Timestamp) else dt
    # find first trading day >= d
    idx = np.searchsorted(trading_days, d)
    if idx < len(trading_days):
        mapped = trading_days[idx]
        gap = (mapped - d).days
        return mapped, gap
    return None, None

date_cols = [
    'election_announcement_date',
    'nomination_period_start',
    'nomination_period_end',
    'election_date',
    'election_result_date',
    'government_formation_date'
]

mapped_summary = []
for col in date_cols:
    parsed = pd.to_datetime(df[col].replace('Not Available', None), format='%m/%d/%Y')
    for val in parsed.dropna():
        mapped, gap = map_to_trading_day(val)
        mapped_summary.append({
            'col': col,
            'raw': val.date(),
            'mapped': mapped,
            'gap': gap,
            'weekday': val.strftime('%a'),
            'mapped_weekday': mapped.strftime('%a')
        })

df_map = pd.DataFrame(mapped_summary)
print(f"Total date observations mapped: {len(df_map)}")
print("Gap distribution:\n", df_map['gap'].value_counts())
print("\nGaps > 0 by weekday:\n", df_map[df_map['gap'] > 0][['col', 'raw', 'mapped', 'gap', 'weekday', 'mapped_weekday']].head(15))
