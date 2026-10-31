import pandas as pd
from pathlib import Path

raw_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(raw_path)

# Let's inspect the text for each Provincial Council row to get the exact province
# Sri Lankan provinces:
# 1. Western
# 2. Central
# 3. Southern
# 4. Northern
# 5. Eastern
# 6. North Western (Wayamba)
# 7. North Central
# 8. Uva
# 9. Sabaragamuwa

def get_province_for_row(idx, row):
    etype = row["election_type"]
    if etype != "Provincial Council":
        return None
    
    text = f"{str(row.get('event_significance', ''))} {str(row.get('relevant_context', ''))}"
    
    # Precise extraction
    if "North Western" in text or "Wayamba" in text:
        return "North Western"
    if "North Central" in text:
        return "North Central"
    if "Sabaragamuwa" in text:
        return "Sabaragamuwa"
    if "Northern" in text or "Northern Province" in text or "CHOGM" in text:
        return "Northern"
    if "Eastern" in text or "Eastern Province" in text:
        return "Eastern"
    if "Southern" in text or "southern stronghold" in text or "southern Sinhala" in text:
        return "Southern"
    if "Western" in text or "Western Province" in text or "Colombo, Gampaha" in text:
        return "Western"
    if "Central" in text or "Central Province" in text:
        return "Central"
    if "Uva" in text or "Badulla" in text:
        return "Uva"
    return None

for idx, r in df.iterrows():
    p = get_province_for_row(idx, r)
    if r["election_type"] == "Provincial Council":
        print(f"Row {idx:2d} ({r['election_date']}): Province = {p}")
    else:
        assert p is None, f"National election has province: {p}"
