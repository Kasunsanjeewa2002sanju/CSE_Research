# Stage F7 Implementation Report: The Model Lab

**Project:** Sri Lankan Political Events & Colombo Stock Exchange (CSE) ASPI Econometric Platform  
**Stage:** F7 — The Model Lab (`/models`, `/models/:id`, `/models/compare`, `/models/statistics`, `/models/final`)  
**Date:** October 16, 2026  
**Status:** Completed & Fully Verified  
**Compliance:** Strict adherence to permanent rules **FR1–FR11** (see [frontend/RULES.md](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/RULES.md))

---

## 1. Executive Summary

Stage F7 delivers the comprehensive **Model Lab** analytical suite spanning five interconnected routes:
1. **Leaderboard (`/models`):** Full multi-phase econometric benchmark ranking table with mean $\pm$ standard deviation, family/horizon/feature set filters, CSV export, and 5 interactive summary diagnostic plots (Bar error plot, Phase $\times$ Model heatmap, Directional accuracy dot plot with 50% coin-flip line, Out-of-Sample $R^2$ dot plot with 0 line, and Accuracy vs. Runtime scatter). Features prominent display of the API's baseline superiority declaration when reference baselines are unbested.
2. **Model Detail (`/models/:id`):** Deep-dive diagnostic dashboard for any selected candidate model, reporting hyperparameters, training data range ($N=7,635$), seed, hardware execution telemetry, per-phase forecast vs. actual trajectory with shaded validation blocks and 95% forecast intervals, cumulative error curves, residual histogram and normal QQ plot, feature importance (tree architectures) or epoch loss curves (deep architectures), directional confusion matrix, and cryptographic SHA-256 verified downloadable artifacts.
3. **Compare (`/models/compare`):** Multi-model evaluation workbench allowing side-by-side comparison of up to 4 concurrent candidate models across metrics, overlaid return forecasts, and 5-phase stability profiles.
4. **Statistics (`/models/statistics`):** Advanced inferential econometrics dashboard presenting pairwise Diebold-Mariano (1995) test p-value heatmaps with Harvey-Leybourne-Newbold (1997) finite-sample adjustments, Hansen, Lunde & Nason (2011) Model Confidence Set (MCS) membership at $\alpha = 0.10$ and $\alpha = 0.05$, Feature Set ablation comparisons (Sets A vs. B vs. C) with paired 95% confidence intervals, and event-window vs. non-event-window sample size ($n$) performance analysis.
5. **Final Champion Model Card (`/models/final`):** Production model card for the pre-registered winning specification (`ridge_regressor_h1_set_a`), complete with 5-tier pre-registered decision trace hierarchy, explicit econometric caveats and limitations, and training data boundary audit.

All data is dynamically supplied by verified backend endpoints in `cse_research/src/cse/api/models.py` (`/models/leaderboard`, `/models/detail`, `/models/compare`, `/models/statistics`, `/models/final`, `/models/artifacts`) and validated at the boundary via strict Zod schemas (`modelLeaderboardResponseSchema`, `modelDetailResponseSchema`, `modelCompareResponseSchema`, `modelStatisticsResponseSchema`, `finalModelResponseSchema`). In full accordance with **Rule FR1** and **Rule FR3**, zero mock fixtures or hardcoded domain values exist in `src/`.

---

## 2. Component Architecture & Modular Design

All components adhere strictly to **Rule FR8** (no file exceeding 300 lines of code):

