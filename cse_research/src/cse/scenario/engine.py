"""
Core Scenario Engine for Stage 11.

Combines Stage 10 news extraction, Stage 4 event-study statistics, and the Stage 9
frozen model into a conditional counterfactual forecasting engine.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from cse.news.llm_extract import extract_event
from cse.news.schema import NewsExtraction
from cse.scenario.conformal import ConformalIntervalEngine
from cse.scenario.evidence import HistoricalEvidenceRetriever
from cse.scenario.explanation import generate_scenario_explanation
from cse.scenario.feature_builder import ScenarioFeatureBuilder
from cse.utils.config import find_project_root

ROOT_DIR = find_project_root()
SCENARIO_MODELS_PATH = ROOT_DIR / "models" / "final" / "scenario_models.pkl"
HORIZONS = [1, 2, 5, 10]


class ScenarioEngine:
    """End-to-end conditional counterfactual scenario forecasting engine."""

    def __init__(self, models_path: Optional[Union[str, Path]] = None) -> None:
        self.feature_builder = ScenarioFeatureBuilder()
        self.conformal_engine = ConformalIntervalEngine()
        self.evidence_retriever = HistoricalEvidenceRetriever()
        
        path = Path(models_path) if models_path else SCENARIO_MODELS_PATH
        if not path.exists():
            raise FileNotFoundError(f"Frozen scenario models not found at {path}. Run prepare_stage11_models.py first.")

        with open(path, "rb") as f:
            self.models = pickle.load(f)

    def run(
        self,
        headline: str,
        description: str = "",
        publication_date: str = "",
        source: Optional[str] = None,
        current_aspi: Optional[float] = None,
        extraction_override: Optional[NewsExtraction] = None,
    ) -> Dict[str, Any]:
        """
        Execute scenario evaluation for an incoming news item.
        
        Args:
            headline: News headline text.
            description: Optional news body / context.
            publication_date: Date string (YYYY-MM-DD).
            source: Optional news source name.
            current_aspi: Optional explicit ASPI level (overrides database value).
            extraction_override: Optional pre-computed NewsExtraction.
        """
        # 1. News extraction (Stage 10)
        if extraction_override is not None:
            extracted = extraction_override
        else:
            extracted = extract_event(
                headline=headline,
                description=description,
                publication_date=publication_date,
                source=source,
                use_cache=True,
            )

        # 2. Date and market baseline resolution
        as_of_date, aspi_level, row_idx, is_stale = self.feature_builder.resolve_date_and_aspi(
            news_date=publication_date,
            override_aspi=current_aspi,
        )

        # 3. Build X_TRUE and X_FALSE feature vectors
        x_true, x_false, event_meta = self.feature_builder.build_scenario_features(
            news_item=extracted,
            row_idx=row_idx,
            as_of_date=as_of_date,
            headline=headline,
        )

        # 4. Multi-horizon scenario evaluation
        scenarios_output: Dict[str, Any] = {"TRUE": {"horizons": {}}, "FALSE": {"horizons": {}}}
        impact_output: Dict[str, Any] = {"horizons": {}}

        for h in HORIZONS:
            h_str = str(h)
            h_model = self.models.get(h)
            if not h_model:
                continue

            reg = h_model["regressor"]
            clf = h_model["classifier"]
            calibrator = h_model["calibrator"]

            # Scenario TRUE predictions
            raw_ret_true = float(reg.predict(x_true)[0])
            capped_ret_true, is_capped_true = self.conformal_engine.apply_magnitude_cap(raw_ret_true, h)
            raw_prob_true = float(clf.predict_proba(x_true)[0, 1])
            cal_prob_true = float(calibrator.predict_proba(np.array([[raw_prob_true]]))[0, 1])

            intervals_true = self.conformal_engine.compute_intervals(
                predicted_log_ret=capped_ret_true,
                aspi_current=aspi_level,
                horizon=h,
                is_event_active=True,
            )

            dir_true = "positive" if capped_ret_true > 0.001 else ("negative" if capped_ret_true < -0.001 else "neutral")

            scenarios_output["TRUE"]["horizons"][h_str] = {
                **intervals_true,
                "prob_up": cal_prob_true,
                "trend_direction": dir_true,
                "is_magnitude_capped": is_capped_true,
            }

            # Scenario FALSE predictions
            raw_ret_false = float(reg.predict(x_false)[0])
            capped_ret_false, is_capped_false = self.conformal_engine.apply_magnitude_cap(raw_ret_false, h)
            raw_prob_false = float(clf.predict_proba(x_false)[0, 1])
            cal_prob_false = float(calibrator.predict_proba(np.array([[raw_prob_false]]))[0, 1])

            intervals_false = self.conformal_engine.compute_intervals(
                predicted_log_ret=capped_ret_false,
                aspi_current=aspi_level,
                horizon=h,
                is_event_active=False,
            )

            dir_false = "positive" if capped_ret_false > 0.001 else ("negative" if capped_ret_false < -0.001 else "neutral")

            scenarios_output["FALSE"]["horizons"][h_str] = {
                **intervals_false,
                "prob_up": cal_prob_false,
                "trend_direction": dir_false,
                "is_magnitude_capped": is_capped_false,
            }

            # Impact = TRUE minus FALSE
            diff_ret = capped_ret_true - capped_ret_false
            diff_aspi = intervals_true["expected_aspi_level"] - intervals_false["expected_aspi_level"]
            diff_prob = cal_prob_true - cal_prob_false

            impact_output["horizons"][h_str] = {
                "diff_log_return": diff_ret,
                "diff_aspi_level": diff_aspi,
                "diff_prob_up": diff_prob,
            }

        # 5. Historical event study evidence
        cat = extracted.event_category
        stg = extracted.stage
        evidence = self.evidence_retriever.get_evidence(event_category=cat, stage=stg)

        # Assemble result
        result: Dict[str, Any] = {
            "input": {
                "headline": headline,
                "description": description,
                "publication_date": publication_date,
                "source": source,
            },
            "extraction": extracted.to_dict(),
            "market_context": {
                "as_of_date": as_of_date,
                "current_aspi_level": aspi_level,
                "is_stale": is_stale,
            },
            "scenarios": scenarios_output,
            "impact": impact_output,
            "historical_evidence": evidence,
        }

        # 6. Generate grounded plain-language explanation
        result["explanation"] = generate_scenario_explanation(result)

        return result


# Module-level convenience function
_engine_singleton: Optional[ScenarioEngine] = None


def get_scenario_engine() -> ScenarioEngine:
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = ScenarioEngine()
    return _engine_singleton


def run_scenario(
    headline: str,
    description: str = "",
    publication_date: str = "",
    source: Optional[str] = None,
    current_aspi: Optional[float] = None,
) -> Dict[str, Any]:
    """Execute scenario evaluation."""
    return get_scenario_engine().run(
        headline=headline,
        description=description,
        publication_date=publication_date,
        source=source,
        current_aspi=current_aspi,
    )
