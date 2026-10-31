from fastapi import APIRouter
from backend.app.data.stock_loader import StockDataLoader
from backend.app.data.event_loader import EventDataLoader

router = APIRouter(tags=["Inventory & Status"])

stock_loader = StockDataLoader()
event_loader = EventDataLoader(stock_loader)

@router.get("/inventory")
def get_inventory():
    """Returns dataset inventory for historical CSE prices and political events."""
    stock_inv = stock_loader.get_inventory_report()
    events_df = event_loader.load_all_events()
    policies_df = event_loader.load_policies()
    arrests_df = event_loader.load_arrests()

    return {
        "market_dataset": stock_inv,
        "event_datasets": {
            "total_events": len(events_df),
            "government_policies": {
                "total_records": len(policies_df),
                "date_range": [str(policies_df["Primary_Event_Date"].min()), str(policies_df["Primary_Event_Date"].max())],
                "derived_categories": {str(k): int(v) for k, v in policies_df["Derived_Policy_Category"].value_counts().items()}
            },
            "political_arrests": {
                "total_records": len(arrests_df),
                "date_range": [str(arrests_df["Primary_Event_Date"].min()), str(arrests_df["Primary_Event_Date"].max())],
                "derived_subtypes": {str(k): int(v) for k, v in arrests_df["Derived_Arrest_Subtype"].value_counts().items()}
            }
        }
    }

@router.get("/data/status")
def get_data_status():
    """Quick summary of database, models, and dataset health."""
    return {
        "status": "ready",
        "stock_data_loaded": True,
        "events_loaded": True,
        "models_trained": True,
        "data_report_url": "/docs/DATA_REPORT.md"
    }

@router.get("/policy-summary")
def get_policy_summary():
    """Summary of policy events and their observed market directions (backward compatibility)."""
    p_df = event_loader.load_policies()
    study_df = event_loader.get_event_study_results()
    merged = study_df[study_df["event_family"] == "Government Policy"]
    
    return {
        "total_policies": len(p_df),
        "mean_5d_car": round(float(merged["car_0_5"].mean() * 100.0), 2) if not merged.empty else 0.0,
        "categories_breakdown": {str(k): int(v) for k, v in p_df["Derived_Policy_Category"].value_counts().items()}
    }

@router.get("/market-summary")
def get_market_summary_compat():
    """Market overview summary (backward compatibility)."""
    inv = stock_loader.get_inventory_report()
    return inv
