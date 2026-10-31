import pandas as pd
from pathlib import Path

raw_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(raw_path)

date_cols = [
    'election_announcement_date',
    'nomination_period_start',
    'nomination_period_end',
    'election_date',
    'election_result_date',
    'government_formation_date'
]

for col in date_cols:
    s = df[col].replace('Not Available', None)
    parsed = pd.to_datetime(s, format='%m/%d/%Y', errors='coerce')
    n_nat = parsed.isna().sum()
    print(f"{col:28s}: {parsed.notna().sum()} valid, {n_nat} null. Min={parsed.min().date() if parsed.notna().any() else 'N/A'}, Max={parsed.max().date() if parsed.notna().any() else 'N/A'}")
