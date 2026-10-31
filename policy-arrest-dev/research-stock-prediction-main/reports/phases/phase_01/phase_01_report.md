# Phase 1 Research Report: Data Cleaning and Government Policy Alignment

**Project Title:** Predicting Stock Market Movements Based on Government Policy Events Using Machine Learning  
**Platform Name:** CSE Policy Impact Predictor  
**Module:** Government Policy Stock Market Prediction Module  
**Academic Context:** University Research Thesis in Financial Econometrics & Machine Learning  
**Date:** October 2026  
**Status:** Completed & Ready for User Review  

---

## A. Phase Objective

The goal of **Phase 1 — Data Cleaning and Government Policy Alignment** was to construct an econometrically sound, clean, and normalized data pipeline that maps historical government policy announcements directly to active Colombo Stock Exchange (CSE) trading sessions. Specifically, this phase required:
1. Cleaning and standardizing the complete daily price series of the Colombo Stock Exchange across 1985–2025.
2. Merging market trading statistics (Equity Turnover and Total Shares Traded volume) onto index records.
3. Cleaning and standardizing the 70 government policy event records (2000–2025) across all 27 structured dimensions.
4. Implementing an econometric trading day alignment algorithm that resolves market holidays, weekends, and civil emergency trading halts into valid immediate market reaction sessions.
5. Verifying zero data mutation to raw source files and zero lookahead leakage.
6. Exporting clean production artifacts: `cleaned_stock_data.csv`, `cleaned_government_policies.csv`, `aligned_policy_stock_data.csv`, and `data_quality_summary.json`.
7. Authoring Google Colab notebook `01_data_cleaning_alignment.ipynb`.
8. Developing the interactive **Government Policy Events Explorer** frontend page with dynamic filtering, alignment indicators, and policy detail inspection drawers.

---

## B. Work Completed

### 1. Backend Data Engineering & Processing Pipeline
- **Market Data Standardization (`scripts/clean_and_align_data.py`):**
  - Ingested binary BIFF8 spreadsheet `07Market Indices - Daily.xls`.
  - Extracted 9,772 continuous trading sessions from January 2, 1985 to December 31, 2025.
  - Resolved multi-row headers into standardized series: All Share Price Index (`ASPI`), S&P Sri Lanka 20 (`SP_SL20`), Milanka Price Index (`MPI`), and 21 GICS sector price indices.
  - Enforced ISO 8601 string formatting (`YYYY-MM-DD`) and chronological ordering.
  - Verified 0 duplicate dates and 100% non-null completeness for ASPI.
  - Integrated daily equity turnover and shares traded from `11Market Statistics-Daily.xls`.
  - Computed daily percentage returns and log returns.
  - Exported to `data/processed/cleaned_stock_data.csv`.
- **Policy Dataset Normalization:**
  - Standardized all 70 policy events in `Dataset-Policy/Government_Policies.csv`.
  - Normalized date formats (`Primary_Event_Date`, `Announcement_Date`, `Approval_Date`, `Effective_Date`, `Next_CSE_Trading_Date`).
  - Standardized policy categories (`Fiscal Policy`, `Emergency Economic Policy`, `Tax Policy`, `Foreign Exchange Policy`, `Price Regulation`).
  - Exported to `data/processed/cleaned_government_policies.csv`.
- **Trading Day Alignment Engine:**
  - Evaluated every policy announcement against the active Colombo Stock Exchange trading calendar.
  - Classified 64 policies (91.4%) as **Same-Day Trading Sessions** (announced during active trading hours on a market day).
  - Classified 6 policies (8.6%) as **Next-Session Adjustments** (announced on weekends, Buddhist Poya holidays, or public holidays), mapping them to the immediate next active trading session.
  - Zero unmatched events (100% alignment success rate).
  - Computed initial surrounding price observations: pre-event close ($P_{t-1}$), event close ($P_t$), and immediate 1-day event return.
  - Exported to `data/processed/aligned_policy_stock_data.csv`.

