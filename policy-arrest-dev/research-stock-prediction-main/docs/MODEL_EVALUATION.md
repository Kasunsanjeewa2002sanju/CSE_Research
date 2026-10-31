# PolitiTrade LK — Machine Learning Model Evaluation Report

Generated: 2026-10-19 21:52:06

## 1. Methodology & Validation Philosophy

Given the empirical dataset constraints (70 government policy changes, 34 political arrest events), PolitiTrade LK implements a **strict chronological expanding-window validation** design:
1. **Zero Future Data Leakage:** Models are evaluated sequentially on out-of-sample forward observations. No future prices, labels, or event indicators enter training windows.
2. **Tri-Model Ensemble Architecture:**
   - **Model 1: Historical Analogue Predictor (Primary):** Explainable case-based reasoning matching closest historical precedents with similar taxonomy, text semantics, and market volatility.
   - **Model 2: L2-Regularized Logistic Regression:** Calibrated probability estimation for positive vs. negative abnormal return direction.
   - **Model 3: Ridge Regression:** Continuous magnitude prediction for Cumulative Abnormal Returns (CAR).
   - **Model 4: Empirical Uncertainty Intervals:** $\pm 1.96 \times \text{Residual Std}$ providing calibrated prediction intervals.

---

## 2. Chronological Expanding-Window Results

### A. Government Policy Model (`policy_model.joblib`)
- **Total Historical Sample Size:** 70 events
- **Forward-Chaining Evaluation Samples:** 55
- **Classification Metrics (Positive vs. Negative CAR):**
  - Out-of-Sample Accuracy: **49.1%**
  - Balanced Accuracy: **43.9%**
  - ROC-AUC: **0.409**
  - Brier Score: **0.340**
  - Majority Class Baseline Accuracy: **60.0%**
- **Continuous Return Regression (5-Day CAR):**
  - Model Mean Absolute Error (MAE): **5.39%**
  - Historical Mean Baseline MAE: **3.53%**
  - Zero-Return Baseline MAE: **3.47%**

### B. Political Arrest Model (`arrest_model.joblib`)
- **Total Historical Sample Size:** 34 events
- **Forward-Chaining Evaluation Samples:** 19
- **Classification Metrics (Positive vs. Negative CAR):**
  - Out-of-Sample Accuracy: **57.9%**
  - Balanced Accuracy: **58.3%**
  - ROC-AUC: **0.589**
  - Brier Score: **0.256**
  - Majority Class Baseline Accuracy: **36.8%**
- **Continuous Return Regression (5-Day CAR):**
  - Model Mean Absolute Error (MAE): **3.64%**
  - Historical Mean Baseline MAE: **2.84%**
  - Zero-Return Baseline MAE: **2.77%**

---

## 3. Confidence Level Formulation

Model confidence ratings (**Low**, **Medium**, **High**) are not assigned based on arbitrary softmax probabilities. Instead, confidence is calculated dynamically from:
1. **Analogue Proximity:** Maximum similarity score among top historical analogues ($>75\%$ = boost, $<50\%$ = low).
2. **Sample Size & Subtype Representation:** Number of previous events sharing the specific subcategory.
3. **Macroeconomic Volatility:** Highly volatile market regimes (e.g. 2022 debt crisis) widen prediction intervals and degrade confidence.

---

## 4. Scientific Limitations & Cautionary Guidance

- **Correlation vs. Causation:** Stock reactions after political events do not prove monocausal impact.
- **Sample Size:** 104 events over 25 years reflect real historical rarity of political shocks in Sri Lanka.
- **Misinformation Baseline:** Scenario B (if event does not occur) is strictly formulated as a **no-event market baseline**, not an invented misinformation model.
