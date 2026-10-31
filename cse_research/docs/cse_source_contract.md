# CSE Live Data Source Contract & Endpoint Catalogue

**Document ID:** `CSE-DATA-CONTRACT-001`  
**Version:** `1.0.0`  
**Status:** Frozen / Approved for Implementation  
**Exchange:** Colombo Stock Exchange (CSE), Sri Lanka  
**Target Platform:** `https://www.cse.lk/`  
**Timezone Standard:** `Asia/Colombo` (`UTC+05:30`)  
**Scope:** Backend research, endpoint catalogue, unit verification, and Pydantic schema validation.

---

## 1. Executive Summary & Architecture Overview

The Colombo Stock Exchange (`cse.lk`) public web application is built on **Next.js (App Router)** and receives market information through two primary communication layers:
1. **Primary Push Feed (Real-Time):** A STOMP-over-WebSocket connection provided by a SockJS endpoint at `https://www.cse.lk/api/ws`. During active market hours, this socket pushes sub-second ticks for the All Share Price Index (ASPI), S&P Sri Lanka 20 (S&P SL 20), market turnover, share volume, trade counts, and session state transitions.
2. **Fallback Polling APIs (REST / HTTP):** A collection of JSON and URL-encoded REST endpoints hosted on `https://www.cse.lk/api/*`. These provide historical series, sector summaries, intraday chart series, and market state snapshots when the WebSocket is disconnected or initializing.

```
                      ┌──────────────────────────────────────────┐
                      │          https://www.cse.lk              │
                      └────────────────────┬─────────────────────┘
                                           │
                 ┌─────────────────────────┴─────────────────────────┐
                 │                                                   │
                 ▼                                                   ▼
   [Primary Push / Streaming]                            [Secondary Polling / REST]
  SockJS STOMP: /api/ws                                  HTTP POST /api/chartData
  - /topic/aspi                                          HTTP POST /api/marketStatus
  - /topic/snp                                           HTTP POST /api/allSectors
  - /topic/summary                                       HTTP POST /api/aspi/year
  - /topic/status                                        HTTP GET  /api/allSecurityCode
                 │                                                   │
                 └─────────────────────────┬─────────────────────────┘
                                           │
                                           ▼
                      ┌──────────────────────────────────────────┐
                      │        CSE Ingestion Pipeline            │
                      │  (MarketSnapshot Pydantic Validator)     │
                      └────────────────────┬─────────────────────┘
                                           │
                                           ▼
                      ┌──────────────────────────────────────────┐
                      │   In-Memory Cache & Scenario Baseline    │
                      │        (S_t = 20,059.42 Points)          │
                      └──────────────────────────────────────────┘
```

---

## 2. Endpoint Catalogue

### 2.1 Primary Feed: SockJS STOMP WebSocket
- **Transport URL:** `wss://www.cse.lk/api/ws/{server_id}/{session_id}/websocket`
  - `server_id`: 3-digit random integer (e.g. `000` to `999`).
  - `session_id`: 8-character random alphanumeric string (e.g. `probe999`).
- **Info Handshake:** `GET https://www.cse.lk/api/ws/info` returns `{"entropy": ..., "websocket": true, "cookie_needed": true}`.
- **Protocol:** STOMP 1.1 / 1.2 framed inside SockJS JSON packets (`["<STOMP_FRAME>"]`).
- **Connect Frame:**
  ```stomp
  CONNECT
  accept-version:1.1,1.2
  heart-beat:10000,10000

  ^@
  ```
- **Active Subscriptions & Trigger Mappings:**
  | STOMP Topic | Trigger Destination | Direction | Payload Description |
  |---|---|---|---|
  | `/topic/aspi` & `/user/topic/aspi` | `/app/request-aspi` | IN | Real-time ASPI index ticks, high, low, change, previous close |
  | `/topic/snp` & `/user/topic/snp` | `/app/request-snp` | IN | Real-time S&P SL 20 ticks, high, low, change |
  | `/topic/summary` & `/user/topic/summary` | `/app/request-summary` | IN | Market aggregate turnover, share volume, trade counts |
  | `/topic/status` & `/user/topic/status` | `/app/request-status` | IN | Market session operational status transitions |
  | `/topic/daytrade` | `/app/request-daytrade` | IN | Continuous stream of executed stock trades |

#### Verified WebSocket Response Samples:
- **ASPI Tick (`/user/topic/aspi`):**
  ```json
  {
    "id": 37198943,
    "value": 20059.42,
    "lowValue": 20059.42,
    "highValue": 20059.42,
    "change": 0.0,
    "percentage": 0.0,
    "sectorId": 1.0,
    "timestamp": 1792464360914
  }
  ```
