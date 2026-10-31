"""Market activity feature engineering (Feature Set B = Set A + Market Activity).

Adheres strictly to:
- Rule R1: Real data only.
- Rule R2: Zero lookahead. Every indicator at date t uses ONLY observations up to the close of t.
- Set B features:
  * Feature Set A (Price-only indicators)
  * S&P SL 20 log return (strictly masked with has_sp20 before 2012-06-27; never filled)
  * ASPI-minus-SP20 return spread (strictly masked with has_sp20 before 2012-06-27; never filled)
  * has_sp20 indicator flag
  * log turnover: ln(turnover_equity_mn)
  * log shares traded: ln(shares_traded_equity_k)
  * 1-day change in log turnover and log shares traded
  * Trailing 60-day rolling z-score of log turnover and log shares traded
  * Turnover-to-5-day-average ratio: turnover_t / SMA_5(turnover)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cse.features.technical import build_feature_set_a


def build_feature_set_b(df_cse: pd.DataFrame) -> pd.DataFrame:
    """Build Feature Set B (Set A + Market Activity features).
    
    Args:
        df_cse: Cleaned CSE DataFrame containing 'aspi', 'sp20', 'has_sp20',
                'turnover_equity_mn', 'shares_traded_equity_k', 'date'.
                
    Returns:
        DataFrame containing all Set A features plus market activity features.
    """
    # 1. Base Set A features
    feats_a = build_feature_set_a(df_cse)
    feats_b = feats_a.copy()

    # 2. S&P SL 20 Return and Spread (Masked before 2012-06-27)
    has_sp20 = df_cse["has_sp20"].astype(bool)
    sp20_series = df_cse["sp20"].astype(float)
    aspi_log_ret = feats_a["ret_1d"].astype(float)

    # Compute SP20 daily log return only where SP20 is active
    sp20_log = np.log(sp20_series.where(has_sp20, np.nan))
    sp20_ret = sp20_log.diff(1)

    # Mask strictly: Before inception date (2012-06-27), SP20 return MUST be NaN (do not fill)
    sp20_ret = sp20_ret.where(has_sp20, np.nan)
    return_spread = (aspi_log_ret - sp20_ret).where(has_sp20, np.nan)

    feats_b["sp20_log_return"] = sp20_ret
    feats_b["aspi_sp20_spread"] = return_spread
    feats_b["has_sp20"] = has_sp20.astype(int)

    # 3. Turnover & Shares Traded (Log levels)
    turnover = df_cse["turnover_equity_mn"].astype(float)
    shares = df_cse["shares_traded_equity_k"].astype(float)

    # Safe log transform (values are verified strictly > 0 in cse_clean)
    log_turnover = np.log(turnover.replace(0.0, np.nan))
    log_shares = np.log(shares.replace(0.0, np.nan))

    feats_b["log_turnover"] = log_turnover
    feats_b["log_shares"] = log_shares

    # 4. Changes in log activity (1-day differences)
    feats_b["turnover_log_change_1d"] = log_turnover.diff(1)
    feats_b["shares_log_change_1d"] = log_shares.diff(1)

    # 5. Trailing 60-day rolling z-scores
    turnover_mean_60 = log_turnover.rolling(window=60, min_periods=60).mean()
    turnover_std_60 = log_turnover.rolling(window=60, min_periods=60).std()
    feats_b["turnover_zscore_60d"] = (log_turnover - turnover_mean_60) / turnover_std_60

    shares_mean_60 = log_shares.rolling(window=60, min_periods=60).mean()
    shares_std_60 = log_shares.rolling(window=60, min_periods=60).std()
    feats_b["shares_zscore_60d"] = (log_shares - shares_mean_60) / shares_std_60

    # 6. Turnover-to-5-day-average ratio
    turnover_sma_5 = turnover.rolling(window=5, min_periods=5).mean()
    feats_b["turnover_to_5d_ratio"] = turnover / turnover_sma_5

    return feats_b