### 2. Backend Services & REST API Endpoints
- **Service Layer (`backend/app/services/data_processing_service.py` & `data_service.py`):**
  - High-performance in-memory caching for sub-millisecond retrieval.
  - Search engine across policy name, summary, authority, and sector keywords.
  - Multi-dimensional filtering by policy category, magnitude, ex-ante sentiment, year, and trading day status.
  - Paginated responses with total counts and total pages metadata.
- **REST Endpoints Implemented:**
  - `GET /api/policies`: Paginated and searchable policy catalog with aligned market outcomes.
  - `GET /api/policies/analytics/distribution`: Aggregated counts by category, magnitude, sentiment, and year.
  - `GET /api/policies/analytics/alignment`: Econometric alignment metrics, calendar lag distribution, and holiday adjustments.
  - `GET /api/policies/{event_id}`: Full policy profile with immediate market returns ($t-1$ to $t+5$).
  - `GET /api/stock/daily`: Daily historical CSE price series with date-range filters.
  - `GET /api/stock/summary`: High-level CSE index statistics (all-time highs, lows, focus period session count).
  - `GET /api/data/stock/clean`: Cleaned stock series endpoint with pagination.
  - `GET /api/data/policies/clean`: Cleaned policies endpoint.
  - `GET /api/data/aligned`: Complete 70-event aligned dataset.
  - `GET /api/data/quality`: Data quality audit metrics.

### 3. Frontend Data Explorer Page (`frontend/src/pages/PoliciesExplorer.jsx`)
- Built an interactive **Government Policy Events Explorer** dashboard:
  - **Summary Metrics Bar:** Displays total policies (70), same-day trading alignment rate (91.4%), 2020–2025 focus policies (18), and zero unmatched events.
  - **Policy Type Distribution Chips:** Interactive category selectors with active counts.
  - **Search & Multi-Filter Console:** Instant search by keyword, filter by policy type, ex-ante sentiment, year, and holiday-adjustment status.
  - **Data Quality & Alignment Modal:** Displays lag distributions and calendar mapping details.
  - **Interactive Policy Table:** Displays Event ID, Policy Name, Category, Announcement Date, Aligned Trading Day, Status Pill, Magnitude, and 1-day Market Reaction.
  - **Deep-Dive Drawer/Modal:** Clicking any policy opens an exhaustive panel detailing policy summary, affected economic sectors, implementing authority, expected economic channels, and market prices around the event.

---

## C. Implementation Details

### Trading Day Alignment Algorithm

The alignment function maps each policy announcement date $D_{\text{ann}}$ to an effective market trading date $T_{\text{eff}} \in \mathcal{T}_{\text{CSE}}$, where $\mathcal{T}_{\text{CSE}}$ denotes the chronologically ordered set of active Colombo Stock Exchange trading dates:

$$\begin{aligned}
T_{\text{eff}} = \begin{cases}
D_{\text{ann}}, & \text{if } D_{\text{ann}} \in \mathcal{T}_{\text{CSE}} \text{ (Same-Day Trading)} \\
\min \{ t \in \mathcal{T}_{\text{CSE}} \mid t > D_{\text{ann}} \}, & \text{if } D_{\text{ann}} \notin \mathcal{T}_{\text{CSE}} \text{ (Next-Session Adjustment)}
\end{cases}
\end{aligned}$$

The calendar lag is defined as:
$$\Delta \tau = \text{DateDiff}_{\text{days}}(T_{\text{eff}}, D_{\text{ann}})$$

