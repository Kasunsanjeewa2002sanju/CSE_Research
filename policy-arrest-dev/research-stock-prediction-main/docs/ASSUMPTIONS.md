# System Assumptions & Quantitative Design Decisions

**Project:** PolitiTrade LK — Colombo Stock Exchange Political Event Impact Predictor  
**Author:** Research & Development Architecture Team  
**Date:** October 2026

---

## 1. Market Data & Calendar Assumptions

1. **Official Price Integrity:**
   - Historical daily index levels for the All Share Price Index (ASPI) and S&P Sri Lanka 20 (S&P SL20) are treated as definitive when sourced from the Colombo Stock Exchange official daily statistics reports (`07Market Indices - Daily.xls` and `11Market Statistics-Daily.xls`).
   - Where historical closing prices had slight typographical formats in original spreadsheets (e.g. string commas or trailing whitespace), deterministic cleaning and floating-point normalization were applied without altering numerical values.

2. **Market Hours & Trading Session Boundary:**
   - Standard CSE regular trading hours are assumed to be **09:30 to 14:30 Sri Lanka Standard Time (SLST / UTC+05:30)**.
   - Any public announcement, government gazette, or political arrest occurring on day $d$ **strictly after 14:30 SLT** is assumed to have zero price impact on day $d$. Its effective reaction session ($t_0$) rolls over to the next active market day ($t_0 = d+1$ or next trading session).
   - Any announcement occurring on a Saturday, Sunday, public holiday, or mercantile holiday rolls forward to the first subsequent active CSE trading session.

3. **Frontier Market Liquidity & Price Limits:**
   - CSE enforces dynamic circuit breakers (e.g., market-wide halts on 5% index drops during extreme volatility). Abnormal return calculations reflect recorded closing transaction prices and acknowledge that circuit breaks may truncate intraday price discovery.

---

## 2. Event Study Econometric Assumptions

1. **Estimation Window Independence:**
   - The estimation window is fixed at **$[-120, -20]$ trading sessions** relative to event day $t_0$ (100 market sessions).
   - The 20-session buffer $[t_0-20, t_0-1]$ is excluded from normal return parameter estimation to insulate against insider leakage, rumors, or pre-announcement positioning.

2. **Normal Return Benchmark Model:**
   - The Constant Mean Return Model ($R_t = \mu + \epsilon_t$) is employed as the primary benchmark for the benchmark ASPI index.
   - For individual equities or sector indices, market model regressions against ASPI are supported.

3. **Additivity of Abnormal Returns:**
   - Cumulative Abnormal Returns ($CAR$) are assumed to be linearly additive over daily logarithmic/percentage returns across the short-to-medium horizons: $CAR[0, 1]$, $CAR[0, 5]$, and $CAR[0, 20]$.

4. **Event Clustering & Confounding:**
   - Multiple political events occurring within a rolling 5-day window are tagged with a shared cluster identifier (`event_cluster_id`) to alert researchers of potential confounding shocks.

---

## 3. Machine Learning & Forecasting Assumptions

1. **The Small-$n$ Sample Regime:**
   - The verified historical catalog contains **70 government policies** and **34 political arrests** (104 total events).
   - In accordance with statistical learning theory, high-capacity models (e.g., deep neural networks, unregularized gradient boosted trees) overfit aggressively in this regime. 
   - **Design Decision:** The system adopts heavily regularized linear models (L2 Logistic Regression, Ridge Regression with $\alpha=1.0$) combined with a case-based Historical Analogue Precedent engine.

2. **Strict Non-Lookahead Guarantee:**
   - Feature engineering for event $i$ occurring at $t_0$ is restricted strictly to information available at or before session $t_0 - 1$.
   - Forward-chaining walk-forward validation (expanding window) is employed without data shuffling.

3. **Residual Uncertainty & Fan Chart Projections:**
   - Predictive uncertainty intervals (80% and 95% bands) are constructed from empirical walk-forward residual variance $\hat{\sigma}_{\text{res}}$, scaled by square-root of time $\sqrt{t/5}$ over the 20-day horizon.

4. **Case-Based Reasoning Priority:**
   - Because financial decision-makers prioritize explainability, Model 1 (Historical Analogue Precedents via cosine semantic & state similarity) serves as the primary qualitative recommendation, while Models 2 and 3 provide bounding probabilities and intervals.

---

## 4. News Fact-Checking & Twin Scenario Assumptions

1. **Credibility Tier Weighting:**
   - Tier 1: Official government, regulatory, and exchange sources (weight: 1.0).
   - Tier 2: Established mainstream financial and national press (weight: 0.8).
   - Tier 3: General digital portals and regional reporting (weight: 0.5).
   - Tier 4: Social media, unverified blogs, anonymous posts (weight: 0.2).

2. **Scenario B Formulation (No-Event Baseline):**
   - If a submitted news claim is uncorroborated, contradicted, or deemed false, **Scenario B simulates normal market continuation (zero-event baseline)**.
   - The system strictly refuses to invent a speculative "fake-news collapse" model, preserving academic integrity.

3. **Network Security & SSRF:**
   - Any external URL submitted for verification is checked against an IP blacklist (blocking loopback `127.0.0.1`, RFC1918 private subnets `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, and cloud metadata services `169.254.169.254`).

---

## 5. Live CSE Integration Assumptions

1. **HTTP Protocol Specifics:**
   - The Colombo Stock Exchange public API endpoints (`https://www.cse.lk/api/*`) reject standard HTTP `GET` requests with `405 Method Not Allowed`. All requests must be executed as **HTTP `POST`** with standard browser headers.

2. **Graceful Fallback:**
   - In cases of upstream CSE downtime, network partitioning, or off-market hours, the system serves cached live data with an explicit staleness flag or falls back to a deterministic demo provider tagged with `is_demo: true`.

3. **Port Assignment:**
   - Backend development port is configured to **8001** (avoiding Windows socket permission errors encountered on port 8000). Frontend Vite server runs on **5173**.
