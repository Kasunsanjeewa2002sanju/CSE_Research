"""
Historical Event Evidence Retrieval & Strength Scoring for Stage 11.

Retrieves documented empirical event-study abnormal return statistics from Stage 4
and assigns evidence strength ratings according to a strict, documented rule.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from cse.utils.config import find_project_root

ROOT_DIR = find_project_root()
STAGE4_TYPE_STAGE_CSV = ROOT_DIR / "results" / "tables" / "event_study_by_type_stage.csv"
STAGE4_STAGE_CSV = ROOT_DIR / "results" / "tables" / "event_study_by_stage.csv"
STAGE4_TYPE_CSV = ROOT_DIR / "results" / "tables" / "event_study_by_type.csv"


def determine_evidence_strength(n: int, p_value: float, small_sample_warning: bool) -> str:
    """
    Documented rule for classifying empirical evidence strength:
    - strong: n >= 10 and p < 0.05 (sufficient sample, statistically significant at 5% level)
    - moderate: (n >= 5 and p < 0.10) or (n >= 15 and p <= 0.20 with consistent sample)
    - weak: n < 5 (small sample warning applies) or p > 0.20 or n == 0
    """
    if n == 0:
        return "weak"
    if n < 5 or small_sample_warning:
        return "weak"
    if n >= 10 and p_value < 0.05:
        return "strong"
    if n >= 5 and p_value < 0.10:
        return "moderate"
    if n >= 15 and p_value <= 0.20:
        return "moderate"
    return "weak"


class HistoricalEvidenceRetriever:
    """Retrieves empirical event study records from Stage 4 tabular archives."""

    def __init__(self) -> None:
        self.df_type_stage: Optional[pd.DataFrame] = None
        self.df_stage: Optional[pd.DataFrame] = None
        self.df_type: Optional[pd.DataFrame] = None
        self._load_tables()

    def _load_tables(self) -> None:
        try:
            if STAGE4_TYPE_STAGE_CSV.exists():
                self.df_type_stage = pd.read_csv(STAGE4_TYPE_STAGE_CSV)
            if STAGE4_STAGE_CSV.exists():
                self.df_stage = pd.read_csv(STAGE4_STAGE_CSV)
            if STAGE4_TYPE_CSV.exists():
                self.df_type = pd.read_csv(STAGE4_TYPE_CSV)
        except Exception:
            pass

    def get_evidence(
        self,
        event_category: str,
        stage: Optional[str] = None,
        window: str = "[0,+7]",
    ) -> Dict[str, Any]:
        """
        Query empirical abnormal returns (CAAR, Brown-Warner t-stat, p-values)
        for a categorized event and cycle stage.
        """
        # Map event_category to event study election_type
        type_mapping = {
            "presidential_election": "Presidential",
            "parliamentary_election": "Parliamentary",
            "provincial_council_election": "Provincial Council",
            "local_government_election": "Local Government",
        }
        elec_type = type_mapping.get(event_category)

        # 1. Try exact (election_type, stage, window) match
        if elec_type and stage and stage != "none" and self.df_type_stage is not None:
            sub = self.df_type_stage[
                (self.df_type_stage["election_type"] == elec_type)
                & (self.df_type_stage["stage"].str.lower() == stage.lower())
                & (self.df_type_stage["window"] == window)
            ]
            if not sub.empty:
                r = sub.iloc[0]
                n = int(r["n"])
                pval = float(r["t_pval"])
                warn = bool(r.get("warn_small_sample", n < 5))
                return {
                    "has_historical_match": True,
                    "matching_type": elec_type,
                    "matching_stage": stage,
                    "window": window,
                    "n_events": n,
                    "mean_car": float(r["caar"]),
                    "median_car": float(r["median_car"]),
                    "std_car": float(r["std_car"]),
                    "t_statistic": float(r["t_stat"]),
                    "t_pvalue": pval,
                    "sign_test_pvalue": float(r.get("sign_test_pval", 1.0)),
                    "permutation_pvalue": float(r.get("wilcoxon_pval", pval)),
                    "small_sample_warning": warn,
                    "evidence_strength": determine_evidence_strength(n, pval, warn),
                }

        # 2. Try stage-only match across all election types
        if stage and stage != "none" and self.df_stage is not None:
            sub = self.df_stage[
                (self.df_stage["stage"].str.lower() == stage.lower())
                & (self.df_stage["window"] == window)
            ]
            if not sub.empty:
                r = sub.iloc[0]
                n = int(r["n"])
                pval = float(r["t_pval"])
                warn = bool(r.get("warn_small_sample", n < 5))
                return {
                    "has_historical_match": True,
                    "matching_type": "Pooled Across Types",
                    "matching_stage": stage,
                    "window": window,
                    "n_events": n,
                    "mean_car": float(r["caar"]),
                    "median_car": float(r["median_car"]),
                    "std_car": float(r["std_car"]),
                    "t_statistic": float(r["t_stat"]),
                    "t_pvalue": pval,
                    "sign_test_pvalue": float(r.get("sign_test_pval", 1.0)),
                    "permutation_pvalue": float(r.get("wilcoxon_pval", pval)),
                    "small_sample_warning": warn,
                    "evidence_strength": determine_evidence_strength(n, pval, warn),
                }

        # 3. Try election_type match across stages
        if elec_type and self.df_type is not None:
            sub = self.df_type[
                (self.df_type["election_type"] == elec_type)
                & (self.df_type["window"] == window)
            ]
            if not sub.empty:
                r = sub.iloc[0]
                n = int(r["n"])
                pval = float(r["t_pval"])
                warn = bool(r.get("warn_small_sample", n < 5))
                return {
                    "has_historical_match": True,
                    "matching_type": elec_type,
                    "matching_stage": "Pooled Stages",
                    "window": window,
                    "n_events": n,
                    "mean_car": float(r["caar"]),
                    "median_car": float(r["median_car"]),
                    "std_car": float(r["std_car"]),
                    "t_statistic": float(r["t_stat"]),
                    "t_pvalue": pval,
                    "sign_test_pvalue": float(r.get("sign_test_pval", 1.0)),
                    "permutation_pvalue": float(r.get("wilcoxon_pval", pval)),
                    "small_sample_warning": warn,
                    "evidence_strength": determine_evidence_strength(n, pval, warn),
                }

        # 4. Default / non-electoral macro shock (IMF, monetary policy, etc.)
        return {
            "has_historical_match": False,
            "matching_type": event_category,
            "matching_stage": stage or "none",
            "window": window,
            "n_events": 0,
            "mean_car": 0.0,
            "median_car": 0.0,
            "std_car": 0.0,
            "t_statistic": 0.0,
            "t_pvalue": 1.0,
            "sign_test_pvalue": 1.0,
            "permutation_pvalue": 1.0,
            "small_sample_warning": True,
            "evidence_strength": "weak",
        }
