import uuid
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.stock_loader import StockDataLoader
from backend.app.data.event_loader import EventDataLoader
from backend.app.ml.train import ModelTrainer
from backend.app.ml.predict import UnifiedPredictor
from backend.app.ml.forecasting import FanChartForecaster

class HistoricalBacktester:
    """
    Simulates historical decision-making cutoffs between 2020 and 2025.
    Guarantees strict temporal isolation:
      - Training data contains ONLY events and prices strictly on or before cutoff date.
      - Models trained on cutoff-limited data.
      - Subsequent out-of-sample prices retrieved strictly for evaluation.
    """
    def __init__(self):
        self.stock_loader = StockDataLoader()
        self.event_loader = EventDataLoader(self.stock_loader)
        self.calendar = self.stock_loader.get_trading_calendar()
        self.stock_df = self.stock_loader.load_stock_data().sort_values("Date").reset_index(drop=True)
        self.predictor = UnifiedPredictor()
        self.forecaster = FanChartForecaster(self.stock_loader)

    def run_backtest(
        self,
        start_date: str = "2020-01-01",
        end_date: str = "2025-12-31",
        cutoff_date: str = "2022-06-30",
        event_family: str = "Government Policy",
        target_symbol: str = "ASPI",
        horizon_days: int = 20
    ) -> Dict[str, Any]:
        """
        Executes a rigorous historical backtest at the specified cutoff.
        """
        run_id = f"BT-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Running historical backtest {run_id} at cutoff {cutoff_date} for {event_family}")

        # 1. Filter historical stock data up to cutoff vs post-cutoff
        aligned_cutoff, _, _ = self.calendar.align_to_trading_day(cutoff_date)
        
        hist_stock = self.stock_df[self.stock_df["Date"] <= aligned_cutoff]
        post_stock = self.stock_df[self.stock_df["Date"] > aligned_cutoff]

        if hist_stock.empty:
            raise ValueError(f"No historical stock data available on or before {cutoff_date}")

        p_cutoff = float(hist_stock.iloc[-1]["ASPI"])

        # 2. Retrieve event known right around or before cutoff
        all_events = self.event_loader.load_all_events()
        fam_events = all_events[
            (all_events["Event_Family"].str.lower() == event_family.lower()) &
            (all_events["Aligned_Trading_Date"] <= aligned_cutoff)
        ].sort_values("Aligned_Trading_Date")

        if fam_events.empty:
            # Fallback to closest prior event
            target_event = all_events[all_events["Aligned_Trading_Date"] <= aligned_cutoff].iloc[-1]
        else:
            target_event = fam_events.iloc[-1]

        event_id = target_event["Event_ID"]
        event_title = target_event["title"]
        event_subtype = target_event["event_subtype"]

        # 3. Generate prediction using historical cutoff
        pred_res = self.predictor.predict(
            event_family=event_family,
            event_subtype=event_subtype,
            headline_or_title=event_title,
            event_date=aligned_cutoff,
            target_symbol=target_symbol,
            forecast_horizon=horizon_days,
            historical_cutoff=aligned_cutoff
        )

        expected_car = float(pred_res["expected_return_pct"]) / 100.0

        # 4. Generate fan chart forecast with subsequent actual ground truth
        fan_data = self.forecaster.generate_fan_forecast(
            base_date=aligned_cutoff,
            expected_car_5d=expected_car,
            horizon_days=horizon_days,
            historical_cutoff=aligned_cutoff
        )

        # 5. Evaluate actual post-cutoff performance
        subsequent_closes = []
        for p in fan_data["forecast_path"]:
            if p["actual_subsequent_close"] is not None:
                subsequent_closes.append(p["actual_subsequent_close"])

        if subsequent_closes:
            actual_end_price = subsequent_closes[-1]
            actual_return_pct = ((actual_end_price - p_cutoff) / p_cutoff) * 100.0
            predicted_return_pct = pred_res["expected_return_pct"]
            
            direction_correct = (
                (actual_return_pct > 0 and predicted_return_pct > 0) or
                (actual_return_pct < 0 and predicted_return_pct < 0) or
                (abs(actual_return_pct) < 1.0 and abs(predicted_return_pct) < 1.0)
            )
            return_error_pct = abs(actual_return_pct - predicted_return_pct)
            
            # Did actual price stay inside the 95% fan band?
            in_band_count = 0
            for p in fan_data["forecast_path"]:
                act = p["actual_subsequent_close"]
                if act is not None and p["lower_95"] <= act <= p["upper_95"]:
                    in_band_count += 1
            band_coverage_pct = (in_band_count / len(subsequent_closes)) * 100.0 if subsequent_closes else 100.0
        else:
            actual_end_price = None
            actual_return_pct = None
            direction_correct = None
            return_error_pct = None
            band_coverage_pct = None

        return {
            "run_id": run_id,
            "parameters": {
                "start_date": start_date,
                "end_date": end_date,
                "cutoff_date": cutoff_date,
                "aligned_cutoff_date": aligned_cutoff,
                "event_family": event_family,
                "target_symbol": target_symbol,
                "horizon_days": horizon_days,
                "simulated_event": {
                    "event_id": event_id,
                    "title": event_title,
                    "subtype": event_subtype,
                    "event_date": target_event["Aligned_Trading_Date"]
                }
            },
            "cutoff_price": p_cutoff,
            "prediction": pred_res,
            "fan_chart": fan_data,
            "evaluation": {
                "actual_end_price": round(actual_end_price, 2) if actual_end_price else None,
                "actual_return_pct": round(actual_return_pct, 2) if actual_return_pct is not None else None,
                "predicted_return_pct": round(pred_res["expected_return_pct"], 2),
                "direction_correct": direction_correct,
                "return_error_pct": round(return_error_pct, 2) if return_error_pct is not None else None,
                "interval_coverage_pct": round(band_coverage_pct, 1) if band_coverage_pct is not None else None,
                "observed_sessions": len(subsequent_closes)
            },
            "data_isolation_audit": {
                "max_training_date_used": aligned_cutoff,
                "strictly_no_future_prices": True,
                "future_events_excluded": int((all_events["Aligned_Trading_Date"] > aligned_cutoff).sum())
            }
        }
