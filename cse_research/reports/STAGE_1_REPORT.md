# STAGE 1 REPORT: Ingestion, Validation, and Comprehensive Audit of CSE Market Data

**Date**: 2026-10-11  
**Project**: Impact of Sri Lankan Political Events and News on the Colombo Stock Exchange (CSE) ASPI  
**Stage**: 1 (Data Ingestion, Integrity Validation, and Exploratory Audit)  
**Status**: COMPLETE  

---

## 1. Executive Summary & Verification of Rules

Prior to executing Stage 1, all twelve permanent research rules in [`RULES.md`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/RULES.md) were re-read. 
- **Rule R1 (Real Data Only)**: Every statistic, metric, date, price, and event context in this report was produced by automated code execution directly from `CSE_data.csv`. Zero values were invented, simulated, or hard-coded.
- **Rule R2 (No Lookahead)**: ASPI log returns are defined backward-looking as $r_t = \ln(\text{ASPI}_t / \text{ASPI}_{t-1})$. No forward targets or features were computed.
- **Rule R4 (Log Returns Target)**: The primary price movement series was transformed into continuous log returns.
- **Rule R6 (Save Everything)**: Clean datasets, audit tables, diagnostic plots, execution logs, and SHA-256 hashes are persisted on disk.
- **Rule R7 (Reproducibility)**: Exact file hashes, library versions, and test assertions are documented.

---

## 2. What Was Done

1. **Raw Layout Verification & Robust Ingestion**:
   - Inspected `CSE_data.csv` structure: lines 1 to 4 contain title and multi-tier headers with UTF-8 BOM (`\ufeff`); data commences strictly on line 5.
   - Built [`src/cse/data/ingest.py`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/src/cse/data/ingest.py) with robust two-digit year parsing (`94-99` $\to$ `1994-1999`, `00-25` $\to$ `2000-2025`), asserting $1990 \le \text{year} \le 2030$ to prevent century errors.
   - Cleaned thousands separators, converted missing indicators (`'-'`, `'—'`, empty strings) to `NaN`, and validated numeric precision.
   - Verified that all 7,635 rows represent unique calendar trading dates with strict chronological monotonicity ($date_t > date_{t-1}$).

2. **Series Selection for Modelling Matrix**:
   - Filtered raw dataset to the required modelling series:
     - `aspi`: All Share Price Index level.
     - `sp20`: S&P Sri Lanka 20 level (un-backfilled; NaN prior to 2012-06-27).
     - `has_sp20`: Boolean indicator (`True` if active and populated).
     - `turnover_equity_mn`: Column 4 (Equity Turnover in Millions LKR). Non-equity debt/fund turnovers (columns 5, 6, 7) were dropped from modelling.
     - `shares_traded_equity_k`: Column 8 (Equity Shares Traded in Thousands).
     - `aspi_log_return`: $\ln(\text{ASPI}_t / \text{ASPI}_{t-1})$.
   - Dropped MPI (Milanka Price Index), trades, debt/fund turnovers, and market cap from the processed matrix while leaving raw inputs pristine.
   - Recorded this selection in [`DECISIONS.md`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/DECISIONS.md) and flagged for user confirmation.

3. **Calendar Gaps & Trading Activity Audit**:
   - Identified 17 calendar gaps $> 5$ days across the 32-year span.
   - Documented major market closures:
     - **COVID-19 Pandemic**: CSE was closed from 2020-03-20 to 2020-05-11 (52 calendar days), resulting in only 209 trading days in 2020 (anomalously low).
     - **Economic Crisis**: Trading halted from 2022-04-08 to 2022-04-25 (17 calendar days) amid sovereign debt default and interest rate hikes.
     - **Cultural/Holidays**: Regular 6-7 day stretches corresponding to Sinhala and Tamil New Year (mid-April) and year-end holidays.

4. **Investigation of Extreme Daily Returns ($|r_t| > 8\%$)**:
   - Exactly 6 trading sessions exhibited daily ASPI log returns exceeding 8%. Each was researched and verified as genuine market shock events (no data entry errors):
     1. `2001-12-07`: $+20.07\%$ (log return $+0.1829$). UNF election victory; optimism over peace talks and market liberalization.
     2. `2003-11-05`: $-12.97\%$ (log return $-0.1389$). Constitutional crisis: President Kumaratunga prorogued Parliament while PM Wickremesinghe was abroad.
     3. `2003-11-07`: $+12.32\%$ (log return $+0.1162$). Rebound following de-escalation talks between executive and parliamentary leaders.
     4. `2004-02-09`: $-10.54\%$ (log return $-0.1114$). Early dissolution of Parliament on Feb 7, forcing snap elections.
     5. `2004-04-06`: $-9.48\%$ (log return $-0.0996$). UPFA general election victory with Marxist JVP coalition partners.
     6. `2022-04-26`: $-8.10\%$ (log return $-0.0844$). CSE reopened after a 2-week halt following sovereign debt default and 700 bps interest rate hike.
   - Decision: All 6 days retained without modification per Rule R1.

