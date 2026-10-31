# Stage 8 Model Comparison & Promotion Review

- **Candidate Model**: `candidate_20261022.cbm`
- **Frozen Model**: `scenario_models.pkl` (Protected - Read Only)
- **Evaluation Period**: Split `test` (N = 102 news events)
- **Report Date**: 2026-10-22 15:50:14
- **Final Decision**: **DO NOT PROMOTE (STAGING ONLY)**

---

## 1. Promotion Gate Evaluation

| Criterion | Requirement | Candidate Result | Gate Status |
|:---|:---:|:---:|:---:|
| **MAE Reduction** | Candidate beats Frozen by **> 5.0%** | **+0.12%** | **FAILED** |
| **Event Feature Share** | Event + Sentiment importance **> 25.0%** | **0.21%** | **FAILED** |

> **Decision Summary**:  
> Candidate model did not satisfy all promotion gates: MAE reduction was 0.12% (required: >5.0%); Event feature importance was 0.21% (required: >25.0%).

---

## 2. Comparative Performance Metrics

| Metric | Frozen Model (57 feats) | Candidate Model (60 feats) | Delta (Improvement) |
|:---|:---:|:---:|:---:|
| **Mean Absolute Error (MAE)** | `0.0224` | `0.0224` | `+0.12%` |
| **Root Mean Squared Error (RMSE)** | `0.0301` | `0.0295` | `+2.12%` |
| **Information Coefficient (IC / r)** | `+0.1413` | `-0.0262` | `-0.1675` |
| **Directional Hit Rate** | `52.0%` | `54.9%` | `+2.9%` |
| **Prediction Diversity (Std Dev)** | `0.0071` | `0.0010` | `-85.54%` |

---

## 3. Feature Importance & News Sensitivity

- **Frozen Model Event Feature Share**: `13.08%`
- **Candidate Model Event Feature Share**: `0.21%`
  * Includes FinBERT Sentiment Share: `0.21%`

### Top 10 Features Comparison

| Rank | Frozen Model Top Features | Candidate Model Top Features | Candidate Category |
|:---:|:---|:---|:---:|
| #1 | `ret_1d` (10.3%) | `shares_zscore_60d` (34.0%) | **Technical** |
| #2 | `ret_vol_20d` (9.1%) | `cal_month` (14.2%) | **Technical** |
| #3 | `ret_2d` (5.8%) | `ret_lag_5` (14.0%) | **Technical** |
| #4 | `dist_from_sma_20` (5.7%) | `ret_mean_20d` (11.6%) | **Technical** |
| #5 | `ret_mean_5d` (5.6%) | `ret_2d` (11.0%) | **Technical** |
| #6 | `ret_mean_20d` (5.5%) | `ret_lag_2` (10.4%) | **Technical** |
| #7 | `days_to_next_known_event` (4.8%) | `turnover_log_change_1d` (4.5%) | **Technical** |
| #8 | `macd_hist` (4.6%) | `sentiment_positive` (0.2%) | **Sentiment** |
| #9 | `ret_mean_10d` (4.2%) | `ret_1d` (0.0%) | **Technical** |
| #10 | `ret_vol_10d` (4.1%) | `ret_3d` (0.0%) | **Technical** |

---

## 4. Operational Safety Invariant

> [!IMPORTANT]
> **Frozen Model Preservation**:  
> The frozen production model at `models/final/scenario_models.pkl` was **NOT modified** during this evaluation.
> Stage 8 is an isolated staging area. Any promotion to production requires deliberate operator approval.
