"""Probability calibration module (Platt scaling and Isotonic regression) fitted on inner validation slice.

Adheres strictly to:
- Rule R2: Zero lookahead. Calibration fitted on inner-validation slice only, never on outer validation.
- Protocol: Provides well-calibrated probability of positive return Pr(y_ret > 0).
- Implementation: Mathematical Platt scaling (Platt 1999) via logistic regression on inner-val scores.
"""

from __future__ import annotations

import warnings
from typing import Any, Optional
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from cse.utils.logger import get_logger

logger = get_logger("cse.models.shallow.calibrator")


class InnerSliceCalibrator:
    """Calibrates classifier probabilities on the inner validation slice using Platt scaling or Isotonic regression."""

    def __init__(self, method: str = "sigmoid") -> None:
        """Args:
            method: 'sigmoid' for Platt scaling or 'isotonic' for Isotonic regression.
        """
        self.method = method.lower()
        self.calibrator_model_: Any = None
        self.fallback_raw: bool = False

    def _get_base_scores(self, base_clf: Any, X: np.ndarray) -> np.ndarray:
        """Extract uncalibrated 1D decision scores or probabilities from base classifier."""
        if hasattr(base_clf, "predict_proba"):
            probs = base_clf.predict_proba(X)
            # Probability of positive class (col 1 if 2 classes, else col 0)
            if probs.ndim == 2 and probs.shape[1] > 1:
                return probs[:, 1]
            return probs.ravel()
        elif hasattr(base_clf, "decision_function"):
            df = base_clf.decision_function(X)
            return 1.0 / (1.0 + np.exp(-df))
        else:
            preds = base_clf.predict(X)
            return preds.astype(float)

    def fit_calibration(
        self,
        base_clf: Any,
        X_inner_val: np.ndarray,
        y_inner_val: np.ndarray,
    ) -> InnerSliceCalibrator:
        """Fit probability calibration strictly on the inner validation slice."""
        unique_classes = np.unique(y_inner_val)
        if len(unique_classes) < 2:
            logger.warning("Inner validation slice contains only 1 class. Falling back to raw probabilities.")
            self.fallback_raw = True
            return self

        try:
            scores_val = self._get_base_scores(base_clf, X_inner_val)

            if self.method == "sigmoid":
                # Platt (1999) scaling: 1D logistic regression P(y=1|score) = 1 / (1 + exp(A*score + B))
                cal_mod = LogisticRegression(C=1.0, solver="lbfgs")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cal_mod.fit(scores_val.reshape(-1, 1), y_inner_val)
                self.calibrator_model_ = cal_mod
                self.fallback_raw = False
            elif self.method == "isotonic":
                # Isotonic regression
                iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    iso.fit(scores_val, y_inner_val)
                self.calibrator_model_ = iso
                self.fallback_raw = False
            else:
                self.fallback_raw = True

        except Exception as exc:
            logger.warning("Calibration fit failed (%s). Falling back to base classifier probabilities.", exc)
            self.fallback_raw = True

        return self

    def predict_proba(self, base_clf: Any, X: np.ndarray) -> np.ndarray:
        """Predict calibrated class probabilities."""
        scores = self._get_base_scores(base_clf, X)

        if self.fallback_raw or self.calibrator_model_ is None:
            p1 = np.clip(scores, 0.0, 1.0)
            return np.column_stack([1.0 - p1, p1])

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if self.method == "sigmoid":
                    probs = self.calibrator_model_.predict_proba(scores.reshape(-1, 1))
                    return probs
                elif self.method == "isotonic":
                    p1 = self.calibrator_model_.predict(scores)
                    p1 = np.clip(p1, 0.0, 1.0)
                    return np.column_stack([1.0 - p1, p1])
        except Exception:
            p1 = np.clip(scores, 0.0, 1.0)
            return np.column_stack([1.0 - p1, p1])

        p1 = np.clip(scores, 0.0, 1.0)
        return np.column_stack([1.0 - p1, p1])
