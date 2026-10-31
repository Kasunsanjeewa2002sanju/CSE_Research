from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from backend.app.data.event_loader import EventDataLoader

router = APIRouter(prefix="/events", tags=["Political Events"])
event_loader = EventDataLoader()

@router.get("")
def list_events(
    family: Optional[str] = None,
    subtype: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Search and filter verified historical political events (Policies and Arrests).
    """
    study_df = event_loader.get_event_study_results().copy()
    
    if family:
        study_df = study_df[study_df["event_family"].str.lower() == family.lower()]
    if subtype:
        study_df = study_df[study_df["event_subtype"].str.lower() == subtype.lower()]
    if date_from:
        study_df = study_df[study_df["aligned_date"] >= date_from]
    if date_to:
        study_df = study_df[study_df["aligned_date"] <= date_to]
    if keyword:
        kw = keyword.lower()
        study_df = study_df[
            study_df["title"].str.lower().str.contains(kw, na=False) |
            study_df["event_subtype"].str.lower().str.contains(kw, na=False)
        ]

    total = len(study_df)
    study_df = study_df.sort_values("aligned_date", ascending=False).iloc[offset:offset+limit]

    results = []
    for _, r in study_df.iterrows():
        results.append({
            "event_id": r["event_id"],
            "title": r["title"],
            "event_family": r["event_family"],
            "event_subtype": r["event_subtype"],
            "aligned_date": r["aligned_date"],
            "car_1d": round(float(r.get("car_0_1", 0.0)) * 100.0, 2),
            "car_5d": round(float(r.get("car_0_5", 0.0)) * 100.0, 2),
            "car_20d": round(float(r.get("car_0_20", 0.0)) * 100.0, 2),
            "impact_direction": r["impact_direction"],
            "cluster_id": r.get("event_cluster_id")
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "events": results
    }

@router.get("/summary")
def get_events_summary():
    """Returns macroeconomic breakdown of all political events."""
    study_df = event_loader.get_event_study_results()
    
    summary_by_family = {}
    for fam, group in study_df.groupby("event_family"):
        summary_by_family[fam] = {
            "count": int(len(group)),
            "mean_car_1d_pct": round(float(group["car_0_1"].mean() * 100.0), 2),
            "mean_car_5d_pct": round(float(group["car_0_5"].mean() * 100.0), 2),
            "mean_car_20d_pct": round(float(group["car_0_20"].mean() * 100.0), 2),
            "impact_direction_counts": {str(k): int(v) for k, v in group["impact_direction"].value_counts().items()}
        }

    return {
        "total_events": int(len(study_df)),
        "by_family": summary_by_family,
        "subtypes_list": sorted(study_df["event_subtype"].unique().tolist())
    }

@router.get("/{event_id}")
def get_event_detail(event_id: str):
    """Detailed event record with complete metadata, sources, and full price trajectory."""
    detail = event_loader.get_event_detail_with_path(event_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    return detail

@router.get("/{event_id}/impact")
def get_event_impact(event_id: str):
    """Returns standalone impact and CAR metrics for a specific event."""
    detail = event_loader.get_event_detail_with_path(event_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found.")
    
    return {
        "event_id": detail["event_id"],
        "title": detail["title"],
        "aligned_date": detail["aligned_date"],
        "impact_direction": detail["impact_direction"],
        "car_1d": detail["car_0_1"],
        "car_5d": detail["car_0_5"],
        "car_20d": detail["car_0_20"],
        "max_drawdown_20d": detail["max_drawdown_20d"],
        "turnover_shock_ratio": detail["turnover_shock_ratio"]
    }
