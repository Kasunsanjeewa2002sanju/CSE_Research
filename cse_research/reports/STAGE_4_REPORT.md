# Stage 4 Report: Event Study on Colombo Stock Exchange ASPI

**Project:** Sri Lanka Political Events and News Impact on CSE ASPI  
**Stage:** 4 — Event Study on ASPI around Electoral Event Stages (Core Individual Component)  
**Execution Timestamp:** 2026-10-11  
**Status:** Complete & Fully Validated (44/44 Unit Tests Passed; 10,000-Draw Placebo Permutation Tests; Full Artifacts Persisted)  

---

## 1. Executive Summary & Verification of Rules

In strict adherence to **RULES.md** and research proposal sections 2.2, 3.3 to 3.5:
- **Rule R1 (Real Data Only):** All market returns computed directly from `cse_clean.parquet` (7,635 rows). All event dates taken directly from `events_stage_level.parquet` (146 stage rows from `Elections.csv`). Zero invented prices, dates, or abnormal returns.
- **Rule R2 (Zero Lookahead):** For every event window $[w_1, w_2]$, the estimation window $[w_1 - L_{est}, w_1 - 1]$ ends strictly 1 trading day before the start of the event window, ensuring zero overlap. The reusable `prior_event_stats` module strictly filters out events whose windows have not concluded before the forecast origin date (`window_end_date < as_of_date`).
- **Rule R6 (Save Everything):** 6 tables, 1 markdown summary, and 3 high-resolution figures saved to `results/tables/` and `results/figures/`.
- **Rule R7 (Reproducibility):** Seed 42 pinned; 10,000 placebo draws reproducible; all library versions and execution logged.
- **Rule R8 (Honest Reporting):** Where sample sizes are small ($n = 5$ for Presidential elections), we explicitly display $n$, issue small-sample warnings, and note that raw $p$-values are not statistically significant ($p > 0.05$). We report both the full sample and the non-overlapping subsample ($\pm 30$ trading days).
- **Rule R10 (Stage Discipline):** Stage 4 scope completed; stopping before Stage 5 model training.

---

## 2. Event Study Experimental Design

### A. Primary Design (Constant-Mean Return Model)
- **Estimation Window:** $L_{est} = 15$ trading days ending 1 day before the event window: $[w_1 - 15, w_1 - 1]$.
- **Normal Return:** $\bar{R} = \frac{1}{15} \sum_{t \in est} R_t$, where $R_t = \ln(\text{ASPI}_t / \text{ASPI}_{t-1})$.
- **Abnormal Return (AR):** $AR_t = R_t - \bar{R}$.
- **Cumulative Abnormal Return (CAR):** $CAR[w_1, w_2] = \sum_{t = w_1}^{w_2} AR_t$.
- **9 Event Windows Evaluated:**
  - Post-event reaction: $[0, +2], [0, +7], [0, +15], [0, +30]$ trading days.
  - Pre-event anticipation: $[-7, -1], [-15, -1], [-30, -1]$ trading days.
  - Symmetric pre/post: $[-2, +2], [-7, +7]$ trading days (for pre-election decline vs. post-election rally).

### B. Robustness Checks
1. **Estimation Window Length:** Repeated with $L_{est} \in \{60, 120\}$ trading days to assess sensitivity to return volatility and local market drift.
2. **Market Model Sensitivity (with S&P SL 20):** For events after 2012-06-27 (when S&P SL 20 launched), estimated $R_{ASPI, t} = \alpha + \beta R_{SP20, t} + \epsilon_t$. Recorded caveat: ASPI is the broader market index and S&P SL 20 constituents overlap ASPI, so this is a secondary sensitivity check.

### C. Multi-Tier Statistical Significance Framework
1. **Brown-Warner (1980, 1985) Single-Event Test:**
   $t_{BW} = \frac{CAR}{\sqrt{L} \cdot \sigma_{AR}}$, testing whether individual event CARs deviate from estimation window volatility.
2. **10,000-Draw Non-Event Placebo Permutation Test:**
   Identified **5,297 clean trading days** in the CSE panel that do NOT fall within $\pm 30$ trading days of ANY electoral event. Sampled 10,000 pseudo-events with replacement to construct the true empirical null distribution of CARs in Sri Lanka. Reported empirical two-sided $p$-value and exact percentile.
