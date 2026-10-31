# PolitiTrade LK — AI-Powered Political Event CSE Market Predictor

> **Predicting the Impact of Sri Lankan Government Policy Changes and Political Arrests on the Colombo Stock Exchange (CSE) Using Machine Learning, Quantitative Event Studies, and News Claim Verification.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Apache ECharts](https://img.shields.io/badge/ECharts-5.5-AA344D?logo=apache-echarts&logoColor=white)](https://echarts.apache.org)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen)](docs/TEST_REPORT.md)

---

## 1. Project Overview & Explanation

### What is PolitiTrade LK?
**PolitiTrade LK** is a full-stack quantitative financial research platform and decision-support system. It is specifically designed to analyze, model, and forecast how political developments—namely **government policy changes** and **high-profile political arrests**—impact equity valuations on the **Colombo Stock Exchange (CSE)**.

Sri Lanka's financial markets are historically sensitive to macroeconomic and political volatility, ranging from debt defaults and IMF negotiations to sudden tax reforms, emergency cabinet reshuffles, and high-profile legal interventions. PolitiTrade LK replaces speculation with rigorous statistical modeling:
- **Historical Event Studies:** Quantifying abnormal returns ($AR_t$) and cumulative abnormal returns ($CAR[t_1, t_2]$) relative to expected market trajectories.
- **Strict Anti-Leakage Machine Learning:** Walk-forward expanding-window models that strictly enforce historical date cutoffs ($t \le t_0 - 1$) with zero lookahead bias.
- **Twin-Conditional News Verification:** An intelligent fact-checking engine that parses news articles against verified local sources and outputs twin projections:
  - **Scenario A (Confirmed):** Expected market absorption if the reported event takes place.
  - **Scenario B (Unverified / Debunked):** Macroeconomic continuation baseline assuming no event occurs.
- **Live CSE Market Monitoring:** Real-time CSE price feeds, market status tracking, and turnover dynamics.

---

## 2. Key Platform Features & Modules

The web platform features 10 specialized interactive views accessible through a financial-terminal interface:

1. **Executive Dashboard (`/`):**
   - High-level market health gauges, live ASPI and S&P SL20 tickers, recent political developments, and quick prediction shortcuts.
2. **Historical Interactive Timeline (`/timeline`):**
   - Multi-year continuous multi-index charting (1985–2025) with color-coded event markers (Government Policy = Blue, Political Arrests = Amber).
   - Clickable event markers showing $CAR_{0, 1}$, $CAR_{0, 5}$, and $CAR_{0, 20}$ windows.
3. **Government Policy Predictor (`/predict-policy`):**
   - Evaluates planned or hypothetical policy actions across 10 categories (Monetary Policy, Fiscal/VAT, IMF Bailouts, Tariffs, Debt Restructuring, etc.).
   - Computes directional probabilities ($P(\text{Up})$ vs $P(\text{Down})$), continuous CAR estimates, empirical uncertainty fan charts ($\pm 1.96\sigma$), and top historical precedent matches.
4. **Political Arrest Impact Predictor (`/predict-arrest`):**
   - Forecasts market absorption of high-profile arrests, corruption indictments, remands, and protest detentions.
5. **Historical Backtesting & Replay Lab (`/backtesting`):**
   - Replay any event between 2020 and 2025 with strict temporal isolation. Models retrain dynamically using only data prior to the selected date.
6. **Live CSE Market Dashboard (`/live`):**
   - Direct monitoring of current ASPI / S&P SL20 values, market status (Open/Closed), daily turnover, volume, and top gainers/losers.
7. **News Center (`/news`):**
   - Ingestion hub polling RSS feeds from verified Sri Lankan financial and national news outlets.
8. **News Fact-Checking & Verification (`/verify`):**
   - Input news URLs or raw claims to verify authenticity against trusted publishers with SSRF protection, providing twin conditional market impact forecasts.
9. **Event Explorer Catalog (`/events`):**
   - Comprehensive searchable and filterable repository of all 104 curated historical events with trajectories ($t-10$ to $t+20$).
10. **Model Information & Transparency (`/model-info`):**
    - Walk-forward empirical benchmark comparison, classification accuracy, ROC-AUC, Brier scores, and mathematical formulations.

---

## 3. Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Server:** Uvicorn (configured on port **8001** to avoid Windows reserved socket conflicts)
- **Data & Computation:** Pandas, NumPy, Scikit-learn, SciPy, Statsmodels, PyArrow (Parquet)
- **Database:** SQLite (operational state & news archive) and Parquet (high-speed timeseries storage)
- **Fuzzy Search & NLP:** RapidFuzz, TF-IDF Vectorizer
- **News Scraping & Web:** HTTPX, BeautifulSoup4, Feedparser, Trafilatura
- **Security:** Private IP / SSRF filter, input sanitization
- **Testing:** Pytest (17 automated test suites)

### Frontend
- **Framework:** React 18 with TypeScript 5.6
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS (Dark financial terminal palette `#0B1220`, `#111C2D`, `#38BDF8`)
- **State Management & Caching:** TanStack Query v5 (React Query)
- **Data Visualization:** Apache ECharts (`echarts`, `echarts-for-react`)
- **Routing:** React Router v6
- **Icons:** Lucide React

---

## 4. Repository Structure

```text
research-dev/
├── .env.example               # Template environment configuration file
├── .env                       # Local environment variables (git-ignored)
├── .gitignore                 # Root git ignore specification
├── requirements.txt           # Python backend dependencies
├── Dataset-Stock/             # Historical CSE market Excel files (1985–2025, git-ignored)
├── Dataset-Events/            # Curated event CSVs (70 policies, 34 arrests) + aliases.yml
├── data/
│   ├── politi_trade.db        # SQLite database (auto-generated on startup, git-ignored)
│   └── processed/             # Cleaned historical CSVs and feature matrices (git-ignored)
├── artifacts/
│   ├── clean/                 # Fast Parquet market & event cache (git-ignored)
│   ├── event_study/           # Precomputed CAR metrics (git-ignored)
│   ├── models/                # Trained Joblib model artifacts (git-ignored)
│   └── reports/               # Chronological model performance reports
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI route endpoints
│   │   ├── core/              # Config, DB connection, logging, SSRF security
│   │   ├── data/              # Trading calendar, stock loader, event loader
│   │   ├── events/            # Policy processor, arrest processor, event study engine
│   │   ├── ml/                # Feature engineering, model trainers, backtesting
│   │   ├── news/              # RSS feed scrapers, classifier, claim verification
│   │   ├── live/              # CSE live market scraper & fallback provider
│   │   └── main.py            # FastAPI application entry point & scheduler
│   ├── scripts/               # Pipeline execution scripts (ingest, train, study)
│   └── tests/                 # 17 automated Pytest suites
├── frontend/
│   ├── package.json           # Node dependencies & scripts
│   ├── vite.config.ts         # Vite bundler configuration
│   ├── tsconfig.json          # TypeScript compiler options
│   └── src/
│       ├── charts/            # ECharts components (TimelineChart, FanChart, etc.)
│       ├── components/        # Navbar, Sidebar, DisclaimerBanner, Modals
│       ├── pages/             # 10 application pages
│       ├── services/          # Typed API client
│       └── App.tsx            # Main layout and routing
└── docs/                      # Scientific and architectural documentation
    ├── METHODOLOGY.md         # Mathematical event study & ML architecture
    ├── API.md                 # Complete REST API specification
    ├── DATA_REPORT.md         # Historical data inventory audit
    ├── MODEL_EVALUATION.md    # Expanding-window benchmark comparison
    ├── ASSUMPTIONS.md         # Econometric and market assumptions
    └── TEST_REPORT.md         # Pytest verification report
```

---

## 5. Dataset & Large Files Placement Guide

To comply with GitHub file size limits and prevent repository bloat, raw historical market spreadsheets (~187MB), processed Parquet caches, SQLite database files, and trained binary model weights are excluded from Git via [`.gitignore`](file:///.gitignore).

Directory structure is preserved in version control through placeholder `.gitkeep` files. Follow the layout below when placing files or regenerating them on a fresh machine.

### 5.1 Exact File Placement Layout

```text
research-dev/
├── Dataset-Stock/                              # [RAW LARGE DATA: ~187 MB, Ignored in Git]
│   │   # Place all Colombo Stock Exchange daily trading archives here:
│   ├── 07Market Indices - Daily.xls            # Daily historical values for ASPI & S&P SL20
│   ├── 11Market Statistics-Daily.xls           # Turnover, traded volume, domestic/foreign shares
│   ├── 29 Beta Value.xls                       # Quoted company beta coefficients
│   ├── 39GICS-Daily.xlsx                       # GICS industry classification indices
│   ├── 01Dividends.xls, 06New Listings...      # Corporate actions and listing history
│   ├── 32Daily Shares Price List - 1991-2000/  # Daily trading session sheets for 1991–2000
│   ├── 31Daily Shares Price List -2001-2010/  # Daily trading session sheets for 2001–2010
│   ├── 32Daily Shares Price List -2011-2020/  # Daily trading session sheets for 2011–2020
│   ├── 40Daily Shares Price List -2021-2025/  # Daily trading session sheets for 2021–2025
│   │   ├── 2021 Data.xls, 2022 Data.xls
│   │   ├── 2023 Data.csv, 2024 Data.xls
│   │   └── 2025 Data.xlsx
│   └── Public Holding/                         # Public shareholding percentage records
│
├── Dataset-Events/                             # [CURATED SMALL DATA: ~160 KB, Tracked in Git]
│   ├── Government_Policies.csv                 # 70 verified Sri Lankan policy announcements
│   ├── Political_Arrests.csv                   # 34 verified high-profile political arrests
│   └── aliases.yml                             # Entity resolution and politician aliases
│
├── data/
│   ├── politi_trade.db                         # [SQLITE DB: Auto-created on backend launch]
│   └── processed/                              # [PROCESSED CSVs: Generated by pipeline]
│       ├── cleaned_stock_data.csv              # Unified 40-year historical daily stock series
│       ├── aligned_policy_stock_data.csv       # Trading-calendar aligned policy events ($t_0$)
│       └── policy_features.csv                 # Pre-event feature matrix ($t \le t_0 - 1$)
│
└── artifacts/                                  # [CACHE & MODEL WEIGHTS: Ignored in Git]
    ├── clean/                                  # Parquet columnar time-series cache
    │   ├── cleaned_stock_data.parquet          # High-speed market price lookup
    │   ├── processed_policies.parquet          # Standardized policy event records
    │   └── processed_arrests.parquet           # Standardized political arrest records
    ├── event_study/                            # Precomputed event study abnormal returns
    │   ├── all_events_study.parquet            # Full event dataset with CAR[0,1], CAR[0,5], CAR[0,20]
    │   └── all_events_study.json               # JSON representation consumed by frontend
    ├── models/                                 # Trained Scikit-learn binary model weights
    │   ├── policy_model.joblib                 # Policy direction classifier & Ridge CAR regressor
    │   ├── arrest_model.joblib                 # Arrest direction classifier & Ridge CAR regressor
    │   └── model_metadata.json                 # Model feature names, hyperparameters, and metrics
    ├── reports/                                # Empirical evaluation outputs
    │   └── model_comparison.json               # Out-of-sample expanding window scores
    └── backtests/                              # Cached historical replay backtest results
```

### 5.2 How to Place Datasets & Regenerate Artifacts

If you clone the repository onto a new machine where large files are missing:

1. **Place Raw Stock Data:**
   - Copy or download the `Dataset-Stock/` folder and place it directly in the project root: `research-dev/Dataset-Stock/`.
   - Ensure the subfolders (`31Daily Shares Price List -2001-2010/`, `32Daily Shares Price List -2011-2020/`, `40Daily Shares Price List -2021-2025/`, etc.) and the root files (`07Market Indices - Daily.xls`, etc.) are placed as listed in Section 5.1.

2. **Verify Curated Events:**
   - Ensure `Dataset-Events/Government_Policies.csv` and `Dataset-Events/Political_Arrests.csv` are present in `research-dev/Dataset-Events/` (these are version-controlled in the repository).

3. **Regenerate Clean Data & Event Studies:**
   - Run the event study script. It will parse the raw stock Excel sheets, execute calendar alignment ($t_0$ rollover for non-trading days or post-14:30 SLT announcements), calculate abnormal returns ($AR_t$) and Cumulative Abnormal Returns ($CAR$), and cache them into `artifacts/clean/` and `artifacts/event_study/`:
     ```powershell
     python backend/scripts/run_event_study.py
     ```

4. **Retrain ML Models:**
   - Train the L2-regularized Logistic Regression and Ridge CAR regression models, and build TF-IDF analogue semantic embeddings. This saves `policy_model.joblib` and `arrest_model.joblib` into `artifacts/models/`:
     ```powershell
     python backend/scripts/train_models.py
     ```

5. **Initialize Database & Scheduler:**
   - Start the FastAPI backend. It automatically creates the SQLite database at `data/politi_trade.db`:
     ```powershell
     python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
     ```

6. **(Optional) Run Live News Ingestion:**
   - Poll and ingest recent financial news articles:
     ```powershell
     python backend/scripts/ingest.py
     ```

---

## 6. Step-by-Step Guide: How to Run the Project

### 6.1 System Prerequisites
Ensure you have the following installed on your machine:
- **Python:** Version 3.11 or higher (`python --version`)
- **Node.js:** Version 18 or higher (`node -v`)
- **npm:** Version 9 or higher (`npm -v`)
- **Git** (optional, for version control)

---

### 6.2 Environment Setup

1. Open your terminal in the project root directory:
   ```powershell
   cd c:\Users\ramzy\Desktop\research-dev
   ```

2. If you do not have a `.env` file yet, copy it from `.env.example`:
   - **PowerShell (Windows):**
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Command Prompt (CMD):**
     ```cmd
     copy .env.example .env
     ```
   - **Bash (Linux / macOS):**
     ```bash
     cp .env.example .env
     ```

The default values inside `.env` will run the app out of the box:
```env
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=8001
FRONTEND_URL=http://127.0.0.1:5173
DATABASE_URL=sqlite:///./data/politi_trade.db
STOCK_DATASET_DIR=Dataset-Stock
EVENT_DATASET_DIR=Dataset-Events
ARTIFACT_DIR=artifacts
NEWS_POLL_MINUTES=15
LIVE_PROVIDER=cse_unofficial
LIVE_CACHE_SECONDS=30
MODEL_RANDOM_STATE=42
```

---

### 6.3 Backend Installation & Startup

1. **Create and Activate a Python Virtual Environment:**
   - **Windows PowerShell:**
     ```powershell
     python -m venv .venv
     # If PowerShell blocks script execution, run:
     # Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows Command Prompt (CMD):**
     ```cmd
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the FastAPI Server:**
   ```bash
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
   ```

4. **Verify Backend Health:**
   - Open your browser at: [http://127.0.0.1:8001/api/v1/health](http://127.0.0.1:8001/api/v1/health)
   - Interactive Swagger API Documentation: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

---

### 6.4 Frontend Installation & Startup

1. Open a **new terminal window** and navigate to the `frontend/` folder:
   ```bash
   cd c:\Users\ramzy\Desktop\research-dev\frontend
   ```

2. **Install Node Packages:**
   ```bash
   npm install
   ```

3. **Start the Development Server:**
   ```bash
   npm run dev
   ```

4. **Access the Application:**
   Open your browser and navigate to:
   👉 **[http://127.0.0.1:5173](http://127.0.0.1:5173)** (or `http://localhost:5173`)

---

### 6.5 Production Build (Optional)

To verify TypeScript types and generate production-ready static assets:
```bash
cd frontend
npm run build
```
The compiled output is saved into `frontend/dist/`. You can preview the production bundle with:
```bash
npm run preview
```

---

## 7. Running Automated Tests

### Backend Pytest Suite
Run all 17 automated backend tests covering API routing, event studies, anti-leakage calendar logic, machine learning inference, and SSRF security:
```bash
# From project root with virtual environment activated:
pytest -v backend/tests
```
*Expected result: 17 passed.*

---

## 8. Key REST API Endpoints Cheat Sheet

| HTTP Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health status and database connectivity |
| `GET` | `/api/v1/timeline/series` | Historical multi-index market price time-series |
| `GET` | `/api/v1/timeline/events` | Historical events overlaid on timeline |
| `GET` | `/api/v1/events` | Filterable list of 104 curated political events |
| `GET` | `/api/v1/events/{id}` | Detailed event trajectory with pre/post CAR windows |
| `POST` | `/api/v1/predict/policy` | Predict market impact of a policy event |
| `POST` | `/api/v1/predict/arrest` | Predict market impact of a political arrest |
| `POST` | `/api/v1/predict/backtest` | Run zero-lookahead historical replay backtest |
| `GET` | `/api/v1/news/feed` | Ingested local financial news articles |
| `POST` | `/api/v1/news/verify` | Claim verification & twin conditional forecasting |
| `GET` | `/api/v1/live/summary` | Real-time CSE market status, indices, and movers |
| `GET` | `/api/v1/models/summary` | Model evaluation metrics and benchmark comparisons |

Full interactive schemas, request payloads, and testing tools are available at `http://127.0.0.1:8001/docs`.

---

## 9. Troubleshooting & Common Issues

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| **PowerShell script execution error** | Execution policy restrictions on Windows | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in PowerShell, then re-run `.\.venv\Scripts\Activate.ps1`. |
| **Port 8000 conflicts** | Windows system services often reserve port 8000 | The app is configured by default to use port **8001**. Ensure you access `http://127.0.0.1:8001`. |
| **Frontend cannot connect to API** | Backend server is not running or CORS mismatch | Verify backend is running on `127.0.0.1:8001` and `FRONTEND_URL` in `.env` is set to `http://127.0.0.1:5173`. |
| **Missing raw stock data** | `Dataset-Stock` is ignored in Git | Place your CSE Excel files into `Dataset-Stock/` and run `python backend/scripts/run_event_study.py`. See Section 5. |
| **Database missing on first launch** | SQLite file has not been created yet | The database automatically initializes on backend startup at `data/politi_trade.db`. |
| **Missing Node modules** | `npm install` has not been run | Run `cd frontend && npm install`. |

---

## 10. Academic & Legal Disclaimer

> **ACADEMIC RESEARCH & INFORMATIONAL PURPOSE ONLY**  
> PolitiTrade LK is an academic research platform designed for econometric and quantitative study of market efficiency on the Colombo Stock Exchange.  
> Nothing generated by this platform constitutes investment advice, financial endorsement, or an offer to buy or sell securities. Historical market performance and machine learning projections do not guarantee future financial results.
