# HOW TO RUN — REPRODUCTION GUIDE

This one-page document provides exact, reproducible instructions for setting up the environment, verifying data integrity, executing the quantitative modeling pipeline, running live news ingestion, and regenerating research assets.

---

## 1. Environment Requirements & Setup

- **Python Version:** 3.11+ (Pinned 3.11.15)
- **Package Manager:** `uv` (recommended) or standard `pip`
- **Operating System:** Windows, Linux, or macOS

```bash
# 1. Clone repository and navigate to root
cd cse_research

# 2. Create virtual environment and activate
uv venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install pinned dependencies
uv pip install -r requirements.txt
```

---

## 2. Verification & Testing

Execute the complete test suite (122 tests covering data ingestion, feature leakage, temporal embargoes, model logic, news ingestion, and counterfactual scenario engines):

```bash
# Run all unit and integration tests (approx. 70 seconds)
python -m pytest tests
```

---

## 3. Pipeline Stage Execution

Execute individual pipeline stages sequentially using the modular stage runner:

```bash
# Stage 0: Environment & Scaffold Smoke Test
python -m cse.run --stage 0

# Stage 1: Data Ingestion & Integrity Audit (CSE_data.csv & Elections.csv)
python -m cse.run --stage 1

# Stage 2: Event Calendar Construction & Trading Day Mapping
python -m cse.run --stage 2

# Stage 3: Walk-Forward Validation Harness & Split Generation
python -m cse.run --stage 3

# Stage 4: Event Study Analysis on ASPI around Electoral Stages
python -m cse.run --stage 4

# Stage 5: Feature Engineering Matrix Generation (Sets A, B, C)
python -m cse.run --stage 5

# Stage 9: Final Model Comparison, Statistical Testing & Selection
python scripts/stage9_model_selection.py

# Stage 10: News Extraction Module Validation
python scripts/stage10_validate.py

# Stage 11: Historical Election Back-Testing
python scripts/stage11_backtest.py

# Stage 12: Live News Ingestion Pipeline
python -m cse.run --stage 12

# Stage 13: Full Skeptical Audit & Research Report Asset Generation
python scripts/stage13_audit_and_report.py
```

---

## 4. Live News Monitoring & Scenario Engine

To run the live news ingestion scheduler or execute an immediate one-shot crawl:

```bash
# Immediate one-shot crawl across verified RSS and API feeds:
python -m cse.run_news --poll-now

# Launch continuous polling daemon (polls every 30 minutes):
python -m cse.run_news --interval-mins 30
```

Results are stored in append-only flat format at `results/tables/news_ingested.csv`.

---

## 5. Artifact & Report Outputs

- **Audit Report:** `reports/audit.md`
- **Research Results & Methods Paper:** `reports/results.md`
- **Master Tables:** `results/master_table.csv` and `results/tables/`
- **Figures:** `results/figures/` (IEEE 300 DPI format)
- **Model Registry:** `results/model_zoo.csv`
- **Result Catalog:** `results/index.md`

python run_backend.py --server-only
