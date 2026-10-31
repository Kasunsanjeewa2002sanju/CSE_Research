# Phase 0 Research Report: Project Inspection and Development Foundation Setup

**Project Title:** Predicting Stock Market Movements Based on Government Policy Events Using Machine Learning  
**Platform Name:** CSE Policy Impact Predictor  
**Module:** Government Policy Stock Market Prediction Module  
**Academic Context:** University Research Thesis in Financial Econometrics & Machine Learning  
**Date:** October 2026  
**Status:** Completed & Ready for User Review  

---

## A. Phase Objective

The primary objective of **Phase 0 — Project Inspection and Initial Setup** was to establish a rock-solid, production-grade development foundation for the university research project and conduct a deep-level empirical audit of all existing raw datasets. This phase required:
1. Inspecting all available Colombo Stock Exchange (CSE) historical datasets and government policy event archives.
2. Confirming data integrity without modifying or mutating any original raw files.
3. Establishing the backend architecture using Python 3.11, FastAPI, and Pydantic schemas.
4. Setting up the frontend architecture using React.js, Vite, and Tailwind CSS styled for professional financial analytics.
5. Implementing automated health checks, dataset discovery, and metadata inventory endpoints.
6. Authoring the initial Google Colab notebook (`00_environment_setup.ipynb`) for reproducible cloud-based machine learning workflows.
7. Validating end-to-end frontend-backend connectivity and providing a manual testing protocol.

---

## B. Work Completed

### 1. Backend Architecture
- **Environment Initialization:** Configured a isolated Python 3.11 virtual environment (`.venv`) equipped with high-performance wheels for `pandas`, `numpy`, `scikit-learn`, `fastapi`, `uvicorn`, `openpyxl`, `xlrd`, and `pydantic`.
- **FastAPI Core (`backend/app/main.py`):** Configured FastAPI with Cross-Origin Resource Sharing (CORS) allowing Vite frontend interactions (`http://localhost:5173`), request execution-time telemetry headers (`X-Process-Time`), and structured error interceptors.
- **Data Inventory Service (`backend/app/services/inventory_service.py`):** Developed a non-destructive data discovery engine that scans the raw data directories, extracts market dates, identifies indices, counts sessions, and validates the 70 government policy records. Caching ensures sub-millisecond query responses.
- **Pydantic Schemas (`backend/app/schemas/inventory.py`):** Formalized strict response schemas for health verification, market index metadata, sector distributions, and policy event catalogs.
- **API Routers (`backend/app/api/`):**
  - `GET /api/health`: System health, runtime environment details, and dataset verification flag.
  - `GET /api/inventory`: Full dataset catalog including ASPI, S&P SL20, sector counts, and policy attributes.
  - `GET /api/inventory/policies/summary`: In-depth breakdown of government policy events, dates, and classifications.
  - `GET /api/inventory/market/summary`: Summary of Colombo Stock Exchange trading sessions and historical timelines.
- **Automated Test Suite (`backend/tests/test_health_and_inventory.py`):** Authored asynchronous tests using `pytest` and `httpx`, confirming 100% test pass rates across all Phase 0 endpoints.

### 2. Frontend Architecture
- **Vite & React Setup (`frontend/`):** Initialized a modern React 18 single-page application using Vite 6, Tailwind CSS 3.4, React Router 7, Axios, Lucide React icons, and Recharts.
- **UI Design System:** Engineered a bespoke dark financial analytics theme inspired by Bloomberg Terminal and TradingView, using deep slate backgrounds (`#090d16`, `#0f172a`), emerald accents for positive market telemetry, and monospace typography for numerical precision.
- **Shell & Navigation (`frontend/src/components/Sidebar.jsx`, `Header.jsx`):**
  - Integrated the complete 8-page navigation roadmap:
    1. *Dashboard* (Active)
    2. *Stock Market Timeline* (Phase 2 Preview)
    3. *Government Policy Events* (Phase 1 Preview)
    4. *Historical Policy Impact* (Phase 3 Preview)
    5. *AI Stock Prediction* (Phase 6 Preview)
    6. *Actual vs Predicted* (Phase 5 Preview)
    7. *Model Performance* (Phase 4 Preview)
    8. *Research Reports* (Phase 0–7 Archive)
  - Added live backend connectivity indicators, auto-refresh triggers, and research environment metadata.
- **Market Data Status Dashboard (`frontend/src/pages/Dashboard.jsx`):** Built dynamic status cards displaying live metrics directly from the backend API: ASPI latest closing value, S&P SL20 status, 2020–2025 focus timeline trading days, verified policy count, and a sample preview table of raw policy events.
- **Phase Route Placeholders (`frontend/src/pages/PhasePlaceholder.jsx`):** Crafted structured informational views for all upcoming phases detailing their scheduled components and research milestones.

### 3. Google Colab Environment Notebook
- Created `notebooks/00_environment_setup.ipynb` with complete executable cells for Google Colab and local Jupyter environments.
- Includes Google Drive mount support, dependency auto-installation, raw data loading, schema inspection, ASPI preview plotting, and export of `dataset_inventory_colab.json`.

