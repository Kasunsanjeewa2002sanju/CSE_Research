"""Technical price-only feature engineering (Feature Set A).

Adheres strictly to:
- Rule R2: Zero lookahead. Every indicator at date t uses ONLY observations up to the close of t.
- Set A: Lagged ASPI log returns (1,2,3,5,10,20 days), rolling return mean and volatility (5,10,20),
  RSI(14), MACD, and percentage distance from 20- and 50-day moving averages.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index (RSI) using exponential Wilder smoothing."""
    delta = prices.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    # Wilder's exponential moving average: alpha = 1 / period
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # Handle cases where loss was zero (RSI = 100) or gain was zero (RSI = 0)
    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.where(avg_gain != 0, 0.0)
    return rsi


def compute_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Compute Moving Average Convergence Divergence (MACD), Signal Line, and Histogram."""
    ema_fast = prices.ewm(span=fast_period, min_periods=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, min_periods=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, min_periods=signal_period, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist


def build_feature_set_a(df_cse: pd.DataFrame) -> pd.DataFrame:
    """Build Feature Set A (Price-Only features) from clean CSE dataset.
    
    Returns DataFrame indexed identically to df_cse with columns:
    - ret_1d, ret_2d, ret_3d, ret_5d, ret_10d, ret_20d (cumulative multi-day returns up to t)
    - ret_lag_1, ret_lag_2, ret_lag_3, ret_lag_5, ret_lag_10, ret_lag_20 (past daily return lags)
    - ret_mean_5d, ret_mean_10d, ret_mean_20d (trailing rolling mean of daily returns)
    - ret_vol_5d, ret_vol_10d, ret_vol_20d (trailing rolling std of daily returns)
    - rsi_14 (Relative Strength Index over trailing 14 days)
    - macd_line, macd_signal, macd_hist (MACD indicators)
    - dist_from_sma_20, dist_from_sma_50 (fractional distance from moving average)
    """
    aspi = df_cse["aspi"].astype(float)
    log_aspi = np.log(aspi)
    r1 = log_aspi.diff(1)

    feats = pd.DataFrame(index=df_cse.index)

    # 1. Multi-day cumulative log returns: ln(ASPI[t] / ASPI[t-k])
    for k in [1, 2, 3, 5, 10, 20]:
        feats[f"ret_{k}d"] = log_aspi.diff(k)

    # 2. Lagged 1-day log returns (observations from previous days)
    for lag in [1, 2, 3, 5, 10, 20]:
        feats[f"ret_lag_{lag}"] = r1.shift(lag)

    # 3. Trailing rolling mean of daily log returns
    for w in [5, 10, 20]:
        feats[f"ret_mean_{w}d"] = r1.rolling(window=w, min_periods=w).mean()

    # 4. Trailing rolling volatility (standard deviation) of daily log returns
    for w in [5, 10, 20]:
        feats[f"ret_vol_{w}d"] = r1.rolling(window=w, min_periods=w).std()

    # 5. Momentum: RSI(14)
    feats["rsi_14"] = compute_rsi(aspi, period=14)

    # 6. Trend / Moving Average Convergence Divergence: MACD(12, 26, 9)
    macd_l, macd_s, macd_h = compute_macd(aspi, fast_period=12, slow_period=26, signal_period=9)
    feats["macd_line"] = macd_l
    feats["macd_signal"] = macd_s
    feats["macd_hist"] = macd_h

    # 7. Distance from moving averages: (ASPI[t] - SMA_w) / SMA_w
    sma_20 = aspi.rolling(window=20, min_periods=20).mean()
    sma_50 = aspi.rolling(window=50, min_periods=50).mean()
    feats["dist_from_sma_20"] = (aspi - sma_20) / sma_20
    feats["dist_from_sma_50"] = (aspi - sma_50) / sma_50

    return feats
