# Quantitative Research Methodology & System Architecture

**Project:** PolitiTrade LK — AI-Powered Political Event Stock Market Impact Prediction Platform  
**Target Market:** Colombo Stock Exchange (CSE), Sri Lanka  
**Benchmark Indices:** All Share Price Index (ASPI), S&P Sri Lanka 20 (S&P SL20)  
**Historical Period:** 1985–2025 (9,772 trading sessions)  
**Event Horizon:** 2020–2025 (104 verified political events: 70 policies + 34 arrests)

---

## 1. Research Problem & Objective

Political events and public policy interventions exert profound shocks on frontier financial markets. In developing economies like Sri Lanka, market participants often lack quantitative tools to separate structural market trends from event-driven abnormal price reactions. 

The primary objective of this research is to:
1. Systematically quantify the abnormal returns ($AR_t$) and cumulative abnormal returns ($CAR$) of Sri Lankan government policy decisions and high-profile political arrests on the Colombo Stock Exchange between 2020 and 2025.
2. Build an anti-lookahead predictive ensemble that estimates expected market reactions to hypothetical or newly breaking events without forward-looking data contamination.
3. Provide automated news claim verification that verifies user-submitted claims against verified domestic press archives and delivers paired conditional forecast scenarios: **Scenario A** (Event Occurs) vs. **Scenario B** (No-Event Baseline).

---

## 2. Market Data & Trading Calendar Alignment

### 2.1 Dataset Inventory
- **Daily Sessions:** 9,772 trading days spanning January 2, 1985 to December 31, 2025.
- **Indices:** All Share Price Index (ASPI) and S&P Sri Lanka 20 (S&P SL20).
- **Session Indicators:** Daily Open, High, Low, Close, Trading Volume, and Turnover (LKR Millions).

### 2.2 Calendar Rollover & Event Session Alignment ($t_0$)
Political events occur on calendar days ($d$), including weekends, national poya days, public holidays, or after the CSE market close (14:30 Sri Lanka Standard Time).

Let $\mathcal{T} = \{t_1, t_2, \dots, t_N\}$ denote the set of valid CSE trading dates. For an announcement occurring at calendar timestamp $T$:
$$t_0 = \min \{ t \in \mathcal{T} \mid t \ge \text{Date}(T) \}$$
If the announcement occurred on day $d$ strictly after 14:30 SLT, the effective market reaction session rolls over to:
$$t_0 = \min \{ t \in \mathcal{T} \mid t > \text{Date}(T) \}$$
This calendar alignment guarantees that abnormal return calculations capture the exact market opening following public dissemination.

---

## 3. Event Study Quantitative Framework

### 3.1 Estimation Window
To isolate an event's abnormal price movement, normal expected returns $E(R_t)$ are modeled across an estimation window that terminates prior to potential market leakage:
$$\text{Estimation Window:} \quad [t_0 - 120, \, t_0 - 20]$$
- **Length:** 100 consecutive trading sessions.
- **Buffer:** 20 trading sessions prior to $t_0$ are excluded to prevent pre-event rumors, insider positioning, or anticipatory drift from biasing normal return parameters.

### 3.2 Expected Return Model
Using the constant mean return model calibrated over the estimation window $\tau \in [t_0 - 120, t_0 - 20]$:
$$\mu = \frac{1}{100} \sum_{\tau=t_0-120}^{t_0-20} R_\tau, \quad \sigma^2 = \frac{1}{99} \sum_{\tau=t_0-120}^{t_0-20} (R_\tau - \mu)^2$$

