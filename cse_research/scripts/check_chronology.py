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
    df[col] = pd.to_datetime(df[col].replace('Not Available', None), format='%m/%d/%Y')

for idx, r in df.iterrows():
    # Check announcement <= polling
    assert r['election_announcement_date'] <= r['election_date'], f"Row {idx}: ann > poll"
    # Check polling <= result
    assert r['election_date'] <= r['election_result_date'], f"Row {idx}: poll > res"
    # Check result <= formation
    assert r['election_result_date'] <= r['government_formation_date'], f"Row {idx}: res > gov"
    if pd.notna(r['nomination_period_start']):
        assert r['election_announcement_date'] <= r['nomination_period_start'], f"Row {idx}: ann > nom_s"
        assert r['nomination_period_start'] <= r['nomination_period_end'], f"Row {idx}: nom_s > nom_e"
        assert r['nomination_period_end'] <= r['election_date'], f"Row {idx}: nom_e > poll"

print("All date chronological invariants pass!")