| Component | Lines | Responsibility & Econometric Features |
|---|---|---|
| [ModelLabNav.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelLabNav.tsx) | 81 | Sub-navigation bar across all 5 Model Lab views with live candidate count badge and responsive scroll wrapper |
| [LeaderboardCharts.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/LeaderboardCharts.tsx) | 163 | Chart tab container, baseline superiority alert banner using raw API copy, and accessible data table view toggle |
| [LeaderboardChartPlots.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/LeaderboardChartPlots.tsx) | 279 | 5 ECharts options renderers: (a) Metric error bars ($\pm 1$ SD), (b) Phase $\times$ Model heatmap, (c) Direction accuracy dot plot with 50% line and 95% Wilson CI, (d) OOS $R^2$ dot plot with 0 line, (e) Accuracy vs. Runtime scatter |
| [LeaderboardFilters.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/LeaderboardFilters.tsx) | 160 | Filter controls for Model Family, Horizon ($h=1, 5$), Feature Set (A, B, C), Metric, Significance-only toggle, and RFC-4180 CSV export |
| [LeaderboardTable.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/LeaderboardTable.tsx) | 244 | Sortable multi-phase performance table displaying mean $\pm$ SD across phases, baseline row highlights, champion trophy, and FDR significance badges |
| [ModelDetailForecast.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelDetailForecast.tsx) | 259 | Model metadata header cards (range, seed, hardware, runtime), hyperparameter list, forecast vs. actual chart with shaded validation blocks, and cumulative error curves |
| [ModelDetailDiagnostics.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelDetailDiagnostics.tsx) | 262 | Error residual histogram with normal fit, normal QQ plot, directional confusion matrix ($2 \times 2$), feature importance/epoch curves, and verified artifact downloads |
| [ModelCompareView.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelCompareView.tsx) | 257 | Up to 4 models selector chips, side-by-side metric comparison table, multi-model forecast overlay chart, and 5-phase stability bar chart |
| [ModelStatisticsView.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelStatisticsView.tsx) | 260 | Pairwise Diebold-Mariano p-value heatmap matrix, Hansen MCS membership card, Feature Set ablation comparison chart (A vs. B vs. C), and event-window ablation table |
| [FinalModelCard.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/FinalModelCard.tsx) | 263 | Official champion model card, 5-tier pre-registered decision trace hierarchy, training data coverage ($N=7,635$), caveats, and documentation explorer |

---

## 3. Five Dedicated Model Lab Routes

### 3.1 Leaderboard (`/models`)
- **Page Component:** [ModelLeaderboardPage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/ModelLeaderboardPage.tsx) (105 lines)
- **Filters & Interactive Exploration:**
  - *Model Family:* All, Statistical, Shallow Machine Learning, Deep Neural Networks, Foundation / LLM, Hybrid Ensembles.
  - *Forecast Horizon:* $h=1$ day, $h=5$ days.
  - *Feature Set:* Set A (24 price/technical), Set B (34 market activity), Set C (57 causal event).
  - *Primary Metric Selection:* Out-of-Sample $R^2$ ($R^2_{OOS}$), Directional Accuracy (DA), Root Mean Squared Error (RMSE), Mean Absolute Error (MAE).
  - *FDR Filter:* Toggle to isolate models passing multiple testing correction (`Benjamini-Hochberg FDR q < 0.05`).
  - *CSV Export:* Fully client-side formatted export of all multi-phase statistics.
- **Summary Diagnostic Charts:**
  1. *Bar Chart with Error Bars:* Displays model performance sorted by selected metric with $\pm 1$ standard deviation error bars across the 5 evaluation phases.
  2. *Phase $\times$ Model Heatmap:* Visualizes phase-by-phase performance variations across walk-forward splits $P1$ through $P5$.
  3. *Directional Accuracy Dot Plot:* Dot plot with 95% Wilson score confidence intervals and a prominent 50% coin-flip reference line.
  4. *Out-of-Sample $R^2$ Dot Plot:* Dot plot displaying $R^2_{OOS}$ relative to the zero reference line (the Campbell-Thompson benchmark showing outperformance over prevailing mean).
  5. *Accuracy vs. Training Time Scatter:* Bubble scatter plot plotting directional accuracy against runtime in seconds with family color coding.
- **Prominent Baseline Superiority Banner:** When the backend indicates no candidate model demonstrates statistically significant outperformance over the benchmark, the exact text from the API (`api_response.baseline_comparison_message`) is displayed in a prominent amber callout banner.

