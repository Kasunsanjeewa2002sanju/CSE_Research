import pandas as pd
from pathlib import Path

csv_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(csv_path)

for idx in range(3, 14):
    r = df.iloc[idx]
    print(f"--- ROW {idx} ({r['election_type']} | Poll: {r['election_date']}) ---")
    print(f"Candidate/Party: {r['candidate_party_info']}")
    print(f"Significance:    {r['event_significance']}")
    print(f"Source:          {r['source_of_information']}")
    print(f"Context:         {r['relevant_context']}\n")
