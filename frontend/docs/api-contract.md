# Colombo Stock Exchange (CSE) Research Platform — Full API Contract Specification

**Document Version:** 2.0.0 (Stage F2: Data Layer)  
**Standard Compliance:** OpenAPI 3.1.0 / Zod Boundary Validation  
**Rule Reference:** [frontend/RULES.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/RULES.md) (FR1: No Hardcoding, FR4: Contract First, FR5: Honest UI, FR9: Gaps Reported)

---

## 1. Architectural Principles & Envelope Standards

1. **Strict Runtime Boundary Validation:**  
   Every single response received by `src/api/client.ts` is validated through a Zod schema before being accepted by TanStack Query hooks. If any field type, required property, or constraint fails validation, execution halts, an institutional `<ContractError />` boundary is displayed with exact issue paths, and a warning toast is dispatched.
2. **Standardized Response Envelope:**  
   All collection endpoints implement the paginated envelope:
   ```json
   {
     "items": [...],
     "total": 1420,
     "page": 1,
     "page_size": 20,
     "total_pages": 71,
     "has_next": true
   }
   ```
3. **Dynamic Refresh & Cache Intervals:**  
   Per the Stage F2 requirements, cache `staleTime` and background `refetchInterval` values are never hardcoded constants. They are derived directly at runtime from `/api/v1/meta` (`refresh_intervals`).
4. **Normalized Error Envelope:**  
   All non-200 HTTP responses or gateway failures return:
   ```json
   {
     "status": 404,
     "code": "HTTP_404",
     "message": "Resource not found",
     "request_id": "req_1728901234_abc",
     "timestamp": "2026-10-14T11:00:00Z",
     "details": null
   }
   ```

---

## 2. Resource Endpoints Catalog (12 Domains)

### 2.1 Meta & Taxonomy (`/api/v1/meta`)
Provides platform taxonomy, metric definitions for tooltips, disclaimers, and dynamic refresh intervals.
- **Method:** `GET`
- **Path:** `/api/v1/meta`
- **Schema:** `metaResponseSchema`
- **Response Shape:**
  ```json
  {
    "version": "1.0.0",
    "as_of_date": "2026-10-14T00:00:00Z",
    "project_info": {
      "title": "Quantitative Evaluation of Sri Lankan Political Events & News on the CSE ASPI",
      "institution": "Sri Lanka Institute of Information Technology (SLIIT)",
      "department": "Faculty of Computing",
      "academic_year": "2026"
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
        "definition": "Accumulated abnormal returns over an event window relative to market expectation.",
        "formula": "sum_t (1/N * sum_i AR_{i,t})",
        "benchmark": "Evaluated against 10,000-draw non-event placebo bootstrap distribution.",
        "unit": "%"
      },
      {
        "metric_id": "oos_r2",
        "name": "Out-of-Sample R-squared (OOS R²)",
        "definition": "Proportion of return variance explained by forecasts relative to historical mean baseline.",
        "formula": "1 - sum((y - y_hat)^2) / sum((y - y_mean)^2)",
        "benchmark": "> 0.0 indicates statistical forecasting skill over naive historical mean.",
        "unit": "ratio"
      }
    ],
    "election_stages": [
      { "id": "stage_1", "stage_number": 1, "name": "Pre-Announcement", "description": "Speculation prior to proclamation." },
      { "id": "stage_2", "stage_number": 2, "name": "Nomination", "description": "Candidate nominations filed." },
      { "id": "stage_3", "stage_number": 3, "name": "Campaign Period", "description": "Intensive electioneering rallies." },
      { "id": "stage_4", "stage_number": 4, "name": "Polling Day", "description": "Nationwide balloting (t=0)." },
      { "id": "stage_5", "stage_number": 5, "name": "Counting & Results", "description": "Vote tallying and commissioner declaration." },
      { "id": "stage_6", "stage_number": 6, "name": "Post-Election Settlement", "description": "Cabinet swearing-in and policy realignment." }
    ],
    "event_types": [
      { "id": "presidential", "name": "Presidential", "description": "National presidential elections." },
      { "id": "parliamentary", "name": "Parliamentary", "description": "General parliamentary elections." },
      { "id": "provincial", "name": "Provincial", "description": "Provincial council elections." },
      { "id": "crisis", "name": "Crisis", "description": "Sovereign default, emergency declarations, constitutional standoffs." }
    ],
    "news_categories": [
      { "id": "monetary", "name": "Central Bank & Monetary Policy" },
      { "id": "fiscal", "name": "Fiscal & IMF Review" },
      { "id": "political", "name": "Elections & Cabinet" }
    ],
    "sectors": [
      { "id": "banks", "name": "Banking & Finance", "code": "BNK" },
      { "id": "diversified", "name": "Capital Goods & Conglomerates", "code": "CAP" }
    ],
    "disclaimers": {
      "causation": "Historical statistical association does not imply direct causality.",
      "financial": "Academic research dashboard; not investment, trading, or legal advice."
    }
  }
  ```

