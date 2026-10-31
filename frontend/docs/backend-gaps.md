# Colombo Stock Exchange (CSE) Research Platform — Backend Gaps Register

**Document Version:** 3.0.0 (Stage F3 Backend Implementation Resolution)  
**Standard Compliance:** Rule FR9 (Gaps are reported, tested, and verified against Zod schemas)  
**Total Registered Gaps:** 12 Gaps (GAP-001 through GAP-012)  
**Resolved Gaps:** 12 / 12 (100% ONLINE & VALIDATED)  
**Verification Date:** 2026-10-14  

---

## 1. Overview & Policy

The backend has implemented all 12 registered gap items using real data outputs from Stages 0 to 13 of the quantitative research pipeline (`cse_clean.csv`, `events_event_level.csv`, `events_stage_level.csv`, `stage8_leaderboard.csv`, `news_ingested.csv`, `feed_status.csv`).
Every endpoint has been validated live through the frontend's contract validation catalog at `/_contract` with 100% pass rate (27/27 endpoints ONLINE + VALID).

---

## 2. Complete Backend Gap Register & Resolution Status

### GAP-001: Unified System Health & Pipeline Status Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** Critical
- **Endpoints:**
  - `GET /api/v1/system/health` (also mounted at `/system/health`)
  - `GET /api/v1/system/status` (also mounted at `/system/status`)
- **Schema:** `systemStatusSchema`, `systemHealthSchema`
- **Contract Verification:** 200 OK | VALID (16 ms)
- **Actual Response (`GET /api/v1/system/status`):**
  ```json
  {
    "status": "ready",
    "pipeline_version": "1.0.0",
    "version": "1.0.0",
    "active_stages": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
    "as_of_date": "2025-12-31",
    "asOfDate": "2025-12-31",
    "is_stale": false,
    "isStale": false,
    "champion_model": "CatBoostRegressor (Horizon h=5)",
    "data_points": 7635,
    "last_pipeline_run": "2026-10-14T02:15:00+05:30",
    "latencyMs": 8,
    "uptime": 7200
  }
  ```

---

### GAP-002: Dynamic Meta, Taxonomy, Glossary & Disclaimers Gateway
- **Status:** RESOLVED (2026-10-14)
- **Priority:** Critical (Required for FR1 No Hardcoding & FR5 Honest UI)
- **Endpoint:** `GET /api/v1/meta` (also mounted at `/meta`)
- **Schema:** `metaResponseSchema`
- **Contract Verification:** 200 OK | VALID (17 ms)
- **Actual Response:**
  ```json
  {
    "version": "1.0.0",
    "as_of_date": "2025-12-31",
    "project_info": {
      "title": "Quantitative Evaluation of Sri Lankan Political Events & News on the CSE ASPI",
      "institution": "Sri Lanka Institute of Information Technology (SLIIT)",
      "department": "Faculty of Computing",
      "academic_year": "2026",
      "lead_author": "Research Batch 2026",
      "repository_url": "https://github.com/cse-political-impact/research"
    },
    "refresh_intervals": {
      "market_seconds": 30,
      "events_seconds": 3600,
      "models_seconds": 86400,
      "news_seconds": 300,
      "system_seconds": 60
    },
    "metric_glossary": [
      {
        "metric_id": "caar",
        "name": "Cumulative Average Abnormal Return (CAAR)",
        "definition": "Accumulated abnormal returns over an event window relative to expected return benchmark.",
        "formula": "CAAR(t1, t2) = sum_{t=t1}^{t2} (1/N sum_i AR_{i,t})",
        "benchmark": "Evaluated against 10,000-draw non-event placebo permutation distribution.",
        "unit": "%"
      }
    ],
    "election_stages": [
      { "id": "stage_1", "stage_number": 1, "name": "Pre-Announcement", "description": "Speculation and political maneuvering prior to official election proclamation." },
      { "id": "stage_2", "stage_number": 2, "name": "Nomination", "description": "Candidate nominations officially submitted to the Election Commission." },
      { "id": "stage_3", "stage_number": 3, "name": "Campaign Period", "description": "Intensive electioneering rallies, manifestos, and public opinion shifts." },
      { "id": "stage_4", "stage_number": 4, "name": "Polling Day", "description": "Nationwide balloting across all 22 electoral districts (t=0)." },
      { "id": "stage_5", "stage_number": 5, "name": "Counting & Results", "description": "Official vote tallying, preference counting, and Election Commissioner declaration." },
      { "id": "stage_6", "stage_number": 6, "name": "Post-Election Settlement", "description": "Cabinet swearing-in, parliamentary speaker election, and policy realignment." }
    ],
    "event_types": [
      { "id": "presidential", "name": "Presidential", "description": "National presidential elections under the 1978 Constitution of Sri Lanka." },
      { "id": "parliamentary", "name": "Parliamentary", "description": "General parliamentary elections for the 225-member legislature." }
    ],
    "sectors": [
      { "id": "banks", "name": "Banking & Financial Services", "code": "BNK" },
      { "id": "capital_goods", "name": "Capital Goods & Conglomerates", "code": "CAP" }
    ],
    "disclaimers": {
      "causation": "Historical statistical association evaluated over 30+ years does not imply direct causation.",
      "financial": "Academic research dashboard developed for econometrics research; strictly not investment advice.",
      "data_embargo": "Strict out-of-sample temporal embargoes prevent future lookahead leakage across all models."
    }
  }
  ```

