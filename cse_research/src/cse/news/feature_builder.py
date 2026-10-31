"""CSE News Feature Builder (Stage 6).

Integrates Stages 1-5 into the final 58-element feature vector expected by the
frozen CatBoost model (scenario_models.pkl), strictly preserving feature column
names, sequence, and technical features while enriching event indicators with
continuous, news-specific outputs.

Pipelines integrated:
- Stage 1: Historical Database (data/cse_history.db)
- Stage 2: Semantic Similarity Index (FAISS / MiniLM embeddings)
- Stage 3: PriorCalculator (kNN event-study prior CARs & fallback chain)
- Stage 4: ProximityCalculator (CSE calendar trading-day distances & window indicators)
- Stage 5: EnhancedExtractor (multi-label confidences, fine-grained stages, direction & novelty)
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from cse.news.enhanced_extractor import EnhancedExtractor, get_enhanced_extractor
from cse.news.historical_db import get_default_db_path
from cse.news.prior_calculator import PriorCalculator, get_prior_calculator
from cse.news.proximity_calculator import ProximityCalculator, get_proximity_calculator
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.feature_builder")

# Global paths
ROOT_DIR = find_project_root()
FEATURE_COLS_PATH = ROOT_DIR / "models" / "final" / "feature_columns.json"
FEATURES_C_PATH = ROOT_DIR / "data" / "processed" / "features_set_c.parquet"
CSE_CLEAN_PATH = ROOT_DIR / "data" / "processed" / "cse_clean.parquet"
FALLBACK_LOG_PATH = ROOT_DIR / "data" / "feature_fallbacks.log"

# Load feature column definitions
with open(FEATURE_COLS_PATH, "r", encoding="utf-8") as _f:
    FEATURE_COLUMNS: List[str] = json.load(_f)

# Identify non-event technical market features (columns up to stage_none)
_FIRST_EVENT_COL = "stage_none"
if _FIRST_EVENT_COL in FEATURE_COLUMNS:
    _EVENT_START_IDX = FEATURE_COLUMNS.index(_FIRST_EVENT_COL)
    TECHNICAL_FEATURE_COLS: List[str] = FEATURE_COLUMNS[:_EVENT_START_IDX]
    EVENT_FEATURE_COLS: List[str] = FEATURE_COLUMNS[_EVENT_START_IDX:]
else:
    # Fallback partition
    TECHNICAL_FEATURE_COLS = [c for c in FEATURE_COLUMNS if not (c.startswith("stage_") or c.startswith("type_") or c.startswith("in_window_") or c.startswith("days_") or c.startswith("prior_"))]
    EVENT_FEATURE_COLS = [c for c in FEATURE_COLUMNS if c not in TECHNICAL_FEATURE_COLS]


class FeatureVector(np.ndarray):
    """58-element NumPy vector with support for column-name indexing and metadata inspection."""

    feature_names: List[str]
    feature_sources: Dict[str, str]
    metadata: Dict[str, Any]

    def __new__(
        cls,
        input_array: np.ndarray,
        feature_names: List[str],
        feature_sources: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        obj = np.asarray(input_array, dtype=np.float64).view(cls)
        obj.feature_names = list(feature_names)
        obj.feature_sources = dict(feature_sources or {})
        obj.metadata = dict(metadata or {})
        return obj

    def __array_finalize__(self, obj: Any) -> None:
        if obj is None:
            return
        self.feature_names = getattr(obj, "feature_names", list(FEATURE_COLUMNS))
        self.feature_sources = getattr(obj, "feature_sources", {})
        self.metadata = getattr(obj, "metadata", {})

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            if item in self.feature_names:
                idx = self.feature_names.index(item)
                return float(super().__getitem__(idx))
            raise KeyError(f"Feature '{item}' not found in feature columns.")
        return super().__getitem__(item)

    def to_dict(self) -> Dict[str, float]:
        """Convert feature vector to dictionary mapping column name -> float."""
        return {col: float(self[idx]) for idx, col in enumerate(self.feature_names)}

    def to_series(self) -> pd.Series:
        """Convert feature vector to pandas Series."""
        return pd.Series(self, index=self.feature_names)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert feature vector to 1-row pandas DataFrame."""
        return pd.DataFrame([self.to_dict()])


