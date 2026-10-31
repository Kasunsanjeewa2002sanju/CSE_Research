"""Zero-lookahead feature engineering and per-phase scaling (Rule R2).

Every feature for day t uses ONLY information available at or before the close of day t.
Scalers and transformers are fitted on training data only.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Union
import numpy as np
import pandas as pd


def build_backward_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build backward-looking historical features from price and volume data.
    
    Guarantees strict zero-lookahead (Rule R2):
    All features at index t are computed using observations at or prior to index t.
    """
    df_feat = pd.DataFrame(index=df.index)
    aspi = df["aspi"].astype(float)

    # 1. Past daily log returns
    log_aspi = np.log(aspi)
    r1 = log_aspi.diff(1)
    df_feat["ret_1d"] = r1

    # 2. Return lags (lags 1 to 5)
    for lag in range(1, 6):
        df_feat[f"ret_lag_{lag}"] = r1.shift(lag)

    # 3. Rolling realized volatility (strictly backward-looking)
    df_feat["vol_5d"] = r1.rolling(window=5, min_periods=5).std()
    df_feat["vol_20d"] = r1.rolling(window=20, min_periods=20).std()

    # 4. Volume and turnover features if available
    if "turnover_equity_mn" in df.columns:
        turnover = df["turnover_equity_mn"].astype(float)
        df_feat["log_turnover"] = np.log(turnover.replace(0, np.nan)).fillna(0.0)
        df_feat["turnover_chg_1d"] = df_feat["log_turnover"].diff(1)

    if "shares_traded_equity_000" in df.columns:
        shares = df["shares_traded_equity_000"].astype(float)
        df_feat["log_shares"] = np.log(shares.replace(0, np.nan)).fillna(0.0)

    return df_feat


class PhaseStandardScaler:
    """Standard scaler fitted strictly on training data (Rule R2).
    
    Never fits on or inspects validation blocks.
    """

    def __init__(self) -> None:
        self.mean_: Optional[np.ndarray] = None
        self.scale_: Optional[np.ndarray] = None
        self.feature_names_: Optional[List[str]] = None

    def fit(self, X: Union[pd.DataFrame, np.ndarray]) -> PhaseStandardScaler:
        """Fit scaler parameters on training window only."""
        if isinstance(X, pd.DataFrame):
            self.feature_names_ = list(X.columns)
            arr = X.values.astype(float)
        else:
            arr = np.asarray(X, dtype=float)

        # Compute mean and standard deviation ignoring NaNs
        self.mean_ = np.nanmean(arr, axis=0)
        scale = np.nanstd(arr, axis=0)
        # Avoid division by zero
        scale[scale == 0] = 1.0
        self.scale_ = scale
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Standardize features using parameters fitted on training window."""
        if self.mean_ is None or self.scale_ is None:
            raise RuntimeError("PhaseStandardScaler must be fitted before transforming.")

        if isinstance(X, pd.DataFrame):
            arr = X.values.astype(float)
        else:
            arr = np.asarray(X, dtype=float)

        return (arr - self.mean_) / self.scale_

    def fit_transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Fit on training window and transform."""
        return self.fit(X).transform(X)
