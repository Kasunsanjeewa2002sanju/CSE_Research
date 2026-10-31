import pandas as pd
from pathlib import Path

csv_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(csv_path)

date_cols = [
    'election_announcement_date', 'nomination_period_start', 'nomination_period_end',
    'election_date', 'election_result_date', 'government_formation_date'
]

groups = df.groupby(["election_type", "election_date"], sort=False)
for (etype, pdate), g in groups:
    if len(g) > 1:
        print(f"\nGroup {etype} - {pdate} ({len(g)} rows):")
        for col in date_cols:
            vals = g[col].unique()
            if len(vals) > 1:
                print(f"  DIFF in {col}: {vals}")
            else:
                print(f"  SAME {col}: {vals[0]}")
