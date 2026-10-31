"""News-Specific Event Study Prior Calculator (Stage 3).

Computes data-driven prior_mean_car, prior_median_car, and prior_std features
for incoming news headlines using kNN semantic similarity over historical CAR values.

Provides:
- Class PriorCalculator(similarity_index, db_conn)
- Method get_prior(headline, horizon, k=10, category_filter=True) -> dict
- Cascading fallback hierarchy:
  a) n_effective < 3 -> Category CAR average
  b) Insufficient category data -> Overall historical CAR average
  c) Final fallback -> 0.0 (neutral baseline)
- Domain clamping to [-5%, +5%]
- Directional sentiment modulation:
  prior_signed = prior_median_car * (0.5 + 0.5 * direction)
- Persistent call logging in data/prior_calls.log
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from cse.news.embedder import EmbeddingEngine
from cse.news.historical_db import get_db_connection, get_default_db_path
from cse.news.offline import OfflineEventExtractor
from cse.news.similarity import SimilarityIndex, get_similarity_index
from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.prior_calculator")

MAX_PRIOR_ABS = 0.05  # 5% clamping limit


def get_default_log_path() -> Path:
    """Resolve path for prior calculation audit log."""
    root = find_project_root()
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "prior_calls.log"


def compute_weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Compute weighted median of 1D array.
    
    Parameters
    ----------
    values : np.ndarray
        Array of observations.
    weights : np.ndarray
        Array of non-negative weights.
        
    Returns
    -------
    float
        Weighted median value.
    """
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])

    order = np.argsort(values)
    sorted_vals = values[order]
    sorted_weights = weights[order]

    total_weight = float(np.sum(sorted_weights))
    if total_weight <= 1e-12:
        return float(np.median(sorted_vals))

    cum_weights = np.cumsum(sorted_weights)
    cutoff = total_weight * 0.5
    idx = int(np.searchsorted(cum_weights, cutoff))
    idx = min(idx, len(sorted_vals) - 1)
    return float(sorted_vals[idx])


def compute_weighted_mean_and_std(
    values: np.ndarray, weights: np.ndarray
) -> Tuple[float, float]:
    """Compute weighted mean and standard deviation of 1D array."""
    if len(values) == 0:
        return 0.0, 0.0
    total_w = float(np.sum(weights))
    if total_w <= 1e-12:
        return float(np.mean(values)), float(np.std(values))

    mean = float(np.sum(values * weights) / total_w)
    variance = float(np.sum(weights * (values - mean) ** 2) / total_w)
    std = float(np.sqrt(max(0.0, variance)))
    return mean, std


