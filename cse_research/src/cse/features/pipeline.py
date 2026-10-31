"""Scikit-learn style phase data pipelines and sequence window generation.

Adheres strictly to:
- Rule R2: Zero lookahead bias.
  * Imputation and scaling are fitted per phase strictly on training data only.
  * Validation and inner-validation sets are transformed using parameters learned on training data.
  * 10 trading-day embargo strictly separates training and validation.
- Protocol:
  * Horizontally supports feature sets 'A', 'B', 'C' and horizons h in {1, 5}.
  * Sequence windows (lookback L in {20, 60, 120}) generated without crossing phase boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from cse.features.events_features import build_feature_set_c
from cse.features.market_activity import build_feature_set_b
from cse.features.technical import build_feature_set_a
from cse.splits.walk_forward import ExpandingWindowSplitter, PhaseSplit
from cse.utils.config import find_project_root, load_config
from cse.utils.logger import get_logger

logger = get_logger("cse.features.pipeline")


def compute_targets(df_cse: pd.DataFrame) -> pd.DataFrame:
    """Compute forward return and direction targets for horizons h=1 and h=5.
    
    Guarantees strict alignment with Stage 3 definitions:
    - y_ret_h1 = ln(ASPI_{t+1} / ASPI_t)
    - y_dir_h1 = 1 if y_ret_h1 > 0 else 0 (NaN at end of series)
    - y_ret_h5 = ln(ASPI_{t+5} / ASPI_t)
    - y_dir_h5 = 1 if y_ret_h5 > 0 else 0 (NaN at end of series)
    """
    df_targets = pd.DataFrame(index=df_cse.index)
    df_targets["date"] = pd.to_datetime(df_cse["date"]).dt.strftime("%Y-%m-%d")
    aspi = df_cse["aspi"].astype(float)
    df_targets["aspi_t"] = aspi

    for h in [1, 5]:
        aspi_future = aspi.shift(-h)
        ret_h = np.log(aspi_future / aspi)
        # Binary direction: 1 if positive return, 0 if non-positive
        dir_h = pd.Series(np.where(ret_h.isna(), np.nan, (ret_h > 0).astype(float)), index=df_cse.index)

        df_targets[f"y_ret_h{h}"] = ret_h
        df_targets[f"y_dir_h{h}"] = dir_h

    return df_targets


class PhaseFeaturePipeline:
    """Scikit-learn style imputer and standardizer fitted per phase on training data only.
    
    Guarantees:
    - Never inspects or fits on validation data (Rule R2).
    - Imputes missing values using training-window medians (or 0.0 for all-NaN columns like SP20 in P1).
    - Standardizes continuous features using training-window mean and sample standard deviation.
    - Preserves binary indicator columns (0/1) without distorting indicator values.
    """

    def __init__(self, standardize_binary: bool = False) -> None:
        self.standardize_binary = standardize_binary
        self.feature_names_: List[str] = []
        self.impute_values_: Dict[str, float] = {}
        self.means_: Dict[str, float] = {}
        self.scales_: Dict[str, float] = {}
        self.is_binary_: Dict[str, bool] = {}

    def fit(self, X: pd.DataFrame) -> PhaseFeaturePipeline:
        """Fit imputation and scaling statistics strictly on training data."""
        self.feature_names_ = list(X.columns)
        self.impute_values_ = {}
        self.means_ = {}
        self.scales_ = {}
        self.is_binary_ = {}

        for col in self.feature_names_:
            series = X[col].astype(float)
            valid_vals = series.dropna().values

            # Check if column is binary indicator (values in {0, 1})
            unique_vals = np.unique(valid_vals) if len(valid_vals) > 0 else np.array([])
            is_bin = len(unique_vals) <= 2 and np.all(np.isin(unique_vals, [0.0, 1.0]))
            self.is_binary_[col] = bool(is_bin)

            # Compute median on training data
            if len(valid_vals) == 0:
                # Column is entirely NaN in training data (e.g. SP20 in Phase P1)
                impute_val = 0.0
            else:
                impute_val = float(np.median(valid_vals))
            self.impute_values_[col] = impute_val

            # Compute mean and standard deviation on imputed training series
            series_imputed = series.fillna(impute_val).values
            mean_val = float(np.mean(series_imputed))
            std_val = float(np.std(series_imputed, ddof=1)) if len(series_imputed) > 1 else 1.0

            if is_bin and not self.standardize_binary:
                # Leave binary indicators unscaled
                self.means_[col] = 0.0
                self.scales_[col] = 1.0
            else:
                self.means_[col] = mean_val
                self.scales_[col] = std_val if std_val > 1e-12 else 1.0

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features using parameters learned on training data."""
        if not self.feature_names_:
            raise RuntimeError("PhaseFeaturePipeline must be fitted before calling transform.")

        X_out = pd.DataFrame(index=X.index)
        for col in self.feature_names_:
            if col not in X.columns:
                raise KeyError(f"Feature '{col}' missing from transform DataFrame.")

            series = X[col].astype(float)
            imp_val = self.impute_values_[col]
            mean_val = self.means_[col]
            scale_val = self.scales_[col]

            # Impute then scale
            imputed = series.fillna(imp_val).values
            scaled = (imputed - mean_val) / scale_val
            X_out[col] = scaled

        return X_out

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Fit on training data and transform."""
        return self.fit(X).transform(X)


@dataclass
class SplitData:
    """Represents a single split's feature matrix and aligned targets."""
    X: pd.DataFrame
    y_ret: pd.Series
    y_dir: pd.Series
    dates: pd.Series
    indices: np.ndarray

    def __iter__(self) -> Iterator[Any]:
        """Support convenient tuple unpacking: X, y_ret, y_dir = split."""
        yield self.X
        yield self.y_ret
        yield self.y_dir