### 3.2 Model Detail (`/models/:id`)
- **Page Component:** [ModelDetailPage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/ModelDetailPage.tsx) (130 lines)
- **Deep Model Inspection:**
  - *Hardware & Environment Telemetry:* Hardware architecture (`NVIDIA RTX A6000`, `AMD EPYC 7763`), random seed (42), peak VRAM/RAM allocation, and total training runtime.
  - *Hyperparameters Table:* Searchable grid displaying exact tuning parameters (e.g., `alpha=100.0`, `solver=saga`, `tol=0.0001`).
  - *Per-Phase Forecast vs. Actual Chart:* Historical actual returns alongside out-of-sample model predictions, with shaded validation windows and 95% forecast interval bands.
  - *Cumulative Error Trajectory:* Running cumulative MAE and RMSE over out-of-sample trading days.
  - *Residual Diagnostics:* Residual frequency histogram overlaid with theoretical Gaussian normal density curve, plus Normal QQ plot (empirical vs. theoretical standard quantiles).
  - *Architecture Specific Diagnostics:* Gini feature importance bar chart for tree-based models (`xgboost_regressor_h1_set_b`, `random_forest_regressor_h1_set_b`) or epoch training/validation loss curves for deep learning architectures (`lstm_regressor_h1_set_a`, `temporal_fusion_transformer_h1_set_c`).
  - *Directional Confusion Matrix:* $2 \times 2$ classification matrix (Up/Down predicted vs. actual) with derived Accuracy, Precision, Recall, and F1 score.
  - *Downloadable Artifacts:* Cryptographically verified downloads for model checkpoints (`.joblib`, `.pt`), ONNX graphs, feature scalers, and metric JSON files with SHA-256 integrity checksums.

### 3.3 Model Comparison (`/models/compare`)
- **Page Component:** [ModelComparePage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/ModelComparePage.tsx) (122 lines)
- **Side-by-Side Multi-Model Evaluation:**
  - Multi-select chip controls to evaluate up to 4 models concurrently.
  - Comprehensive metrics comparison matrix (OOS $R^2$, Directional Accuracy, MAE, RMSE, Runtime, Total Parameters).
  - Multi-series forecast overlay chart rendering synchronized out-of-sample predictions against Colombo Stock Exchange benchmark returns.
  - 5-Phase stability analysis bar chart highlighting cross-regime robustness and variance across historical market shocks (1994–2025).

### 3.4 Econometric Hypothesis Testing & Statistics (`/models/statistics`)
- **Page Component:** [ModelStatisticsPage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/ModelStatisticsPage.tsx) (93 lines)
- **Rigorous Hypothesis Testing:**
  - *Diebold-Mariano (1995) Matrix:* Pairwise p-value heatmap with Harvey-Leybourne-Newbold (1997) finite-sample adjustments testing null hypothesis of equal predictive accuracy.
  - *Hansen Model Confidence Set (MCS):* Displays models included in the superior set $\widehat{\mathcal{M}}^*_{90\%}$ and $\widehat{\mathcal{M}}^*_{95\%}$ based on block-bootstrapped loss differentials.
  - *Feature Set Ablation Chart:* Bar and whisker visualization contrasting Set A (price only), Set B (price + volume), and Set C (price + volume + event features) with paired 95% confidence intervals.
  - *Event-Window vs. Non-Event-Window Performance:* Econometric performance breakdown inside vs. outside political event windows, complete with exact sample sizes ($n_{\text{inside}}=412$, $n_{\text{outside}}=7,223$).

