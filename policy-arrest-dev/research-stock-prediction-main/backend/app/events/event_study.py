from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.trading_calendar import TradingCalendar

class EventStudyEngine:
    """
    Econometric Event-Study Engine for Colombo Stock Exchange.
    Calculates Abnormal Returns (AR) and Cumulative Abnormal Returns (CAR)
    using pre-event estimation windows (-120 to -20 trading days).
    """
    def __init__(self, stock_df: pd.DataFrame, calendar: TradingCalendar):
        self.stock_df = stock_df.sort_values("Date").reset_index(drop=True)
        self.calendar = calendar
        self.date_to_idx = {d: i for i, d in enumerate(self.stock_df["Date"])}
        
        # Ensure returns are calculated
        if "ASPI_Daily_Return" not in self.stock_df.columns:
            self.stock_df["ASPI_Daily_Return"] = self.stock_df["ASPI"].pct_change()
            
        self.aspi_returns = self.stock_df["ASPI_Daily_Return"].values
        self.aspi_prices = self.stock_df["ASPI"].values
        self.turnover = self.stock_df["Turnover_Equity_Mn"].values if "Turnover_Equity_Mn" in self.stock_df.columns else None

    def analyze_event(
        self,
        event_id: str,
        aligned_date: str,
        event_family: str,
        event_subtype: str,
        title: str,
        est_window: Tuple[int, int] = (-120, -20)
    ) -> Optional[Dict[str, Any]]:
        """
        Runs event study for a single event at t0 = aligned_date.
        Estimation window: [t0 + est_window[0], t0 + est_window[1]] (e.g. [-120, -20])
        Event window: [-10, +20]
        """
        t0_idx = self.date_to_idx.get(aligned_date)
        if t0_idx is None:
            aligned_date, _, _ = self.calendar.align_to_trading_day(aligned_date)
            t0_idx = self.date_to_idx.get(aligned_date)
            if t0_idx is None:
                return None

        # Check estimation window availability
        est_start_idx = t0_idx + est_window[0]
        est_end_idx = t0_idx + est_window[1]
        
        # Fallback if history is shorter than 120 days (e.g. earliest 1985-1990 events)
        if est_start_idx < 0:
            est_start_idx = max(1, t0_idx - 60)
            est_end_idx = max(est_start_idx + 10, t0_idx - 10)
            
        if est_start_idx >= est_end_idx or est_end_idx >= t0_idx:
            # Insufficient pre-event history
            mean_return = 0.0005  # Average long-run market drift (~12% annual)
            est_vol = 0.012
        else:
            est_returns = self.aspi_returns[est_start_idx:est_end_idx]
            valid_est = est_returns[~np.isnan(est_returns)]
            mean_return = float(np.mean(valid_est)) if len(valid_est) > 5 else 0.0005
            est_vol = float(np.std(valid_est)) if len(valid_est) > 5 else 0.012

        p_t0 = float(self.aspi_prices[t0_idx])
        p_prev = float(self.aspi_prices[t0_idx - 1]) if t0_idx > 0 else p_t0

        # Helper to compute returns and AR
        def get_window_return(h1: int, h2: int) -> Tuple[float, float]:
            """Compute raw cumulative return and CAR between relative day h1 and h2."""
            idx_1 = max(0, min(len(self.stock_df) - 1, t0_idx + h1))
            idx_2 = max(0, min(len(self.stock_df) - 1, t0_idx + h2))
            
            p1 = float(self.aspi_prices[idx_1])
            p2 = float(self.aspi_prices[idx_2])
            
            if h1 < 0:
                # Pre-event return up to t0
                raw_ret = (p_t0 - p1) / p1 if p1 > 0 else 0.0
            else:
                raw_ret = (p2 - p_t0) / p_t0 if p_t0 > 0 else 0.0

            # Sum of abnormal returns
            ar_sum = 0.0
            for k in range(min(idx_1, idx_2), max(idx_1, idx_2) + 1):
                r_k = self.aspi_returns[k]
                if not np.isnan(r_k):
                    ar_sum += (r_k - mean_return)
                    
            return float(raw_ret), float(ar_sum)

        raw_ret_1d, car_0_1 = get_window_return(0, 1)
        raw_ret_3d, car_0_3 = get_window_return(0, 3)
        raw_ret_5d, car_0_5 = get_window_return(0, 5)
        raw_ret_10d, car_0_10 = get_window_return(0, 10)
        raw_ret_20d, car_0_20 = get_window_return(0, 20)
        raw_ret_pre5d, car_pre5d = get_window_return(-5, -1)

        # Immediate day 0 return
        ret_day_0 = float(self.aspi_returns[t0_idx]) if not np.isnan(self.aspi_returns[t0_idx]) else 0.0
        ar_day_0 = ret_day_0 - mean_return

        # Price path from -10 to +20 trading sessions
        price_path = []
        path_start = max(0, t0_idx - 10)
        path_end = min(len(self.stock_df) - 1, t0_idx + 20)
        
        for k in range(path_start, path_end + 1):
            rel_day = k - t0_idx
            p_k = float(self.aspi_prices[k])
            pct_from_t0 = ((p_k - p_t0) / p_t0) * 100.0 if p_t0 > 0 else 0.0
            price_path.append({
                "relative_day": rel_day,
                "date": self.stock_df.loc[k, "Date"],
                "aspi_close": p_k,
                "pct_change_from_event": round(pct_from_t0, 3)
            })

        # Maximum drawdown over subsequent 20 trading sessions
        post_20_prices = [p["aspi_close"] for p in price_path if p["relative_day"] >= 0]
        max_drawdown = 0.0
        if post_20_prices:
            peak = post_20_prices[0]
            for p in post_20_prices:
                if p > peak:
                    peak = p
                dd = (peak - p) / peak if peak > 0 else 0.0
                if dd > max_drawdown:
                    max_drawdown = dd

        # Volume / Turnover shock ratio
        turnover_shock = 1.0
        if self.turnover is not None and t0_idx < len(self.turnover):
            t_curr = self.turnover[t0_idx]
            t_est = self.turnover[est_start_idx:est_end_idx]
            valid_t_est = t_est[~np.isnan(t_est)]
            if len(valid_t_est) > 5 and np.mean(valid_t_est) > 0 and not np.isnan(t_curr):
                turnover_shock = float(t_curr / np.mean(valid_t_est))

        impact_direction = "Positive" if car_0_5 > 0.005 else ("Negative" if car_0_5 < -0.005 else "Neutral")

        return {
            "event_id": event_id,
            "title": title,
            "event_family": event_family,
            "event_subtype": event_subtype,
            "aligned_date": aligned_date,
            "aspi_close_event": p_t0,
            "mean_expected_daily_return": round(mean_return, 6),
            "estimation_volatility": round(est_vol, 6),
            "ar_day_0": round(ar_day_0, 5),
            "ret_day_0": round(ret_day_0, 5),
            "raw_return_1d": round(raw_ret_1d, 5),
            "raw_return_3d": round(raw_ret_3d, 5),
            "raw_return_5d": round(raw_ret_5d, 5),
            "raw_return_10d": round(raw_ret_10d, 5),
            "raw_return_20d": round(raw_ret_20d, 5),
            "raw_return_pre_5d": round(raw_ret_pre5d, 5),
            "car_0_1": round(car_0_1, 5),
            "car_0_3": round(car_0_3, 5),
            "car_0_5": round(car_0_5, 5),
            "car_0_10": round(car_0_10, 5),
            "car_0_20": round(car_0_20, 5),
            "car_pre_5d": round(car_pre5d, 5),
            "max_drawdown_20d": round(max_drawdown, 5),
            "turnover_shock_ratio": round(turnover_shock, 2),
            "impact_direction": impact_direction,
            "price_path": price_path,
            "interpretation_notice": "Observed market price changes indicate concurrent correlation, not verified monocausal effect."
        }

    def run_full_event_study(self, events_df: pd.DataFrame) -> pd.DataFrame:
        """Runs the event study across all provided events and returns a comprehensive tabular result."""
        results = []
        for _, row in events_df.iterrows():
            eid = row["Event_ID"]
            d = row.get("Aligned_Trading_Date", row.get("Primary_Event_Date"))
            fam = row.get("Event_Family", "Unknown")
            sub = row.get("event_subtype", row.get("Derived_Policy_Category", row.get("Derived_Arrest_Subtype", "General")))
            title = row.get("title", row.get("Policy_Name", row.get("Official_Reason_for_Arrest", eid)))
            
            res = self.analyze_event(
                event_id=eid,
                aligned_date=str(d),
                event_family=fam,
                event_subtype=sub,
                title=str(title)
            )
            if res:
                # Exclude complex price_path from flat table
                flat_res = {k: v for k, v in res.items() if k != "price_path"}
                # Preserve cluster id if present
                if "event_cluster_id" in row:
                    flat_res["event_cluster_id"] = row["event_cluster_id"]
                results.append(flat_res)
                
        return pd.DataFrame(results)