---

### 2.2 System Health & Status (`/api/v1/system/*`)
- **GET `/api/v1/system/health`:** Checks database and worker liveness.
- **GET `/api/v1/system/status`:** Pipeline execution status, active stages (0–13), staleness flag, data-as-of date, and champion model ID.
- **Schema:** `systemStatusSchema`, `systemHealthSchema`

---

### 2.3 Market Series & Summary (`/api/v1/market/*`)
- **GET `/api/v1/market/summary`:** Latest ASPI index level, daily return, S&P SL 20 level, equity turnover in LKR, shares traded, annualized realized volatility (20d), and staleness indicator.
- **GET `/api/v1/market/series?range={1M|3M|6M|1Y|5Y|All}`:** Daily index levels, log returns, turnover, and rolling volatility points.
- **Schema:** `marketSummarySchema`, `marketSeriesResponseSchema`

---

### 2.4 Data Audit & Integrity (`/api/v1/data/audit`)
Reports empirical audit dimensions over CSE historical market data (1997–2026).
- **GET `/api/v1/data/audit`**
- **Schema:** `dataAuditSchema`
- **Key Metrics:** Total records ($N \ge 7,400$), missingness percentage, abnormal index jumps detected, trading days per year table (expected ~240 vs realized), Augmented Dickey-Fuller (ADF) stationarity test ($p < 0.01$ on log returns), and data dictionary columns.

---

### 2.5 Political Events & Election Stages (`/api/v1/events`)
Catalog of 24 major Sri Lankan political and macroeconomic shocks.
- **GET `/api/v1/events?category={Presidential|Parliamentary|Crisis|All}`:** List of political events with election stage, turnout %, margin %, and event-day ASPI return.
- **GET `/api/v1/events/{id}`:** Detailed event profile including 6 election stages with exact dates, economic context, and outcome margin.
- **Schema:** `eventsListResponseSchema`, `eventDetailSchema`

---

### 2.6 Event-Study Econometric Results (`/api/v1/event-study/*`)
- **GET `/api/v1/event-study/caar?window={[-3,+3]|[-10,+10]|[-20,+20]}`:** Daily Cumulative Average Abnormal Return (CAAR) trajectory across event window days, with 95% bootstrap confidence interval bounds, 10,000-draw non-event placebo permutation $p$-value, and statistical significance flag.
- **GET `/api/v1/event-study/subgroups`:** Segmented CAAR by election category (Presidential vs Parliamentary), outcome party (SLPP vs UNP/SJB vs NPP), and political crisis.
- **Schema:** `eventStudyCaarResponseSchema`, `eventStudySubgroupsResponseSchema`

---

### 2.7 Research Protocol & Feature Dictionary (`/api/v1/protocol`, `/api/v1/features/dictionary`)
- **GET `/api/v1/protocol`:** The 5 evaluation phases (P1 Baseline, P2 Macro Expansion, P3 Political Shocks, P4 Deep Crisis/Default, P5 Contemporary Out-of-Sample), embargo rules, and lookahead leakage verification status.
- **GET `/api/v1/features/dictionary`:** Catalog of engineered features (Technical, Macro, Political, News Sentiment) with strict lag days ($\ge 1\text{ day}$) and stationarity flags.
- **Schema:** `protocolResponseSchema`, `featureDictionaryResponseSchema`