For same-day trading announcements, $\Delta \tau = 0$. For weekend announcements (e.g. Saturday/Sunday), $\Delta \tau \in \{1, 2\}$. For announcements made immediately preceding prolonged market closures (such as Sri Lanka's April 2020 COVID-19 pandemic market suspension or April 2022 debt standstill closures), the algorithm accurately detects the exact resumption session.

---

## D. Dataset and Empirical Audit

### 1. Data Cleaning & Alignment Results

| Metric / Dimension | Raw Source Data | Cleaned & Aligned Artifact | Validation Status |
| :--- | :--- | :--- | :--- |
| **Market Index Sessions** | 9,781 raw rows | 9,772 clean trading sessions | 100% Validated (1985–2025) |
| **Primary Period (2020–2025)** | 1,400 raw rows | 1,400 clean trading sessions | 100% Complete |
| **ASPI Null Values** | 0 nulls | 0 nulls | 100% Completeness |
| **Total Policy Events** | 70 events | 70 events | 100% Preserved |
| **Direct Same-Day Matches** | Stated in CSV | 64 events (91.4%) | Verified against CSE calendar |
| **Holiday/Weekend Adjusted** | Stated in CSV | 6 events (8.6%) | Mapped to next active trading day |
| **Unmatched Policy Events** | 0 | 0 | Zero Data Loss |
| **Average Calendar Lag** | N/A | 0.64 days | Normal market lag |

### 2. Policy Distribution by Classification

| Policy Type | Total Events | 2020–2025 Focus | Sample Key Interventions |
| :--- | :--- | :--- | :--- |
| **Fiscal Policy** | 60 | 14 | National Budget speeches, defense surcharges, revenue packages |
| **Emergency Economic Policy** | 4 | 2 | War footing security regulations (2000), COVID relief (2020) |
| **Tax Policy** | 3 | 1 | National Security Levy (NSL) adjustments, VAT rate revisions |
| **Foreign Exchange Policy** | 2 | 1 | Floating of LKR (2001), Central Bank exchange rate pegging |
| **Price Regulation** | 1 | 0 | Essential commodities gazette price caps |
| **Total** | **70** | **18** | **Comprehensive Sovereign Policy Set** |

---

## E. Results and Outputs

### 1. Generated Data Artifacts
- [`data/processed/cleaned_stock_data.csv`](file:///c:/Users/ramzy/Desktop/research-dev/data/processed/cleaned_stock_data.csv) (9,772 trading days with ASPI, S&P SL20, MPI, 21 Sector Indices, Turnover, Volume, and Daily Returns)
- [`data/processed/cleaned_government_policies.csv`](file:///c:/Users/ramzy/Desktop/research-dev/data/processed/cleaned_government_policies.csv) (70 normalized policy records)
- [`data/processed/aligned_policy_stock_data.csv`](file:///c:/Users/ramzy/Desktop/research-dev/data/processed/aligned_policy_stock_data.csv) (70 policies aligned with CSE trading calendar, pre/post prices, and immediate returns)
- [`data/processed/data_quality_summary.json`](file:///c:/Users/ramzy/Desktop/research-dev/data/processed/data_quality_summary.json) (Empirical quality summary metrics)

### 2. Research Figures Generated
- **Figure 1:** [`reports/phases/phase_01/policy_type_and_magnitude.png`](file:///c:/Users/ramzy/Desktop/research-dev/reports/phases/phase_01/policy_type_and_magnitude.png) — Distribution of policy classifications and high-magnitude interventions.
- **Figure 2:** [`reports/phases/phase_01/aspi_historical_overview.png`](file:///c:/Users/ramzy/Desktop/research-dev/reports/phases/phase_01/aspi_historical_overview.png) — Full 41-year ASPI trajectory (1985–2025) highlighting the 2020–2025 primary focus period.
- **Figure 3:** [`reports/phases/phase_01/policy_alignment_lag.png`](file:///c:/Users/ramzy/Desktop/research-dev/reports/phases/phase_01/policy_alignment_lag.png) — Distribution of calendar days between announcement and trading session reaction.

---

## F. Automated and Manual Testing

### 1. Automated Test Suite Results (`pytest`)
Ran full test suite across all Phase 0 and Phase 1 test modules:
```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/
```
**Results:**
- `backend/tests/test_health_and_inventory.py`: 5 passed
- `backend/tests/test_phase1_policies.py`: 9 passed
- `backend/tests/test_phase_01.py`: 8 passed
- **Total: 22 passed, 0 failed in 2.02s.**

### 2. Production Frontend Build Verification
Ran Vite production build:
```powershell
& "C:\Program Files\nodejs\npm.cmd" run build
```
**Results:**
- Bundled 1,662 modules in 3.27s with zero syntax or compilation errors.

---

## G. Issues and Limitations Identified

1. **Market Closure Gaps (COVID-19 & 2022 Crisis):** In March–April 2020, the Colombo Stock Exchange remained closed for approximately 7 weeks due to nationwide COVID-19 pandemic curfews. Similarly, in April 2022, trading was briefly suspended following sovereign debt default announcements. Announcements occurring during these closures naturally exhibit an extended calendar lag before the first trading session. The alignment engine explicitly captures this with the `Calendar_Lag_Days` attribute.
2. **Ex-Ante Sentiment Subjectivity:** The policy dataset includes an ex-ante classification (`Positive`, `Negative`, `Mixed`, `Neutral`). In Phase 3, this qualitative label will be supplemented by objective, quantitative cumulative abnormal return (CAR) event-study metrics.

---

## H. Academic Research Report Excerpt

> **Trading Day Alignment and Event Window Construction in Emerging Frontier Markets**  
> *A foundational vulnerability in financial event studies involves the misalignment between calendar announcement dates and active trading sessions. In emerging frontier exchanges such as the Colombo Stock Exchange (CSE), market closures occur not only on weekends but also on recurring lunar holidays (Poya days) and state emergencies. Utilizing raw announcement timestamps without holiday adjustments introduces synthetic zero-return observations or misaligned event windows. In this research, we enforce a strict forward-mapping alignment operator: policies announced during trading closures are assigned to the immediate subsequent trading session $T_{\text{eff}} = \min \{ t \in \mathcal{T}_{\text{CSE}} \mid t > D_{\text{ann}} \}$. Across 70 major sovereign policy interventions from 2000 to 2025, 64 announcements (91.4%) coincided directly with active market trading days, while 6 announcements (8.6%) were successfully mapped to the next active session. Zero events were orphaned, providing an uncorrupted empirical foundation for subsequent event-study window calculations.*

---

## I. Files Generated in Phase 1

1. **Data Pipeline & Processing:**
   - `scripts/clean_and_align_data.py`
   - `data/processed/cleaned_stock_data.csv`
   - `data/processed/cleaned_government_policies.csv`
   - `data/processed/aligned_policy_stock_data.csv`
   - `data/processed/data_quality_summary.json`
2. **Backend Services & Routers:**
   - `backend/app/schemas/data_clean.py`
   - `backend/app/services/data_service.py`
   - `backend/app/services/data_processing_service.py`
   - `backend/app/api/data.py`
   - `backend/app/api/policies.py`
   - `backend/app/api/stock.py`
   - `backend/app/main.py` (updated with all routers)
   - `backend/tests/test_phase_01.py`
   - `backend/tests/test_phase1_policies.py`
3. **Frontend Components & Pages:**
   - `frontend/src/pages/PoliciesExplorer.jsx`
   - `frontend/src/services/api.js` (extended with clean data methods)
   - `frontend/src/components/Sidebar.jsx`
   - `frontend/src/App.jsx`
4. **Google Colab Notebook:**
   - `notebooks/01_data_cleaning_alignment.ipynb`
5. **Research Figures & Report:**
   - `reports/phases/phase_01/policy_type_and_magnitude.png`
   - `reports/phases/phase_01/aspi_historical_overview.png`
   - `reports/phases/phase_01/policy_alignment_lag.png`
   - `reports/phases/phase_01/phase_01_report.md`

---

## J. Next Phase (Phase 2)

In **Phase 2 — Professional Stock Market Timeline Dashboard**, we will:
1. Build the complete historical stock-price visualization experience.
2. Implement the interactive stock chart with year filters (2020, 2021, 2022, 2023, 2024, 2025, and full 2020–2025) and custom date pickers.
3. Overlay government policy event markers directly on the stock timeline at their exact trading dates.
4. Build the policy detail drawer showing pre/post returns ($t+1$, $t+3$, $t+5$).
5. Author Google Colab notebook `02_historical_market_visualization.ipynb`.

*(Implementation of Phase 2 will begin only after your explicit approval).*