---

## C. Implementation Details

### API Endpoints Implemented

| Endpoint | Method | Response Schema | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | `Dict[str, str]` | Platform welcome and documentation index |
| `/api/health` | `GET` | `HealthResponse` | Verifies server uptime, Python version, and dataset readiness |
| `/api/inventory` | `GET` | `DatasetInventory` | Consolidated metadata across stock and policy datasets |
| `/api/inventory/policies/summary` | `GET` | `PolicySummary` | Policy categories, date ranges, and sample records |
| `/api/inventory/market/summary` | `GET` | `MarketSummary` | Stock market trading sessions, indices, and file coverage |

### Key Frontend Components

| Component | Path | Functionality |
| :--- | :--- | :--- |
| `App.jsx` | `frontend/src/App.jsx` | Core router, periodic background health polling, API state provider |
| `Sidebar.jsx` | `frontend/src/components/Sidebar.jsx` | 8-item navigation, real-time backend connection status badge |
| `Header.jsx` | `frontend/src/components/Header.jsx` | Top telemetry bar, research badges, manual re-fetch trigger |
| `MarketStatusCard.jsx` | `frontend/src/components/MarketStatusCard.jsx` | Key financial indicators with monospace values and trend highlights |
| `Dashboard.jsx` | `frontend/src/pages/Dashboard.jsx` | Complete Phase 0 market dashboard with dataset inventory & policy table |
| `PhasePlaceholder.jsx` | `frontend/src/pages/PhasePlaceholder.jsx` | Roadmap preview panels for subsequent development phases |

---

## D. Dataset and Empirical Audit

### 1. Government Policy Dataset (`Government_Policies.csv`)
- **Location:** `Dataset-Policy/Government_Policies.csv`
- **Total Records:** 70 verified policy events.
- **Dimensionality:** 27 columns spanning metadata, implementation status, economic channels, and trading day markers.
- **Historical Scope:** February 14, 2000 to February 17, 2025.
- **Policy Classification Distribution:**
  - Fiscal Policy: 60 events (85.7%)
  - Emergency Economic Policy: 4 events (5.7%)
  - Tax Policy: 3 events (4.3%)
  - Foreign Exchange Policy: 2 events (2.9%)
  - Price Regulation: 1 event (1.4%)
- **Implementation Status:** 69 Implemented (98.6%), 1 Approved (1.4%).
- **Trading Day Alignment Flag:** Contains `CSE_Trading_Day` and `Next_CSE_Trading_Date` fields, which will be rigorously verified against the market calendar in Phase 1.

### 2. Colombo Stock Exchange (CSE) Stock Market Datasets
The project repository contains an extensive, pristine collection of Colombo Stock Exchange records:
- **Primary Market Indices File:** `Dataset-Stock/07Market Indices - Daily.xls`
  - **Total Recorded Trading Days:** 9,773 trading sessions.
  - **Date Range:** January 2, 1985 to December 31, 2025 (over 41 years of continuous daily data).
  - **Primary Index:** All Share Price Index (ASPI), recorded from 96.09 (1985) to 22,624.31 (December 31, 2025).
  - **Secondary Index:** S&P Sri Lanka 20 (S&P SL20), recorded over 3,210 sessions up to 6,157.38 (December 31, 2025).
  - **Historical Benchmark:** Milanka Price Index (MPI), 7,835 sessions (precursor to S&P SL20).
  - **Sector Breakdown:** 21 GICS Sector Indices (Banks & Finance, Food & Beverage, Diversified, Healthcare, Manufacturing, Telecommunications, etc.).
- **Primary Research Focus Period (2020–2025):**
  - Exactly **1,400 trading days** recorded between January 1, 2020 and December 31, 2025.
  - Fully encompasses the critical Sri Lankan macroeconomic and political restructuring periods (2020–2025).
- **Market Statistics File:** `Dataset-Stock/11Market Statistics-Daily.xls`
  - 7,640 trading days (1994 to 2025) containing Equity Turnover (LKR Mn), Domestic/Foreign turnover, and Total Shares Traded (Volume).
- **Company-Level Share Price Archives:**
  - Granular High, Low, Close (OHLC) daily files covering individual quoted companies across 1991–2000, 2001–2010, 2011–2020, and 2021–2025 (`40Daily Shares Price List -2021-2025`).

---

## E. Results and Outputs

### 1. System Inventory Summary Table

| Metric / Dimension | Government Policy Dataset | CSE Market Indices Dataset | Market Statistics Dataset |
| :--- | :--- | :--- | :--- |
| **Source File** | `Government_Policies.csv` | `07Market Indices - Daily.xls` | `11Market Statistics-Daily.xls` |
| **Total Rows** | 70 events | 9,773 trading days | 7,640 trading days |
| **Total Features / Columns** | 27 attributes | 25 columns (Date + 24 Indices) | 11 columns |
| **Historical Range** | 2000-02-14 to 2025-02-17 | 1985-01-02 to 2025-12-31 | 1994-01-03 to 2025-12-31 |
| **2020–2025 Focus Sessions** | 24 policy events | 1,400 trading days | 1,400 trading days |
| **Latest Available Value** | Feb 17, 2025 | ASPI: 22,624.31 (Dec 31, 2025) | Turnover: 9.3B LKR |
| **Raw Data Mutation** | None (0 bytes modified) | None (0 bytes modified) | None (0 bytes modified) |