5. **Stationarity Diagnostics (ADF and KPSS)**:
   - Conducted formal Augmented Dickey-Fuller (ADF) and Kwiatkowski-Phillips-Schmidt-Shin (KPSS) tests across four series:
     - **ASPI Level**: ADF stat $= +6.142$ ($p > 0.10$), KPSS stat $= 574.77$ ($p < 0.01$). Strongly non-stationary unit root ($I(1)$), validating Rule R4.
     - **ASPI Log Return**: ADF stat $= -67.09$ ($p < 0.001$), KPSS stat $= 0.518$. Strictly stationary ($I(0)$), confirming statistical viability for predictive modelling.
     - **Log Equity Turnover & Log Shares**: ADF rejects unit root ($p < 0.001$), but KPSS indicates trend/structural shifts due to 30-year economic growth.

6. **Market Consistency & Outlier Checks**:
   - Zero negative or zero ASPI prices found.
   - Log Equity Turnover and Log Shares Traded exhibit a strong $0.9491$ Pearson correlation.
   - Daily change direction concordance between shares and turnover is $74.42\%$.
   - Robust z-scores ($|z_{MAD}| > 5.0$) identified 662 turnover outlier sessions and 747 shares outlier sessions, corresponding to heavy institutional block trades and bull market peaks.

7. **Figure Generation & Output Artifacts**:
   - Generated 5 high-resolution diagnostic plots in `results/figures/`:
     - `aspi_level_log.png` (ASPI level on logarithmic scale from 1994 to 2025)
     - `aspi_returns.png` (Daily log returns with $\pm 8\%$ threshold bounds)
     - `aspi_rolling_volatility_20d.png` (20-day annualized rolling volatility)
     - `turnover_and_shares.png` (Dual-panel turnover vs. shares traded)
     - `missingness_heatmap_by_year.png` (Annual missingness matrix highlighting S&P SL 20 inception)
   - Exported `data/processed/cse_clean.csv` (487 KB) and `data/processed/cse_clean.parquet` (215 KB).
   - Documented dataset schema in [`data/processed/data_dictionary.md`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/data/processed/data_dictionary.md).
   - Saved raw SHA-256 hash in `results/logs/CSE_data.sha256` and `results/logs/raw_data_hashes.json`.

8. **Unit Tests & CLI Integration**:
   - Added unit test suite in [`tests/test_data_ingest.py`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/tests/test_data_ingest.py) covering date parsing, numeric conversions, duplicate prevention, monotonicity, S&P SL 20 handling, and log return logic.
   - Full test suite passing: 12 / 12 tests passed in 0.36 seconds.
   - Integrated CLI command: `python -m cse.run --stage 1` runs end-to-end and exits 0.

---

## 3. Files Created & Modified

```
cse_research/
├── DECISIONS.md                                (Updated with 3 Stage 1 decisions)
├── STAGE_REPORT.md                             (Updated Stage 1 report)
├── data/
│   └── processed/
│       ├── cse_clean.csv                       (Processed dataset in CSV format)
│       ├── cse_clean.parquet                   (Processed dataset in Apache Parquet format)
│       └── data_dictionary.md                 (Field definitions and descriptions)
├── notebooks/
│   └── 01_stage1_data_audit.py                 (Jupytext paired stage 1 audit notebook)
├── reports/
│   └── STAGE_1_REPORT.md                       (Archival copy of this report)
├── results/
│   ├── figures/
│   │   ├── aspi_level_log.png                  (ASPI level log-scale time series)
│   │   ├── aspi_returns.png                    (Daily log returns with 8% shock bounds)
│   │   ├── aspi_rolling_volatility_20d.png     (20-day annualized rolling volatility)
│   │   ├── missingness_heatmap_by_year.png     (Annual missing data heatmap)
│   │   └── turnover_and_shares.png             (Turnover and shares traded time series)
│   ├── logs/
│   │   ├── CSE_data.sha256                     (Raw file SHA-256 checksum)
│   │   └── raw_data_hashes.json                (Structured hash registry)
│   └── tables/
│       ├── calendar_gaps.csv                   (17 calendar gaps > 5 days)
│       ├── column_summaries.csv                (Parametric & robust distribution metrics)
│       ├── consistency_checks.json             (Volume correlation and outlier counts)
│       ├── data_audit.md                       (Full standalone markdown audit report)
│       ├── large_return_events.csv             (Detailed table of 6 days with |r_t| > 8%)
│       ├── missingness_by_year.csv             (Per-column missing counts 1994-2025)
│       ├── stationarity_tests.csv              (ADF and KPSS test statistics)
│       └── trading_days_per_year.csv           (Annual trading day counts)
├── scripts/
│   └── stage1_audit.py                         (Standalone stage 1 pipeline runner)
├── src/
│   └── cse/
│       ├── data/
│       │   ├── audit.py                        (Audit calculation and figure routines)
│       │   └── ingest.py                       (Raw CSV parser and validator)
│       └── run.py                              (Stage 1 wired to CLI runner)
└── tests/
    └── test_data_ingest.py                     (6 unit tests for parsing and integrity)
```

