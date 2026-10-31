from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query
import pandas as pd
import numpy as np

from backend.app.data.stock_loader import StockDataLoader
from backend.app.data.event_loader import EventDataLoader

router = APIRouter(tags=["Market & Timeline"])

stock_loader = StockDataLoader()
event_loader = EventDataLoader(stock_loader)

@router.get("/timeline")
def get_timeline(
    date_from: str = Query("2020-01-01", alias="from"),
    date_to: str = Query("2025-12-31", alias="to"),
    event_family: Optional[str] = Query(None, alias="family"),
    subtype: Optional[str] = None,
    impact_direction: Optional[str] = None
):
    """
    Returns historical price series and connected political event markers
    for the interactive Timeline Explorer (2020-2025 default).
    """
    stock_df = stock_loader.load_stock_data()
    
    # Filter prices
    mask_stock = (stock_df["Date"] >= date_from) & (stock_df["Date"] <= date_to)
    sub_stock = stock_df[mask_stock].sort_values("Date").reset_index(drop=True)
    
    price_series = []
    for _, r in sub_stock.iterrows():
        price_series.append({
            "date": r["Date"],
            "aspi": float(r["ASPI"]) if pd.notna(r["ASPI"]) else None,
            "sp_sl20": float(r["SP_SL20"]) if "SP_SL20" in r and pd.notna(r["SP_SL20"]) else None,
            "turnover_mn": float(r["Turnover_Equity_Mn"]) if "Turnover_Equity_Mn" in r and pd.notna(r["Turnover_Equity_Mn"]) else None,
            "daily_return_pct": round(float(r["ASPI_Daily_Return"]) * 100.0, 2) if pd.notna(r.get("ASPI_Daily_Return")) else 0.0
        })

    # Retrieve and filter events
    study_df = event_loader.get_event_study_results()
    mask_events = (study_df["aligned_date"] >= date_from) & (study_df["aligned_date"] <= date_to)
    sub_events = study_df[mask_events].copy()

    if event_family:
        sub_events = sub_events[sub_events["event_family"].str.lower() == event_family.lower()]
    if subtype:
        sub_events = sub_events[sub_events["event_subtype"].str.lower() == subtype.lower()]
    if impact_direction:
        sub_events = sub_events[sub_events["impact_direction"].str.lower() == impact_direction.lower()]

    event_markers = []
    for _, r in sub_events.iterrows():
        event_markers.append({
            "event_id": r["event_id"],
            "title": r["title"],
            "event_family": r["event_family"],
            "event_subtype": r["event_subtype"],
            "aligned_date": r["aligned_date"],
            "aspi_close_event": r["aspi_close_event"],
            "car_1d": round(float(r.get("car_0_1", 0.0)) * 100.0, 2),
            "car_5d": round(float(r.get("car_0_5", 0.0)) * 100.0, 2),
            "car_20d": round(float(r.get("car_0_20", 0.0)) * 100.0, 2),
            "raw_return_5d": round(float(r.get("raw_return_5d", 0.0)) * 100.0, 2),
            "impact_direction": r["impact_direction"]
        })

    return {
        "date_range": {"from": date_from, "to": date_to},
        "total_sessions": len(price_series),
        "total_events_in_range": len(event_markers),
        "price_series": price_series,
        "event_markers": event_markers
    }

@router.get("/market/series")
def get_market_series(
    symbol: str = "ASPI",
    date_from: str = Query("2020-01-01", alias="from"),
    date_to: str = Query("2025-12-31", alias="to"),
    resolution: str = "1D"
):
    """Returns historical price series for ASPI, S&P SL20, or a specified sector."""
    stock_df = stock_loader.load_stock_data()
    mask = (stock_df["Date"] >= date_from) & (stock_df["Date"] <= date_to)
    sub = stock_df[mask].sort_values("Date").reset_index(drop=True)

    target_col = symbol if symbol in sub.columns else "ASPI"
    
    series_data = []
    for _, r in sub.iterrows():
        val = float(r[target_col]) if pd.notna(r[target_col]) else None
        series_data.append({
            "date": r["Date"],
            "value": val,
            "turnover_mn": float(r["Turnover_Equity_Mn"]) if "Turnover_Equity_Mn" in r and pd.notna(r["Turnover_Equity_Mn"]) else None
        })

    return {
        "symbol": target_col,
        "date_from": date_from,
        "date_to": date_to,
        "count": len(series_data),
        "series": series_data
    }

@router.get("/market/symbols")
def get_market_symbols():
    """List available market indices and sectors."""
    stock_df = stock_loader.load_stock_data()
    inv = stock_loader.get_inventory_report()
    
    symbols = [
        {"symbol": "ASPI", "name": "All Share Price Index", "type": "Benchmark Index"},
        {"symbol": "SP_SL20", "name": "S&P Sri Lanka 20", "type": "Blue-Chip Index"},
    ]
    for s in inv["available_sectors"]:
        symbols.append({
            "symbol": s,
            "name": s.replace("_", " "),
            "type": "Sector Index"
        })
        
    return {"symbols": symbols}

@router.get("/market/summary")
def get_market_summary():
    """Returns overview statistics of market data."""
    return stock_loader.get_inventory_report()
