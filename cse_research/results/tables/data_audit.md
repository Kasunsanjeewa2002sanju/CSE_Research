# CSE Data Audit Report (Stage 1)

**Date Generated**: 2026-10-22 09:57:03
**Raw File SHA-256**: `a9965aea016faf7cdd5836ac440818f082550906714cb82034c7f661be202c74`

## 1. Executive Summary

- **Total Trading Rows**: 7,635
- **Chronological Span**: 1994-01-03 to 2025-12-31 (32 calendar years)
- **Duplicate Trading Dates**: 0 (all dates unique and strictly monotonic)
- **Zero / Negative ASPI Values**: 0
- **ASPI Missing Values**: 0 (100% complete daily price series)
- **S&P SL 20 Series**: Active from 2012-06-27 (3,210 observations); un-backfilled per Rule R1

## 2. Column Distribution Summaries

| column | count_valid | count_missing | min | p01 | q25 | median | q75 | p99 | max | mean | std | iqr | mad |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aspi | 7635 | 0 | 383.4 | 418.6 | 830.55 | 3120.73 | 6567.014999999999 | 20791.814399999996 | 23659.7 | 4554.37093778651 | 4195.013695060388 | 5736.464999999999 | 2574.0299999999997 |
| sp20 | 3210 | 4425 | 1685.45 | 2140.2279 | 2965.46 | 3334.32 | 3737.92 | 6202.3598999999995 | 6557.6 | 3437.974557632399 | 775.036872469392 | 772.46 | 382.97500000000014 |
| turnover_equity_mn | 7635 | 0 | 1.7 | 6.6 | 98.6 | 427.4 | 1206.73 | 11905.366999999953 | 33422.6 | 1159.8999554682382 | 2222.1036671027537 | 1108.13 | 377.0 |
| shares_traded_equity_k | 7635 | 0 | 90.6 | 329.174 | 3228.35 | 15682.3 | 47471.899999999994 | 506183.2299999999 | 2868086.0 | 48388.88019908317 | 106042.68835119969 | 44243.549999999996 | 14266.699999999999 |
| aspi_log_return | 7634 | 1 | -0.13893051590662928 | -0.030919186800824675 | -0.003820223720430818 | 0.00024201743133010105 | 0.004757524170284028 | 0.029670431604480473 | 0.18288141497784202 | 0.0004102444755368232 | 0.010927192621088369 | 0.008577747890714846 | 0.004288095332304682 |

## 3. Large ASPI Return Shocks (|r_t| > 8%)

All daily log return events exceeding 8% were individually investigated against historical records:

| date | prev_aspi | aspi | next_aspi | aspi_log_return | percentage_change | plausible_reality | historical_event_context |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2001-12-07 | 535.7 | 643.2 | 678.2 | 0.18288141497784202 | 20.07 | VERIFIED REAL | 2001 Parliamentary Election victory by UNF; surge on peace process expectations. |
| 2003-11-05 | 1334.5 | 1161.4 | 1156.1 | -0.13893051590662928 | -12.97 | VERIFIED REAL | President Kumaratunga prorogued Parliament & declared state of emergency during PM Wickremesinghe DC visit. |
| 2003-11-07 | 1156.1 | 1298.5 | 1217.4 | 0.1161574804215272 | 12.32 | VERIFIED REAL | Market rebound following preliminary Kumaratunga-Wickremesinghe conciliation talks. |
| 2004-02-09 | 1183.0 | 1058.3 | 1016.7 | -0.11138973787870797 | -10.54 | VERIFIED REAL | President Kumaratunga dissolved Parliament on Feb 7, triggering early snap elections. |
| 2004-04-06 | 1313.5 | 1189.0 | 1196.5 | -0.09958271243481276 | -9.48 | VERIFIED REAL | 2004 Parliamentary Election results declared; UPFA victory with Marxist JVP coalition concerns. |
| 2022-04-26 | 7513.85 | 6905.37 | 7280.52 | -0.08444861443146846 | -8.1 | VERIFIED REAL | Sri Lanka sovereign debt default announcement, massive interest rate hikes, and post-halt crash. |