### 3.5 Champion Model Card (`/models/final`)
- **Page Component:** [FinalModelPage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/FinalModelPage.tsx) (95 lines)
- **Pre-Registered Selection Decision Trace:**
  - Hero banner announcing the official pre-registered production model: **L2 Regularized Ridge Regressor ($h=1$, Feature Set A)**.
  - Step-by-step visual decision hierarchy illustrating why this specification was selected:
    1. *Tier 1: Multiple testing baseline beat:* No complex non-linear model survived Benjamini-Hochberg FDR correction.
    2. *Tier 2: Non-negative Out-of-Sample $R^2$:* Linear models maintained $R^2_{OOS} \ge 0$, whereas deep networks exhibited overparameterized negative $R^2$ in small-sample emerging market regimes.
    3. *Tier 3: Directional Accuracy:* Maintained the highest cross-phase stability (51.8% $\pm 1.4\%$).
    4. *Tier 4: Model Parsimony:* Lowest Bayesian Information Criterion (BIC) and parameter count (24 coefficients vs. 150,000+ deep network weights).
    5. *Tier 5: Operational Runtime:* 1.2s training latency ensuring instant daily retraining.
  - *Training Boundary Audit:* Complete sample summary ($N=7,635$ trading days, January 1994 to December 2025).
  - *Explicit Caveats & Limitations:* Full list of academic constraints provided by the API (small-sample liquidity regime shifts, currency devaluations, price bands).

---

## 4. Visual Verification & Responsive Breakpoints

Visual presentation has been verified across all target viewports using the local browser engine and saved to `frontend/docs/screenshots/`:

| Screenshot | Description | Viewport | Path |
|---|---|---|---|
| `models-leaderboard-1280.png` | Model Leaderboard: filters, summary charts (error bar, heatmap, dot plot, scatter), and full multi-phase table | 1280px (Desktop) | [models-leaderboard-1280.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/docs/screenshots/models-leaderboard-1280.png) |
| `models-detail-1280.png` | Model Detail: metadata cards, hyperparameters, forecast vs. actual with shaded validation, residuals, confusion matrix | 1280px (Desktop) | [models-detail-1280.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/docs/screenshots/models-detail-1280.png) |
| `models-compare-1280.png` | Model Compare: 4-model selection, side-by-side metric table, forecast overlay chart, phase stability bar plot | 1280px (Desktop) | [models-compare-1280.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/docs/screenshots/models-compare-1280.png) |
| `models-statistics-1280.png` | Model Statistics: Diebold-Mariano p-value heatmap, Hansen MCS membership, feature ablation with paired CI | 1280px (Desktop) | [models-statistics-1280.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/docs/screenshots/models-statistics-1280.png) |
| `models-final-1280.png` | Champion Model Card: hero card, 5-tier pre-registered decision trace hierarchy, limitations, and data range | 1280px (Desktop) | [models-final-1280.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/docs/screenshots/models-final-1280.png) |
| `models-768.png` | Tablet view: responsive horizontal navigation, adapted card grids, and touch-scrollable tables | 768px (Tablet) | [models-768.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/docs/screenshots/models-768.png) |
| `models-360.png` | Mobile view: stacked filter controls, compact metric summary cards, and responsive chart containers | 360px (Mobile) | [models-360.png](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/docs/screenshots/models-360.png) |

---

## 5. Chart Styling & Visual Standards

In strict accordance with the prompt guidelines and **Rule FR3 / Rule FR6**:
- **Consistent Family Color Palette:**
  - *Shallow ML (Ridge, Lasso, ElasticNet, RF, XGBoost):* Institutional Deep Navy (`#0A2A66`)
  - *Deep Learning (LSTM, GRU, TFT, MLP):* Vibrant Cyan / Teal (`#0095B3`)
  - *Statistical (ARIMA, GARCH, VAR):* Classic Academic Blue (`#3563C1`)
  - *Foundation / LLM (FinGPT, Llama-Finance):* Modern Violet (`#4F46E5`)
  - *Hybrid Ensembles (ARIMA-LSTM, Stacking):* Sky Blue (`#0284C7`)
  - *Reference Baselines (Historical Mean, Random Walk, Momentum):* Warm Amber (`#F59E0B`)
- **Strictly No Red/Green for Model Quality:**
  - Model evaluation avoids green/red judgment cues. Outperformance badges utilize institutional teal (`#0D9488`), baseline comparisons utilize neutral slate (`#64748B`), and warnings/unbested baselines utilize academic amber (`#D97706`).
  - Reference lines (50% direction accuracy, 0 Out-of-Sample $R^2$) are rendered in subtle dashed amber (`#F59E0B`) to provide neutral mathematical anchoring.

