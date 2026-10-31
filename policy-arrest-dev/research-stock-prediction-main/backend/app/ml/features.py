from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.app.data.stock_loader import StockDataLoader
from backend.app.data.trading_calendar import TradingCalendar

class FeatureEngineer:
    """
    Constructs pre-event market features and event metadata features strictly
    avoiding any lookahead bias or future-data leakage.
    All market metrics are calculated strictly on or before t0 - 1.
    """
    def __init__(self, stock_df: pd.DataFrame, calendar: TradingCalendar):
        self.stock_df = stock_df.sort_values("Date").reset_index(drop=True)
        self.calendar = calendar
        self.date_to_idx = {d: i for i, d in enumerate(self.stock_df["Date"])}
        
        # Precompute rolling market indicators
        aspi = self.stock_df["ASPI"]
        ret = aspi.pct_change()
        self.stock_df["ret_1d"] = ret
        self.stock_df["ma_20"] = aspi.rolling(20, min_periods=5).mean()
        self.stock_df["ma_50"] = aspi.rolling(50, min_periods=10).mean()
        self.stock_df["vol_5d"] = ret.rolling(5, min_periods=3).std() * np.sqrt(252)
        self.stock_df["vol_20d"] = ret.rolling(20, min_periods=5).std() * np.sqrt(252)
        self.stock_df["max_60d"] = aspi.rolling(60, min_periods=10).max()

    def get_market_state(self, date_str: str) -> Dict[str, float]:
        """
        Calculates pre-event market momentum, volatility, and trend
        strictly up to trading day t0 - 1.
        """
        idx = self.date_to_idx.get(date_str)
        if idx is None:
            aligned_d, _, _ = self.calendar.align_to_trading_day(date_str)
            idx = self.date_to_idx.get(aligned_d, len(self.stock_df) - 1)

        # Pre-event index t_pre = t0 - 1
        t_pre = max(0, idx - 1)
        p_pre = float(self.stock_df.loc[t_pre, "ASPI"])

        def calc_ret(lag_days: int) -> float:
            idx_past = max(0, t_pre - lag_days)
            p_past = float(self.stock_df.loc[idx_past, "ASPI"])
            return float((p_pre - p_past) / p_past) if p_past > 0 else 0.0

        ret_5d = calc_ret(5)
        ret_20d = calc_ret(20)
        ret_60d = calc_ret(60)

        ma20 = float(self.stock_df.loc[t_pre, "ma_20"]) if pd.notna(self.stock_df.loc[t_pre, "ma_20"]) else p_pre
        ma50 = float(self.stock_df.loc[t_pre, "ma_50"]) if pd.notna(self.stock_df.loc[t_pre, "ma_50"]) else p_pre
        price_to_ma20 = (p_pre / ma20) - 1.0 if ma20 > 0 else 0.0
        price_to_ma50 = (p_pre / ma50) - 1.0 if ma50 > 0 else 0.0

        vol_5d = float(self.stock_df.loc[t_pre, "vol_5d"]) if pd.notna(self.stock_df.loc[t_pre, "vol_5d"]) else 0.15
        vol_20d = float(self.stock_df.loc[t_pre, "vol_20d"]) if pd.notna(self.stock_df.loc[t_pre, "vol_20d"]) else 0.18

        max60 = float(self.stock_df.loc[t_pre, "max_60d"]) if pd.notna(self.stock_df.loc[t_pre, "max_60d"]) else p_pre
        drawdown_60d = (p_pre - max60) / max60 if max60 > 0 else 0.0

        return {
            "market_ret_5d": ret_5d,
            "market_ret_20d": ret_20d,
            "market_ret_60d": ret_60d,
            "market_vol_5d": vol_5d,
            "market_vol_20d": vol_20d,
            "price_to_ma20": price_to_ma20,
            "price_to_ma50": price_to_ma50,
            "drawdown_60d": drawdown_60d,
            "pre_close_aspi": p_pre
        }

    def build_feature_vector(
        self,
        event_family: str,
        event_subtype: str,
        date_str: str,
        text_description: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Constructs an explainable dictionary of market and categorical features."""
        meta = additional_metadata or {}
        market_feats = self.get_market_state(date_str)

        features = {
            "event_family": event_family,
            "event_subtype": event_subtype,
            **market_feats
        }

        if event_family == "Government Policy":
            features["is_temporary"] = 1.0 if "temporary" in str(meta.get("temporary_or_permanent", "")).lower() else 0.0
            features["has_tax"] = 1.0 if "tax" in event_subtype.lower() else 0.0
            features["has_imf"] = 1.0 if "imf" in event_subtype.lower() else 0.0
            features["has_budget"] = 1.0 if "budget" in event_subtype.lower() else 0.0
            features["has_monetary"] = 1.0 if "monetary" in event_subtype.lower() else 0.0
        else:
            features["is_remand_detention"] = 1.0 if "remand" in event_subtype.lower() or "detention" in event_subtype.lower() else 0.0
            features["is_sentencing"] = 1.0 if "sentencing" in event_subtype.lower() else 0.0
            features["is_release_pardon"] = 1.0 if "pardon" in event_subtype.lower() or "release" in event_subtype.lower() else 0.0
            features["is_opposition"] = 1.0 if "opposition" in str(meta.get("government_or_opposition", "")).lower() else 0.0
            features["is_crisis_related"] = 1.0 if "yes" in str(meta.get("government_crisis_related", "")).lower() else 0.0

        return features