---

### GAP-003: Market Summary & Historical Series REST Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** High
- **Endpoints:**
  - `GET /api/v1/market/summary` (also mounted at `/market/summary`)
  - `GET /api/v1/market/series` (also mounted at `/market/series`)
- **Schema:** `marketSummarySchema`, `marketSeriesResponseSchema`
- **Contract Verification:** 200 OK | VALID (summary: 8 ms, series: 37 ms)
- **Actual Response (`GET /api/v1/market/summary`):**
  ```json
  {
    "aspi_level": 22624.31,
    "daily_return": 0.7917,
    "five_day_return": 3.18,
    "ytd_return": 42.94,
    "sp_sl20_level": 6157.38,
    "sp_sl20_daily_return": 0.7917,
    "equity_turnover_lkr": 9309760000.0,
    "shares_traded": 245620000,
    "realized_volatility_annualized": 15.7,
    "as_of_date": "2025-12-31",
    "is_stale": false,
    "asOfDate": "2025-12-31",
    "isStale": false,
    "metrics": {
      "aspi": { "value": 22624.31, "change": 178.42, "changePct": 0.7917 },
      "spSl20": { "value": 6157.38, "change": 46.03, "changePct": 0.7917 },
      "equityTurnover": { "value": 9309760000.0, "change": 2452750000.0, "changePct": 35.77 },
      "sharesTraded": { "value": 245620000, "change": 42886000, "changePct": 21.15 }
    }
  }
  ```
- **Actual Response (`GET /api/v1/market/series?range=1M`):**
  ```json
  {
    "series": [
      {
        "date": "2025-12-31",
        "value": 22624.31,
        "aspi": 22624.31,
        "sp_sl20": 6157.38,
        "return_pct": 0.7917,
        "return": 0.007917,
        "turnover_lkr": 9309760000.0,
        "turnover": 9309760000.0,
        "volume": 245620000,
        "realized_vol_20d": 15.7,
        "volatility_20d": 15.7
      }
    ],
    "sample_size": 22,
    "count": 22,
    "start_date": "2025-11-28",
    "end_date": "2025-12-31"
  }
  ```

---

### GAP-004: Data Audit, Stationarity & Integrity Verification Endpoint
- **Status:** RESOLVED (2026-10-14)
- **Priority:** High
- **Endpoint:** `GET /api/v1/data/audit` (also mounted at `/data/audit`)
- **Schema:** `dataAuditSchema`
- **Contract Verification:** 200 OK | VALID (14 ms)
- **Actual Response:**
  ```json
  {
    "total_records": 7635,
    "date_range": { "start": "1994-01-03", "end": "2025-12-31" },
    "missingness_pct": 0.0,
    "jumps_detected": 6,
    "trading_days_per_year": [{ "year": 1994, "trading_days": 234, "expected": 240 }],
    "stationarity_adf_test": {
      "test_name": "Augmented Dickey-Fuller (ADF)",
      "test_statistic": -15.3734,
      "p_value": 0.0001,
      "is_stationary": true,
      "critical_values": { "1%": -3.4312, "5%": -2.8619, "10%": -2.567 }
    },
    "stationarity_kpss_test": {
      "test_name": "KPSS Test",
      "test_statistic": 0.235,
      "p_value": 0.1,
      "is_stationary": true,
      "critical_values": { "1%": 0.739, "5%": 0.463, "10%": 0.347 }
    },
    "large_moves": [
      {
        "date": "2001-12-07",
        "return_pct": 20.07,
        "flag": "VERIFIED REAL",
        "note": "2001 Parliamentary Election victory by UNF; surge on peace process expectations."
      }
    ],
    "dictionary": [
      {
        "column": "aspi",
        "type": "Float64",
        "description": "All Share Price Index closing level (Base year 1985 = 100). Reconstructed level.",
        "non_null_count": 7635
      }
    ]
  }
  ```

---

### GAP-005: Political Events Catalog & Stage Timeline Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** High
- **Endpoints:**
  - `GET /api/v1/events` (also mounted at `/events`)
  - `GET /api/v1/events/{id}` (also mounted at `/events/{id}`)
- **Schema:** `eventsListResponseSchema`, `eventDetailSchema`
- **Contract Verification:** 200 OK | VALID (list: 42 ms, detail: 15 ms)
- **Actual Response (`GET /api/v1/events`):**
  ```json
  {
    "events": [
      {
        "id": "ELEC_23",
        "date": "2024-09-23",
        "event_date": "2024-09-23",
        "name": "2024 Sri Lankan Presidential Election",
        "category": "Presidential",
        "current_stage": "Post-Election Settlement",
        "turnout_pct": 76.5,
        "margin_pct": 5.8,
        "winner_party": "Anura Kumara Dissanayake (NPP)",
        "description": "First presidential election since the 2022 economic collapse and mass protests.",
        "aspi_return_event_day": 0.0125
      }
    ],
    "total": 24,
    "count": 24
  }
  ```

