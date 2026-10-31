# STAGE 0 REPORT: Research Scaffold & Environment Initialization

**Date**: 2026-10-11  
**Project**: Impact of Sri Lankan Political Events and News on the Colombo Stock Exchange (CSE) ASPI  
**Stage**: 0 (Scaffold, Tooling, Rules & Smoke Verification)  
**Status**: COMPLETE  

---

## 1. What Was Done

1. **Workspace Isolation**:
   - Initialized a brand new, isolated project directory `cse_research/` at the root workspace. All work is strictly self-contained within this tree.

2. **Permanent Rules Institutionalization (Rule R1 - R12)**:
   - Written verbatim to `cse_research/RULES.md`. These 12 permanent rules govern real data integrity, zero lookahead, conservative threshold checks, log return modeling, strict reproducibility, and honest negative reporting across all upcoming stages.

3. **Architectural Decisions Log**:
   - Initialized `cse_research/DECISIONS.md` containing the mandated tabular template (`Date`, `Decision`, `Reason`, `Alternatives`).

4. **Configuration Specification (`config/config.yaml`)**:
   - Established complete YAML experiment configuration including:
     - Project metadata and global random seed (`42`).
     - Standard directory layout paths.
     - Raw input data file specifications (`CSE_data.csv`, `Elections.csv`, proposal PDF).
     - Research phases (1 to 5).
     - Standardized forecast horizons: `h1` (1-day), `h5` (5-day / 1-week), `h20` (20-day / 1-month).
     - Walk-forward expanding window splits with embargo gaps.
     - Model family registry: `statistical`, `shallow`, `deep`, `foundation`, and `hybrid`.
     - Evaluation metrics suite (magnitude and directional metrics) with strict suspicion thresholds (Rule R3).
     - Hardware detection settings and structured JSON logging.

5. **Python 3.11 Runtime & Virtual Environment**:
   - Provisioned Python 3.11 (`cpython-3.11.15-windows-x86_64-none`).
   - Built a local virtual environment `.venv` located at `cse_research/.venv`.
   - Pinned dependencies defined in `cse_research/requirements.txt`.

6. **Typed Modular Architecture (`src/cse/`)**:
   - Constructed package layout:
     - `src/cse/__init__.py`
     - `src/cse/data/` (data ingestion, validation, and preprocessing)
     - `src/cse/events/` (election calendar alignment and political regime tagging)
     - `src/cse/features/` (zero-lookahead feature engineering)
     - `src/cse/splits/` (walk-forward cross-validation splits)
     - `src/cse/eval/` (evaluation protocols and leakage sanity checks)
     - `src/cse/models/` (`statistical/`, `shallow/`, `deep/`, `foundation/`, `hybrid/`)
     - `src/cse/news/` (news ingestion, NLP parsing, sentiment, veracity tagging)
     - `src/cse/scenario/` (counterfactual analysis: if true vs. if false)
     - `src/cse/utils/` (`seed.py`, `device.py`, `logger.py`, `config.py`, `notebook_runner.py`)

7. **Tooling & Infrastructure**:
   - **Hardware Detection**: `cse.utils.device` detects NVIDIA GPU with automatic CPU fallback and captures detailed device metadata.
   - **Global Seeding**: `cse.utils.seed.seed_everything` seeds Python `random`, `numpy`, and `torch` (when present), enforcing Rule R7.
   - **Structured Logging**: `cse.utils.logger` produces structured JSON log lines into `results/logs/cse_research.log` alongside console output.
   - **Stage Runner CLI**: `python -m cse.run --stage N` implemented in `src/cse/run.py`.
   - **Notebook Execution**: `cse.utils.notebook_runner` and `scripts/run_notebook.py` enable automated Colab-style execution with full output capture via papermill/nbconvert.

8. **Pristine Raw Data Placement**:
   - Input files placed into `cse_research/data/raw/` without modification:
     - `CSE_data.csv` (793,108 bytes)
     - `Elections.csv` (18,625 bytes)
     - `Predicting Stock Market Movements Using Government_Changes_updated.pdf` (2,176,654 bytes)

