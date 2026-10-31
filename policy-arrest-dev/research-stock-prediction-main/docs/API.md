# PolitiTrade LK — REST API Reference Documentation

**Base URL:** `http://127.0.0.1:8001`  
**OpenAPI Specification:** `http://127.0.0.1:8001/docs`  
**Data Format:** JSON  
**Encoding:** UTF-8

---

## 1. System & Health Endpoints

### 1.1 Health Check
- **Endpoint:** `GET /api/health`
- **Description:** Verifies backend server health, database connectivity, and data availability.
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "app_name": "PolitiTrade LK",
  "version": "1.0.0",
  "environment": "development",
  "port": 8001,
  "market_data_available": true,
  "total_trading_sessions": 9772
}
```

### 1.2 Data Inventory Audit
- **Endpoint:** `GET /api/inventory`
- **Description:** Returns inventory of historical market sessions, price dates, event counts, and model artifacts.
- **Response `200 OK`:**
```json
{
  "market_data": {
    "sessions_count": 9772,
    "start_date": "1985-01-02",
    "end_date": "2025-12-31",
    "symbols": ["ASPI", "S&P SL20"]
  },
  "events_data": {
    "total_events": 104,
    "government_policies": 70,
    "political_arrests": 34
  },
  "models": {
    "policy_model_ready": true,
    "arrest_model_ready": true
  }
}
```

---

## 2. Market Series & Historical Timeline

### 2.1 Historical Timeline
- **Endpoint:** `GET /api/timeline`
- **Query Parameters:**
  - `from` *(string, optional, default: "2020-01-01")*: ISO start date.
  - `to` *(string, optional, default: "2025-12-31")*: ISO end date.
  - `family` *(string, optional)*: Filter by event family ("Government Policy" | "Political Arrest").
  - `subtype` *(string, optional)*: Filter by specific category or legal subtype.
  - `impact_direction` *(string, optional)*: "Positive" | "Negative" | "Neutral".
- **Response `200 OK`:**
```json
{
  "date_range": { "from": "2020-01-01", "to": "2025-12-31" },
  "total_sessions": 1450,
  "total_events_in_range": 104,
  "price_series": [
    {
      "date": "2020-01-02",
      "aspi": 6129.21,
      "sp_sl20": 2936.85,
      "turnover_mn": 482.1,
      "daily_return_pct": 0.42
    }
  ],
  "event_markers": [
    {
      "event_id": "POL-2022-005",
      "title": "CBSL Hikes Policy Rates by 700 bps",
      "event_family": "Government Policy",
      "event_subtype": "Monetary Policy",
      "aligned_date": "2022-04-08",
      "aspi_close_event": 7824.5,
      "car_1d": 0.015,
      "car_5d": -0.042,
      "car_20d": -0.118,
      "raw_return_5d": -0.038,
      "impact_direction": "Negative"
    }
  ]
}
```

### 2.2 Market Series Slice
- **Endpoint:** `GET /api/market/series`
- **Query Parameters:** `symbol` ("ASPI" | "S&P SL20"), `from`, `to`
- **Response `200 OK`:** Array of `{ "date": "YYYY-MM-DD", "close": 1234.56, "return_pct": 0.12, "volume": 1000000 }`

---

## 3. Verified Political Event Catalog

### 3.1 List Events
- **Endpoint:** `GET /api/events`
- **Query Parameters:** `family`, `subtype`, `date_from`, `date_to`, `keyword`, `limit`, `offset`
- **Response `200 OK`:**
```json
{
  "total": 104,
  "limit": 50,
  "offset": 0,
  "events": [
    {
      "event_id": "ARR-2022-003",
      "title": "Arrest of Former Central Bank Governor",
      "event_family": "Political Arrest",
      "event_subtype": "Financial Crime",
      "aligned_date": "2022-05-18",
      "car_1d": 1.25,
      "car_5d": 3.42,
      "car_20d": 4.10,
      "impact_direction": "Positive",
      "cluster_id": "CLU-2022-05"
    }
  ]
}
```

### 3.2 Event Summary
- **Endpoint:** `GET /api/events/summary`
- **Response `200 OK`:** Aggregated counts, mean CARs by family, and complete sub-categories list.

### 3.3 Event Detail & Trajectory
- **Endpoint:** `GET /api/events/{event_id}`
- **Description:** Returns complete event metadata, abnormal return metrics, news sources, and trajectory price path from $t-10$ to $t+20$.
- **Response `200 OK`:**
```json
{
  "event_id": "POL-2023-012",
  "title": "IMF Executive Board Approves Extended Fund Facility",
  "event_family": "Government Policy",
  "event_subtype": "IMF & External Debt Restructuring",
  "aligned_date": "2023-03-21",
  "aspi_close_event": 9742.10,
  "car_0_1": 0.021,
  "car_0_5": 0.068,
  "car_0_20": 0.124,
  "turnover_shock_ratio": 2.45,
  "impact_direction": "Positive",
  "summary": "Approval of $3bn EFF arrangement...",
  "sources": [{ "name": "Daily FT", "url": "https://ft.lk/..." }],
  "price_path": [
    { "relative_day": -5, "date": "2023-03-14", "aspi_close": 9410.2, "pct_change_from_event": -3.4 },
    { "relative_day": 0, "date": "2023-03-21", "aspi_close": 9742.1, "pct_change_from_event": 0.0 },
    { "relative_day": 5, "date": "2023-03-28", "aspi_close": 10405.6, "pct_change_from_event": 6.8 }
  ]
}
```

---

## 4. Machine Learning Prediction Endpoints

### 4.1 Predict Government Policy Impact
- **Endpoint:** `POST /api/predict/policy`
- **Request Body:**
```json
{
  "policy_type": "Fiscal & Tax Policy",
  "policy_headline": "Cabinet Approves VAT Rate Increase from 15% to 18%",
  "announcement_date": "2024-01-01",
  "affected_sectors": ["Retail", "Consumer Services"],
  "target_symbol": "ASPI",
  "forecast_horizon": 5,
  "historical_cutoff": "2023-12-31"
}
```
- **Response `200 OK`:**
```json
{
  "event_family": "Government Policy",
  "event_subtype": "Fiscal & Tax Policy",
  "target_symbol": "ASPI",
  "prediction_date": "2024-01-01",
  "predicted_direction": "Negative",
  "probability_up": 0.38,
  "probability_down": 0.62,
  "expected_return_pct": -1.45,
  "interval_lower_pct": -4.20,
  "interval_upper_pct": 1.30,
  "confidence_level": "Medium",
  "horizons_breakdown": {
    "1d": { "expected_car_pct": -0.45, "lower_bound_pct": -1.8, "upper_bound_pct": 0.9 },
    "5d": { "expected_car_pct": -1.45, "lower_bound_pct": -4.2, "upper_bound_pct": 1.3 },
    "20d": { "expected_car_pct": -2.80, "lower_bound_pct": -7.5, "upper_bound_pct": 1.9 }
  },
  "similar_events": [
    {
      "event_id": "POL-2022-019",
      "title": "VAT Standard Rate Raised to 15%",
      "aligned_date": "2022-09-01",
      "similarity_score": 0.88,
      "car_5d": -0.021,
      "impact_direction": "Negative"
    }
  ],
  "fan_chart": {
    "base_date": "2024-01-01",
    "base_price": 10650.4,
    "forecast_path": [
      {
        "trading_day": 1,
        "date": "2024-01-02",
        "baseline_no_event": 10650.4,
        "event_predicted_central": 10602.5,
        "lower_80": 10480.0,
        "upper_80": 10725.0,
        "lower_95": 10390.0,
        "upper_95": 10815.0
      }
    ]
  }
}
```

### 4.2 Predict Political Arrest Impact
- **Endpoint:** `POST /api/predict/arrest`
- **Request Body:**
```json
{
  "person_name": "Former Cabinet Minister",
  "event_description": "Remanded over alleged misappropriation of state funds in procurement tender",
  "event_subtype": "Misappropriation of Public Funds",
  "government_or_opposition": "Opposition",
  "announcement_date": "2024-05-15",
  "forecast_horizon": 5
}
```
- **Response `200 OK`:** Full `PredictionResult` structure with directional probabilities, analogue precedents, and Fan Chart.

---

## 5. Walk-Forward Backtesting Lab

### 5.1 Run Historical Replay Backtest
- **Endpoint:** `POST /api/backtest`
- **Description:** Replays any past event with a strict historical cutoff date. Models are trained only on data preceding the cutoff, and predictions are audited against ground-truth prices.
- **Request Body:**
```json
{
  "cutoff_date": "2022-04-07",
  "event_family": "Government Policy",
  "target_symbol": "ASPI",
  "horizon_days": 5
}
```
- **Response `200 OK`:**
```json
{
  "run_id": "bt-20220407-1234",
  "cutoff_price": 7824.5,
  "evaluation": {
    "actual_end_price": 7495.8,
    "actual_return_pct": -4.20,
    "predicted_return_pct": -3.85,
    "direction_correct": true,
    "return_error_pct": 0.35,
    "interval_coverage_pct": 100.0,
    "observed_sessions": 5
  },
  "data_isolation_audit": {
    "max_training_date_used": "2022-04-06",
    "strictly_no_future_prices": true,
    "future_events_excluded": 42
  }
}
```

---

## 6. News Center & Claim Verification

### 6.1 Get Latest News
- **Endpoint:** `GET /api/news/latest?limit=30&family=Government+Policy`
- **Response `200 OK`:** Array of indexed news articles categorized by event type.

### 6.2 Trigger RSS & News Ingestion
- **Endpoint:** `POST /api/news/poll`
- **Response `200 OK`:** `{ "status": "success", "fetched_count": 14, "indexed_count": 11 }`

### 6.3 Verify News Claim & Paired Scenarios
- **Endpoint:** `POST /api/news/verify`
- **Request Body:**
```json
{
  "headline_or_text": "Government considering reduction in corporate income tax for manufacturing exporters"
}
```
- **Response `200 OK`:**
```json
{
  "verdict": "Partially corroborated",
  "heuristic_evidence_score": 68.5,
  "claim_summary": "Corporate income tax reduction proposed for manufacturing exporters",
  "detected_event_family": "Government Policy",
  "detected_event_subtype": "Fiscal & Tax Policy",
  "entities_detected": ["Cabinet", "Ministry of Finance"],
  "matched_evidence": [
    {
      "source_name": "Daily FT",
      "source_url": "https://www.ft.lk/business/...",
      "source_tier": 2,
      "headline": "Finance Ministry reviews corporate tax slabs for export industry",
      "published_at": "2024-03-12",
      "similarity_score": 0.74
    }
  ],
  "scenarios": {
    "scenario_a_true": {
      "label": "Scenario A: Event Confirmed / Implemented",
      "expected_return_pct": 1.25,
      "predicted_direction": "Positive"
    },
    "scenario_b_false": {
      "label": "Scenario B: Claim False / No Policy Change",
      "expected_return_pct": 0.05,
      "predicted_direction": "Neutral",
      "scientific_notice": "Reflects macro continuation baseline without event shock."
    }
  }
}
```

---

## 7. Live CSE Market Data

### 7.1 Market Status
- **Endpoint:** `GET /api/live/status`
- **Response `200 OK`:**
```json
{
  "market_status": "Market Closed",
  "is_open": false,
  "timestamp": "2026-10-19T21:40:00+05:30",
  "provider": "Colombo Stock Exchange Direct API",
  "is_demo": false,
  "is_stale": false
}
```

### 7.2 Live Indices
- **Endpoint:** `GET /api/live/indices`
- **Response `200 OK`:** Real ASPI and S&P SL20 index values, net point changes, and percentage changes.

### 7.3 Top Gainers / Losers
- **Endpoints:** `GET /api/live/gainers`, `GET /api/live/losers`
- **Response `200 OK`:** Ranked arrays of listed equities with symbol, price, change, and trade volume.