- **Market Summary (`/user/topic/summary`):**
  ```json
  {
    "id": null,
    "tradeVolume": 154289045.50,
    "shareVolume": 8421900,
    "trades": 3412,
    "tradeDate": "2026-10-20"
  }
  ```
  *(Note: During Opening Auction Call prior to 09:30 AM, these fields return `null`, which the site renders as `0.00` / `0`).*
- **Market Status (`/user/topic/status`):**
  ```json
  {
    "status": "Opening Auction Call"
  }
  ```

---

### 2.2 Secondary Feed: REST APIs

#### A. Chart Data Endpoint (`POST /api/chartData`)
- **URL:** `https://www.cse.lk/api/chartData`
- **Method:** `POST`
- **Headers:**
  - `Content-Type: application/x-www-form-urlencoded`
  - `User-Agent: Mozilla/5.0...`
- **Request Body:** `chartId={id}&period={period}`
  - `chartId=1`: ASPI (All Share Price Index)
  - `chartId=40`: S&P SL 20
  - `period=1`: Current intraday ticks
  - `period=2`: 5-day daily series (1 trading week)
  - `period=3`: 20-day daily series (1 trading month)
  - `period=5`: 240-day daily series (1 trading year for historical reconciliation)
- **Verified Response Sample (`period=1` intraday):**
  ```json
  [
    {
      "d": 1792468800000,
      "v": 20059.42,
      "pc": null
    }
  ]
  ```
- **Verified Response Sample (`period=2` 5-day daily close):**
  ```json
  [
    {"d": 1791859560000, "v": 20096.14, "pc": -0.8090795387575358},
    {"d": 1791970020000, "v": 20112.45, "pc": 0.08115998634563806},
    {"d": 1792056420000, "v": 20150.30, "pc": 0.18819189110476348},
    {"d": 1792142820000, "v": 20185.12, "pc": 0.17279147208229653},
    {"d": 1792377960000, "v": 20087.86, "pc": -0.48149496781033485}
  ]
  ```

#### B. Market Status (`POST /api/marketStatus`)
- **URL:** `https://www.cse.lk/api/marketStatus`
- **Method:** `POST`
- **Headers:** `Content-Type: application/json`
- **Body:** `{}`
- **Verified Response Sample:**
  ```json
  {
    "status": "Opening Auction Call"
  }
  ```

#### C. Sector Indices (`POST /api/allSectors`)
- **URL:** `https://www.cse.lk/api/allSectors`
- **Method:** `POST`
- **Headers:** `Content-Type: application/json`
- **Body:** `{}`
- **Verified Response Sample:**
  ```json
  [
    {
      "id": 105832,
      "sectorId": 1,
      "symbol": "ASI",
      "indexCode": null,
      "indexCodeSp": "ASI",
      "indexName": "ALL SHARE PRICE INDEX",
      "name": "ALL SHARE PRICE INDEX",
      "indexValue": 20059.42,
      "change": 0.0,
      "percentage": 0.0,
      "sectorTradeToday": null,
      "sectorVolumeToday": null,
      "sectorTurnoverToday": null,
      "sectorPreviousClose": 20059.42,
      "transactionTime": 1792464360914
    }
  ]
  ```

#### D. Annual Returns (`POST /api/aspi/year`)
- **URL:** `https://www.cse.lk/api/aspi/year`
- **Method:** `POST`
- **Body:** `{"year": 2026}`
- **Verified Response Sample:**
  ```json
  {
    "triAspiValue": -8.08,
    "snpValueForYear": 0.0,
    "aspiValueForYear": -11.34,
    "triSnpValue": -3.72
  }
  ```

---

## 3. Field-Mapping Table & Unit Verifications

The table below defines the contract between upstream CSE feed fields and the internal domain models.