9. **Smoke Testing Suite**:
   - Formulated 6 comprehensive test cases in `cse_research/tests/test_smoke.py`.
   - Executed via `pytest`: 6 passed in 0.34 seconds.
   - Executed Stage 0 via CLI runner (`python -m cse.run --stage 0`): exited 0.

---

## 2. Files Created

```
cse_research/
├── RULES.md
├── DECISIONS.md
├── README.md
├── Makefile
├── requirements.txt
├── STAGE_REPORT.md
├── config/
│   └── config.yaml
├── data/
│   ├── raw/
│   │   ├── CSE_data.csv
│   │   ├── Elections.csv
│   │   └── Predicting Stock Market Movements Using Government_Changes_updated.pdf
│   ├── interim/
│   └── processed/
├── src/
│   └── cse/
│       ├── __init__.py
│       ├── run.py
│       ├── data/__init__.py
│       ├── events/__init__.py
│       ├── features/__init__.py
│       ├── splits/__init__.py
│       ├── eval/__init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── statistical/__init__.py
│       │   ├── shallow/__init__.py
│       │   ├── deep/__init__.py
│       │   ├── foundation/__init__.py
│       │   └── hybrid/__init__.py
│       ├── news/__init__.py
│       ├── scenario/__init__.py
│       └── utils/
│           ├── __init__.py
│           ├── seed.py
│           ├── device.py
│           ├── logger.py
│           ├── config.py
│           └── notebook_runner.py
├── notebooks/
│   ├── README.md
│   ├── 00_environment_smoke_test.py
│   └── executed/
├── models/
│   └── README.md
├── results/
│   ├── README.md
│   ├── metrics/
│   ├── predictions/
│   ├── figures/
│   ├── tables/
│   └── logs/
│       └── cse_research.log
├── reports/
│   └── STAGE_0_REPORT.md
├── tests/
│   └── test_smoke.py
└── scripts/
    └── run_notebook.py
```

---

## 3. Key Numbers & Metrics

| Metric | Value |
|---|---|
| Python Version | `3.11.15` (CPython x86_64) |
| Active OS Platform | Windows (AMD64) |
| Detected GPU Device | NVIDIA GeForce (2048 MB memory, Driver 516.40, CUDA 11.7 capability) |
| Active Fallback Mode | CPU fallback verified and active |
| Global Random Seed | `42` |
| Forecast Horizons Configured | 3 (`h1`: 1 day, `h5`: 5 days, `h20`: 20 days) |
| Model Families Scaffolded | 5 (`statistical`, `shallow`, `deep`, `foundation`, `hybrid`) |
| Raw Data Files Verified | 3 files (CSE_data.csv: 793,108 B, Elections.csv: 18,625 B, Proposal PDF: 2,176,654 B) |
| Unit Tests Executed | 6 |
| Unit Tests Passing | 6 / 6 (100% pass rate in 0.34s) |
| Stage 0 CLI Exit Code | `0` |

---

## 4. Problems & Resolutions

1. **Execution Pathing & Drive Isolation on Windows**:
   - *Problem*: Windows PowerShell in the terminal default environment starts on `C:\` and attempts relative path resolution against `C:\` instead of the project directory on drive `D:\`.
   - *Resolution*: Anchored `find_project_root` in `cse.utils.config` to dynamically find the project root via marker file (`RULES.md`), and parameterized all scripts to work robustly with absolute and workspace-anchored paths.

2. **Cross-Drive Hardlinking in `uv`**:
   - *Problem*: `uv` cache resided on `C:\Users\rpc\AppData\Local\uv\cache`, while the project environment is located on `D:\SLIIT\...`. Windows filesystem forbids hardlinks across distinct volume boundaries (`C:` to `D:`).
   - *Resolution*: Enforced `--link-mode=copy` across package installations and embedded it within `Makefile` and tool invocation guidelines.

---

## 5. Open Decisions

- None for Stage 0. The scaffolding, configurations, tooling, and smoke tests are completely in place and passing.
- In Stage 1 (Data Ingestion and Integrity Validation), raw column date formats, trading day calendar alignment, and missing value imputation policies will be documented in `DECISIONS.md`.