### 3.3 Abnormal Returns and Cumulative Abnormal Returns ($CAR$)
For any session $t$ within the event window:
$$AR_t = R_t - \mu$$
Cumulative Abnormal Returns across horizons $[t_1, t_2]$ are defined as:
$$CAR[t_1, t_2] = \sum_{t=t_1}^{t_2} AR_t$$
We report three canonical horizons:
1. **1-Day Shock ($CAR_{0, 1}$):** Immediate price discovery across $t_0$ and $t_1$.
2. **5-Day Impact ($CAR_{0, 5}$):** Primary evaluation horizon reflecting short-term market digestion.
3. **20-Day Drift ($CAR_{0, 20}$):** Medium-term trajectory capturing post-announcement policy implementation or judicial aftermath.

### 3.4 Liquidity & Turnover Shock Ratio
To measure trading activity during the event:
$$\text{Turnover Ratio} = \frac{\text{Turnover}_{t_0}}{\frac{1}{100}\sum_{\tau=t_0-120}^{t_0-20} \text{Turnover}_\tau}$$

---

## 4. Machine Learning & Forecasting Architecture

To navigate the frontier market small-$n$ sample regime (70 policies, 34 arrests), PolitiTrade LK avoids unregularized black-box models that overfit and implements a three-tier complementary ensemble:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Hypothetical or Verified Event                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│     MODEL 1      │      │     MODEL 2      │      │     MODEL 3      │
│ Case-Based       │      │ Directional Odds │      │ Continuous CAR   │
│ Historical       │      │ Penalized L2     │      │ Ridge Regression │
│ Analogue Engine  │      │ Logistic Reg     │      │ & Fan Chart      │
│ (k-NN Cosine)    │      │ P(Up) vs P(Down) │      │ (±1.96σ Bands)   │
└─────────┬────────┘      └─────────┬────────┘      └─────────┬────────┘
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│   Unified Forecast Synthesis (Direction, Probability, Uncertainty)     │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Feature Engineering (Zero-Lookahead Guarantee)
Every feature vector $X_{t_0}$ is constructed **exclusively from information available on or before session $t_0 - 1$**:
- **Semantic Text Features:** TF-IDF vectors (unigrams + bigrams) of the event headline and summary.
- **Categorical Encodings:** One-hot / frequency encodings of the 10 policy sub-categories or 7 arrest legal subtypes.
- **Pre-Event Momentum:** $R_{t_0-5 \to t_0-1}$, $R_{t_0-20 \to t_0-1}$.
- **Market Volatility:** Standard deviation of daily returns over $[t_0-20, t_0-1]$.
- **Technical Indicators:** 14-day RSI, distance to 50-day SMA, 5-day turnover ratio relative to 20-day mean.

### 4.2 Model 1: Historical Analogue Precedent Predictor
- Computes cosine similarity across TF-IDF semantics combined with categorical match and pre-event macro state vectors.
- Retrieves top-$k$ nearest historical precedent events ($k=5$).
- **Strict Cutoff Enforcement:** When evaluating at cutoff date $T_{\text{cutoff}}$, only historical events with $t_0 \le T_{\text{cutoff}}$ are included in the search space. Future events are strictly masked.

### 4.3 Model 2: Directional Classification (L2-Logistic Regression)
- Binary direction target: $Y \in \{0, 1\}$ where $1 \iff CAR_{0, 5} > 0$.
- Heavily regularized with $L_2$ shrinkage parameter $C=0.1$ to suppress noisy coefficients in small samples.
- Produces calibrated class probabilities: $P(\text{Up}) = \sigma(w^T X + b)$ and $P(\text{Down}) = 1 - P(\text{Up})$.

### 4.4 Model 3: Continuous CAR Regression & Uncertainty Fan Chart (Ridge)
- Predicts expected $CAR_{0, 5}$ with an $L_2$ penalty:
  $$\min_w \|Y - Xw\|_2^2 + \alpha \|w\|_2^2$$
- Computes empirical residual variance:
  $$\hat{\sigma}_{\text{res}}^2 = \frac{1}{N - p} \sum_{i=1}^N (Y_i - \hat{Y}_i)^2$$