---

## 6. Test Suite, Hardcoding & Quality Verification

1. **Unit Test Suite (`vitest`):**
   - File: `frontend/tests/unit/stage-f7-model-lab.test.ts`
   - Total Tests: **12 test suites, 80 tests passing**.
   - Verification Areas:
     - Boundary validation of `modelLeaderboardResponseSchema`, `modelDetailResponseSchema`, `modelCompareResponseSchema`, `modelStatisticsResponseSchema`, and `finalModelResponseSchema`.
     - Filter reducers for model family, forecast horizon, feature set, and multiple testing significance.
     - Multiple testing correction naming verification (`Benjamini-Hochberg FDR q < 0.05`).
     - Mathematical Wilson score confidence interval computation.
     - Null baseline superiority warning banner rendering when baselines are unbested.
2. **Hardcoding & Mock Data Scanner (`check-hardcoding.ts`):**
   - Result: `[PASS] Zero hardcoded domain data or mock fixtures found in src/.`
   - Rule FR1 Adherence: All metrics, parameter values, hardware telemetry, model names, and decision explanations originate from the live API.
3. **TypeScript & Linter (`eslint`):**
   - Result: **0 errors, 0 warnings** with `--max-warnings 0`.
4. **Production Build (`tsc -b && vite build`):**
   - Result: Built cleanly in 25.31 seconds with optimized chunks and full source-map generation.

---

## 7. Deliverables Summary

- **Routes Mounted in [router.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/app/router.tsx):**
  - `/models` $\to$ [ModelLeaderboardPage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/ModelLeaderboardPage.tsx)
  - `/models/:id` $\to$ [ModelDetailPage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/ModelDetailPage.tsx)
  - `/models/compare` $\to$ [ModelComparePage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/ModelComparePage.tsx)
  - `/models/statistics` $\to$ [ModelStatisticsPage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/ModelStatisticsPage.tsx)
  - `/models/final` $\to$ [FinalModelPage.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/pages/FinalModelPage.tsx)
  - `/model-lab` $\to$ Redirect to `/models`
- **Components Created (all under 280 lines):**
  - [ModelLabNav.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelLabNav.tsx)
  - [LeaderboardCharts.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/LeaderboardCharts.tsx)
  - [LeaderboardChartPlots.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/LeaderboardChartPlots.tsx)
  - [LeaderboardFilters.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/LeaderboardFilters.tsx)
  - [LeaderboardTable.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/LeaderboardTable.tsx)
  - [ModelDetailForecast.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelDetailForecast.tsx)
  - [ModelDetailDiagnostics.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelDetailDiagnostics.tsx)
  - [ModelCompareView.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelCompareView.tsx)
  - [ModelStatisticsView.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/ModelStatisticsView.tsx)
  - [FinalModelCard.tsx](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/components/FinalModelCard.tsx)
- **Data Layer & Schemas:**
  - [zod-schemas.ts](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/api/zod-schemas.ts)
  - [types.ts](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/api/types.ts)
  - [useModelLab.ts](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/src/features/model-lab/hooks/useModelLab.ts)
- **Backend API Endpoints:**
  - [models.py](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/src/cse/api/models.py) (`/models/leaderboard`, `/models/detail`, `/models/compare`, `/models/statistics`, `/models/final`, `/models/artifacts`)
- **Unit Tests:**
  - [stage-f7-model-lab.test.ts](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/tests/unit/stage-f7-model-lab.test.ts)
- **Screenshots:**
  - [frontend/docs/screenshots/](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/frontend/docs/screenshots/)

---

## 8. Open Decisions & Stage Discipline

- In accordance with **Rule FR10**, Stage F7 is complete and fully verified.
- The next stage in sequence is **Stage F8: News & LLM Narrative (`/news`)**. Work will pause here awaiting user review and direction.
