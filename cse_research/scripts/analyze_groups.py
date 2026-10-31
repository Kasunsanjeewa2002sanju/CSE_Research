import pandas as pd
from pathlib import Path

csv_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(csv_path)

# Let's inspect unique election_date by election_type
groups = df.groupby(["election_type", "election_date"], sort=False)
print(f"Total rows in Elections.csv: {len(df)}")
print(f"Total distinct (type, poll_date) groups: {len(groups)}")

for (etype, pdate), g in groups:
    print(f"{etype:20s} | Poll: {pdate:10s} | Count: {len(g)} rows | Indices: {list(g.index)}")
