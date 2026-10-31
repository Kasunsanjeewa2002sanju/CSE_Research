import pandas as pd
import numpy as np
from pathlib import Path

raw_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\raw\Elections.csv")
cse_path = Path(r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research\data\processed\cse_clean.parquet")

df_raw = pd.read_csv(raw_path)
df_cse = pd.read_parquet(cse_path)

# Build date to trading day index map
trading_days = pd.to_datetime(df_cse["date"]).dt.date.sort_values().values
date_to_td_idx = {d: i for i, d in enumerate(trading_days)}

def map_dt(dt):
    if pd.isna(dt):
        return None, None
    d = dt.date() if isinstance(dt, pd.Timestamp) else dt
    idx = np.searchsorted(trading_days, d)
    if idx < len(trading_days):
        mapped = trading_days[idx]
        gap = (mapped - d).days
        return mapped, gap
    return None, None

# Group distinct elections
groups = df_raw.groupby(["election_type", "election_date"], sort=False)
events = []
for event_idx, ((etype, pdate), g) in enumerate(groups):
    poll_raw = pd.to_datetime(pdate, format="%m/%d/%Y").date()
    poll_mapped, poll_gap = map_dt(poll_raw)
    td_idx = date_to_td_idx[poll_mapped]
    
    events.append({
        "event_id": f"ELEC_{event_idx+1:02d}",
        "election_type": etype,
        "raw_poll_date": poll_raw,
        "mapped_poll_date": poll_mapped,
        "poll_td_idx": td_idx,
        "n_provinces": len(g) if etype == "Provincial Council" else 1,
        "raw_indices": list(g.index)
    })

df_ev = pd.DataFrame(events)

# Compute pairwise trading day distance between distinct events based on mapped polling date
df_ev["min_dist_other_poll_td"] = np.nan
df_ev["overlapping_events_30td"] = ""
df_ev["has_overlap_30td"] = False

for i, row_i in df_ev.iterrows():
    overlaps = []
    min_dist = float("inf")
    for j, row_j in df_ev.iterrows():
        if i == j:
            continue
        dist = abs(row_i["poll_td_idx"] - row_j["poll_td_idx"])
        if dist < min_dist:
            min_dist = dist
        if dist <= 30:
            overlaps.append(f"{row_j['event_id']}({dist}td)")
    df_ev.loc[i, "min_dist_other_poll_td"] = min_dist
    df_ev.loc[i, "overlapping_events_30td"] = "; ".join(overlaps)
    df_ev.loc[i, "has_overlap_30td"] = len(overlaps) > 0

print("Event Overlap Summary (based on polling date within +/-30 trading days):")
print(df_ev[["event_id", "election_type", "mapped_poll_date", "poll_td_idx", "min_dist_other_poll_td", "has_overlap_30td", "overlapping_events_30td"]])
