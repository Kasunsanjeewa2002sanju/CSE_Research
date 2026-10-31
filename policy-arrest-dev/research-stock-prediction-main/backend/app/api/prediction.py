from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.ml.predict import UnifiedPredictor
from backend.app.ml.forecasting import FanChartForecaster
from backend.app.ml.backtesting import HistoricalBacktester

router = APIRouter(prefix="", tags=["Prediction & Backtesting"])

predictor = UnifiedPredictor()
forecaster = FanChartForecaster()
backtester = HistoricalBacktester()

_backtest_cache: Dict[str, Any] = {}

class PolicyPredictionRequest(BaseModel):
    policy_type: str = Field(..., description="Derived or raw policy category")
    policy_headline: str = Field(..., description="Headline or description of government policy")
    announcement_date: str = Field(..., description="Announcement or effective date in YYYY-MM-DD format")
    affected_sectors: Optional[List[str]] = Field(default=None, description="List of exposed sectors")
    target_symbol: str = Field(default="ASPI", description="CSE Index (ASPI or SP_SL20)")
    forecast_horizon: int = Field(default=5, description="Prediction horizon in trading days (1, 5, 10, 20)")
    historical_cutoff: Optional[str] = Field(default=None, description="Optional cutoff for backtesting")
    temporary_or_permanent: Optional[str] = Field(default="Permanent", description="Policy permanence")

class ArrestPredictionRequest(BaseModel):
    person_name: str = Field(..., description="Name of public political figure")
    event_description: str = Field(..., description="Details or charges surrounding arrest/legal action")
    event_subtype: str = Field(default="Arrest", description="Legal action subtype")
    government_or_opposition: Optional[str] = Field(default="Opposition", description="Political affiliation")
    announcement_date: str = Field(..., description="Date of arrest or court ruling in YYYY-MM-DD format")
    crisis_or_protest: Optional[str] = Field(default="No", description="Associated protest or state crisis")
    target_symbol: str = Field(default="ASPI", description="CSE Index")
    forecast_horizon: int = Field(default=5, description="Horizon in trading days")
    historical_cutoff: Optional[str] = Field(default=None, description="Optional historical cutoff")

class ScenarioPredictionRequest(BaseModel):
    headline: str = Field(..., description="Headline of event")
    event_family: str = Field(default="Government Policy")
    event_subtype: str = Field(default="Tax Changes")
    event_date: str = Field(..., description="Date in YYYY-MM-DD")
    forecast_horizon: int = Field(default=5)

class BacktestRequest(BaseModel):
    start_date: str = Field(default="2020-01-01")
    end_date: str = Field(default="2025-12-31")
    cutoff_date: str = Field(default="2022-06-30")
    event_family: str = Field(default="Government Policy")
    target_symbol: str = Field(default="ASPI")
    horizon_days: int = Field(default=20)


@router.post("/predict/policy")
def predict_policy(req: PolicyPredictionRequest):
    """
    Predicts Colombo Stock Exchange market impact following a Government Policy decision.
    Returns probabilities, expected return, uncertainty intervals, and historical analogue policies.
    """
    res = predictor.predict(
        event_family="Government Policy",
        event_subtype=req.policy_type,
        headline_or_title=req.policy_headline,
        event_date=req.announcement_date,
        affected_sectors=req.affected_sectors,
        target_symbol=req.target_symbol,
        forecast_horizon=req.forecast_horizon,
        historical_cutoff=req.historical_cutoff,
        additional_metadata={"temporary_or_permanent": req.temporary_or_permanent}
    )

    # Attach fan forecast path
    fan = forecaster.generate_fan_forecast(
        base_date=res["prediction_date"],
        expected_car_5d=float(res["expected_return_pct"]) / 100.0,
        horizon_days=req.forecast_horizon,
        historical_cutoff=req.historical_cutoff
    )
    res["fan_chart"] = fan
    return res


@router.post("/predict/arrest")
def predict_arrest(req: ArrestPredictionRequest):
    """
    Predicts market impact surrounding a Political Arrest or legal proceeding.
    """
    full_text = f"{req.person_name}: {req.event_description}"
    res = predictor.predict(
        event_family="Political Arrest",
        event_subtype=req.event_subtype,
        headline_or_title=full_text,
        event_date=req.announcement_date,
        target_symbol=req.target_symbol,
        forecast_horizon=req.forecast_horizon,
        historical_cutoff=req.historical_cutoff,
        additional_metadata={
            "government_or_opposition": req.government_or_opposition,
            "government_crisis_related": req.crisis_or_protest
        }
    )

    fan = forecaster.generate_fan_forecast(
        base_date=res["prediction_date"],
        expected_car_5d=float(res["expected_return_pct"]) / 100.0,
        horizon_days=req.forecast_horizon,
        historical_cutoff=req.historical_cutoff
    )
    res["fan_chart"] = fan
    return res


@router.post("/predict/scenarios")
def predict_scenarios(req: ScenarioPredictionRequest):
    """
    Generates conditional True vs. False market evolution paths (Section 13).
    Scenario A: If event occurs.
    Scenario B: No-event baseline.
    """
    pred_res = predictor.predict(
        event_family=req.event_family,
        event_subtype=req.event_subtype,
        headline_or_title=req.headline,
        event_date=req.event_date,
        forecast_horizon=req.forecast_horizon
    )

    fan_a = forecaster.generate_fan_forecast(
        base_date=pred_res["prediction_date"],
        expected_car_5d=float(pred_res["expected_return_pct"]) / 100.0,
        horizon_days=req.forecast_horizon
    )

    fan_b = forecaster.generate_fan_forecast(
        base_date=pred_res["prediction_date"],
        expected_car_5d=0.0,  # Zero political shock
        horizon_days=req.forecast_horizon
    )

    return {
        "event_family": req.event_family,
        "event_subtype": req.event_subtype,
        "headline": req.headline,
        "base_date": pred_res["prediction_date"],
        "scenario_a_true": {
            "label": "Scenario A: If Event Occurs / True",
            "expected_return_pct": pred_res["expected_return_pct"],
            "interval_lower_pct": pred_res["interval_lower_pct"],
            "interval_upper_pct": pred_res["interval_upper_pct"],
            "direction": pred_res["predicted_direction"],
            "forecast_path": fan_a["forecast_path"]
        },
        "scenario_b_false": {
            "label": "Scenario B: No-Event Baseline (If Event Does Not Occur)",
            "expected_return_pct": 0.0,
            "direction": "Baseline Drift",
            "forecast_path": fan_b["forecast_path"],
            "scientific_notice": "Scenario B depicts market evolution without this event, not an empirical misinformation model."
        }
    }


@router.post("/backtest")
def run_backtest(req: BacktestRequest):
    """
    Executes a historical backtest for a specific cutoff date between 2020 and 2025.
    Proves strict temporal data isolation.
    """
    try:
        res = backtester.run_backtest(
            start_date=req.start_date,
            end_date=req.end_date,
            cutoff_date=req.cutoff_date,
            event_family=req.event_family,
            target_symbol=req.target_symbol,
            horizon_days=req.horizon_days
        )
        _backtest_cache[res["run_id"]] = res
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Backtest error: {str(e)}")


@router.get("/backtest/{run_id}")
def get_backtest_by_id(run_id: str):
    """Retrieves cached backtest execution results."""
    res = _backtest_cache.get(run_id.upper())
    if not res:
        raise HTTPException(status_code=404, detail=f"Backtest run {run_id} not found.")
    return res
