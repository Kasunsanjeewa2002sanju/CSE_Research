import pandas as pd
from pathlib import Path

raw_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(raw_path)

df["poll_dt"] = pd.to_datetime(df["election_date"], format="%m/%d/%Y")

print("Elections before 2009:")
print(df[df["poll_dt"] < "2009-01-01"][["election_type", "election_date"]].drop_duplicates())

print("\nElections 2009-2025 (Proposal sample):")
print(df[(df["poll_dt"] >= "2009-01-01") & (df["poll_dt"] <= "2025-12-31")][["election_type", "election_date"]].drop_duplicates())
