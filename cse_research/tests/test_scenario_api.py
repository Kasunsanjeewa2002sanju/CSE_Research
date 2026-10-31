"""
Tests for Stage F9 Scenario Predictor REST API endpoints.
Verifies the exact API contract:
- GET /meta (categories, sectors, latest ASPI value)
- POST /scenario (TRUE/FALSE forecasts, direction, evidence strength, disclaimer, stale warning, meaning of FALSE)
- GET /scenario/evidence (historical matches: n, mean CAR, p-values, CAR series, evidence-strength text)
- GET /scenario/explanation (backend-generated text)
- GET /scenario/back-tests (predictions vs actual, hits & misses)
- API-defined meaning of FALSE: "the event does not occur"
"""

import pytest
from fastapi.testclient import TestClient

from cse.news.api import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_get_meta_contract(client):
    """GET /meta must return categories, sectors, and latest ASPI value."""
    res = client.get("/meta")
    assert res.status_code == 200
    data = res.json()

    assert "categories" in data or "news_categories" in data
    assert "sectors" in data
    assert "latest_aspi_value" in data
    assert data["latest_aspi_value"] > 0
    assert "disclaimers" in data or "disclaimer" in data


def test_post_scenario_contract(client):
    """
    POST /scenario must accept headline/description/date/category/sector
    and return TRUE/FALSE forecasts, direction, evidence strength, disclaimer,
    stale warning, and meaning_of_false = 'the event does not occur'.
    """
    payload = {
        "headline": "Presidential election proclamation gazetted for November 2026",
        "description": "Election commission releases timetable for nominations and balloting.",
        "publication_date": "2026-10-18",
        "category": "political",
        "sector": "banks",
    }
    res = client.post("/scenario", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Required fields per contract
    assert data["status"] == "success"
    assert "meaning_of_false" in data
    assert data["meaning_of_false"] == "the event does not occur"
    assert "disclaimer" in data
    assert "is_stale" in data
    assert data["is_stale"] is True  # 2026 is after 2025-12-31 baseline
    assert data["stale_warning"] is not None
    assert "expected_direction" in data
    assert data["expected_direction"] in {"positive", "negative", "neutral", "uncertain"}
    assert "evidence_strength" in data
    assert data["evidence_strength"] in {"strong", "moderate", "weak"}

    # Scenarios: CURRENT, TRUE, FALSE
    scenarios = data["scenarios"]
    assert "CURRENT" in scenarios
    assert "TRUE" in scenarios
    assert "FALSE" in scenarios

    for key in ["TRUE", "FALSE"]:
        sc = scenarios[key]
        assert "expected_return_pct" in sc
        assert "target_aspi" in sc
        assert "probability_up" in sc
        assert 0.0 <= sc["probability_up"] <= 1.0
        assert "interval_80" in sc
        assert len(sc["interval_80"]) == 2
        assert "interval_95" in sc
        assert len(sc["interval_95"]) == 2
        assert "trend_direction" in sc

    # Comparison matrix
    assert "comparison_matrix" in data
    assert len(data["comparison_matrix"]["rows"]) >= 5

    # Evidence block
    ev = data["historical_evidence"]
    assert "n_events" in ev
    assert "mean_car" in ev
    assert "evidence_strength_text" in ev
    assert "car_series" in ev
    assert len(ev["car_series"]) >= 10

    # Combined fan chart data
    assert "fan_chart" in data
    assert len(data["fan_chart"]["horizons"]) == 4

    # Explanation
    assert "explanation" in data
    assert len(data["explanation"]) > 20


def test_post_scenario_irrelevant_news(client):
    """Irrelevant news must flag no material impact detected."""
    payload = {
        "headline": "Local high school cricket championship concludes in Kandy",
        "description": "Annual sporting fixture ends in draw after three days.",
        "publication_date": "2024-06-10",
        "category": "not_relevant",
    }
    res = client.post("/scenario", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["is_material_impact"] is False
    assert "no material impact detected" in data["material_impact_summary"].lower()


def test_get_evidence_contract(client):
    """GET /scenario/evidence must return n, mean CAR, p-values, CAR series, and evidence-strength text."""
    res = client.get("/scenario/evidence?category=presidential_election&stage=announcement")
    assert res.status_code == 200
    data = res.json()

    assert "n" in data
    assert "mean_car" in data
    assert "p_values" in data
    assert "t_pvalue" in data["p_values"]
    assert "car_series" in data
    assert len(data["car_series"]) > 0
    assert "evidence_strength_text" in data
    assert data["meaning_of_false"] == "the event does not occur"


def test_get_explanation_contract(client):
    """GET /scenario/explanation must return backend-generated text and meaning of false."""
    res = client.get("/scenario/explanation?headline=Cabinet+approves+tax+incentive+package")
    assert res.status_code == 200
    data = res.json()

    assert "explanation" in data
    assert "Tax" in data["headline"] or "tax" in data["explanation"].lower()
    assert data["meaning_of_false"] == "the event does not occur"


def test_get_backtests_contract(client):
    """GET /scenario/back-tests must return predictions vs actuals with hits and misses."""
    res = client.get("/scenario/back-tests")
    assert res.status_code == 200
    data = res.json()

    summary = data["summary"]
    assert summary["total_tests"] == 20
    assert summary["hits"] == 15
    assert summary["misses"] == 5
    assert summary["hit_rate_pct"] == 75.0
    assert summary["coverage_95_pct"] == 85.0

    backtests = data["backtests"]
    assert len(backtests) == 20
    for b in backtests:
        assert "scenario_name" in b
        assert "predicted_impact_pct" in b
        assert "actual_impact_pct" in b
        assert "error_pct" in b
        assert "hit_direction" in b
        assert "inside_ci_95" in b
