from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from backend.app.data.stock_loader import StockDataLoader
from backend.app.data.trading_calendar import TradingCalendar

class FanChartForecaster:
    """
    Constructs multi-day probabilistic index projections (Fan Charts) from t0 to t+H
    incorporating empirical volatility, historical drift, and model-estimated event shocks.
    Visually separates:
      - Historical actual prices leading up to t0
      - Baseline no-event market path
      - Event shock path with 80% and 95% uncertainty intervals
      - Post-cutoff actual prices (when backtesting against historical ground truth)
    """
    def __init__(self, stock_loader: Optional[StockDataLoader] = None):
        self.stock_loader = stock_loader or StockDataLoader()
        self.calendar = self.stock_loader.get_trading_calendar()
        self.stock_df = self.stock_loader.load_stock_data().sort_values("Date").reset_index(drop=True)
        self.date_to_idx = {d: i for i, d in enumerate(self.stock_df["Date"])}

    def generate_fan_forecast(
        self,
        base_date: str,
        expected_car_5d: float,
        horizon_days: int = 20,
        historical_cutoff: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates fan forecast time-series data points.
        """
        aligned_date, _, _ = self.calendar.align_to_trading_day(base_date)
        t0_idx = self.date_to_idx.get(aligned_date)
        
        if t0_idx is None:
            t0_idx = len(self.stock_df) - 1
            aligned_date = self.stock_df.loc[t0_idx, "Date"]

        p_t0 = float(self.stock_df.loc[t0_idx, "ASPI"])
        
        # Estimate recent daily volatility from previous 20 sessions
        idx_start = max(0, t0_idx - 20)
        recent_returns = self.stock_df.loc[idx_start:t0_idx, "ASPI_Daily_Return"].dropna().values
        daily_vol = float(np.std(recent_returns)) if len(recent_returns) > 3 else 0.01
        daily_drift = float(np.mean(recent_returns)) if len(recent_returns) > 3 else 0.0003

        # Historical pre-event trajectory (previous 15 trading days)
        pre_history = []
        hist_start = max(0, t0_idx - 15)
        for i in range(hist_start, t0_idx + 1):
            pre_history.append({
                "trading_day": i - t0_idx,
                "date": self.stock_df.loc[i, "Date"],
                "actual_close": float(self.stock_df.loc[i, "ASPI"]),
                "is_historical": True
            })

        # Forecast forward path
        forecast_points = []
        actual_subsequent = []
        
        # Event shock scaling per day: shock unfolds over 5-10 days and stabilizes
        for h in range(1, horizon_days + 1):
            future_idx = t0_idx + h
            future_date = self.calendar.get_offset_date(aligned_date, h) or f"t+{h}"
            
            # Cumulative drift and shock
            shock_factor = min(1.0, np.sqrt(h / 5.0)) * expected_car_5d
            cum_drift = h * daily_drift
            
            # Central paths
            baseline_price = p_t0 * np.exp(cum_drift)
            event_price = p_t0 * np.exp(cum_drift + shock_factor)
            
            # Expanding uncertainty bounds (standard error ~ daily_vol * sqrt(h))
            sigma_h = daily_vol * np.sqrt(h) * p_t0
            upper_80 = event_price + (1.28 * sigma_h)
            lower_80 = max(0.0, event_price - (1.28 * sigma_h))
            upper_95 = event_price + (1.96 * sigma_h)
            lower_95 = max(0.0, event_price - (1.96 * sigma_h))

            # Check if actual historical prices exist for backtest comparison
            act_close = None
            if future_idx < len(self.stock_df):
                act_close = float(self.stock_df.loc[future_idx, "ASPI"])

            point = {
                "trading_day": h,
                "date": future_date,
                "baseline_no_event": round(baseline_price, 2),
                "event_predicted_central": round(event_price, 2),
                "lower_80": round(lower_80, 2),
                "upper_80": round(upper_80, 2),
                "lower_95": round(lower_95, 2),
                "upper_95": round(upper_95, 2),
                "actual_subsequent_close": round(act_close, 2) if act_close is not None else None,
                "is_historical": False
            }
            forecast_points.append(point)

        return {
            "base_date": aligned_date,
            "base_price": p_t0,
            "daily_volatility_pct": round(daily_vol * 100.0, 2),
            "pre_history": pre_history,
            "forecast_path": forecast_points,
            "has_actual_ground_truth": any(p["actual_subsequent_close"] is not None for p in forecast_points)
        }
