# Architectural & Mathematical Decisions: Live Market Data, Storage & Returns

**Project:** ASPI Research – Political Events & Econometrics  
**Stage:** Stage 3 – Storage, Cache, Historical Append  
**Date:** October 20, 2026  
**Document Path:** `/docs/live_data/DECISIONS.md`  

---

## 1. Intraday-Aware Returns vs. Official Daily Returns

### 1.1 The Mathematical Problem
In an active equity market such as the Colombo Stock Exchange (CSE), there are two distinct return conventions that serve different purposes:
1. **Public Market Display Convention:** Retail investors and exchange tickers expect simple arithmetic percentage change relative to the previous day's close.
2. **Econometric & Machine Learning Convention:** Time-series models, event study estimators, CatBoost regressors, and conformal prediction bands require continuous log returns to maintain time-additivity, symmetry, and guaranteed positive index values under compounding ($S_{t+h} = S_t \cdot e^{\hat{r}_h}$).

Furthermore, a live trading session introduces an intra-day transition: the index is actively fluctuating, whereas official historical data consists of finalized close-to-close bars.

### 1.2 Mathematical Formulations

#### A. Intraday Session Return (Continuous Trading: 09:30 – 14:30 Colombo Time)
During an active session, each tick $S_t$ (at time $t$ on date $T$) is evaluated against the previous confirmed closing level $S_{T-1}^{\text{close}}$:

$$\text{Simple Intraday Return } (\%): \quad R_{\text{intraday}} = \left(\frac{S_t - S_{T-1}^{\text{close}}}{S_{T-1}^{\text{close}}}\right) \times 100\%$$

$$\text{Continuous Log Intraday Return}: \quad r_{\text{intraday}} = \ln\left(\frac{S_t}{S_{T-1}^{\text{close}}}\right)$$

- **SLA & Freshness Coupling:** If $t - t_{\text{tick}} \le 60\text{s}$, the state is marked `LIVE`. If delayed ($>60\text{s}$), it is marked `DELAYED`. If exceeding $120\text{s}$ or source offline, it degrades to `STALE`.
- **Dynamic Scenario Baseline:** The Scenario Predictor on `/scenario` binds its baseline $S_{\text{baseline}} = S_t$. Forward projections scale as $S_{t+h} = S_t \cdot e^{\hat{r}_h}$.

#### B. Official Daily Close Return (Post-Close: after 14:30 Colombo Time)
After market close and upon confirmation of the final closing print ($S_T^{\text{close}}$):

$$\text{Official Simple Daily Return } (\%): \quad R_T = \left(\frac{S_T^{\text{close}} - S_{T-1}^{\text{close}}}{S_{T-1}^{\text{close}}}\right) \times 100\%$$

$$\text{Official Continuous Daily Log Return}: \quad r_T = \ln\left(\frac{S_T^{\text{close}}}{S_{T-1}^{\text{close}}}\right)$$

- **Reconciliation:** The confirmed close $S_T^{\text{close}}$ is compared against official CSE publication records (e.g. from `/api/chartData` daily bars or market status summaries). Discrepancies exceeding $0.05$ points are logged in the append audit trail.
- **Econometric Append:** The daily bar is appended to `live_daily.csv` with unrounded log return $r_T$ to preserve float precision for downstream modeling.

### 1.3 Summary Comparison Matrix

| Dimension | Intraday Session Return | Official Post-Close Return |
| :--- | :--- | :--- |
| **Numerator** | Current live index tick $S_t$ | Final confirmed auction close $S_T^{\text{close}}$ |
| **Denominator** | Previous confirmed close $S_{T-1}^{\text{close}}$ | Previous confirmed close $S_{T-1}^{\text{close}}$ |
| **Evaluation Timing** | Real-time continuous (every 5 seconds) | Once at EOD (after 14:30 + 2x confirmation) |
| **Freshness Tag** | `LIVE`, `DELAYED`, or `STALE` | `CLOSED` |
| **Storage Destination** | In-memory cache + `intraday_series.json` | `live_daily.csv` + `append_audit.log` |
| **Consumer** | Live UI badges, fan chart baseline, sparklines | Historical research panel, model retraining |

---

## 2. Storage & Caching Layer Architecture

