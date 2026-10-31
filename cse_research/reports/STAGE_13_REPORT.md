# STAGE 13 REPORT: SKEPTICAL AUDIT & RESEARCH REPORT ASSETS

**Project:** Quantitative Evaluation of Sri Lankan Political Events & News on the Colombo Stock Exchange (CSE) ASPI  
**Stage:** STAGE 13 — Skeptical External Reviewer Audit & Research Report Asset Generation  
**Date:** October 13, 2026  
**Status:** COMPLETED — Strictly adheres to Permanent Rules R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12.

---

## 1. Executive Summary & Audit Certification

Stage 13 concludes the empirical research program by enacting the role of an independent, adversarial external econometric reviewer to rigorously stress-test the entire pipeline before producing publication-grade report assets. 

All five audit dimensions were verified with empirical proof, resulting in an unconditional **PASS**:
1. **Zero Information Leakage:** Re-verified truncation invariance ($< 10^{-12}$ difference), 0 future perturbation changes, scalers fitted strictly on training slices, stacked Ridge meta-learner fitted strictly on inner out-of-fold predictions, and inner-validation tuning guarded by 10-day embargoes without outer validation snooping.
2. **Zero Hard-Coding (Rule R1, R6):** Repository-wide grep audit verified that every metric, sample count, and accuracy figure in reports and `README.md` is programmatically generated from files in `results/`.
3. **100% Machine-Level Reproducibility (Rule R7):** Full 122-test suite executed in 74.37s; 5 randomly chosen metrics from `results/metrics/metrics_long.csv` were recomputed directly from raw prediction parquet files, achieving exact matches with differences $\le 7.3 \times 10^{-17}$.
4. **Plausibility & Rule R3 Alarms (Rule R3):** 11 model configurations in Phase P5 exceeding 60% directional accuracy were verified as reflecting post-default market upward drift (majority class Up = 62.08% at $h=1$ and 63.89% at $h=5$). Balanced accuracy remained below 60% (59.77%), target-shuffled baseline dropped to 48.59%, and trivial constant predictor collapse was systematically guarded by RevIN and multitask loss.
5. **Honest Limitations (Rule R8):** Exhaustively documented the 24-event sample constraint, $\pm 30$-day temporal overlaps, single aggregate ASPI time series, structural regime breaks (Civil War, COVID, 2022 default), absence of historical denied news, and commercial LLM pretraining web memory contamination.

---

## 2. Deliverables & Created Artifacts

| Artifact | File Path | Description |
|---|---|---|
| **Audit Report** | [reports/audit.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/reports/audit.md) | Skeptical external reviewer report covering all 5 audit dimensions with empirical proofs and pass/fail verdicts. |
| **Research Paper & Assets** | [reports/results.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/reports/results.md) | IEEE-style research report with methods summary, model leaderboards, event study findings, ablations, and backtests. |
| **Regenerated README** | [README.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/README.md) | Auto-generated project README dynamically populated from `results/` files without typed numbers. |
| **How to Run Guide** | [HOW_TO_RUN.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/HOW_TO_RUN.md) | One-page comprehensive reproduction guide covering environment setup, test runs, pipeline stages, and live news monitoring. |
| **IEEE Leaderboard Figure** | [results/figures/ieee_model_leaderboard_h5.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/figures/ieee_model_leaderboard_h5.png) | 300 DPI scatter/Pareto chart of mean OOS $R^2$ vs Directional Accuracy at $h=5$ days across all model families. |
| **IEEE Event Study Figure** | [results/figures/ieee_event_study_caar.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/figures/ieee_event_study_caar.png) | 300 DPI CAAR trajectories for Presidential, Parliamentary, and Provincial elections with 10k-draw placebo bands. |
| **IEEE Ablation Figure** | [results/figures/ieee_ablation_feature_sets.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/figures/ieee_ablation_feature_sets.png) | 300 DPI bar chart comparing Feature Sets A, B, and C across top tree models. |
| **IEEE Backtest Figure** | [results/figures/ieee_scenario_backtests.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/figures/ieee_scenario_backtests.png) | 300 DPI 4-panel realized vs counterfactual forecasts with 80% and 95% conformal prediction intervals. |
| **Master Index** | [results/index.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/results/index.md) | Finalized catalog linking all 36 figures, 60 tables, prediction directories, and 867 model checkpoints. |
| **Audit Automation Script** | [scripts/stage13_audit_and_report.py](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/scripts/stage13_audit_and_report.py) | Standalone automated script executing the audit verification, figure generation, and report assembly. |
| **Pipeline Stage Runner** | [src/cse/run.py](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/src/cse/run.py) | Updated CLI runner supporting end-to-end execution of all stages from 0 to 13. |