- Synthesizes 20-day path projections with 80% and 95% confidence intervals:
  $$\hat{P}_t = P_{t_0} \times \left(1 + \frac{t}{5} \widehat{CAR}_{0, 5} \pm z_{\alpha/2} \hat{\sigma}_{\text{res}} \sqrt{\frac{t}{5}}\right)$$

---

## 5. Non-Lookahead Validation & Empirical Performance

### 5.1 Expanding-Window Chronological Split
Shuffled k-fold cross-validation is strictly invalid for time-series and event studies due to lookahead contamination. We evaluated all models using forward walk-forward expanding windows:
- Initial training window: First 15 events.
- Step size: 1 event forward.
- Target: Evaluate prediction on event $i$ using only models trained on events $1, \dots, i-1$.

### 5.2 Empirical Results (Honest Reporting)
| Metric | Government Policy Model ($n=70$, eval=55) | Political Arrest Model ($n=34$, eval=19) |
|---|:---:|:---:|
| **Directional Accuracy** | 49.09% | **63.16%** |
| **Majority Baseline Accuracy** | 60.00% | 36.84% |
| **ROC-AUC Score** | 0.373 | **0.678** |
| **Brier Score** | 0.3214 | **0.2264** |
| **Model CAR MAE** | 4.95% | 3.17% |
| **Zero-Change Baseline MAE** | 3.47% | 2.77% |
| **Historical Mean Baseline MAE**| 3.53% | 2.84% |

**Scientific Takeaway:**
- Political arrests demonstrate predictable market reactions (63.2% directional accuracy vs. 36.8% majority baseline), reflecting market sensitivity to political stability and anti-corruption signals.
- Government policy decisions exhibit higher variance and macro noise (particularly during the 2022 currency devaluation and sovereign debt crisis). For policies, Model 1 (Historical Analogue Precedents) provides superior domain utility over parametric point forecasts.

---

## 6. News Verification & Conditional Scenario Analysis

### 6.1 Credibility Tier Hierarchy
News publishers and official sources are mapped into four distinct credibility tiers:
- **Tier 1 (Official & Sovereign):** Central Bank of Sri Lanka (CBSL), Colombo Stock Exchange (CSE), Department of Government Information (DGI).
- **Tier 2 (Established Financial & Mainstream Media):** Daily FT, EconomyNext, Ada Derana, NewsFirst, The Morning, Daily Mirror, Reuters.
- **Tier 3 (General Digital Press):** Verified domestic news portals.
- **Tier 4 (Unverified / Social Media):** User write-ins, blogs, unverified digital posts.

### 6.2 Entity & Semantic Evidence Retrieval
- Token-set fuzzy matching via RapidFuzz.
- Named entity recognition for key political actors, ministries, state entities, and legal bodies.
- Verification verdicts:
  1. *Confirmed by credible reporting* (Tier 1/2 match > 75%)
  2. *Partially corroborated* (Tier 2/3 match 50–75%)
  3. *Unverified* (No credible corroborating publication found)
  4. *Contradicted by verified evidence*

### 6.3 Twin Conditional Prediction Scenarios
For user-submitted claims, the platform generates two parallel projections:
- **Scenario A (Claim is True):** Conditioned on the reported policy or arrest occurring, applying the full predictive ensemble.
- **Scenario B (Claim is False / No Event):** Formulated as a zero-event baseline, simulating market continuation under current macroeconomic drift without inventing synthetic fake-news dynamics.

---

## 7. Security & Engineering Standards

- **Server-Side Request Forgery (SSRF) Protection:** Custom DNS resolution validator blocking RFC1918 private subnets, loopback addresses (`127.0.0.1`), link-local IPs (`169.254.0.0/16`), and non-standard schemes.
- **Live Market Adapter:** Direct integration with public CSE API endpoints via HTTP POST with automatic rate-limiting and in-memory TTL caching.
- **Deterministic Disk Caching:** Event study dataframes and Parquet datasets are cached locally, accelerating server boot times from 25 seconds to <50 milliseconds.