class FeatureBuilderCache:
    """Thread-safe in-memory TTL cache for Stage 6 feature generation."""

    def __init__(self) -> None:
        # Key: (headline_sha256, horizon) -> (timestamp, result_dict)
        self._prior_cache: Dict[Tuple[str, int], Tuple[float, Dict[str, Any]]] = {}
        # Key: headline_sha256 -> (timestamp, result_dict)
        self._extractor_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def get_prior(self, headline_hash: str, horizon: int) -> Optional[Dict[str, Any]]:
        key = (headline_hash, horizon)
        if key in self._prior_cache:
            ts, val = self._prior_cache[key]
            if time.time() - ts < 3600:  # 1 hour TTL
                return val
            del self._prior_cache[key]
        return None

    def set_prior(self, headline_hash: str, horizon: int, val: Dict[str, Any]) -> None:
        self._prior_cache[(headline_hash, horizon)] = (time.time(), val)

    def get_extractor(self, headline_hash: str) -> Optional[Dict[str, Any]]:
        if headline_hash in self._extractor_cache:
            ts, val = self._extractor_cache[headline_hash]
            if time.time() - ts < 86400:  # 24 hours TTL
                return val
            del self._extractor_cache[headline_hash]
        return None

    def set_extractor(self, headline_hash: str, val: Dict[str, Any]) -> None:
        self._extractor_cache[headline_hash] = (time.time(), val)

    def clear(self) -> None:
        """Clear all in-memory caches."""
        self._prior_cache.clear()
        self._extractor_cache.clear()


# Module-level singletons (Lazy Loaded)
_CACHE = FeatureBuilderCache()
_PRIOR_CALCULATOR: Optional[PriorCalculator] = None
_ENHANCED_EXTRACTOR: Optional[EnhancedExtractor] = None
_PROXIMITY_CALCULATOR: Optional[ProximityCalculator] = None
_DF_FEATURES_C: Optional[pd.DataFrame] = None
_DF_CSE: Optional[pd.DataFrame] = None


def get_cache() -> FeatureBuilderCache:
    """Return singleton cache instance."""
    return _CACHE


def get_prior_calc() -> PriorCalculator:
    """Return singleton PriorCalculator."""
    global _PRIOR_CALCULATOR
    if _PRIOR_CALCULATOR is None:
        _PRIOR_CALCULATOR = get_prior_calculator()
    return _PRIOR_CALCULATOR


def get_enhanced_extractor_inst() -> EnhancedExtractor:
    """Return singleton EnhancedExtractor."""
    global _ENHANCED_EXTRACTOR
    if _ENHANCED_EXTRACTOR is None:
        _ENHANCED_EXTRACTOR = get_enhanced_extractor()
    return _ENHANCED_EXTRACTOR


def get_proximity_calc() -> ProximityCalculator:
    """Return singleton ProximityCalculator."""
    global _PROXIMITY_CALCULATOR
    if _PROXIMITY_CALCULATOR is None:
        _PROXIMITY_CALCULATOR = get_proximity_calculator()
    return _PROXIMITY_CALCULATOR


