# Stage 11 Historical Back-Test Evaluation Report

Executed on: 2026-10-22 09:58:50

### Aggregate Metrics (5 Historical Elections x 4 Horizons)

- **Directional Accuracy:** **75.0%** (15/20 hits)
- **80% Conformal Range Coverage:** **40.0%** (8/20 hits)
- **95% Conformal Range Coverage:** **85.0%** (17/20 hits)

### Detailed Forecasts vs Realized Outcomes

| event | as_of_date | horizon_h | target_date | aspi_t | pred_aspi | actual_aspi | pred_ret_pct | actual_ret_pct | dir_hit | range_80_hit | range_95_hit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 Presidential Election | 2015-01-08 | 1 | 2015-01-09 | 7,497.6 | 7,547.1 | 7,605.8 | +0.66% | +1.43% | **HIT** | MISS | HIT |
| 2015 Presidential Election | 2015-01-08 | 2 | 2015-01-12 | 7,497.6 | 7,528.8 | 7,566.7 | +0.41% | +0.92% | **HIT** | HIT | HIT |
| 2015 Presidential Election | 2015-01-08 | 5 | 2015-01-19 | 7,497.6 | 7,606.8 | 7,366.7 | +1.45% | -1.76% | MISS | MISS | HIT |
| 2015 Presidential Election | 2015-01-08 | 10 | 2015-01-26 | 7,497.6 | 7,628.8 | 7,316.1 | +1.73% | -2.45% | MISS | MISS | HIT |
| 2015 Parliamentary Election | 2015-08-17 | 1 | 2015-08-18 | 7,492.0 | 7,538.8 | 7,498.7 | +0.62% | +0.09% | **HIT** | HIT | HIT |
| 2015 Parliamentary Election | 2015-08-17 | 2 | 2015-08-19 | 7,492.0 | 7,536.3 | 7,498.8 | +0.59% | +0.09% | **HIT** | HIT | HIT |
| 2015 Parliamentary Election | 2015-08-17 | 5 | 2015-08-24 | 7,492.0 | 7,571.0 | 7,331.1 | +1.05% | -2.17% | MISS | MISS | HIT |
| 2015 Parliamentary Election | 2015-08-17 | 10 | 2015-08-31 | 7,492.0 | 7,612.7 | 7,306.9 | +1.60% | -2.50% | MISS | MISS | HIT |
| 2019 Presidential Election | 2019-11-15 | 1 | 2019-11-18 | 6,023.0 | 6,042.4 | 6,129.6 | +0.32% | +1.75% | **HIT** | MISS | HIT |
| 2019 Presidential Election | 2019-11-15 | 2 | 2019-11-19 | 6,023.0 | 6,048.8 | 6,142.8 | +0.43% | +1.97% | **HIT** | MISS | HIT |
| 2019 Presidential Election | 2019-11-15 | 5 | 2019-11-22 | 6,023.0 | 6,096.9 | 6,119.3 | +1.22% | +1.59% | **HIT** | HIT | HIT |
| 2019 Presidential Election | 2019-11-15 | 10 | 2019-11-29 | 6,023.0 | 6,128.4 | 6,212.0 | +1.73% | +3.09% | **HIT** | HIT | HIT |
| 2020 Parliamentary Election | 2020-08-05 | 1 | 2020-08-06 | 5,146.4 | 5,131.8 | 5,176.9 | -0.28% | +0.59% | MISS | MISS | HIT |
| 2020 Parliamentary Election | 2020-08-05 | 2 | 2020-08-07 | 5,146.4 | 5,156.1 | 5,176.5 | +0.19% | +0.58% | **HIT** | HIT | HIT |
| 2020 Parliamentary Election | 2020-08-05 | 5 | 2020-08-12 | 5,146.4 | 5,171.5 | 5,220.6 | +0.49% | +1.43% | **HIT** | HIT | HIT |
| 2020 Parliamentary Election | 2020-08-05 | 10 | 2020-08-19 | 5,146.4 | 5,201.8 | 5,351.0 | +1.07% | +3.90% | **HIT** | HIT | HIT |
| 2024 Presidential Election | 2024-09-20 | 1 | 2024-09-23 | 10,966.5 | 10,983.7 | 11,096.8 | +0.16% | +1.18% | **HIT** | MISS | HIT |
| 2024 Presidential Election | 2024-09-20 | 2 | 2024-09-24 | 10,966.5 | 10,967.5 | 11,334.1 | +0.01% | +3.30% | **HIT** | MISS | MISS |
| 2024 Presidential Election | 2024-09-20 | 5 | 2024-09-27 | 10,966.5 | 11,057.8 | 11,773.9 | +0.83% | +7.10% | **HIT** | MISS | MISS |
| 2024 Presidential Election | 2024-09-20 | 10 | 2024-10-04 | 10,966.5 | 11,091.0 | 12,053.5 | +1.13% | +9.45% | **HIT** | MISS | MISS |

### Econometric Integrity Note
- Every back-test inputs only information available strictly on or before the news date (Rule R2 zero-lookahead).
- Hits and misses are reported with equal prominence without filtering (Rule R8 honest reporting).
