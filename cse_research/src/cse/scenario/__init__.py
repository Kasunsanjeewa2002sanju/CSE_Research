"""
Stage 11 Scenario Engine & Counterfactual Forecasting Package.
"""

from cse.scenario.conformal import ConformalIntervalEngine
from cse.scenario.engine import ScenarioEngine, get_scenario_engine, run_scenario
from cse.scenario.evidence import HistoricalEvidenceRetriever, determine_evidence_strength
from cse.scenario.explanation import generate_scenario_explanation
from cse.scenario.feature_builder import ScenarioFeatureBuilder

__all__ = [
    "ScenarioEngine",
    "run_scenario",
    "get_scenario_engine",
    "ConformalIntervalEngine",
    "HistoricalEvidenceRetriever",
    "determine_evidence_strength",
    "ScenarioFeatureBuilder",
    "generate_scenario_explanation",
]
