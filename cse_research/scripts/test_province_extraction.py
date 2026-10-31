import pandas as pd
from pathlib import Path
import re

csv_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
df = pd.read_csv(csv_path)

provinces_list = [
    "Western", "Central", "Southern", "Northern", "Eastern",
    "North Western", "North Central", "Uva", "Sabaragamuwa"
]

def extract_province(row):
    text = f"{str(row.get('event_significance', ''))} {str(row.get('relevant_context', ''))}"
    found = []
    # Check compound names first
    if "North Western" in text or "Wayamba" in text:
        found.append("North Western")
    if "North Central" in text:
        found.append("North Central")
    if "Sabaragamuwa" in text:
        found.append("Sabaragamuwa")
    if "Western" in text and "North Western" not in text and "Western Province" in text:
        found.append("Western")
    elif "Western Province" in text and "Western" not in found:
        found.append("Western")
    if "Central" in text and "North Central" not in text and "Central Province" in text:
        found.append("Central")
    elif "Central Province" in text and "Central" not in found:
        found.append("Central")
    if "Southern" in text and "Southern Province" in text:
        found.append("Southern")
    elif "Southern" in text and "southern" in text.lower() and "Southern" not in found:
        found.append("Southern")
    if "Northern" in text and "Northern Province" in text:
        found.append("Northern")
    if "Eastern" in text and "Eastern Province" in text:
        found.append("Eastern")
    if "Uva" in text:
        found.append("Uva")
    return list(dict.fromkeys(found))

for idx, r in df.iterrows():
    prov = extract_province(r)
    print(f"Row {idx:2d} | {r['election_type']:18s} | Poll: {r['election_date']:10s} | Extracted: {prov}")
