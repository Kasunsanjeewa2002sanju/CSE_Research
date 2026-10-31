import pytest
from backend.app.ml.predict import UnifiedPredictor
from backend.app.ml.analogues import HistoricalAnaloguePredictor
from backend.app.ml.backtesting import HistoricalBacktester

def test_unified_predictor_policy():
    predictor = UnifiedPredictor()
    res = predictor.predict(
        event_family="Government Policy",
        event_subtype="Tax Changes",
        headline_or_title="Government increases corporate income tax rate",
        event_date="2022-05-10",
        forecast_horizon=5
    )

    assert "predicted_direction" in res
    assert 0.0 <= res["probability_up"] <= 1.0
    assert 0.0 <= res["probability_down"] <= 1.0
    assert "expected_return_pct" in res
    assert "interval_lower_pct" in res
    assert "interval_upper_pct" in res
    assert res["interval_lower_pct"] <= res["expected_return_pct"] <= res["interval_upper_pct"]
    assert "similar_events" in res
    assert len(res["similar_events"]) > 0

def test_historical_analogues_cutoff():
    analogue_engine = HistoricalAnaloguePredictor()
    # Query with strict cutoff in 2021
    analogues = analogue_engine.find_analogues(
        event_family="Government Policy",
        event_subtype="Budget Changes",
        query_text="National Budget Presentation",
        historical_cutoff="2021-12-31",
        top_k=3
    )

    assert len(analogues) > 0
    for a in analogues:
        assert a["aligned_date"] <= "2021-12-31"

def test_historical_backtester_execution():
    backtester = HistoricalBacktester()
    res = backtester.run_backtest(
        start_date="2020-01-01",
        end_date="2025-12-31",
        cutoff_date="2022-06-30",
        event_family="Government Policy",
        target_symbol="ASPI",
        horizon_days=20
    )

    assert "run_id" in res
    assert res["parameters"]["cutoff_date"] == "2022-06-30"
    assert "evaluation" in res
    assert "fan_chart" in res
    assert res["data_isolation_audit"]["strictly_no_future_prices"] is True
