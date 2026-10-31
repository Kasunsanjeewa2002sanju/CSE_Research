import sys
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

from backend.app.ml.train import ModelTrainer

def main():
    print("==================================================")
    print("POLITITRADE LK — TRAINING & EVALUATING ML MODELS")
    print("==================================================")
    
    trainer = ModelTrainer()
    results = trainer.train_all_models()
    
    docs_dir = base_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    p_eval = results["models"]["government_policy"]["eval_metrics"]
    a_eval = results["models"]["political_arrest"]["eval_metrics"]
    
    model_eval_md = f"""# PolitiTrade LK — Machine Learning Model Evaluation Report

Generated: {results["evaluated_at"]}

## 1. Methodology & Validation Philosophy

Given the empirical dataset constraints (70 government policy changes, 34 political arrest events), PolitiTrade LK implements a **strict chronological expanding-window validation** design:
1. **Zero Future Data Leakage:** Models are evaluated sequentially on out-of-sample forward observations. No future prices, labels, or event indicators enter training windows.
2. **Tri-Model Ensemble Architecture:**
   - **Model 1: Historical Analogue Predictor (Primary):** Explainable case-based reasoning matching closest historical precedents with similar taxonomy, text semantics, and market volatility.
   - **Model 2: L2-Regularized Logistic Regression:** Calibrated probability estimation for positive vs. negative abnormal return direction.
   - **Model 3: Ridge Regression:** Continuous magnitude prediction for Cumulative Abnormal Returns (CAR).
   - **Model 4: Empirical Uncertainty Intervals:** $\\pm 1.96 \\times \\text{{Residual Std}}$ providing calibrated prediction intervals.

---

## 2. Chronological Expanding-Window Results

### A. Government Policy Model (`policy_model.joblib`)
- **Total Historical Sample Size:** {results["models"]["government_policy"]["sample_size"]} events
- **Forward-Chaining Evaluation Samples:** {p_eval["eval_sample_count"]}
- **Classification Metrics (Positive vs. Negative CAR):**
  - Out-of-Sample Accuracy: **{p_eval["classification"]["accuracy"] * 100:.1f}%**
  - Balanced Accuracy: **{p_eval["classification"]["balanced_accuracy"] * 100:.1f}%**
  - ROC-AUC: **{p_eval["classification"]["roc_auc"]:.3f}**
  - Brier Score: **{p_eval["classification"]["brier_score"]:.3f}**
  - Majority Class Baseline Accuracy: **{p_eval["classification"]["majority_baseline_accuracy"] * 100:.1f}%**
- **Continuous Return Regression (5-Day CAR):**
  - Model Mean Absolute Error (MAE): **{p_eval["regression"]["mae_model_pct"]:.2f}%**
  - Historical Mean Baseline MAE: **{p_eval["regression"]["mae_mean_baseline_pct"]:.2f}%**
  - Zero-Return Baseline MAE: **{p_eval["regression"]["mae_zero_baseline_pct"]:.2f}%**

### B. Political Arrest Model (`arrest_model.joblib`)
- **Total Historical Sample Size:** {results["models"]["political_arrest"]["sample_size"]} events
- **Forward-Chaining Evaluation Samples:** {a_eval["eval_sample_count"]}
- **Classification Metrics (Positive vs. Negative CAR):**
  - Out-of-Sample Accuracy: **{a_eval["classification"]["accuracy"] * 100:.1f}%**
  - Balanced Accuracy: **{a_eval["classification"]["balanced_accuracy"] * 100:.1f}%**
  - ROC-AUC: **{a_eval["classification"]["roc_auc"]:.3f}**
  - Brier Score: **{a_eval["classification"]["brier_score"]:.3f}**
  - Majority Class Baseline Accuracy: **{a_eval["classification"]["majority_baseline_accuracy"] * 100:.1f}%**
- **Continuous Return Regression (5-Day CAR):**
  - Model Mean Absolute Error (MAE): **{a_eval["regression"]["mae_model_pct"]:.2f}%**
  - Historical Mean Baseline MAE: **{a_eval["regression"]["mae_mean_baseline_pct"]:.2f}%**
  - Zero-Return Baseline MAE: **{a_eval["regression"]["mae_zero_baseline_pct"]:.2f}%**

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
"""
    
    with open(docs_dir / "MODEL_EVALUATION.md", "w", encoding="utf-8") as f:
        f.write(model_eval_md)
        
    print("\n[OK] Trained models and generated docs/MODEL_EVALUATION.md successfully.")

if __name__ == "__main__":
    main()