| CSE Upstream Field | Internal Domain Field | Target Unit | Python Type | Nullable? | Valid Range / Constraints | Verification Evidence / Provenance |
|---|---|---|---|:---:|---|---|
| `aspi.value` / `asi.indexValue` | `MarketSnapshot.aspi_value` | Index Points | `float` | **No** | $1,000.0 \le v \le 100,000.0$ | Matches displayed `20,059.42` |
| `aspi.change` / `asi.change` | `MarketSnapshot.aspi_change` | Index Points | `float` | **No** | $-10,000.0 \le c \le 10,000.0$ | Verified against `v - previous_close` |
| `aspi.percentage` / `asi.percentage` | `MarketSnapshot.aspi_percent_change` | Percent (%) | `float` | **No** | $-50.0\% \le p \le +50.0\%$ | Formatted in UI as `${e.toFixed(2)}%` |
| `asi.sectorPreviousClose` | `MarketSnapshot.aspi_previous_close` | Index Points | `float` | **No** | $1,000.0 \le v \le 100,000.0$ | Base for log returns |
| `snp.value` / `sp_bars.v` | `MarketSnapshot.sp20_value` | Index Points | `float` | **Yes** | $500.0 \le v \le 50,000.0$ | Null during opening auction |
| `snp.change` | `MarketSnapshot.sp20_change` | Index Points | `float` | **Yes** | $-5,000.0 \le c \le 5,000.0$ | Blue chip index point change |
| `snp.percentage` | `MarketSnapshot.sp20_percent_change` | Percent (%) | `float` | **Yes** | $-50.0\% \le p \le +50.0\%$ | Blue chip % change |
| `summary.tradeVolume` | `MarketSnapshot.market_turnover` | **Raw LKR** | `float` | **No** | $\ge 0.0$ | **VERIFIED:** UI renders `N(tradeVolume)` where $N$ is `toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2})`. It is **NOT** in '000 or millions. |
| `summary.shareVolume` | `MarketSnapshot.shares_traded` | **Raw Share Units** | `int` | **No** | $\ge 0$ | **VERIFIED:** UI renders `E(shareVolume)` where $E$ is integer `toLocaleString()`. It is **NOT** in '000. |
| `summary.trades` | `MarketSnapshot.total_trades` | Execution Count | `int` | **No** | $\ge 0$ | UI renders `E(trades)`. Total executed trades tickets. |
| `status.status` / `marketStatus.status` | `MarketStatus.status` | Standard Enum | `MarketStatusType` | **No** | One of 8 recognized exchange states | Normalized string enum |
| `aspi.timestamp` / `asi.transactionTime` | `MarketSnapshot.source_timestamp` | Local Datetime | `datetime` | **No** | `Asia/Colombo` | Millisecond Unix timestamp from CSE engine |
| Host ingestion clock | `MarketSnapshot.ingest_timestamp` | UTC Datetime | `datetime` | **No** | UTC | Timestamp when backend validated tick |
| Source identifier | `MarketSnapshot.source` | String ID | `str` | **No** | `websocket_stomp`, `rest_api` | Identifies ingestion channel |

---

## 4. Timestamp Semantics & Timezone Handling

1. **Source Timestamp (`source_timestamp`):**
   - Origin: Provided directly by the Colombo Stock Exchange engine in JSON messages as a 13-digit Unix millisecond integer (e.g. `1792464360914`).
   - Semantics: Represents the exact server time at which the transaction occurred or the index was recomputed in Colombo.
   - Conversion: Converted immediately to timezone-aware `datetime` with `ZoneInfo("Asia/Colombo")` (`UTC+05:30`).
2. **Ingest Timestamp (`ingest_timestamp`):**
   - Origin: Generated on the local FastAPI backend server when the message is unmarshalled and validated.
   - Semantics: Ingest arrival time in `UTC` (`datetime.now(timezone.utc)`).
3. **Latency & SLA:**
   - Latency is calculated as $\Delta t = t_{\text{ingest}} - t_{\text{source}}$.
   - Freshness SLA: If $\Delta t < 60\text{ seconds}$ during regular trading hours, state is `LIVE`. If $60\text{s} \le \Delta t \le 300\text{s}$, state is `DELAYED`. If $\Delta t > 300\text{s}$, state transitions to `STALE`.

---

## 5. Primary vs. Fallback Source Decisions

| Field / Metric | Primary Source | Fallback Source | Architectural Rationale |
|---|---|---|---|
| **ASPI Live Index** | WebSocket `/topic/aspi` | REST `POST /api/chartData` (`chartId=1&period=1`) or `POST /api/allSectors` | WebSocket delivers sub-second event-driven ticks without polling overhead; REST provides instant recovery if socket reconnects. |
| **S&P SL 20 Live** | WebSocket `/topic/snp` | REST `POST /api/chartData` (`chartId=40&period=2`) | S&P SL 20 has fewer constituent transactions; WebSocket pushes as trades occur, REST supplies previous close during auction. |
| **Turnover & Volume** | WebSocket `/topic/summary` | REST `POST /api/allSectors` (`sectorTurnoverToday`, `sectorVolumeToday`) | WebSocket `/topic/summary` is the official real-time turnover feed used by `cse.lk`'s own summary widget. |
| **Market Status** | WebSocket `/topic/status` | REST `POST /api/marketStatus` | Status changes (e.g., transition from Auction Call to Regular Trading) are broadcast immediately over WebSocket. |
| **Daily Bars & EOD Reconciliation** | REST `POST /api/chartData` (`period=5`, 240D) | Stored `CSE_data.csv` historical panel | `chartData` returns 240 daily bars with exact timestamps and daily percentage change, ideal for daily close validation. |