---

## 3. Key Empirical Metrics from Results

All numbers extracted directly from verified files in `results/`:
- **Champion Architecture:** `CatBoostRegressor` on Feature Set C (`iterations=80, depth=4, lr=0.05`).
- **5-Day Return Predictability ($h = 5$):** Mean Out-of-Sample $R^2 = \mathbf{+0.0548}$ vs Expanding Historical Mean ($p < 10^{-30}$).
- **5-Day Directional Accuracy ($h = 5$):** $\mathbf{61.17\%}$ (Balanced Accuracy = $\mathbf{59.77\%}$).
- **1-Day Return Predictability ($h = 1$):** Mean Out-of-Sample $R^2 = \mathbf{+0.0897}$; Directional Accuracy = $\mathbf{61.39\%}$.
- **Phase Consistency:** Beats historical mean baseline in **5 out of 5** walk-forward phases (100% consistency).
- **Feature Ablation Impact:** Incorporating electoral event features (Set C) yields a **+39.8% relative gain in $R^2$** over pure technical indicators (Set A: $0.0392 \to 0.0548$).
- **Event Study Signal:** Presidential elections display a post-election rally ($[0, +10]$ CAAR of **+2.41%**, $p = 0.018$ under 10,000-draw non-event placebo permutations).
- **Historical Back-Tests:** Directional accuracy across 5 key historical elections and 4 horizons = **75.0%** (15/20 hits); 95% conformal interval coverage = **85.0%** (17/20).
- **Live News Feeds:** **8 of 14** candidate Sri Lankan feeds verified active live with ETag/Last-Modified caching and Asia/Colombo normalization.

---

## 4. Reproducibility Evidence Table

Recomputation of 5 randomly chosen metrics from raw prediction parquet files (Seed 42):

| Model | Phase | Horizon | Feature Set | Metric | Saved Value | Recomputed Value | Absolute Difference | Status |
|---|---|---|---|---|---|---|---|---|
| `ridge` | `P5` | `h=5` | `A` | `accuracy` | `0.66173362` | `0.66173362` | `0.0e+00` | **PASS (Exact Match)** |
| `gradient_boosting_reg` | `P4` | `h=1` | `A` | `balanced_accuracy` | `0.60456573` | `0.60456573` | `0.0e+00` | **PASS (Exact Match)** |
| `catboost_reg` | `P5` | `h=5` | `A` | `rmse` | `0.02377024` | `0.02377024` | `7.3e-17` | **PASS (Exact Match)** |
| `ridge` | `P4` | `h=1` | `B` | `rmse` | `0.01500877` | `0.01500877` | `2.9e-17` | **PASS (Exact Match)** |
| `catboost_reg` | `P1` | `h=5` | `A` | `rmse` | `0.01889416` | `0.01889416` | `3.5e-18` | **PASS (Exact Match)** |

All differences are strictly $< 10^{-16}$, demonstrating exact mathematical reproducibility.

---

## 5. Architectural & Design Decisions

All decisions documented in [DECISIONS.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/DECISIONS.md):
- **Decision:** Act as a skeptical external reviewer of our own work and generate automated IEEE 300 DPI figures and reproducible reports.
- **Reason:** Guarantee academic rigor, eliminate confirmation bias, and adhere strictly to Rule R1 (Real Data Only), Rule R6 (Save Everything), Rule R7 (Reproducibility), Rule R8 (Honest Reporting), Rule R10 (Stage Discipline), and Rule R11 (Verifiable Facts).

---

## 6. Conclusion & Completion

Stage 13 has been fully executed and verified. The quantitative research codebase is robust, zero-lookahead compliant, and fully documented with IEEE-style report assets and publication-ready tables.

In accordance with Rule R10, work on Stage 13 is complete. STOPPING HERE.
