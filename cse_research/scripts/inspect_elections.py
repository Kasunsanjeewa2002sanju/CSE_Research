import pandas as pd
from pathlib import Path

csv_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(csv_path)

print(f"Total rows: {len(df)}")
print("Columns:", list(df.columns))

for idx, r in df.iterrows():
    print(
        f"Row {idx:2d}: {r['election_type']:18s} | "
        f"Ann: {str(r['election_announcement_date']):10s} | "
        f"NomS: {str(r['nomination_period_start']):12s} | "
        f"NomE: {str(r['nomination_period_end']):12s} | "
        f"Poll: {str(r['election_date']):10s} | "
        f"Res: {str(r['election_result_date']):10s} | "
        f"Gov: {str(r['government_formation_date']):10s} | "
        f"Ctx: {str(r['event_significance'])[:40]}"
    )