---

### 2.8 Machine Learning Models & Leaderboard (`/api/v1/models/*`)
- **GET `/api/v1/models/leaderboard`:** Evaluated models (CatBoost, LightGBM, Random Forest, Ridge, Historical Mean Baseline) with OOS $R^2$, Directional Accuracy, Balanced Accuracy, RMSE, MAE, and Diebold-Mariano $p$-values against baseline.
- **GET `/api/v1/models/predictions?model_id={id}&horizon={days}`:** Time-series of realized vs predicted returns with residual uncertainty bands.
- **GET `/api/v1/models/dm-tests`:** Full pairwise Diebold-Mariano test matrix across all candidate models.
- **GET `/api/v1/models/ablation`:** Feature set ablations (Technical vs +Macro vs +Political vs +News) and event window ablations.
- **GET `/api/v1/models/artifacts`:** Checkpoint weights, ONNX/Pickle models, and evaluation tables.
- **Schema:** `leaderboardResponseSchema`, `modelPredictionsResponseSchema`, `dmTestMatrixResponseSchema`, `ablationResponseSchema`, `modelArtifactsResponseSchema`

---

### 2.9 Live News & RSS Feeds (`/api/v1/news/*`)
- **GET `/api/v1/news/items?page=1&page_size=20`:** Paginated feed of parsed Sri Lankan political and business news with sentiment tags and source links.
- **GET `/api/v1/news/feeds`:** Health status of the 8 monitored news feeds (Daily Mirror, Ada Derana, EconomyNext, Daily FT, NewsFirst, Colombo Gazette, The Island, Sunday Times).
- **GET `/api/v1/news/pipeline-runs`:** Execution history of the continuous ingestion daemon.
- **Schema:** `newsItemsResponseSchema`, `newsFeedsResponseSchema`, `pipelineRunsResponseSchema`

---

### 2.10 Counterfactual Scenario Predictor (`/api/v1/scenarios/*`)
- **POST `/api/v1/scenarios/predict`:** Simulates market response to a hypothetical electoral or political scenario.
  - Request: `{ event_type: "Presidential", expected_turnout_pct: 75.0, expected_margin_pct: 4.2, lead_party: "NPP", market_regime: "neutral", horizon_days: 5 }`
  - Response: `{ scenario_id, predicted_aspi_impact_pct, confidence_interval_95, confidence_interval_80, historical_analogues, explanation, disclaimer }`
- **GET `/api/v1/scenarios/backtests`:** Historical back-tests evaluating scenario engine predictions against realized election returns.
- **Schema:** `scenarioPredictRequestSchema`, `scenarioPredictResponseSchema`, `scenarioBacktestsResponseSchema`

---

### 2.11 Research Artifacts, Audit & Exports (`/api/v1/research/*`)
- **GET `/api/v1/research/index`:** Comprehensive index of all 36 generated high-resolution charts, figures, and publication tables.
- **GET `/api/v1/research/audit-report`:** 5-dimension skeptical audit results verifying zero lookahead bias, stationarity adherence, and robust inference.
- **GET `/api/v1/research/exports`:** Direct CSV/Parquet export endpoints for replication.
- **Schema:** `researchIndexResponseSchema`, `researchAuditReportResponseSchema`, `researchExportsResponseSchema`

---

### 2.12 User Preferences & Usability Survey (`/api/v1/user/*`, `/api/v1/survey/*`)
- **GET `/api/v1/user/favorites`:** Locally or server-persisted bookmarked research figures and models.
- **GET `/api/v1/survey/sus`:** Standard 10-item System Usability Scale (SUS) survey questions for academic thesis evaluation.
- **Schema:** `favoritesResponseSchema`, `susSurveyResponseSchema`