3. **Cross-Event CAAR Tests:**
   - Parametric one-sample $t$-test ($H_0: CAAR = 0$).
   - Non-parametric Wilcoxon signed-rank test.
   - Non-parametric Sign test ($H_0: \text{median} = 0$).
4. **Benjamini-Hochberg (1995) FDR Correction:**
   Applied across all hypothesis tests to control False Discovery Rate under multiple testing.

---

## 3. Key Empirical Findings (Strictly Grounded in Generated Tables)

### A. Polling Date Reactions across Election Types (Window [0, +7], `event_study_by_type_stage.csv`):

| Election Type | Sample ($n$) | Small Sample Warning | Polling CAAR [0, +7] (%) | Median CAR (%) | $t$-stat | $t$-pval (Raw) | Sign Test $p$ | Non-Overlapping CAAR (%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Presidential** | 5 | ⚠️ YES ($n<5$) | **-0.82%** | +0.37% | -0.22 | 0.8354 | 1.0000 | -0.56% ($n=4$) |
| **Parliamentary** | 7 | No | **-1.40%** | -4.70% | -0.50 | 0.6364 | 0.4531 | -1.12% ($n=6$) |
| **Provincial Council** | 12 | No | **-0.85%** | -0.53% | -0.87 | 0.4025 | 0.7744 | +0.10% ($n=8$) |

> [!NOTE]
> **Across All Electoral Stages Combined (All 30 Presidential Stages, Window [0, +7]):**
> - Presidential CAAR across all stages: **+0.67%** (Median: +0.74%, $t = 0.73, p = 0.4696$).
> - Parliamentary CAAR across all stages: **-1.05%** (Median: -1.22%, $t = -1.12, p = 0.2686$).
> - Provincial Council CAAR across all stages: **-0.64%** (Median: -0.05%, $t = -1.36, p = 0.1790$).

### B. Pre-Election Anticipation vs. Post-Election Rally (Windows [-7, -1] vs. [0, +7]):

| Election Type | Window | Sample ($n$) | CAAR (%) | Median CAR (%) | $t$-stat | $t$-pval | Sign Test $p$ |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Presidential** | [-7, -1] (Pre) | 30 | **+0.67%** | +0.22% | 1.18 | 0.2494 | 1.0000 |
| **Presidential** | [0, +7] (Post) | 30 | **+0.67%** | +0.74% | 0.73 | 0.4696 | 0.3616 |
| **Presidential** | [-2, +2] (Symm) | 30 | **+0.52%** | +1.75% | 0.52 | 0.6090 | 0.0161* |
| **Presidential** | [0, +30] (Post) | 30 | **+1.80%** | +4.79% | 0.79 | 0.4338 | 0.5847 |
| **Parliamentary** | [-7, -1] (Pre) | 42 | **-0.54%** | +0.34% | -0.62 | 0.5389 | 0.6440 |
| **Parliamentary** | [0, +7] (Post) | 42 | **-1.05%** | -1.22% | -1.12 | 0.2686 | 0.0436* |
| **Provincial Council** | [-7, -1] (Pre) | 70 | **+0.33%** | +0.41% | 0.65 | 0.5176 | 0.1882 |
| **Provincial Council** | [0, +7] (Post) | 70 | **-0.64%** | -0.05% | -1.36 | 0.1790 | 0.9050 |

### C. Electoral Stages Comparison (Presidential Elections, Window [0, +7]):

| Stage | Sample ($n$) | Small Sample Warning | CAAR [0, +7] (%) | Median CAR (%) | $t$-stat | $t$-pval | Sign Test $p$ |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **announcement** | 5 | ⚠️ YES ($n<5$) | **-1.28%** | -1.73% | -0.90 | 0.4198 | 0.3750 |
| **nomination_start** | 5 | ⚠️ YES ($n<5$) | **+2.36%** | +3.70% | 2.18 | 0.0991 | 0.3750 |
| **nomination_end** | 5 | ⚠️ YES ($n<5$) | **+2.95%** | +3.80% | 2.15 | 0.1028 | 0.3750 |
| **polling** | 5 | ⚠️ YES ($n<5$) | **-0.82%** | +0.37% | -0.22 | 0.8354 | 1.0000 |
| **result** | 5 | ⚠️ YES ($n<5$) | **-0.29%** | +0.37% | -0.10 | 0.9281 | 1.0000 |
| **government_formation** | 5 | ⚠️ YES ($n<5$) | **+1.08%** | +0.37% | 0.53 | 0.6245 | 1.0000 |

### D. Estimation Window Length Sensitivity ($L_{est} \in \{15, 60, 120\}$ TD, Polling Stage [0, +7]):

| Election Type | $L_{est} = 15$ TD CAAR | $L_{est} = 60$ TD CAAR | $L_{est} = 120$ TD CAAR | Directional Stability |
|:---|:---:|:---:|:---:|:---:|
| **Presidential** | -0.82% ($p = 0.84$) | +0.06% ($p = 0.99$) | -0.43% ($p = 0.91$) | Hovering near zero, high variance |
| **Parliamentary** | -1.40% ($p = 0.64$) | -0.31% ($p = 0.91$) | +0.83% ($p = 0.77$) | Moderate shift toward zero |
| **Provincial Council** | -0.85% ($p = 0.40$) | -0.39% ($p = 0.68$) | +0.17% ($p = 0.87$) | Consistent lack of market reaction |

---

## 4. Reusable Zero-Lookahead Module (`src/cse/events/prior_stats.py`)

A fully tested, reusable module was built for subsequent machine learning stages:
```python
from cse.events.prior_stats import prior_event_stats

# Query prior statistics as of 2018-01-01 (P3 validation start)
stats = prior_event_stats(
    as_of_date="2018-01-01",
    election_type="Presidential",
    stage="polling",
    window="[0,+7]",
)
# Returns: {'mean': 0.0076, 'median': 0.0076, 'std': 0.0321, 'n': 3}
# Strictly excludes 2019 and 2024 Presidential elections!
```

---

## 5. Figures and Tables Created

### Tables (`results/tables/`):
1. [`event_study_per_event.csv`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/tables/event_study_per_event.csv): 1,314 rows (every event stage $\times$ 9 windows, with Brown-Warner $t$, placebo $p$-value, percentile).
2. [`event_study_by_type.csv`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/tables/event_study_by_type.csv): 54 rows (aggregated by election type $\times$ window, all and non-overlapping).
3. [`event_study_by_stage.csv`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/tables/event_study_by_stage.csv): 108 rows (aggregated by stage $\times$ window, all and non-overlapping).
4. [`event_study_by_type_stage.csv`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/tables/event_study_by_type_stage.csv): 324 rows (aggregated by type $\times$ stage $\times$ window).
5. [`event_study_robustness_windows.csv`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/tables/event_study_robustness_windows.csv): 486 rows ($L_{est} \in \{15, 60, 120\}$ comparison).
6. [`event_study_market_model_sp20.csv`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/tables/event_study_market_model_sp20.csv): 126 rows (S&P SL 20 market model sensitivity for post-2012 events).
7. [`event_study_summary.md`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/tables/event_study_summary.md): Quantitative interpretation strictly grounded in data.

### Figures (`results/figures/`):
1. [`car_curves_polling_by_election_type.png`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/figures/car_curves_polling_by_election_type.png): Daily CAR curves from day -30 to +30 relative to poll date for Presidential, Parliamentary, and Provincial Council elections against the 95% permutation null band.
2. [`car_curves_presidential_stages.png`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/figures/car_curves_presidential_stages.png): Trajectory comparison across announcement, polling, result, and government formation stages.
3. [`caar_heatmap_type_x_stage.png`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/figures/caar_heatmap_type_x_stage.png): Heatmap of CAAR [0, +7] by Election Type $\times$ Stage annotated with sample sizes.

---

## 6. Unit Test Suite (44/44 Tests Passed)
Executed via `pytest tests/ -v -p no:cacheprovider`:
- `test_event_study.py`: BH correction monotonicity/bounds, 9 event window definitions, Brown-Warner standard errors, small sample warnings. **PASSED**.
- `test_prior_stats.py`: Proves no future event is ever used, verifies window end date filtering, monotonicity over time, pre-sample $n=0$. **PASSED**.
- Ingestion, smoke, splits, metrics, and leakage test suites: All 37 existing tests **PASSED**.

---

## 7. Stage Discipline Confirmation (Rule R10)
Stage 4 is complete. All outputs are saved to disk. Ready for your review before proceeding to Stage 5.
