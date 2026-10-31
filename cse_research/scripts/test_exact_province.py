import pandas as pd
from pathlib import Path
import re

raw_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(raw_path)

def extract_province_exact(row):
    if row["election_type"] != "Provincial Council":
        return None
    
    sig = str(row.get("event_significance", ""))
    ctx = str(row.get("relevant_context", ""))
    full_text = f"{sig} | {ctx}"
    
    # Priority rules matching the exact subject of the row
    # Row 11: held in the Eastern Province
    if "held in the Eastern Province" in sig or "election in Eastern Province" in sig:
        return "Eastern"
    # Row 13: win for UPFA in Sabaragamuwa Province
    if "win for the ruling UPFA in Sabaragamuwa Province" in sig or "Sabaragamuwa Province" in ctx or "Sabaragamuwa Province" in sig and "alongside North Central" in sig:
        return "Sabaragamuwa"
    # Row 24: retained by the UPFA in Central Province
    if "retained by the UPFA in Central Province" in sig:
        return "Central"
    # Row 25: sweeping victory in North Western Province
    if "sweeping victory in North Western Province" in sig:
        return "North Western"
    # Row 26: Northern Provincial Council
    if "Northern Provincial Council" in sig:
        return "Northern"
    # Row 27: Western Province with a reduced majority
    if "Western Province with a reduced majority" in sig:
        return "Western"
    # Row 28: control in Southern Province
    if "control in Southern Province" in sig:
        return "Southern"
    # Row 29: Badulla District / Uva
    if "Badulla District" in ctx:
        return "Uva"
    # Row 12: North Central Province
    if "North Central Province" in ctx:
        return "North Central"
    # Row 14: Central Province (Kandy, Matale...)
    if "Central Province (Kandy" in ctx:
        return "Central"
    # Row 15: North Western Province (Wayamba)
    if "North Western Province (Wayamba)" in sig:
        return "North Western"
    # Row 16: Western Province
    if "Western Province" in sig:
        return "Western"
    # Row 17: Uva Province
    if "Uva Province" in ctx:
        return "Uva"
    # Row 18: Southern Province
    if "Southern Province" in sig:
        return "Southern"
    # Row 21: Eastern Province
    if "Eastern Province" in sig:
        return "Eastern"
    # Row 22: North Central Province
    if "North Central Province" in sig:
        return "North Central"
    # Row 23: Sabaragamuwa Province
    if "Sabaragamuwa Province" in ctx:
        return "Sabaragamuwa"
    # Row 3: North Western
    if "North Western Province" in ctx or "Wayamba" in ctx:
        return "North Western"
    # Row 4: Central
    if "Central Province" in ctx:
        return "Central"
    # Row 5: North Central
    if "North Central Province" in sig:
        return "North Central"
    # Row 6: Sabaragamuwa
    if "Sabaragamuwa Province" in sig:
        return "Sabaragamuwa"
    # Row 7: Southern
    if "southern stronghold" in sig:
        return "Southern"
    # Row 8: Uva
    if "Uva Provincial Council" in sig:
        return "Uva"
    # Row 9: Western
    if "Colombo, Gampaha, and Kalutara" in ctx:
        return "Western"
        
    return "UNKNOWN"

for idx, r in df.iterrows():
    if r["election_type"] == "Provincial Council":
        prov = extract_province_exact(r)
        print(f"Row {idx:2d} ({r['election_date']}): Province = {prov}")
