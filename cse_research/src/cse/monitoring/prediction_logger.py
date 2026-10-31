"""Prediction logger and distribution monitoring for CSE news predictions (Stage 7).

Tracks every prediction made by the news pipeline:
- Logs: {timestamp, headline, features_hash, predicted_car, prediction_interval,
  horizon, prior_used, days_to_next, fallback_used}
- Computes daily prediction distribution: mean, std, min, max
- Emits health alerts:
    * ALERT (warning) if std of predictions < 0.1% (predictions converging = bug)
    * ALERT (warning) if fallback_used rate > 20% (prior calculator failing too often)
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from cse.utils.config import find_project_root

logger = logging.getLogger("cse.monitoring.prediction_logger")

ROOT_DIR = find_project_root()
DEFAULT_PREDICTION_LOG_PATH = ROOT_DIR / "data" / "predictions.jsonl"


class PredictionLogger:
    """Logs prediction invocations and monitors prediction health."""

    def __init__(
        self,
        log_path: Optional[Union[str, Path]] = None,
        min_samples_for_alerts: int = 3,
    ) -> None:
        self.log_path = Path(log_path) if log_path else DEFAULT_PREDICTION_LOG_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.min_samples_for_alerts = min_samples_for_alerts
        self._in_memory_records: List[Dict[str, Any]] = []

    def log_prediction(
        self,
        headline: str,
        features_hash: str,
        predicted_car: float,
        horizon: int = 5,
        prediction_interval: Optional[Union[Tuple[float, float], List[float]]] = None,
        prior_used: Optional[float] = None,
        days_to_next: Optional[float] = None,
        fallback_used: bool = False,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a single prediction event.

        Parameters
        ----------
        headline : str
            News headline.
        features_hash : str
            Unique hash of the input feature vector.
        predicted_car : float
            Predicted CAR or return (e.g., 0.015 for +1.5%).
        horizon : int
            Forecast horizon in trading days (default 5).
        prediction_interval : list/tuple, optional
            Confidence / conformal interval [lower, upper].
        prior_used : float, optional
            Value of prior CAR feature used.
        days_to_next : float, optional
            Trading days to next known event.
        fallback_used : bool
            Whether a fallback prior was used.
        timestamp : str, optional
            ISO8601 timestamp string (default current UTC time).

        Returns
        -------
        dict
            Logged prediction dictionary.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        interval_list: Optional[List[float]] = None
        if prediction_interval is not None:
            interval_list = [float(prediction_interval[0]), float(prediction_interval[1])]

        record: Dict[str, Any] = {
            "timestamp": timestamp,
            "headline": str(headline),
            "features_hash": str(features_hash),
            "predicted_car": float(predicted_car),
            "prediction_interval": interval_list,
            "horizon": int(horizon),
            "prior_used": float(prior_used) if prior_used is not None else None,
            "days_to_next": float(days_to_next) if days_to_next is not None else None,
            "fallback_used": bool(fallback_used),
        }

        # Append to in-memory store
        self._in_memory_records.append(record)

        # Append JSON line to disk
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error("Failed to append prediction log to %s: %s", self.log_path, e)

        return record

    def load_records(
        self,
        date_str: Optional[str] = None,
        horizon: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Load records from disk (and/or in-memory cache) matching filters."""
        records: List[Dict[str, Any]] = []

        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                            records.append(item)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error("Error reading %s: %s", self.log_path, e)

        # Merge with any memory records that might not have been flushed or in tests
        seen_hashes = {(r.get("timestamp"), r.get("features_hash")) for r in records}
        for mem_r in self._in_memory_records:
            key = (mem_r.get("timestamp"), mem_r.get("features_hash"))
            if key not in seen_hashes:
                records.append(mem_r)
                seen_hashes.add(key)

        # Filter by date if specified
        if date_str:
            clean_date = date_str[:10]
            records = [r for r in records if r.get("timestamp", "")[:10] == clean_date]

        # Filter by horizon if specified
        if horizon is not None:
            records = [r for r in records if r.get("horizon") == horizon]

        return records

    def compute_daily_distribution(
        self,
        date_str: Optional[str] = None,
        horizon: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compute summary statistics and trigger health alerts.

        Parameters
        ----------
        date_str : str, optional
            Target date string (YYYY-MM-DD). If omitted, finds latest date or today.
        horizon : int, optional
            Filter to a specific horizon (e.g. 5).

        Returns
        -------
        dict
            Distribution metrics and list of triggered alerts.
        """
        all_records = self.load_records()
        if not all_records:
            return {
                "date": date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "fallback_count": 0,
                "fallback_rate": 0.0,
                "alerts": [],
            }

        if date_str is None:
            # Find latest available date in records
            dates = [r.get("timestamp", "")[:10] for r in all_records if r.get("timestamp")]
            date_str = max(dates) if dates else datetime.now(timezone.utc).strftime("%Y-%m-%d")

        clean_date = date_str[:10]
        day_records = [r for r in all_records if r.get("timestamp", "")[:10] == clean_date]
        if horizon is not None:
            day_records = [r for r in day_records if r.get("horizon") == horizon]

        n = len(day_records)
        if n == 0:
            return {
                "date": clean_date,
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "fallback_count": 0,
                "fallback_rate": 0.0,
                "alerts": [],
            }

        cars = [float(r["predicted_car"]) for r in day_records]
        mean_val = float(np.mean(cars))
        std_val = float(np.std(cars, ddof=1)) if n > 1 else 0.0
        min_val = float(np.min(cars))
        max_val = float(np.max(cars))

        fallback_count = sum(1 for r in day_records if r.get("fallback_used", False))
        fallback_rate = float(fallback_count / n)

        alerts: List[str] = []

        # ALERT 1: std of predictions < 0.1% (0.001) -> predictions converging (bug)
        # Note: 0.1% = 0.001. We check if count meets min_samples.
        if n >= self.min_samples_for_alerts and std_val < 0.001:
            msg = (
                f"ALERT: Prediction standard deviation ({std_val:.4f} / {std_val * 100:.3f}%) "
                f"is below 0.10% across {n} predictions on {clean_date}. "
                "Predictions appear to be converging to a static constant (potential feature/model bug)!"
            )
            logger.warning(msg)
            alerts.append(msg)

        # ALERT 2: fallback_used rate > 20% (0.20) -> prior calculator failing too often
        if n >= self.min_samples_for_alerts and fallback_rate > 0.20:
            msg = (
                f"ALERT: Fallback prior rate ({fallback_rate:.1%}) exceeds 20.0% threshold "
                f"({fallback_count}/{n} fallbacks on {clean_date}). "
                "Semantic similarity or historical CAR prior retrieval may be degrading!"
            )
            logger.warning(msg)
            alerts.append(msg)

        return {
            "date": clean_date,
            "count": n,
            "mean": round(mean_val, 6),
            "std": round(std_val, 6),
            "min": round(min_val, 6),
            "max": round(max_val, 6),
            "fallback_count": fallback_count,
            "fallback_rate": round(fallback_rate, 4),
            "alerts": alerts,
        }

    def check_health_alerts(self, date_str: Optional[str] = None) -> List[str]:
        """Convenience function to inspect active alert messages."""
        summary = self.compute_daily_distribution(date_str)
        return summary["alerts"]


_default_logger_inst: Optional[PredictionLogger] = None


def get_prediction_logger(log_path: Optional[Union[str, Path]] = None) -> PredictionLogger:
    """Retrieve singleton or configured PredictionLogger instance."""
    global _default_logger_inst
    if _default_logger_inst is None or log_path is not None:
        _default_logger_inst = PredictionLogger(log_path=log_path)
    return _default_logger_inst