### 2.1 Latest Snapshot Store
- **In-Memory TTL:** All read requests (`GET /api/market/latest`) are served directly from RAM with negligible latency (< 1ms).
- **Atomic Persistence:** Disk writes to `cse_data_cache/last_snapshot.json` use a write-to-tempfile followed by `os.replace`. This eliminates file corruption from server aborts or power loss.
- **Server Restart Resilience:**
  - Upon server restart mid-session, the latest snapshot is loaded instantly from disk.
  - The store checks the snapshot timestamp against the current market clock. If the market is open but the tick is older than `stale_after_seconds` (120s), the snapshot is marked `STALE` with `persisted_recovery: true`.
- **Optional Redis Backend:** Configured via `REDIS_ENABLED=true` and `REDIS_URL`. Defaults to `false` for standalone, zero-dependency deployment.

### 2.2 Intraday Rolling Series Store
- **1-Minute Downsampling:** High-frequency ticks are aggregated into 1-minute buckets containing `open`, `high`, `low`, `close` (value), `turnover`, and `volume`.
- **Bounded Memory:**
  - Keeps the active trading session plus $K$ prior sessions (`INTRADAY_RETENTION_SESSIONS=3`).
  - At ~300 minutes per session (09:30 to 14:30), total memory footprint is capped at ~1,200 points per metric. Older sessions are evicted automatically.
- **Disk Persistence:** Serialized atomically to `cse_data_cache/intraday_series.json` to ensure sparklines survive server restarts.

---

## 3. Safe End-of-Day (EOD) Append & Merged View Engine

### 3.1 Strict Isolation Rule
- **Rule:** `CSE_data.csv` and `cse_clean.csv` must **NEVER** be modified in place.
- **Implementation:** All live daily bars are appended strictly to `cse_data_cache/live_daily.csv`.
- **Merged View:** `MergedMarketHistory` unifies the immutable 7,635-row baseline with `live_daily.csv` at runtime.

### 3.2 Idempotency Guarantee
- Calling the EOD append job multiple times for the same date is guaranteed to be idempotent:
  - If a bar for date $T$ already exists with identical values, the operation returns `action: "NOOP"`, `is_duplicate: true`, and skips writing.
  - If values differ (e.g. following official reconciliation), the row is updated in place (`action: "UPDATE"`).
  - No duplicate date rows can ever be created.

### 3.3 Audit Trail
- Every append or reconciliation check writes an entry to `cse_data_cache/append_audit.log`:
  ```json
  {
    "timestamp": "2026-10-20T14:32:00Z",
    "date": "2026-10-20",
    "action": "INSERT",
    "source": "cse_live_eod",
    "aspi": 22650.12,
    "sp20": 6165.40,
    "turnover_equity_mn": 8420.50,
    "shares_traded_equity_k": 210500.0,
    "aspi_log_return": 0.001140,
    "reconciled": true,
    "discrepancy": null
  }
  ```

---

## 4. Derived Statistics & Baseline Regression Equations

All statistical derived metrics strictly reproduce the empirical research formulas established in Stage 0:

1. **Panel Size ($N$):**
   $$N = \text{count of trading days in merged view} = 7,635 \text{ (baseline)}$$

2. **Annualized Realized Volatility ($\sigma_{\text{ann}}$):**
   Computed over a 20-day rolling window of continuous log returns ($r_i$):
   $$\bar{r} = \frac{1}{20}\sum_{i=1}^{20} r_i$$
   $$s^2 = \frac{1}{19}\sum_{i=1}^{20} (r_i - \bar{r})^2$$
   $$\sigma_{\text{ann}} = \sqrt{s^2} \times \sqrt{240.0} \times 100\% = 15.70\% \text{ on 2025-12-31 baseline}$$

3. **1D Daily Return ($R_{1D}$):**
   $$r_{1D} = \ln\left(\frac{22,624.31}{22,445.89}\right) \times 100\% = 0.7917\% \approx 0.79\%$$

4. **5D Return ($R_{5D}$):**
   $$R_{5D} = \left(\frac{22,624.31 - 21,927.00}{21,927.00}\right) \times 100\% = 3.18\%$$
   $$r_{5D} = \ln\left(\frac{22,624.31}{21,927.00}\right) \times 100\% = 3.13\%$$