---

### GAP-006: Event-Study CAAR Trajectory & Subgroup Results Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** High
- **Endpoints:**
  - `GET /api/v1/event-study/caar` (also mounted at `/event-study/caar`)
  - `GET /api/v1/event-study/subgroups` (also mounted at `/event-study/subgroups`)
- **Schema:** `eventStudyCaarResponseSchema`, `eventStudySubgroupsResponseSchema`
- **Contract Verification:** 200 OK | VALID (caar: 23 ms, subgroups: 13 ms)

---

### GAP-007: Walk-Forward Protocol & Feature Dictionary Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** Medium
- **Endpoints:**
  - `GET /api/v1/protocol` (also mounted at `/protocol`)
  - `GET /api/v1/features/dictionary` (also mounted at `/features/dictionary`)
- **Schema:** `protocolResponseSchema`, `featureDictionaryResponseSchema`
- **Contract Verification:** 200 OK | VALID (protocol: 16 ms, dictionary: 14 ms)

---

### GAP-008: Model Leaderboard, Forecasts, DM Tests & Ablation Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** High
- **Endpoints:**
  - `GET /api/v1/models/leaderboard`
  - `GET /api/v1/models/predictions`
  - `GET /api/v1/models/dm-tests`
  - `GET /api/v1/models/ablation`
  - `GET /api/v1/models/artifacts`
- **Schema:** `leaderboardResponseSchema`, `modelPredictionsResponseSchema`, `dmTestMatrixResponseSchema`, `ablationResponseSchema`, `modelArtifactsResponseSchema`
- **Contract Verification:** 200 OK | VALID (all between 8 ms and 17 ms)

---

### GAP-009: Live News Ingestion, Feed Health & Pipeline Runs Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** Medium
- **Endpoints:**
  - `GET /api/v1/news/items`
  - `GET /api/v1/news/feeds`
  - `GET /api/v1/news/pipeline-runs`
- **Schema:** `newsItemsResponseSchema`, `newsFeedsResponseSchema`, `pipelineRunsResponseSchema`
- **Contract Verification:** 200 OK | VALID (14 ms to 16 ms)

---

### GAP-010: Counterfactual Scenario Predictor & Backtests Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** Medium
- **Endpoints:**
  - `POST /api/v1/scenarios/predict`
  - `GET /api/v1/scenarios/backtests`
- **Schema:** `scenarioPredictResponseSchema`, `scenarioBacktestsResponseSchema`
- **Contract Verification:** 200 OK | VALID (predict: 15 ms, backtests: 14 ms)

---

### GAP-011: Research Figures Index, Audit Report & Data Exports Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** Low
- **Endpoints:**
  - `GET /api/v1/research/index`
  - `GET /api/v1/research/audit-report`
  - `GET /api/v1/research/exports`
- **Schema:** `researchIndexResponseSchema`, `researchAuditReportResponseSchema`, `researchExportsResponseSchema`
- **Contract Verification:** 200 OK | VALID (14 ms to 18 ms)

---

### GAP-012: User Favorites & System Usability Scale (SUS) Survey Endpoints
- **Status:** RESOLVED (2026-10-14)
- **Priority:** Low
- **Endpoints:**
  - `GET /api/v1/user/favorites`
  - `GET /api/v1/survey/sus`
- **Schema:** `favoritesResponseSchema`, `susSurveyResponseSchema`
- **Contract Verification:** 200 OK | VALID (10 ms to 15 ms)

---

### GAP-013: Modelled Trajectory for Event Study Expected-Return Benchmark
- **Status:** DOCUMENTED BY DESIGN / BACKEND GAP (Stage F5)
- **Priority:** Low / Informational
- **Context:** In accordance with the Stage F5 specification: *"ACTUAL vs MODEL TRAJECTORY: if the API provides a modelled trajectory for the selected type and stage, offer the Both / Actual only / Predicted only toggle from the prototype and label the predicted line as a model estimate with its interval; otherwise hide it and log a backend gap."*
- **Current Backend Behavior:** `GET /event-study/caar` produces empirical historical Cumulative Abnormal Return ($\text{CAAR}$) paths computed using Campbell, Lo & MacKinlay (1997) event study methodology (Constant-Mean Return and S&P SL 20 Market Model with Brown-Warner standard errors and 10,000 non-event permutation draws). The backend does not generate a multi-step forward predictive path (`modelled_trajectory`) inside this retrospective econometric event study endpoint.
- **Frontend Handling:** In strict compliance with Rule FR5 and the prompt instructions, the Both / Actual / Predicted toggle is conditionally rendered only when `caarData.modelled_trajectory` is provided by the API. When absent, the toggle is hidden, and the UI displays the honest institutional label: *"Actual Trajectory: Grounded in Historical ASPI | Econometric Model: Constant-Mean Return"*.
