# PolitiTrade LK — Test & Quality Assurance Report

**Execution Environment:** Windows 11 / Python 3.11.15 / Node.js v20+  
**Test Suite:** Pytest 9.1.1, Starlette TestClient, Vite v5.4.21, TypeScript 5.5  
**Execution Date:** October 19, 2026  
**Result:** **100% Passed (17 / 17 Backend Tests Passed, Zero Frontend Build Errors)**

---

## 1. Automated Test Execution Summary

| Suite / Test File | Tests | Passed | Failed | Skipped | Duration |
|---|:---:|:---:|:---:|:---:|:---:|
| `backend/tests/test_api_endpoints.py` | 7 | 7 | 0 | 0 | 4.82s |
| `backend/tests/test_data_and_calendar.py` | 3 | 3 | 0 | 0 | 1.15s |
| `backend/tests/test_event_study.py` | 1 | 1 | 0 | 0 | 2.10s |
| `backend/tests/test_ml_and_backtest.py` | 3 | 3 | 0 | 0 | 5.34s |
| `backend/tests/test_news_and_security.py` | 3 | 3 | 0 | 0 | 3.21s |
| **Total Backend Test Suite** | **17** | **17** | **0** | **0** | **16.62s** |
| **Frontend TypeScript & Vite Build** | **2,222 Modules** | **Passed** | **0** | **0** | **20.87s** |

---

## 2. Backend Test Specifications & Verification

### 2.1 API Endpoint Verification (`test_api_endpoints.py`)
- **`test_api_health`**: Verifies that `GET /api/health` returns status `200 OK`, `status == "healthy"`, and confirms 9,772 historical trading sessions loaded in memory.
- **`test_api_inventory`**: Verifies that `GET /api/inventory` reports all 104 verified political events (70 policies, 34 arrests) and confirms both `policy_model_ready` and `arrest_model_ready`.
- **`test_api_timeline`**: Verifies `GET /api/timeline?from=2020-01-01&to=2025-12-31` delivers continuous daily price points (ASPI, S&P SL20) and overlay markers with calculated CAR values.
- **`test_api_events_list`**: Validates `GET /api/events` filter parameters (`family`, `subtype`, `keyword`) and pagination logic.
- **`test_api_predict_policy`**: Submits a sample tax policy payload to `POST /api/predict/policy` and verifies directional probabilities ($P(\text{Up}) + P(\text{Down}) \approx 1.0$), CAR estimates, and Fan Chart bounds.
- **`test_api_live_status`**: Tests `GET /api/live/status` for correct JSON structure and live provider reporting.
- **`test_api_live_indices`**: Validates `GET /api/live/indices` for ASPI and S&P SL20 price points and percentage changes.

### 2.2 Data Ingestion & Calendar Alignment (`test_data_and_calendar.py`)
- **`test_trading_calendar_basic`**: Asserts calendar alignment logic:
  - Weekend announcements roll to Monday session.
  - Holiday announcements roll to next open session.
  - After-hours announcements (> 14:30 SLT) roll to next trading day.
- **`test_policy_taxonomy_derivation`**: Verifies all 70 government policy records cleanly map into the 10-category derived taxonomy without unassigned categories.
- **`test_arrest_parsing_and_subtypes`**: Tests political actor extraction and verifies all 34 arrest records cleanly categorize into the 7 legal subtypes.

### 2.3 Event Study & Econometrics (`test_event_study.py`)
- **`test_event_study_returns_and_car`**: Validates abnormal return calculations:
  - Verifies estimation window $[-120, -20]$ excludes the $[-20, 0]$ buffer.
  - Confirms daily abnormal return formula $AR_t = R_t - \mu$.
  - Confirms Cumulative Abnormal Returns ($CAR_{0, 1}$, $CAR_{0, 5}$, $CAR_{0, 20}$) match manual rolling sums.

### 2.4 Machine Learning & Walk-Forward Replay (`test_ml_and_backtest.py`)
- **`test_unified_predictor_policy`**: Verifies end-to-end multi-model ensemble synthesis, including confidence scores and limitations disclosures.
- **`test_historical_analogues_cutoff`**: **Strict Non-Lookahead Audit**. Submits a historical cutoff date (e.g. `2022-04-01`) and asserts that:
  - Retrieved analogue precedents strictly have $t_0 \le 2022-04-01$.
  - Zero future events are visible or scored.
- **`test_historical_backtester_execution`**: Replays an event using `POST /api/backtest` and audits actual vs. predicted prices and interval coverage.

### 2.5 Security, Classifier & News Verification (`test_news_and_security.py`)
- **`test_ssrf_protection`**: **Security Test**. Attempts HTTP requests to internal IP addresses (`127.0.0.1`, `10.0.0.1`, `192.168.1.1`, `169.254.169.254`) and asserts `is_safe_url` returns `False` and blocks requests.
- **`test_news_classifier`**: Tests automated classification of headline strings into policy and arrest categories using keyword and semantic matching.
- **`test_news_verifier_unverified_fallback`**: Verifies that when a fake or unverified headline is submitted, the system correctly issues an "Unverified" verdict and returns Scenario B (No-Event continuation baseline) without synthetic hallucinated drops.

---

## 3. Frontend TypeScript & Asset Build Verification

```
> polititrade-lk-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 2222 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                     0.93 kB │ gzip:   0.52 kB
dist/assets/index-iblMIwim.css     25.94 kB │ gzip:   5.37 kB
dist/assets/index-By0d0RkK.js   1,400.59 kB │ gzip: 444.69 kB
✓ built in 20.87s
```

- **TypeScript Compilation:** Zero errors (`tsc` exited code 0).
- **Component Coverage:** All 10 pages and supporting components rendered with full type safety:
  - `Dashboard.tsx`
  - `HistoricalTimeline.tsx`
  - `PolicyPrediction.tsx`
  - `ArrestPrediction.tsx`
  - `Backtesting.tsx`
  - `NewsCenter.tsx`
  - `NewsVerification.tsx`
  - `LiveMarket.tsx`
  - `EventExplorer.tsx`
  - `ModelInformation.tsx`
- **Charts:** ECharts responsive rendering for interactive Timeline, Fan Chart (with confidence bands), and Event Study Trajectory.