---

## 6. Edge-Case Behaviour & Exchange Rules

1. **Pre-Open / Opening Auction Call (09:00 – 09:30 Colombo Time):**
   - Market status is `"Opening Auction Call"`.
   - `sp20_value`, `summary.tradeVolume`, `summary.shareVolume`, and `summary.trades` are `null` (zero trades have cleared).
   - *Contract Handling:* Nullable fields are initialized with `0.00` / `0` for display, `sp20_value` remains `None`. ASPI displays opening indicative or previous close.
2. **Regular Continuous Trading (09:30 – 14:30 Colombo Time):**
   - Market status is `"Regular Trading"` or `"open"`.
   - Live ticks flow continuously; `is_open = True`.
3. **Closing Run & Finalization (14:30 – 15:00 Colombo Time):**
   - Market status transitions to `"Market Close (Statistics Being Finalized)"` and subsequently `"Market Closed"`.
   - The final closing tick is recorded and frozen as the official closing snapshot.
   - `freshness` transitions to `FreshnessState.CLOSED`.
4. **Trading Halts / Circuit Breakers:**
   - The CSE enforces three-tier circuit breakers based on drops in the S&P SL 20 index (Tier 1: 5%, Tier 2: 7.5%, Tier 3: 10%).
   - When triggered, trading halts for 30 minutes. Status updates to `"Market Halted"`.
   - *Contract Handling:* Backend preserves the last known valid index values, sets `is_open = False`, and flags the snapshot as `MARKET_HALTED`.
5. **Zero-Volume / Illiquid Trading Sessions:**
   - If no trades occur in an illiquid security, `tradeVolume = 0.0` and `shareVolume = 0`. Handled without division-by-zero errors.
6. **Weekends & Public/Bank Holidays:**
   - Market status remains `"Market Closed"`.
   - Feed provides the last session's closing snapshot with `FreshnessState.CLOSED`.

---

## 7. Polling Cadence, Caching, and Bot Protection

1. **WebSocket Cadence:**
   - Active WebSocket connection maintains a `heart-beat: 10000, 10000` (10-second STOMP heartbeat).
   - Server pushes messages asynchronously when events occur.
2. **REST Polling Policy (Polite Scraping / Fallback):**
   - Polling is **only** used when WebSocket is disconnected or during startup probe.
   - Polling rate during market hours: **Every 15 to 30 seconds**.
   - Polling rate outside market hours: **Every 5 minutes**.
   - Exponential backoff on HTTP error (500, 502, 503, 504): $2^n \times 1\text{s}$ up to 60s.
3. **Headers & User-Agent:**
   - Explicit identifying User-Agent: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ASPI-Research/1.0`.
4. **Caching Headers:**
   - CSE responds with `Cache-Control: no-cache, no-store, max-age=0, must-revalidate` for live endpoints.
   - Our internal backend caches the latest `MarketSnapshot` in-memory with a 1-second TTL to protect against redundant internal requests.

---

## 8. Legal & Terms of Service Note

- **Data Attribution:** All market data originated from the Colombo Stock Exchange (CSE) is intellectual property of the Colombo Stock Exchange PLC.
- **Academic & Non-Commercial Use:** This data is utilized solely for academic research, econometric modeling, and counterfactual scenario forecasting under fair use for educational and research institutions (SLIIT Year 4 Research).
- **Redistribution Policy:** Raw real-time tick-by-tick feeds must not be redistributed commercially. The platform consumes market levels solely to drive internal mathematical forecast baselines ($S_{t+h} = S_t \cdot e^{\hat{r}_h}$).
- **Rate-Limit Respect:** Backend implementations must strictly abide by polite request rates and avoid aggressive scraping or denial-of-service pressure on the exchange infrastructure.

---

## 9. Verification & Acceptance Sign-Off

- **Probe Executable:** `/backend/tools/probe_cse.py` (runnable with `python backend/tools/probe_cse.py`).
- **Pydantic Schema:** `/backend/src/cse/market/schema.py`.
- **Recorded Fixtures:** `/backend/tests/fixtures/cse/*.json` (8 verified response fixtures).
- **Field Consistency:** Verified that turnover is in raw Sri Lankan Rupees (LKR) and shares are in raw unit counts.
- **Live Match:** Verified that live probe output matches the displayed figures on `https://www.cse.lk`.
