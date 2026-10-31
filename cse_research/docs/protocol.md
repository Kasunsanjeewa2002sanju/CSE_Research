# Cross-Validation Protocol & Shared Evaluation Harness

**Research Project:** Predicting Stock Market Movements Using Political News Categories (SLIIT, Sri Lanka)  
**Permanent Rules Applied:** R1 (Real data only), R2 (No lookahead), R3 (Suspicious results rule: direction > 60% or OOS $R^2 > 0.10$ triggers leakage alarm), R4 (Models predict log returns), R5 (Uniform protocol for all models), R7 (Reproducibility), R10 (Stage discipline).

---

## 1. Five Expanding-Window Walk-Forward Validation Phases

To reflect realistic out-of-sample deployment without lookahead bias and align with the university research proposal's 2009–2025 focus, we define five chronological phases. Each phase expands the historical training history and tests on an untouched, future validation block:

| Phase | Training Window (Dates) | Embargo Window (10 Trading Days) | Validation Block (Dates) | Train Days ($N$) | Val Days ($N$) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **P1** | 1994-01-03 to 2011-12-15 | 2011-12-16 to 2011-12-30 | 2012-01-02 to 2014-12-31 | 4,299 | 725 |
| **P2** | 1994-01-03 to 2014-12-16 | 2014-12-17 to 2014-12-31 | 2015-01-02 to 2017-12-29 | 5,024 | 720 |
| **P3** | 1994-01-03 to 2017-12-14 | 2017-12-15 to 2017-12-29 | 2018-01-02 to 2020-12-31 | 5,744 | 690 |
| **P4** | 1994-01-03 to 2020-12-15 | 2020-12-16 to 2020-12-31 | 2021-01-04 to 2023-12-29 | 6,434 | 713 |
| **P5** | 1994-01-03 to 2023-12-13 | 2023-12-14 to 2023-12-29 | 2024-01-02 to 2025-12-31 | 7,147 | 478 |
| **TOTAL** | — | — | **2012-01-02 to 2025-12-31** | — | **3,326** |

### Embargo Gap (Rule R2):
- An embargo gap of exactly **10 trading days** is enforced between the end of each training window and the start of validation.
- Since our maximum forecasting horizon is $h=5$ trading days, a 10-trading-day embargo strictly prevents any forward-looking target overlap or auto-regressive state leakage into the validation window.

---

## 2. Hyperparameter Tuning Protocol (Inner Chronological Split)

- **Mandatory Constraint:** The validation block ($t \in \text{val}$) is strictly held out and **never** used for hyperparameter selection, threshold tuning, or model selection.
- Inside each training window, an **inner chronological split** is established:
  - **Inner Validation Set:** The chronologically final **15%** of the training window.
  - **Inner Embargo:** Exactly 10 trading days preceding the inner validation set.
  - **Inner Training Set:** The remaining early $\approx 85\%$ of the training window.
- All scalers, encoders, and feature imputers are fitted **only** on the training set (or inner training set) and never see validation data.

---

## 3. Forecasting Horizons & Target Formulations

Models predict log returns (Rule R4); index levels are reconstructed post-prediction:

1. **Horizon $h=1$ Trading Day (Next-Day Return)**:
   $$y_{ret, t}^{(1)} = \ln\left(\frac{\text{ASPI}_{t+1}}{\text{ASPI}_t}\right), \quad y_{dir, t}^{(1)} = \mathbb{I}\left(y_{ret, t}^{(1)} > 0\right)$$
2. **Horizon $h=5$ Trading Days (Weekly Return, matching proposal)**:
   $$y_{ret, t}^{(5)} = \ln\left(\frac{\text{ASPI}_{t+5}}{\text{ASPI}_t}\right), \quad y_{dir, t}^{(5)} = \mathbb{I}\left(y_{ret, t}^{(5)} > 0\right)$$
3. **Reconstructed ASPI Level**:
   $$\widehat{\text{ASPI}}_{t+h} = \text{ASPI}_t \cdot \exp\left(\hat{y}_{ret, t}^{(h)}\right)$$

### Overlapping vs. Non-Overlapping Weekly Evaluation:
Because 5-day returns sampled daily share 4 days of overlapping price changes:
- Primary evaluation is conducted on all daily evaluation points ($t \in \text{val}$) using Newey-West / HAC standard errors (lag bandwidth $q = h-1 = 4$).
- Secondary robustness evaluation is conducted on **non-overlapping weekly samples** (every 5th trading day).

---

## 4. Execution Protocol for Every Model (Uniform Protocol, Rule R5)