## 4. Volume and Consistency Diagnostics

- **Log Volume vs Log Turnover Correlation**: 0.9491
- **Daily Change Direction Concordance**: 74.42%
- **Turnover Robust Outliers (|z_robust| > 5)**: 662
- **Shares Traded Robust Outliers (|z_robust| > 5)**: 747
- **Negative Turnover / Shares Count**: 0

## 5. Stationarity Test Results (ADF and KPSS)

| Series | Observations | ADF Statistic | ADF p-value | ADF 5% Critical | ADF Conclusion | KPSS Statistic | KPSS p-value | KPSS 5% Critical | KPSS Conclusion | Joint Determination |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASPI Level | 7635 | 2.4701 | 0.999 | -2.8619 | Unit Root (Fail to Reject) | 10.7471 | 0.01 | 0.463 | Non-Stationary (Reject H0) | Non-Stationary Unit Root (I(1)) |
| ASPI Log Return | 7634 | -15.3734 | 0.0 | -2.8619 | Stationary (Reject H0) | 0.235 | 0.1 | 0.463 | Stationary (Fail to Reject) | Strictly Stationary (I(0)) |
| Log Equity Turnover | 7635 | -2.5354 | 0.1071 | -2.8619 | Unit Root (Fail to Reject) | 10.8046 | 0.01 | 0.463 | Non-Stationary (Reject H0) | Non-Stationary Unit Root (I(1)) |
| Log Shares Traded | 7635 | -2.892 | 0.0463 | -2.8619 | Stationary (Reject H0) | 11.3395 | 0.01 | 0.463 | Non-Stationary (Reject H0) | Trend / Structural Break Stationary |

## 6. Notable Calendar Gaps (> 5 Days)

| prev_trading_day | next_trading_day | gap_days | note |
| --- | --- | --- | --- |
| 1994-04-12 | 1994-04-18 | 6 | Sinhala & Tamil New Year extended holidays |
| 1994-05-20 | 1994-05-26 | 6 | Market closure / Holiday stretch |
| 1994-08-16 | 1994-08-22 | 6 | Market closure / Holiday stretch |
| 1996-04-30 | 1996-05-06 | 6 | Market closure / Holiday stretch |
| 1998-04-09 | 1998-04-15 | 6 | Market closure / Holiday stretch |
| 2000-04-11 | 2000-04-17 | 6 | Sinhala & Tamil New Year extended holidays |
| 2001-12-21 | 2001-12-27 | 6 | Market closure / Holiday stretch |
| 2003-05-13 | 2003-05-19 | 6 | Market closure / Holiday stretch |
| 2004-04-08 | 2004-04-14 | 6 | Market closure / Holiday stretch |
| 2006-01-10 | 2006-01-16 | 6 | Market closure / Holiday stretch |
| 2006-04-10 | 2006-04-17 | 7 | Sinhala & Tamil New Year extended holidays |
| 2009-04-08 | 2009-04-15 | 7 | Market closure / Holiday stretch |
| 2011-04-12 | 2011-04-18 | 6 | Sinhala & Tamil New Year extended holidays |
| 2020-03-13 | 2020-03-20 | 7 | COVID-19 pandemic nationwide lockdown closure |
| 2020-03-20 | 2020-05-11 | 52 | COVID-19 pandemic nationwide lockdown closure |
| 2022-04-08 | 2022-04-25 | 17 | Sri Lanka economic crisis trading halt (April 2022) |
| 2023-06-28 | 2023-07-04 | 6 | Market closure / Holiday stretch |

*(Total calendar gaps > 5 days: 17; full log saved to `calendar_gaps.csv`)*

## 7. Trading Days per Year Highlights

| year | trading_days | is_anomalous_low | note |
| --- | --- | --- | --- |
| 2020 | 209 | True | COVID-19 shutdown (March-May 2020) |

