import pytest
import pandas as pd
import numpy as np
from backend.app.data.trading_calendar import TradingCalendar
from backend.app.events.event_study import EventStudyEngine

def test_event_study_returns_and_car():
    # Synthetic test stock series
    dates = [f"2022-01-{i:02d}" for i in range(1, 31)]
    # 30 days of prices starting at 100 with flat drift
    prices = [100.0 + (i * 0.5) for i in range(len(dates))]
    
    df_stock = pd.DataFrame({"Date": dates, "ASPI": prices})
    calendar = TradingCalendar(dates)
    engine = EventStudyEngine(df_stock, calendar)

    res = engine.analyze_event(
        event_id="TEST-001",
        aligned_date="2022-01-15",
        event_family="Government Policy",
        event_subtype="Tax Changes",
        title="Test Tax Increase",
        est_window=(-10, -2)
    )

    assert res is not None
    assert res["event_id"] == "TEST-001"
    assert "car_0_1" in res
    assert "car_0_5" in res
    assert "price_path" in res
    assert len(res["price_path"]) > 0
    assert "interpretation_notice" in res