class PriorCalculator:
    """Calculates news-specific historical CAR priors using kNN semantic retrieval."""

    def __init__(
        self,
        similarity_index: Optional[SimilarityIndex] = None,
        db_conn: Optional[Union[sqlite3.Connection, str, Path]] = None,
        log_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self.similarity_index = (
            similarity_index if similarity_index is not None else get_similarity_index()
        )
        self.embedder: EmbeddingEngine = self.similarity_index.embedder
        self.log_path = Path(log_path) if log_path else get_default_log_path()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Connection handling
        self._owned_conn = False
        if isinstance(db_conn, sqlite3.Connection):
            self.conn = db_conn
        elif db_conn is not None:
            self.conn = get_db_connection(db_conn)
            self._owned_conn = True
        else:
            self.conn = get_db_connection()
            self._owned_conn = True

    def __del__(self) -> None:
        if getattr(self, "_owned_conn", False) and getattr(self, "conn", None):
            try:
                self.conn.close()
            except Exception:
                pass

    def _get_direction(self, headline: str) -> float:
        """Derive directional sentiment scalar between -1.0 and +1.0.
        
        Leverages FinBERT sentiment compound, supplemented with domain-specific
        financial directional polarities for monetary policy and credit shocks.
        """
        text_lower = headline.lower()

        # 1. Base sentiment from FinBERT
        sentiment = self.embedder.sentiment(headline)
        compound = float(sentiment.get("compound", 0.0))

        # 2. Domain-specific macro direction adjustments
        # Rate cuts / monetary easing are equity-positive
        if any(w in text_lower for w in ["cut", "cuts", "cutting", "reduce", "reduces", "reduction", "lower", "lowers"]):
            if any(w in text_lower for w in ["rate", "rates", "srr", "policy corridor", "corridor"]):
                return max(compound, 0.8)

        # Rate hikes / monetary tightening are equity-negative
        if any(w in text_lower for w in ["raise", "raises", "raising", "hike", "hikes", "hiking", "tighten", "tightens"]):
            if any(w in text_lower for w in ["rate", "rates", "corridor"]):
                return min(compound, -0.7)

        # Loan / tranche approvals are positive
        if any(w in text_lower for w in ["approve", "approves", "approved", "disburse", "disburses", "disbursed", "release", "releasing"]):
            if any(w in text_lower for w in ["imf", "tranche", "facility", "loan", "eff", "adb", "world bank"]):
                return max(compound, 0.6)

        # Loan / tranche delays or halts are negative
        if any(w in text_lower for w in ["delay", "delays", "delayed", "postpone", "postponed", "stall", "stalls", "halt", "halts", "reject", "rejects"]):
            if any(w in text_lower for w in ["imf", "tranche", "loan", "debt", "eff"]):
                return min(compound, -0.6)

        return float(np.clip(compound, -1.0, 1.0))

    def _log_call(
        self,
        headline: str,
        horizon: int,
        prior_median_car: float,
        n_effective: float,
        fallback_used: bool,
    ) -> None:
        """Write single structured audit line to data/prior_calls.log."""
        try:
            timestamp = datetime.datetime.now().isoformat()
            headline_hash = hashlib.sha256(headline.strip().encode("utf-8")).hexdigest()[:16]
            line = (
                f"{timestamp} | hash={headline_hash} | horizon={horizon} | "
                f"prior_median_car={prior_median_car:+.6f} | "
                f"n_effective={n_effective:.4f} | fallback_used={fallback_used}\n"
            )
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            logger.warning("Could not append to prior log %s: %s", self.log_path, e)

    def get_prior(
        self,
        headline: str,
        horizon: int,
        k: int = 10,
        category_filter: bool = True,
    ) -> Dict[str, Any]:
        """Compute news-specific CAR prior features.
        
        Parameters
        ----------
        headline : str
            Incoming news headline.
        horizon : int
            Forecast horizon in trading days (e.g. 1, 2, 5, 10).
        k : int, default 10
            Number of top similar news to retrieve.
        category_filter : bool, default True
            If True, restrains kNN search to same event_category.

        Returns
        -------
        Dict[str, Any]
            {
                similar_news: list,
                prior_mean_car: float,
                prior_median_car: float,
                prior_std: float,
                n_effective: float,
                fallback_used: bool,
                direction: float,
                prior_signed: float,
                prior_median_raw: float,
                prior_mean_raw: float,
            }
        """
        horizon_col = f"car_{horizon}d"
        direction = self._get_direction(headline)
        multiplier = 0.5 + 0.5 * direction

        # 1. Retrieve top-k similar news from SimilarityIndex
        similar_news = []
        try:
            similar_news = self.similarity_index.find_similar(
                query_text=headline,
                k=k,
                same_category_only=category_filter,
                min_similarity=0.35,
            )
        except Exception as e:
            logger.warning("Similarity search failed (%s). Proceeding to fallback.", e)

        # 2. Extract valid CAR observations and weights (w_i = similarity_i^2)
        valid_items: List[Dict[str, Any]] = []
        valid_cars: List[float] = []
        valid_weights: List[float] = []

        for item in similar_news:
            car_val = item.get(horizon_col)
            if car_val is not None and not np.isnan(car_val):
                sim = float(item.get("similarity", 0.0))
                w = sim ** 2
                valid_items.append(item)
                valid_cars.append(float(car_val))
                valid_weights.append(w)

        n_effective = float(np.sum(valid_weights)) if valid_weights else 0.0
        fallback_used = False
        fallback_level = "none"

        # 3. Apply Fallback Strategy
        if n_effective >= 3.0 and len(valid_cars) > 0:
            # Primary strategy: weighted kNN event study
            cars_arr = np.array(valid_cars, dtype=np.float32)
            weights_arr = np.array(valid_weights, dtype=np.float32)
            prior_mean_raw, prior_std = compute_weighted_mean_and_std(cars_arr, weights_arr)
            prior_median_raw = compute_weighted_median(cars_arr, weights_arr)
        else:
            # Fallback a: All news of same event_category
            fallback_used = True
            extractor = OfflineEventExtractor()
            category = extractor.extract(headline).event_category

            cat_rows: List[float] = []
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    f"SELECT {horizon_col} FROM news_history WHERE event_category = ? AND {horizon_col} IS NOT NULL",
                    (category,),
                )
                cat_rows = [float(r[0]) for r in cursor.fetchall() if r[0] is not None]
            except Exception as e:
                logger.debug("Category fallback query failed: %s", e)

            if len(cat_rows) >= 3:
                cars_arr = np.array(cat_rows, dtype=np.float32)
                weights_arr = np.ones_like(cars_arr)
                prior_mean_raw = float(np.mean(cars_arr))
                prior_median_raw = float(np.median(cars_arr))
                prior_std = float(np.std(cars_arr))
                n_effective = float(len(cat_rows))
                fallback_level = "category"
            else:
                # Fallback b: Overall historical CAR average across all news
                all_rows: List[float] = []
                try:
                    cursor = self.conn.cursor()
                    cursor.execute(
                        f"SELECT {horizon_col} FROM news_history WHERE {horizon_col} IS NOT NULL"
                    )
                    all_rows = [float(r[0]) for r in cursor.fetchall() if r[0] is not None]
                except Exception as e:
                    logger.debug("Overall fallback query failed: %s", e)

                if len(all_rows) >= 1:
                    cars_arr = np.array(all_rows, dtype=np.float32)
                    prior_mean_raw = float(np.mean(cars_arr))
                    prior_median_raw = float(np.median(cars_arr))
                    prior_std = float(np.std(cars_arr))
                    n_effective = float(len(all_rows))
                    fallback_level = "overall"
                else:
                    # Fallback c: 0.0 (empty database / zero signal baseline)
                    prior_mean_raw = 0.0
                    prior_median_raw = 0.0
                    prior_std = 0.0
                    n_effective = 0.0
                    fallback_level = "zero"

        # 4. Clamp to [-5%, +5%]
        prior_mean_raw = float(np.clip(prior_mean_raw, -MAX_PRIOR_ABS, MAX_PRIOR_ABS))
        prior_median_raw = float(np.clip(prior_median_raw, -MAX_PRIOR_ABS, MAX_PRIOR_ABS))

        # 5. Modulate by direction: prior_signed = prior_median_car * (0.5 + 0.5 * direction)
        prior_signed = float(np.clip(prior_median_raw * multiplier, -MAX_PRIOR_ABS, MAX_PRIOR_ABS))
        prior_mean_signed = float(np.clip(prior_mean_raw * multiplier, -MAX_PRIOR_ABS, MAX_PRIOR_ABS))

        # 6. Audit logging to data/prior_calls.log
        self._log_call(
            headline=headline,
            horizon=horizon,
            prior_median_car=prior_signed,
            n_effective=n_effective,
            fallback_used=fallback_used,
        )

        return {
            "similar_news": valid_items if valid_items else similar_news,
            "prior_mean_car": round(prior_mean_signed, 6),
            "prior_median_car": round(prior_signed, 6),
            "prior_std": round(float(prior_std), 6),
            "n_effective": round(float(n_effective), 4),
            "fallback_used": fallback_used,
            "direction": round(float(direction), 4),
            "prior_signed": round(prior_signed, 6),
            "prior_median_raw": round(prior_median_raw, 6),
            "prior_mean_raw": round(prior_mean_raw, 6),
            "horizon": horizon,
            "fallback_level": fallback_level,
        }


# Global singleton
_DEFAULT_PRIOR_CALCULATOR: Optional[PriorCalculator] = None


def get_prior_calculator() -> PriorCalculator:
    """Retrieve or initialize the global singleton PriorCalculator."""
    global _DEFAULT_PRIOR_CALCULATOR
    if _DEFAULT_PRIOR_CALCULATOR is None:
        _DEFAULT_PRIOR_CALCULATOR = PriorCalculator()
    return _DEFAULT_PRIOR_CALCULATOR
