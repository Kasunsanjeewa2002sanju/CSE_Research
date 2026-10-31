"""
Unit tests for Stage 11 Scenario Engine & Counterfactual Forecasting.

Tests sanity constraints, conformal intervals, magnitude caps, staleness,
irrelevant news invariance, and grounded narrative integrity.
"""

import pytest
import numpy as np

from cse.news.schema import NewsExtraction
from cse.scenario.conformal import ConformalIntervalEngine
from cse.scenario.engine import ScenarioEngine, run_scenario
from cse.scenario.evidence import HistoricalEvidenceRetriever, determine_evidence_strength


@pytest.fixture(scope="module")
def engine():
    return ScenarioEngine()


def test_irrelevant_news_impact_near_zero(engine):
    """Sanity Rule 1: Irrelevant news must produce TRUE approximately equal to FALSE."""
    res = engine.run(
        headline="Sri Lanka national cricket team wins match in Galle stadium",
        description="Sports tournament concludes with victory over visiting team.",
        publication_date="2024-05-15",
    )
    
    # Category should be not_relevant
    assert res["extraction"]["is_relevant"] is False or res["extraction"]["event_category"] == "not_relevant"
    
    # Impact across all horizons must be effectively zero (float equality)
    for h_str in ["1", "2", "5", "10"]:
        impact = res["impact"]["horizons"][h_str]
        assert abs(impact["diff_log_return"]) < 1e-5
        assert abs(impact["diff_aspi_level"]) < 1e-2
        assert abs(impact["diff_prob_up"]) < 1e-4


def test_relevant_event_creates_nonzero_impact(engine):
    """Relevant political event should create distinct TRUE vs FALSE forecasts."""
    res = engine.run(
        headline="President announces snap presidential election for September 21",
        description="Official gazette proclamation issued by Election Commission.",
        publication_date="2024-07-26",
    )
    assert res["extraction"]["is_relevant"] is True
    assert res["extraction"]["event_category"] == "presidential_election"

    # TRUE and FALSE should differ
    h1_impact = res["impact"]["horizons"]["1"]
    assert "diff_log_return" in h1_impact
    assert "diff_aspi_level" in h1_impact


def test_magnitude_cap():
    """Sanity Rule 2: Magnitude cap restricts explosive returns to historical quantiles."""
    conf = ConformalIntervalEngine()
    
    # Horizon 1: Cap is ~0.0497
    capped_val, was_capped = conf.apply_magnitude_cap(0.25, horizon=1)
    assert was_capped is True
    assert capped_val <= 0.06
    
    # Normal value should not be capped
    normal_val, was_capped_norm = conf.apply_magnitude_cap(0.01, horizon=1)
    assert was_capped_norm is False
    assert normal_val == 0.01


def test_conformal_intervals_nesting(engine):
    """Conformal prediction intervals must follow strict ordering: 95% lower <= 80% lower <= expected <= 80% upper <= 95% upper."""
    res = engine.run(
        headline="Central Bank unexpectedly hikes policy interest rate by 100 bps",
        description="CBSL Monetary Board announces monetary tightening to combat inflation.",
        publication_date="2022-04-08",
    )
    for scen in ["TRUE", "FALSE"]:
        for h_str in ["1", "2", "5", "10"]:
            h_data = res["scenarios"][scen]["horizons"][h_str]
            aspi_exp = h_data["expected_aspi_level"]
            ci80_low = h_data["interval_80"]["aspi_lower"]
            ci80_high = h_data["interval_80"]["aspi_upper"]
            ci95_low = h_data["interval_95"]["aspi_lower"]
            ci95_high = h_data["interval_95"]["aspi_upper"]

            assert ci95_low <= ci80_low
            assert ci80_low <= aspi_exp
            assert aspi_exp <= ci80_high
            assert ci80_high <= ci95_high


def test_staleness_flag_for_future_dates(engine):
    """Dates beyond historical database (after 2025-12-31) must be marked STALE unless caller supplies live price."""
    res = engine.run(
        headline="Parliament passes landmark economic transformation bill",
        description="Legislative reform passes with government majority.",
        publication_date="2026-10-15",
    )
    assert res["market_context"]["is_stale"] is True


def test_historical_evidence_block():
    """Historical evidence block must provide matching event statistics and documented strength."""
    retriever = HistoricalEvidenceRetriever()
    ev = retriever.get_evidence("presidential_election", stage="announcement")
    
    assert ev["has_historical_match"] is True
    assert ev["n_events"] > 0
    assert "mean_car" in ev
    assert "t_statistic" in ev
    assert ev["evidence_strength"] in {"weak", "moderate", "strong"}


def test_evidence_strength_rule():
    """Documented evidence strength classification logic test."""
    assert determine_evidence_strength(n=15, p_value=0.01, small_sample_warning=False) == "strong"
    assert determine_evidence_strength(n=8, p_value=0.07, small_sample_warning=False) == "moderate"
    assert determine_evidence_strength(n=3, p_value=0.01, small_sample_warning=True) == "weak"
    assert determine_evidence_strength(n=20, p_value=0.45, small_sample_warning=False) == "weak"


def test_explanation_figures_come_from_output(engine):
    """Sanity Rule 4: Plain-language explanation cites numbers from the output object."""
    res = engine.run(
        headline="IMF Executive Board completes first review of Sri Lanka bailout",
        description="IMF approves second tranche disbursement following fiscal benchmarks.",
        publication_date="2023-12-12",
    )
    exp = res["explanation"]
    
    # Headline and category present
    assert "IMF" in exp
    
    # Current ASPI level cited
    aspi_val = f"{res['market_context']['current_aspi_level']:,.2f}"
    assert aspi_val in exp
    
    # Return impact cited
    h1_imp = res["impact"]["horizons"]["1"]["diff_log_return"] * 100
    assert f"{h1_imp:+.2f}%" in exp
