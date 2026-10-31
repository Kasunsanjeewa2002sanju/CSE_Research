"""Feature engineering pipelines with strict zero-lookahead guarantees (Rule R2).

Provides:
- Feature Set A: Technical / price-only features
- Feature Set B: Set A + Market activity features (S&P SL 20, turnover, shares)
- Feature Set C: Set B + Event features (as-of causal) + Calendar features
- PhaseDataPipeline: Training-only fitting of imputation and scaling per phase
- get_phase_data: Walk-forward splits (train, inner-val, val) with embargo
- get_sequence_windows: 3D sequence tensors (lookbacks 20, 60, 120) strictly within phase bounds
"""

from cse.features.builder import PhaseStandardScaler, build_backward_features
from cse.features.events_features import (
    build_calendar_features,
    build_causal_event_features,
    build_feature_set_c,
)
from cse.features.market_activity import build_feature_set_b
from cse.features.pipeline import (
    PhaseDataManager,
    PhaseDataSet,
    PhaseFeaturePipeline,
    PhaseSequenceDataSet,
    SequenceSplitData,
    SplitData,
    compute_targets,
    get_phase_data,
    get_sequence_windows,
)
from cse.features.technical import (
    build_feature_set_a,
    compute_macd,
    compute_rsi,
)

__all__ = [
    "build_backward_features",
    "PhaseStandardScaler",
    "build_feature_set_a",
    "compute_rsi",
    "compute_macd",
    "build_feature_set_b",
    "build_calendar_features",
    "build_causal_event_features",
    "build_feature_set_c",
    "compute_targets",
    "PhaseFeaturePipeline",
    "PhaseDataManager",
    "PhaseDataSet",
    "PhaseSequenceDataSet",
    "SplitData",
    "SequenceSplitData",
    "get_phase_data",
    "get_sequence_windows",
]