@dataclass
class PhaseDataSet:
    """Container holding train, inner-val, and outer-val splits for a phase."""
    phase: str
    horizon: int
    feature_set: str
    train: SplitData
    inner_val: SplitData
    val: SplitData
    feature_names: List[str]
    pipeline: PhaseFeaturePipeline

    def __iter__(self) -> Iterator[SplitData]:
        """Support convenient unpacking: train, inner_val, val = get_phase_data(...)."""
        yield self.train
        yield self.inner_val
        yield self.val


@dataclass
class SequenceSplitData:
    """Represents 3D sequence tensors for deep models."""
    X_seq: np.ndarray  # Shape: (N_samples, lookback, n_features)
    y_ret: np.ndarray  # Shape: (N_samples,)
    y_dir: np.ndarray  # Shape: (N_samples,)
    dates: List[str]   # Length: N_samples

    def __iter__(self) -> Iterator[Any]:
        """Support convenient tuple unpacking: X_seq, y_ret, y_dir = seq_split."""
        yield self.X_seq
        yield self.y_ret
        yield self.y_dir


@dataclass
class PhaseSequenceDataSet:
    """Container holding sequence tensors across all splits for deep models."""
    phase: str
    horizon: int
    feature_set: str
    lookback: int
    train: SequenceSplitData
    inner_val: SequenceSplitData
    val: SequenceSplitData

    def __iter__(self) -> Iterator[SequenceSplitData]:
        """Support convenient unpacking: train_seq, inner_val_seq, val_seq = get_sequence_windows(...)."""
        yield self.train
        yield self.inner_val
        yield self.val


