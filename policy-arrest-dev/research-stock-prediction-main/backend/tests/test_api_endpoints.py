import pytest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_api_inventory():
    res = client.get("/api/inventory")
    assert res.status_code == 200
    data = res.json()
    assert "market_dataset" in data
    assert "event_datasets" in data
    assert data["event_datasets"]["total_events"] == 104

def test_api_timeline():
    res = client.get("/api/timeline?from=2022-01-01&to=2022-12-31")
    assert res.status_code == 200
    data = res.json()
    assert "price_series" in data
    assert "event_markers" in data

def test_api_events_list():
    res = client.get("/api/events?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data["events"]) > 0

def test_api_predict_policy():
    payload = {
        "policy_type": "Tax Changes",
        "policy_headline": "Parliament enacts Social Security Contribution Levy",
        "announcement_date": "2022-09-08",
        "forecast_horizon": 5
    }
    res = client.post("/api/predict/policy", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_direction" in data
    assert "expected_return_pct" in data
    assert "similar_events" in data

def test_api_live_status():
    res = client.get("/api/live/status")
    assert res.status_code == 200
    data = res.json()
    assert "market_status" in data

def test_api_live_indices():
    res = client.get("/api/live/indices")
    assert res.status_code == 200
    data = res.json()
    assert "aspi" in data