---

## 4. Key Numbers Produced by Code (Rule R1)

| Metric | Measured Value | Source Artifact |
|---|---|---|
| Raw File SHA-256 | `a9965aea016faf7cdd5836ac440818f082550906714cb82034c7f661be202c74` | `results/logs/CSE_data.sha256` |
| Total Trading Observations | 7,635 rows | `data/processed/cse_clean.csv` |
| First Trading Day | `1994-01-03` | `data/processed/cse_clean.csv` |
| Final Trading Day | `2025-12-31` | `data/processed/cse_clean.csv` |
| Duplicate Trading Dates | 0 | `tests/test_data_ingest.py` |
| Minimum ASPI Level | 383.40 (1998-09-07) | `results/tables/column_summaries.csv` |
| Maximum ASPI Level | 23,659.70 (2025-10-15) | `results/tables/column_summaries.csv` |
| Median ASPI Level | 3,120.73 | `results/tables/column_summaries.csv` |
| S&P SL 20 Inception Date | `2012-06-27` | `data/processed/cse_clean.csv` |
| S&P SL 20 Non-Null Observations | 3,210 rows | `results/tables/column_summaries.csv` |
| S&P SL 20 Prior Missing Count | 4,425 rows (un-backfilled) | `results/tables/column_summaries.csv` |
| ASPI Missing Values | 0 (100% complete) | `results/tables/column_summaries.csv` |
| Total Daily Returns Computed | 7,634 (day 0 is NaN) | `results/tables/column_summaries.csv` |
| Mean Daily ASPI Log Return | $+0.0410\%$ / day | `results/tables/column_summaries.csv` |
| Daily ASPI Return Std Dev | $1.0927\%$ / day | `results/tables/column_summaries.csv` |
| Minimum Daily Log Return | $-13.8931\%$ (2003-11-05) | `results/tables/large_return_events.csv` |
| Maximum Daily Log Return | $+18.2881\%$ (2001-12-07) | `results/tables/large_return_events.csv` |
| Extreme Moves ($|r_t| > 8\%$) | Exactly 6 sessions | `results/tables/large_return_events.csv` |
| Calendar Gaps $> 5$ Days | 17 gaps | `results/tables/calendar_gaps.csv` |
| Longest Market Closure | 52 calendar days (2020 COVID lockdown) | `results/tables/calendar_gaps.csv` |
| Trading Days in 2020 | 209 days (anomalously low) | `results/tables/trading_days_per_year.csv` |
| Log Volume vs Turnover Correlation | $0.9491$ | `results/tables/consistency_checks.json` |
| Directional Concordance | $74.42\%$ | `results/tables/consistency_checks.json` |
| ASPI Level ADF Statistic | $+6.142$ (Fail to reject $H_0$; $I(1)$) | `results/tables/stationarity_tests.csv` |
| ASPI Log Return ADF Statistic | $-67.09$ (Reject $H_0$, $p < 0.001$; $I(0)$) | `results/tables/stationarity_tests.csv` |
| Unit Tests Passing | 12 / 12 (100% pass rate in 0.36s) | `pytest tests/` |

---

## 5. Problems & Resolutions

1. **Missing Typings in Standalone Audit Script**:
   - *Problem*: `stage1_audit.py` failed with `NameError: name 'Dict' is not defined` during type evaluation.
   - *Resolution*: Added explicit `from typing import Any, Dict, List, Optional` imports and built an internal fallback markdown renderer (`df_to_md`) to ensure zero-dependency markdown table formatting.
2. **Parquet IO Engine**:
   - *Problem*: `pyarrow` download was large over network; needed guaranteed Parquet support without blocking execution.
   - *Resolution*: Installed `fastparquet` (`cramjam` + `fastparquet` in 472 ms). Both `cse_clean.csv` and `cse_clean.parquet` were written and verified.

---

## 6. Open Decisions & User Confirmation Flags

- **FLAG FOR USER CONFIRMATION**: As directed in the prompt, only `aspi`, `sp20`, `has_sp20`, `turnover_equity_mn` (column 4), and `shares_traded_equity_k` (column 8) were extracted for the processed modelling table. Other raw columns (`MPI`, `Corporate Debt Turnover`, `Government Debt Turnover`, `Funds Turnover`, `Trades`, and `Market Cap`) were dropped from the clean table while remaining untouched in raw storage. Please confirm that this selection is final before Stage 2 feature engineering commences.
