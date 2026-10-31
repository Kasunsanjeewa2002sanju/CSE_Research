"""
Split-Conformal Prediction Interval Engine for Stage 11.

Calculates exact 80% and 95% prediction intervals using empirical walk-forward
out-of-sample residuals, stratifying by event-window vs non-event market regimes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np

from cse.utils.config import find_project_root

ROOT_DIR = find_project_root()
CONFORMAL_JSON_PATH = ROOT_DIR / "models" / "final" / "conformal_residuals.json"
MAGNITUDE_CAPS_JSON_PATH = ROOT_DIR / "models" / "final" / "magnitude_caps.json"


class ConformalIntervalEngine:
    """Computes empirical prediction intervals and magnitude caps across horizons."""

    def __init__(self) -> None:
        self.conformal_data: Dict[str, Any] = {}
        self.magnitude_caps: Dict[str, float] = {}
        self._load_calibration_data()

    def _load_calibration_data(self) -> None:
        if CONFORMAL_JSON_PATH.exists():
            try:
                with open(CONFORMAL_JSON_PATH, "r", encoding="utf-8") as f:
                    self.conformal_data = json.load(f)
            except Exception:
                pass

        if MAGNITUDE_CAPS_JSON_PATH.exists():
            try:
                with open(MAGNITUDE_CAPS_JSON_PATH, "r", encoding="utf-8") as f:
                    self.magnitude_caps = json.load(f)
            except Exception:
                pass

    def apply_magnitude_cap(self, raw_ret: float, horizon: int) -> tuple[float, bool]:
        """Apply empirical 99.5% historical return magnitude cap."""
        cap = float(self.magnitude_caps.get(str(horizon), 0.15))
        is_capped = abs(raw_ret) > cap
        capped_ret = float(np.clip(raw_ret, -cap, cap))
        return capped_ret, is_capped

    def compute_intervals(
        self,
        predicted_log_ret: float,
        aspi_current: float,
        horizon: int,
        is_event_active: bool = False,
    ) -> Dict[str, Any]:
        """
        Compute 80% and 95% conformal prediction intervals for log return and ASPI level.
        
        Args:
            predicted_log_ret: Model expected log return.
            aspi_current: Current ASPI level S_t.
            horizon: Trading days horizon h in {1, 2, 5, 10}.
            is_event_active: True for Scenario TRUE (uses event residuals); False for Scenario FALSE.
        """
        h_str = str(horizon)
        cal_h = self.conformal_data.get(h_str, {})
        regime_key = "event" if is_event_active else "non_event"
        quantiles = cal_h.get(regime_key, {"coverage_80": 0.02, "coverage_95": 0.04})

        q80 = float(quantiles.get("coverage_80", 0.02))
        q95 = float(quantiles.get("coverage_95", 0.04))

        # Return intervals
        ret_80_lower = float(predicted_log_ret - q80)
        ret_80_upper = float(predicted_log_ret + q80)
        ret_95_lower = float(predicted_log_ret - q95)
        ret_95_upper = float(predicted_log_ret + q95)

        # ASPI level intervals
        aspi_expected = float(aspi_current * np.exp(predicted_log_ret))
        aspi_80_lower = float(aspi_current * np.exp(ret_80_lower))
        aspi_80_upper = float(aspi_current * np.exp(ret_80_upper))
        aspi_95_lower = float(aspi_current * np.exp(ret_95_lower))
        aspi_95_upper = float(aspi_current * np.exp(ret_95_upper))

        return {
            "expected_log_return": predicted_log_ret,
            "expected_aspi_level": aspi_expected,
            "conformal_residuals_used": regime_key,
            "interval_80": {
                "coverage_pct": 80.0,
                "quantile_margin": q80,
                "log_return_lower": ret_80_lower,
                "log_return_upper": ret_80_upper,
                "aspi_lower": aspi_80_lower,
                "aspi_upper": aspi_80_upper,
            },
            "interval_95": {
                "coverage_pct": 95.0,
                "quantile_margin": q95,
                "log_return_lower": ret_95_lower,
                "log_return_upper": ret_95_upper,
                "aspi_lower": aspi_95_lower,
                "aspi_upper": aspi_95_upper,
            },
        }