### 2. Live Application Endpoints Verified
- `http://127.0.0.1:8000/api/health` &rarr; `HTTP 200 OK`
- `http://127.0.0.1:8000/api/inventory` &rarr; `HTTP 200 OK`
- `http://localhost:5173/` &rarr; `HTTP 200 OK`

---

## F. Automated and Manual Testing

### 1. Automated Unit Tests (`pytest`)
Ran test suite `backend/tests/test_health_and_inventory.py`:
- `test_root_endpoint`: PASSED
- `test_health_endpoint`: PASSED
- `test_inventory_full_endpoint`: PASSED
- `test_policy_summary_endpoint`: PASSED
- `test_market_summary_endpoint`: PASSED
**Summary:** 5 passed, 0 failed in 18.93s.

### 2. Production Build Verification
Ran `npm run build` in `frontend/`:
- Bundled 1,661 modules with Vite.
- Generated optimized distribution files (`dist/`) without syntax or TypeScript errors in 9.51s.

---

## G. Issues and Limitations Identified

1. **Excel Parsing Performance:** The raw historical file `07Market Indices - Daily.xls` is a 2.7 MB binary BIFF8 spreadsheet spanning 9,781 rows. In Phase 0, loading and parsing via `xlrd` requires several seconds on cold start. In Phase 1, we will convert this data into high-performance, cleaned Parquet and CSV formats (`cleaned_stock_data.csv`) while preserving the raw original untouched.
2. **Policy Event Frequency:** The policy dataset contains 70 discrete events across 25 years. This sample size is optimal for financial event-study econometrics and classic machine learning algorithms (Logistic Regression, Ridge Regression, Random Forest, Gradient Boosting), confirming the architectural choice to prioritize these over overparameterized deep neural networks.
3. **Point-in-Time Discipline:** 24 of the 70 policy events occurred between 2020 and 2025. All ML feature pipelines must strictly use only information known prior to market close on the announcement date.

---

## H. Academic Research Report Excerpt

> **Empirical Architecture for Policy-Driven Financial Forecasting**  
> *The Colombo Stock Exchange (CSE), established as an emerging frontier equity market, exhibits pronounced sensitivity to macroeconomic interventions, sovereign debt restructurings, tax reform legislations, and central bank monetary pronouncements. While existing computational literature frequently relies on noisy social media sentiment or unverified unstructured news feeds, this study establishes an empirical baseline rooted strictly in verified, dated government policy actions. Spanning 9,773 historical trading sessions from 1985 to 2025 and 70 major sovereign policy interventions, the CSE Policy Impact Predictor system addresses the dual challenges of point-in-time informational alignment and statistical sample efficiency. By decoupling historical price series from forward-looking scenario simulations, the framework preserves strict chronological out-of-sample validity.*

---

## I. Files Generated in Phase 0

1. **Backend:**
   - `backend/app/main.py`
   - `backend/app/schemas/inventory.py`
   - `backend/app/services/inventory_service.py`
   - `backend/app/api/health.py`
   - `backend/app/api/inventory.py`
   - `backend/tests/test_health_and_inventory.py`
2. **Frontend:**
   - `frontend/package.json`
   - `frontend/vite.config.js`
   - `frontend/tailwind.config.js`
   - `frontend/postcss.config.js`
   - `frontend/index.html`
   - `frontend/src/index.css`
   - `frontend/src/main.jsx`
   - `frontend/src/App.jsx`
   - `frontend/src/services/api.js`
   - `frontend/src/components/Sidebar.jsx`
   - `frontend/src/components/Header.jsx`
   - `frontend/src/components/MarketStatusCard.jsx`
   - `frontend/src/pages/Dashboard.jsx`
   - `frontend/src/pages/PhasePlaceholder.jsx`
3. **Google Colab Notebook:**
   - `notebooks/00_environment_setup.ipynb`
4. **Research Documentation:**
   - `reports/phases/phase_00/phase_00_report.md`

---

## J. Next Phase (Phase 1)

In **Phase 1 — Data Cleaning and Government Policy Alignment**, we will:
1. Parse and standardize the full Colombo Stock Exchange daily price series into `cleaned_stock_data.csv`.
2. Clean and validate the 70 government policy records into `cleaned_government_policies.csv`.
3. Align each policy announcement date with the exact active CSE trading session (`aligned_policy_stock_data.csv`), handling weekend announcements, national holidays, and market halts.
4. Build the interactive **Data Explorer** frontend page with searchable policy tables and category filters.
5. Create Google Colab notebook `01_data_cleaning_alignment.ipynb`.

*(Implementation of Phase 1 will begin only after explicit approval).*