class PhaseDataManager:
    """Central manager for cached feature loading, phase data splitting, and sequence generation."""

    def __init__(self, df_cse: Optional[pd.DataFrame] = None) -> None:
        root = find_project_root()
        if df_cse is None:
            p_cse = root / "data" / "processed" / "cse_clean.parquet"
            self.df_cse = pd.read_parquet(p_cse)
        else:
            self.df_cse = df_cse.copy()

        self.df_cse["date"] = pd.to_datetime(self.df_cse["date"]).dt.strftime("%Y-%m-%d")
        self.splitter = ExpandingWindowSplitter(self.df_cse, embargo_days=10)
        self.targets = compute_targets(self.df_cse)

        # Cache for raw feature sets
        self._feat_cache: Dict[str, pd.DataFrame] = {}

    def get_raw_features(self, feature_set: str) -> pd.DataFrame:
        """Retrieve raw unscaled feature matrix for set 'A', 'B', or 'C'."""
        f_set = feature_set.upper()
        if f_set in self._feat_cache:
            return self._feat_cache[f_set]

        root = find_project_root()
        proc_dir = root / "data" / "processed"

        # Check if saved parquet exists first
        pq_path = proc_dir / f"features_set_{f_set.lower()}.parquet"
        if pq_path.exists():
            df_feat = pd.read_parquet(pq_path)
        else:
            if f_set == "A":
                df_feat = build_feature_set_a(self.df_cse)
            elif f_set == "B":
                df_feat = build_feature_set_b(self.df_cse)
            elif f_set == "C":
                df_feat = build_feature_set_c(self.df_cse)
            else:
                raise ValueError(f"Unknown feature set '{feature_set}'. Must be 'A', 'B', or 'C'.")

        self._feat_cache[f_set] = df_feat
        return df_feat

    def get_phase_data(
        self,
        phase: str,
        horizon: int = 1,
        feature_set: str = "A",
        standardize_binary: bool = False,
    ) -> PhaseDataSet:
        """Extract train, inner-validation, and validation splits with fitted scaling and embargo.
        
        Args:
            phase: Phase identifier ('P1' to 'P5').
            horizon: Forecasting horizon in {1, 5}.
            feature_set: Feature set identifier ('A', 'B', or 'C').
            standardize_binary: Whether to standardize binary indicator columns.
            
        Returns:
            PhaseDataSet containing .train, .inner_val, .val splits (supports tuple unpacking).
        """
        if horizon not in [1, 5]:
            raise ValueError(f"Horizon must be 1 or 5, got {horizon}.")

        phase_split: PhaseSplit = self.splitter.get_phase(phase)
        df_feat = self.get_raw_features(feature_set)

        ret_col = f"y_ret_h{horizon}"
        dir_col = f"y_dir_h{horizon}"

        # 1. Outer Training Window [0, train_end_idx]
        train_slice = slice(phase_split.train.start_idx, phase_split.train.end_idx + 1)
        X_train_raw = df_feat.iloc[train_slice].copy()
        y_train_ret_raw = self.targets[ret_col].iloc[train_slice]
        y_train_dir_raw = self.targets[dir_col].iloc[train_slice]
        train_dates_raw = self.df_cse["date"].iloc[train_slice]
        train_indices_raw = np.arange(phase_split.train.start_idx, phase_split.train.end_idx + 1)

        # 2. Outer Validation Window [val_start_idx, val_end_idx] (Embargo strictly holds!)
        val_slice = slice(phase_split.val.start_idx, phase_split.val.end_idx + 1)
        X_val_raw = df_feat.iloc[val_slice].copy()
        y_val_ret_raw = self.targets[ret_col].iloc[val_slice]
        y_val_dir_raw = self.targets[dir_col].iloc[val_slice]
        val_dates_raw = self.df_cse["date"].iloc[val_slice]
        val_indices_raw = np.arange(phase_split.val.start_idx, phase_split.val.end_idx + 1)

        # 3. Inner Validation Window within training [inner_val_start_idx, inner_val_end_idx]
        inner_val_slice = slice(phase_split.inner_val.start_idx, phase_split.inner_val.end_idx + 1)
        X_inner_val_raw = df_feat.iloc[inner_val_slice].copy()
        y_inner_val_ret_raw = self.targets[ret_col].iloc[inner_val_slice]
        y_inner_val_dir_raw = self.targets[dir_col].iloc[inner_val_slice]
        inner_val_dates_raw = self.df_cse["date"].iloc[inner_val_slice]
        inner_val_indices_raw = np.arange(phase_split.inner_val.start_idx, phase_split.inner_val.end_idx + 1)

        # 4. Fit Pipeline strictly on training window
        pipeline = PhaseFeaturePipeline(standardize_binary=standardize_binary)
        pipeline.fit(X_train_raw)

        # 5. Transform all splits
        X_train_trans = pipeline.transform(X_train_raw)
        X_val_trans = pipeline.transform(X_val_raw)
        X_inner_val_trans = pipeline.transform(X_inner_val_raw)

        # 6. Filter out boundary rows where forward target is beyond series end
        def clean_split(
            X_df: pd.DataFrame,
            y_ret: pd.Series,
            y_dir: pd.Series,
            dates: pd.Series,
            indices: np.ndarray,
        ) -> SplitData:
            valid_mask = (~y_ret.isna()).values
            return SplitData(
                X=X_df.iloc[valid_mask].reset_index(drop=True),
                y_ret=y_ret.iloc[valid_mask].reset_index(drop=True),
                y_dir=y_dir.iloc[valid_mask].reset_index(drop=True).astype(int),
                dates=dates.iloc[valid_mask].reset_index(drop=True),
                indices=indices[valid_mask],
            )

        train_data = clean_split(X_train_trans, y_train_ret_raw, y_train_dir_raw, train_dates_raw, train_indices_raw)
        val_data = clean_split(X_val_trans, y_val_ret_raw, y_val_dir_raw, val_dates_raw, val_indices_raw)
        inner_val_data = clean_split(
            X_inner_val_trans, y_inner_val_ret_raw, y_inner_val_dir_raw, inner_val_dates_raw, inner_val_indices_raw
        )

        return PhaseDataSet(
            phase=phase,
            horizon=horizon,
            feature_set=feature_set.upper(),
            train=train_data,
            inner_val=inner_val_data,
            val=val_data,
            feature_names=pipeline.feature_names_,
            pipeline=pipeline,
        )

    def get_sequence_windows(
        self,
        phase: str,
        horizon: int = 1,
        feature_set: str = "A",
        lookback: int = 20,
        standardize_binary: bool = False,
    ) -> PhaseSequenceDataSet:
        """Produce 3D sequence tensors (N, L, D) for deep models without crossing phase boundaries.
        
        Args:
            phase: Phase identifier ('P1' to 'P5').
            horizon: Forecasting horizon in {1, 5}.
            feature_set: Feature set identifier ('A', 'B', or 'C').
            lookback: Sequence length L in {20, 60, 120}.
            standardize_binary: Whether to standardize binary indicator columns.
            
        Returns:
            PhaseSequenceDataSet containing .train, .inner_val, .val sequence datasets.
        """
        if lookback not in [20, 60, 120]:
            raise ValueError(f"Lookback must be in {{20, 60, 120}}, got {lookback}.")

        p_data = self.get_phase_data(
            phase=phase,
            horizon=horizon,
            feature_set=feature_set,
            standardize_binary=standardize_binary,
        )

        def make_sequences(split: SplitData) -> SequenceSplitData:
            arr_X = split.X.values.astype(float)
            arr_y_ret = split.y_ret.values.astype(float)
            arr_y_dir = split.y_dir.values.astype(int)
            dates_list = list(split.dates.values)

            n_samples = len(arr_X)
            if n_samples < lookback:
                raise ValueError(
                    f"Split has only {n_samples} samples, which is fewer than lookback {lookback}."
                )

            # Construct sequences strictly contained within this split
            n_seq = n_samples - lookback + 1
            n_feat = arr_X.shape[1]

            X_seq = np.zeros((n_seq, lookback, n_feat), dtype=float)
            for i in range(n_seq):
                # Window [i, i + lookback] is strictly inside split bounds [0, n_samples-1]
                X_seq[i] = arr_X[i : i + lookback]

            # Targets and dates aligned with the final step (t) of each lookback sequence
            y_ret_seq = arr_y_ret[lookback - 1 :]
            y_dir_seq = arr_y_dir[lookback - 1 :]
            dates_seq = dates_list[lookback - 1 :]

            return SequenceSplitData(
                X_seq=X_seq,
                y_ret=y_ret_seq,
                y_dir=y_dir_seq,
                dates=dates_seq,
            )

        train_seq = make_sequences(p_data.train)
        inner_val_seq = make_sequences(p_data.inner_val)
        val_seq = make_sequences(p_data.val)

        return PhaseSequenceDataSet(
            phase=phase,
            horizon=horizon,
            feature_set=feature_set.upper(),
            lookback=lookback,
            train=train_seq,
            inner_val=inner_val_seq,
            val=val_seq,
        )