1. **Model Fitting**: Fit the model parameters $\theta$ once on the training window $[0, t_{train\_end}]$.
2. **Out-of-Sample Stepping**: For each day $t \in [t_{val\_start}, t_{val\_end}]$, the model generates a forecast $\hat{y}_{ret, t}^{(h)}$ using only information available at the close of day $t$.
3. **Parameter Stability**: Model parameters remain fixed during out-of-sample stepping; feature inputs and lag states advance dynamically with observed data.
4. **Sensitivity Refit Protocol (Optional)**: An optional sensitivity protocol allows refitting parameters every 63 trading days (approx. quarterly) across the validation window.

---

## 5. Model Selection Decision Rule

To be designated as the superior model for a given horizon, a candidate model must satisfy the following hierarchical criteria:

1. **Primary Metric**:
   - Out-of-sample $R^2$ ($R^2_{OOS}$) on the **5-day log return ($h=5$)** evaluated against the expanding historical mean benchmark:
     $$R^2_{OOS} = 1 - \frac{\sum (y_{true} - \hat{y}_{pred})^2}{\sum (y_{true} - \bar{y}_{hist})^2} > 0$$
   - AND Diebold-Mariano test with Harvey-Leybourne-Newbold (HLN 1997) correction versus the random walk benchmark must be statistically significant at $p < 0.05$.
2. **Secondary Metric**:
   - Balanced Directional Accuracy ($\frac{\text{TPR} + \text{TNR}}{2}$).
3. **Phase Consistency**:
   - A model must beat the baselines in **at least 3 out of 5 phases** ($60\%$ phase stability).
4. **Tie-Breaker**:
   - Parity or ties are strictly resolved by **model simplicity** (fewer parameters, simpler structural inductive bias, lower inference complexity).
5. **Suspicious Result Circuit Breaker (Rule R3)**:
   - Any model producing daily/weekly directional accuracy $> 60\%$ or $R^2_{OOS} > 0.10$ is flagged as a potential leakage bug. Training immediately halts and leakage diagnostics are executed.

---

## 6. Prediction File Schema

Every model prediction file is saved as both Parquet and CSV:  
Path: `results/predictions/<family>/<model>_<phase>_h<horizon>.parquet`

| Field | Type | Description |
|:---|:---:|:---|
| `model` | String | Model identifier (e.g. `historical_mean`, `ridge`, `lstm`) |
| `family` | String | Model category (`baseline`, `shallow`, `deep`, `foundation`) |
| `phase` | String | Validation phase (`P1`, `P2`, `P3`, `P4`, `P5`) |
| `horizon` | Integer | Prediction horizon in trading days ($1$ or $5$) |
| `feature_set` | String | Feature set used (`none`, `univariate`, `macro_events`) |
| `date` | String | Forecast origin date $t$ (`YYYY-MM-DD`) |
| `y_true_ret` | Float | Actual realized forward log return $r_{t, t+h}$ |
| `y_pred_ret` | Float | Model predicted log return $\hat{r}_{t, t+h}$ |
| `p_up` | Float (Nullable) | Predicted probability of positive return $\Pr(y > 0)$ |
| `y_true_dir` | Integer | Realized direction: 1 if $y_{true\_ret} > 0$ else 0 |
| `y_pred_dir` | Integer | Predicted direction: 1 if $y_{pred\_ret} > 0$ (or $p_{up} > 0.5$) else 0 |
| `aspi_t` | Float | Actual ASPI index closing level at date $t$ |
| `aspi_pred_level` | Float | Reconstructed ASPI forecast level: $\text{ASPI}_t \cdot \exp(\hat{y}_{pred\_ret})$ |
| `seed` | Integer | Random seed used for model initialization |

---

## 7. Model Artifact Standard

Trained model artifacts are stored systematically:  
Path: `models/<family>/<model>/<phase>/`
- `model.pkl` / `weights.pt` / `model.json`: Serialized fitted model artifact.
- `meta.json`:
  ```json
  {
    "model": "historical_mean",
    "family": "baseline",
    "phase": "P1",
    "horizon": 5,
    "seed": 42,
    "train_date_range": ["1994-01-03", "2011-12-15"],
    "embargo_date_range": ["2011-12-16", "2011-12-30"],
    "val_date_range": ["2012-01-02", "2014-12-31"],
    "embargo_days": 10,
    "feature_set": "none",
    "raw_data_hash": "a9965aea016faf7cdd5836ac440818f082550906714cb82034c7f661be202c74",
    "library_versions": {
      "numpy": "2.4.6",
      "pandas": "3.0.6",
      "scipy": "1.17.1",
      "statsmodels": "0.15.0"
    },
    "runtime_seconds": 0.045,
    "hardware": {
      "device_type": "cpu",
      "device_name": "CPU"
    },
    "prediction_file": "results/predictions/baseline/historical_mean_P1_h5.parquet"
  }
  ```