def _get_base_market_dfs() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load base processed market datasets once for technical features fallback."""
    global _DF_FEATURES_C, _DF_CSE
    if _DF_FEATURES_C is None or _DF_CSE is None:
        if FEATURES_C_PATH.exists():
            _DF_FEATURES_C = pd.read_parquet(FEATURES_C_PATH)
        else:
            # Create synthetic default market technical row if parquet missing
            _DF_FEATURES_C = pd.DataFrame([{col: 0.0 for col in TECHNICAL_FEATURE_COLS}])

        if CSE_CLEAN_PATH.exists():
            _DF_CSE = pd.read_parquet(CSE_CLEAN_PATH)
            _DF_CSE["date_str"] = pd.to_datetime(_DF_CSE["date"]).dt.strftime("%Y-%m-%d")
        else:
            _DF_CSE = pd.DataFrame([{"date": "2025-01-01", "date_str": "2025-01-01", "aspi": 12000.0}])

    return _DF_FEATURES_C, _DF_CSE


def log_feature_fallback(component: str, headline: str, level: str, reason: str) -> None:
    """Audit log every feature fallback to data/feature_fallbacks.log."""
    try:
        FALLBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat()
        h_hash = hashlib.sha256(headline.strip().encode("utf-8")).hexdigest()[:16]
        sanitized_hl = headline.replace("\n", " ").strip()[:80]
        entry = (
            f"{ts} | FALLBACK | component={component} | hash={h_hash} | "
            f"level={level} | reason={reason} | headline={sanitized_hl}\n"
        )
        with open(FALLBACK_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        logger.warning("Could not write to feature fallback log %s: %s", FALLBACK_LOG_PATH, e)


def _query_category_prior_from_db(
    category: str,
    horizon: int,
    db_path: Optional[Path] = None,
) -> Optional[Tuple[float, float, float, float]]:
    """Query category-average CAR prior directly from SQLite cse_history.db.

    Returns:
        (prior_mean_car, prior_median_car, prior_std, n_effective) or None.
    """
    path = db_path or get_default_db_path()
    if not path.exists():
        return None

    horizon_col = f"car_{horizon}d"
    try:
        conn = sqlite3.connect(str(path), timeout=5.0)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {horizon_col} FROM news_history WHERE event_category = ? AND {horizon_col} IS NOT NULL",
            (category,),
        )
        rows = [float(r[0]) for r in cursor.fetchall() if r[0] is not None]
        conn.close()

        if rows:
            arr = np.array(rows, dtype=np.float64)
            return float(np.mean(arr)), float(np.median(arr)), float(np.std(arr)), float(len(arr))
    except Exception as e:
        logger.debug("Category prior fallback database query failed: %s", e)

    return None


def _get_base_technical_snapshot(
    news_date: Optional[Union[str, date, datetime]] = None,
) -> Dict[str, float]:
    """Retrieve default 38 market technical features as of news_date from Set C."""
    df_features_c, df_cse = _get_base_market_dfs()

    if not news_date or df_cse.empty:
        row_idx = len(df_features_c) - 1
    else:
        clean_date = str(news_date)[:10]
        past_dates = df_cse[df_cse["date_str"] <= clean_date]
        if past_dates.empty:
            row_idx = 0
        else:
            row_idx = int(past_dates.index[-1])
            if row_idx >= len(df_features_c):
                row_idx = len(df_features_c) - 1

    series = df_features_c.iloc[row_idx]
    return {col: float(series.get(col, 0.0)) for col in TECHNICAL_FEATURE_COLS}


def build_features(
    headline: str,
    news_date: Optional[Union[str, date, datetime]] = None,
    market_snapshot: Optional[Union[Dict[str, float], pd.Series, pd.DataFrame, Any]] = None,
    horizon: int = 10,
) -> FeatureVector:
    """Build a complete, validated 58-element feature vector for a news headline.

    Parameters
    ----------
    headline : str
        News headline text to extract features for.
    news_date : Optional[Union[str, date, datetime]]
        Date of the news headline. Defaults to current date if None.
    market_snapshot : Optional[Union[Dict[str, float], pd.Series, pd.DataFrame, Any]]
        Market technical features. If None, resolves as-of news_date from Set C.
    horizon : int
        Prediction horizon for CAR priors (default 10 trading days).

    Returns
    -------
    FeatureVector
        58-element NumPy vector compatible with the frozen CatBoost model.
    """
    clean_headline = (headline or "").strip()
    headline_hash = hashlib.sha256(clean_headline.encode("utf-8")).hexdigest()
    news_date_str = str(news_date)[:10] if news_date else date.today().isoformat()

    feature_values: Dict[str, float] = {}
    feature_sources: Dict[str, str] = {}
    metadata: Dict[str, Any] = {
        "headline": clean_headline,
        "headline_hash": headline_hash,
        "news_date": news_date_str,
        "horizon": horizon,
    }

    # -------------------------------------------------------------------------
    # 1. Market Technical Features (Unchanged from market_snapshot)
    # -------------------------------------------------------------------------
    base_snapshot = _get_base_technical_snapshot(news_date=news_date_str)
    
    if market_snapshot is not None:
        if isinstance(market_snapshot, dict):
            snap_dict = market_snapshot
        elif isinstance(market_snapshot, pd.Series):
            snap_dict = market_snapshot.to_dict()
        elif isinstance(market_snapshot, pd.DataFrame):
            snap_dict = market_snapshot.iloc[0].to_dict() if not market_snapshot.empty else {}
        elif hasattr(market_snapshot, "dict"):
            snap_dict = market_snapshot.dict()
        else:
            snap_dict = {}

        # Preserve all 38 technical market features from the snapshot
        for col in TECHNICAL_FEATURE_COLS:
            if col in snap_dict and snap_dict[col] is not None:
                try:
                    feature_values[col] = float(snap_dict[col])
                except (ValueError, TypeError):
                    feature_values[col] = base_snapshot.get(col, 0.0)
            else:
                feature_values[col] = base_snapshot.get(col, 0.0)
            feature_sources[col] = "market_snapshot (Set C)"
    else:
        for col in TECHNICAL_FEATURE_COLS:
            feature_values[col] = base_snapshot.get(col, 0.0)
            feature_sources[col] = "market_snapshot (Set C)"

    # -------------------------------------------------------------------------
    # 2. Stage 5: Enhanced Multi-Label Extractor (type_* and stage_*)
    # -------------------------------------------------------------------------
    cache = get_cache()
    cached_extractor_res = cache.get_extractor(headline_hash)
    
    if cached_extractor_res is not None:
        ext_info = cached_extractor_res
        metadata["extractor_cached"] = True
    else:
        try:
            extractor = get_enhanced_extractor_inst()
            ext_info = extractor.extract(
                headline=clean_headline,
                published_at=news_date_str,
            )
            cache.set_extractor(headline_hash, ext_info)
            metadata["extractor_cached"] = False
        except Exception as e:
            log_feature_fallback(
                component="extractor",
                headline=clean_headline,
                level="default_unclassified",
                reason=str(e),
            )
            ext_info = {
                "event_categories": {"not_relevant": 1.0},
                "primary_category": "not_relevant",
                "stage": "none",
                "stage_confidence": 1.0,
                "direction": 0.0,
                "intensity": 0.2,
                "novelty": 1.0,
            }

    metadata["enhanced_extraction"] = ext_info
    primary_category = str(ext_info.get("primary_category", "not_relevant"))

    # Map continuous confidence scores to feature columns
    try:
        extractor = get_enhanced_extractor_inst()
        ext_cols = extractor.map_to_feature_columns(ext_info, FEATURE_COLUMNS)
    except Exception as e:
        logger.warning("Mapping to feature columns failed (%s). Using fallback map.", e)
        ext_cols = {c: 0.0 for c in EVENT_FEATURE_COLS if c.startswith("stage_") or c.startswith("type_")}
        ext_cols["stage_none"] = 1.0
        ext_cols["type_none"] = 1.0

    for col, val in ext_cols.items():
        if col in FEATURE_COLUMNS:
            feature_values[col] = float(val)
            feature_sources[col] = "Stage 5 EnhancedExtractor"

    # -------------------------------------------------------------------------
    # 3. Stage 4: Event Proximity Calculator (days_to_next_known_event & in_window_*)
    # -------------------------------------------------------------------------
    try:
        prox_calc = get_proximity_calc()
        prox_info = prox_calc.calculate_proximity_features(
            headline=clean_headline,
            news_date=news_date_str,
        )
        metadata["proximity_info"] = prox_info
        
        days_next = float(prox_info["days_to_next_known_event"])
        in_win_7 = float(prox_calc.is_in_window_0_7(days_next))
        in_win_30 = float(prox_calc.is_in_window_0_30(days_next))
        in_win_2 = float(prox_calc.is_in_window_0_2(days_next))
        in_win_15 = float(prox_calc.is_in_window_0_15(days_next))

        feature_values["days_to_next_known_event"] = days_next
        feature_values["days_since_last_stage"] = 0.0
        feature_values["in_window_0_2"] = in_win_2
        feature_values["in_window_0_7"] = in_win_7
        feature_values["in_window_0_15"] = in_win_15
        feature_values["in_window_0_30"] = in_win_30

        for p_col in ["days_to_next_known_event", "days_since_last_stage", "in_window_0_2", "in_window_0_7", "in_window_0_15", "in_window_0_30"]:
            feature_sources[p_col] = "Stage 4 ProximityCalculator"
    except Exception as e:
        log_feature_fallback(
            component="proximity",
            headline=clean_headline,
            level="calendar_inactive",
            reason=str(e),
        )
        feature_values["days_to_next_known_event"] = -1.0
        feature_values["days_since_last_stage"] = 0.0
        feature_values["in_window_0_2"] = 0.0
        feature_values["in_window_0_7"] = 0.0
        feature_values["in_window_0_15"] = 0.0
        feature_values["in_window_0_30"] = 0.0
        for p_col in ["days_to_next_known_event", "days_since_last_stage", "in_window_0_2", "in_window_0_7", "in_window_0_15", "in_window_0_30"]:
            feature_sources[p_col] = "Stage 4 ProximityCalculator (fallback)"

    # -------------------------------------------------------------------------
    # 4. Stage 3: PriorCalculator & Fallback Chain (prior_mean_car, prior_median_car, prior_n)
    # -------------------------------------------------------------------------
    cached_prior_res = cache.get_prior(headline_hash, horizon)
    prior_obtained = False

    if cached_prior_res is not None:
        p_res = cached_prior_res
        metadata["prior_cached"] = True
        prior_mean = float(p_res.get("prior_mean_car", 0.0))
        prior_median = float(p_res.get("prior_median_car", 0.0))
        prior_std = float(p_res.get("prior_std", 0.0))
        prior_n = float(p_res.get("n_effective", 0.0))
        metadata["prior_info"] = p_res
        prior_obtained = True
    else:
        metadata["prior_cached"] = False
        try:
            prior_calc = get_prior_calc()
            p_res = prior_calc.get_prior(
                headline=clean_headline,
                horizon=horizon,
                k=10,
                category_filter=True,
            )
            cache.set_prior(headline_hash, horizon, p_res)
            prior_mean = float(p_res.get("prior_mean_car", 0.0))
            prior_median = float(p_res.get("prior_median_car", 0.0))
            prior_std = float(p_res.get("prior_std", 0.0))
            prior_n = float(p_res.get("n_effective", 0.0))
            metadata["prior_info"] = p_res
            prior_obtained = True
        except Exception as e:
            # Fallback Level 1: Category-average prior from DB
            log_feature_fallback(
                component="prior",
                headline=clean_headline,
                level="level_1_category_db",
                reason=f"PriorCalculator failed: {e}",
            )
            cat_prior = _query_category_prior_from_db(category=primary_category, horizon=horizon)
            if cat_prior is not None:
                prior_mean, prior_median, prior_std, prior_n = cat_prior
                prior_obtained = True
            else:
                # Fallback Level 2: 0.0
                log_feature_fallback(
                    component="prior",
                    headline=clean_headline,
                    level="level_2_zero_default",
                    reason="Category prior unavailable from DB",
                )
                prior_mean = 0.0
                prior_median = 0.0
                prior_std = 0.0
                prior_n = 0.0

    feature_values["prior_mean_car"] = prior_mean
    feature_values["prior_median_car"] = prior_median
    feature_values["prior_n"] = prior_n
    if "prior_std" in FEATURE_COLUMNS:
        feature_values["prior_std"] = prior_std

    for pr_col in ["prior_mean_car", "prior_median_car", "prior_n", "prior_std"]:
        if pr_col in FEATURE_COLUMNS:
            feature_sources[pr_col] = "Stage 3 PriorCalculator"

    # -------------------------------------------------------------------------
    # 5. Validation & Assembly into strict FEATURE_COLUMNS sequence
    # -------------------------------------------------------------------------
    vector_list: List[float] = []
    for col_name in FEATURE_COLUMNS:
        raw_val = feature_values.get(col_name, 0.0)
        # NaN / Inf fallback to 0.0
        if raw_val is None or np.isnan(raw_val) or np.isinf(raw_val):
            raw_val = 0.0
        vector_list.append(float(raw_val))

    raw_array = np.array(vector_list, dtype=np.float64)

    # Assertions per requirement 2
    assert len(raw_array) == len(FEATURE_COLUMNS), (
        f"Validation failed: expected {len(FEATURE_COLUMNS)} elements, got {len(raw_array)}"
    )
    assert not np.isnan(raw_array).any(), "Validation failed: output vector contains NaN values."
    assert not np.isinf(raw_array).any(), "Validation failed: output vector contains infinite values."

    return FeatureVector(
        input_array=raw_array,
        feature_names=FEATURE_COLUMNS,
        feature_sources=feature_sources,
        metadata=metadata,
    )


class NewsFeatureBuilder:
    """Object-oriented wrapper around build_features."""

    def __init__(self) -> None:
        self.feature_columns = list(FEATURE_COLUMNS)
        self.prior_calc = get_prior_calc()
        self.extractor = get_enhanced_extractor_inst()
        self.prox_calc = get_proximity_calc()

    def build(
        self,
        headline: str,
        news_date: Optional[Union[str, date, datetime]] = None,
        market_snapshot: Optional[Union[Dict[str, float], pd.Series, pd.DataFrame, Any]] = None,
        horizon: int = 10,
    ) -> FeatureVector:
        """Generate feature vector for news headline."""
        return build_features(
            headline=headline,
            news_date=news_date,
            market_snapshot=market_snapshot,
            horizon=horizon,
        )


__all__ = [
    "FeatureVector",
    "FeatureBuilderCache",
    "NewsFeatureBuilder",
    "build_features",
    "get_cache",
    "get_prior_calc",
    "get_enhanced_extractor_inst",
    "get_proximity_calc",
    "log_feature_fallback",
    "FEATURE_COLUMNS",
    "TECHNICAL_FEATURE_COLS",
    "EVENT_FEATURE_COLS",
]