# Global singleton manager for quick module-level access
_DATA_MANAGER: Optional[PhaseDataManager] = None


def get_phase_data(
    phase: str,
    horizon: int = 1,
    feature_set: str = "A",
    standardize_binary: bool = False,
    df_cse: Optional[pd.DataFrame] = None,
) -> PhaseDataSet:
    """Retrieve train, inner-validation, and validation splits for a phase and feature set."""
    global _DATA_MANAGER
    if df_cse is not None or _DATA_MANAGER is None:
        mgr = PhaseDataManager(df_cse=df_cse)
        if df_cse is None:
            _DATA_MANAGER = mgr
    else:
        mgr = _DATA_MANAGER

    return mgr.get_phase_data(
        phase=phase,
        horizon=horizon,
        feature_set=feature_set,
        standardize_binary=standardize_binary,
    )


def get_sequence_windows(
    phase: str,
    horizon: int = 1,
    feature_set: str = "A",
    lookback: int = 20,
    standardize_binary: bool = False,
    df_cse: Optional[pd.DataFrame] = None,
) -> PhaseSequenceDataSet:
    """Retrieve 3D sequence tensors (N, L, D) for deep models without crossing phase boundaries."""
    global _DATA_MANAGER
    if df_cse is not None or _DATA_MANAGER is None:
        mgr = PhaseDataManager(df_cse=df_cse)
        if df_cse is None:
            _DATA_MANAGER = mgr
    else:
        mgr = _DATA_MANAGER

    return mgr.get_sequence_windows(
        phase=phase,
        horizon=horizon,
        feature_set=feature_set,
        lookback=lookback,
        standardize_binary=standardize_binary,
    )
