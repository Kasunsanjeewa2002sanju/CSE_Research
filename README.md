# CSE_Research

Quantitative evaluation and live forecasting platform analyzing the impact of Sri Lankan electoral/government events and news on the Colombo Stock Exchange (CSE) All Share Price Index (ASPI).

## Architecture Overview

This monorepo contains the complete research, backend, and frontend stack:

- **`cse_research/`**: Quantitative modeling, causal event study, walk-forward evaluation harness, and model zoo.
- **`backend/` & `cse_live/`**: FastAPI live service, real-time news extraction, market clock, and scheduler.
- **`frontend/`**: React + TypeScript + Vite + Tailwind CSS interactive dashboard.
- **`data/`**: Core datasets (`CSE_data.csv`, `Elections.csv`) and historical event mappings.
- **`results/`**: Empirical findings, benchmark leaderboards, IEEE publication figures, and prediction metrics.

## Quick Start

### 1. Unified Backend & Pipeline Runner
```bash
# Run entire pipeline reproduction + launch live backend API server:
python run_backend.py

# Launch backend API server only:
python run_backend.py --server-only
```

### 2. Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```

For detailed replication steps and research documentation, see [cse_research/HOW_TO_RUN.md](cse_research/HOW_TO_RUN.md) and [cse_research/README.md](cse_research/README.md).

