# Election Event Calendar & Coverage Audit Report (Stage 2)

**Research Project:** Predicting Stock Market Movements Using Political News Categories (SLIIT)
**Authoritative Input:** `data/raw/Elections.csv` (SHA-256: `ac71d986fcbf121ed6eb1bd504cd573fbd711a5015e7188eb694d16c48cc043f`)
**CSE Trading Baseline:** `data/processed/cse_clean.parquet` (7,635 trading days, 1994–2025)

---

## 1. Executive Summary

- **Total Distinct Election Events Identified:** `24` (from 36 raw provincial/national records)
- **Proposal Sample Period (2009–2025) Events:** `16` (`66.7%` of all elections)
- **Pre-Sample Historical Events (2000–2008):** `8` (`33.3%` of all elections)
- **Total Stage Observations Mapped to Trading Days:** `142`
- **Trading Day Reaction Day Mappings:** 100% of recorded stages successfully mapped to next available CSE trading day (`mapped_date >= raw_date`)

---

## 2. Event Breakdown by Election Type

| Election Type | Total Events | In Proposal Sample (2009–2025) | Pre-Sample (2000–2008) | Total Raw Rows |
|:---|:---:|:---:|:---:|:---:|
| **Presidential** | 5 | 4 | 1 | 5 |
| **Parliamentary** | 7 | 4 | 3 | 7 |
| **Provincial Council** | 12 | 8 | 4 | 24 |
| **TOTAL** | **24** | **16** | **8** | **36** |

---

## 3. Electoral Stage Coverage

The 6 canonical electoral stages specified in the research methodology:

| Stage Name | Description | Available Observations | Missing Observations | Missingness Rationale |
|:---|:---|:---:|:---:|:---|
| `announcement` | Official proclamation / gazette date setting the election | 24 | 0 | 100% complete across all 24 elections |
| `nomination_start` | First day political parties submit candidate lists | 22 | 2 | Missing in Row 3 (Wayamba 2004 PC) and Row 16 (Western 2009 PC) marked 'Not Available' in raw archive |
| `nomination_end` | Final nomination deadline / gazetting of accepted lists | 22 | 2 | Missing in Row 3 (Wayamba 2004 PC) and Row 16 (Western 2009 PC) marked 'Not Available' in raw archive |
| `polling` | The election day when citizens cast ballots | 24 | 0 | 100% complete across all 24 elections |
| `result` | Official declaration of count and winning seats / votes | 24 | 0 | 100% complete across all 24 elections |
| `government_formation` | Swearing in of President / Prime Minister / Provincial Board of Ministers | 26 | 0 | Includes staggered formation dates for 2012 (Eastern vs NC/Sabaragamuwa) and 2013 (Central/NW vs Northern) (26 total observations) |

---

## 4. Distinct Elections Master Table

| Event ID | Type | Poll Date (Raw) | Poll Date (Mapped) | Gap (Days) | Provinces (n) | Overlap Poll (±30 TD) | Proposal Sample (09–25) |
|:---|:---|:---:|:---:|:---:|:---|:---:|:---:|
| `ELEC_01` | Parliamentary | 2000-10-10 | `2000-10-10` | 0 | National | No | No (Pre-sample) |
| `ELEC_02` | Parliamentary | 2001-12-05 | `2001-12-05` | 0 | National | No | No (Pre-sample) |
| `ELEC_03` | Parliamentary | 2004-04-02 | `2004-04-02` | 0 | National | YES (12td) | No (Pre-sample) |
| `ELEC_04` | Provincial Council | 2004-04-25 | `2004-04-26` | 1 | 1 (North Western) | YES (12td) | No (Pre-sample) |
| `ELEC_05` | Provincial Council | 2004-07-10 | `2004-07-12` | 2 | 6 (Central; North Central; Sabaragamuwa; Southern; Uva; Western) | No | No (Pre-sample) |
| `ELEC_06` | Presidential | 2005-11-17 | `2005-11-17` | 0 | National | No | No (Pre-sample) |
| `ELEC_07` | Provincial Council | 2008-05-10 | `2008-05-12` | 2 | 1 (Eastern) | No | No (Pre-sample) |
| `ELEC_08` | Provincial Council | 2008-08-23 | `2008-08-25` | 2 | 2 (North Central; Sabaragamuwa) | No | No (Pre-sample) |
| `ELEC_09` | Provincial Council | 2009-02-14 | `2009-02-16` | 2 | 2 (Central; North Western) | No | YES |
| `ELEC_10` | Provincial Council | 2009-04-25 | `2009-04-27` | 2 | 1 (Western) | No | YES |
| `ELEC_11` | Provincial Council | 2009-08-08 | `2009-08-10` | 2 | 1 (Uva) | No | YES |
| `ELEC_12` | Provincial Council | 2009-10-10 | `2009-10-12` | 2 | 1 (Southern) | No | YES |
| `ELEC_13` | Presidential | 2010-01-26 | `2010-01-26` | 0 | National | No | YES |
| `ELEC_14` | Parliamentary | 2010-04-08 | `2010-04-08` | 0 | National | No | YES |
| `ELEC_15` | Provincial Council | 2012-09-08 | `2012-09-10` | 2 | 3 (Eastern; North Central; Sabaragamuwa) | No | YES |
| `ELEC_16` | Provincial Council | 2013-09-21 | `2013-09-23` | 2 | 3 (Central; North Western; Northern) | No | YES |
| `ELEC_17` | Provincial Council | 2014-03-29 | `2014-03-31` | 2 | 2 (Southern; Western) | No | YES |
| `ELEC_18` | Provincial Council | 2014-09-20 | `2014-09-22` | 2 | 1 (Uva) | No | YES |
| `ELEC_19` | Presidential | 2015-01-08 | `2015-01-08` | 0 | National | No | YES |
| `ELEC_20` | Parliamentary | 2015-08-17 | `2015-08-17` | 0 | National | No | YES |
| `ELEC_21` | Presidential | 2019-11-16 | `2019-11-18` | 2 | National | No | YES |
| `ELEC_22` | Parliamentary | 2020-08-05 | `2020-08-05` | 0 | National | No | YES |
| `ELEC_23` | Presidential | 2024-09-21 | `2024-09-23` | 2 | National | No | YES |
| `ELEC_24` | Parliamentary | 2024-11-14 | `2024-11-14` | 0 | National | No | YES |

---

## 5. Event Overlap & Confounding Analysis (±30 Trading Days)

In accordance with Event Study methodology (Brown & Warner 1985; MacKinlay 1997), overlapping event windows can contaminate abnormal return estimation:

1. **ELEC_03 (Parliamentary 2004-04-02) & ELEC_04 (Provincial Council Wayamba 2004-04-25):**
   - Polling dates are separated by only **12 trading days** (23 calendar days).
   - Parliamentary government formation occurred on `2004-04-22`, just 3 calendar days before the Wayamba provincial council poll!
   - *Action:* Flagged with `has_overlap_poll_30td = True`. Both events retained (Rule R1), but flagged for multi-event window controls in Stage 3.

2. **ELEC_23 (Presidential 2024-09-21) & ELEC_24 (Parliamentary 2024-11-14):**
   - Presidential polling date mapped to `2024-09-23` (trading day index 7329).
   - Parliamentary announcement date occurred on **`2024-09-24`** (trading day index 7330) — immediately following the presidential swearing-in!
   - Polling dates are 36 trading days apart, but their stage windows overlap continuously from September to November 2024.

---

## 6. Audit of Missing Events Named in Research Proposal (Rule R1, R11)

The research proposal report (`Predicting Stock Market Movements Using Government_Changes_updated.pdf`) explicitly discusses several political event categories and specific events that are **NOT** contained in `Elections.csv`:

### A. Local Government Elections
- **March 2025 LG Poll Announcement:** Proposal Section 1.6 (page 12) cites 'March 2025 announcement triggering panic selling' [29].
- **May 2025 LG Polling Date:** Proposal Section 1.6 (page 12) notes 'the May 2025 polls saw stocks slide 0.76% as the NPP failed to secure a majority, with the ASPI falling by 119.99 basis points' [30][31][32][33].
- **Historical LG Elections:** 2011 and February 2018 local government elections (SLPP emergence) are not present in `Elections.csv`.

### B. Ministry & Cabinet Transitions
- **21-Member Cabinet Formation (18 November 2024):** Mentioned in Proposal Abstract (page 3) and Section 1.5 (page 12).
- **October 2025 Cabinet Reshuffle:** Reorganizing the Lanka Electricity Company and energy sector state-owned enterprise (SOE) reforms (Proposal Abstract page 3).
- **Historical Cabinet Reshuffles:** Crucial macroeconomic leadership shifts (e.g., changes in Minister of Finance / Central Bank Governor appointments) are not in `Elections.csv`.

### C. Post-2024 Scheduled Provincial Council Elections
- **End-2025 Provincial Council Elections:** Proposal Abstract (page 3) notes 'Provincial Council elections, scheduled no later than end-2025'. Not in file as elections have been delayed since 2018.

### Protocol Implemented (Rules R1, R11):
- In strict adherence to Rule R1 ('Real data only... never invent, simulate, hard-code') and Rule R11 ('Do not state external facts from memory... verify from files or live check, record source, otherwise mark UNKNOWN'):
- **We have NOT added any missing events from memory.**
- A standardized template has been provided at: `data/raw/events_supplement_TEMPLATE.csv`.
- When the user/researcher provides a verified, sourced CSV at `data/raw/events_supplement.csv`, `cse.data.events.load_and_merge_events()` will automatically merge these records and tag them with `added_by_researcher = True`.

---

## 7. Artifacts & Deliverables Generated

| Deliverable | Path | Format | Rows / Size |
|:---|:---|:---:|:---:|
| Event-Level Dataset | `data/processed/events_event_level.parquet` | Parquet | 24 rows |
| Event-Level Dataset (CSV) | `data/processed/events_event_level.csv` | CSV | 24 rows |
| Stage-Level Dataset | `data/processed/events_stage_level.parquet` | Parquet | 144 rows |
| Stage-Level Dataset (CSV) | `data/processed/events_stage_level.csv` | CSV | 144 rows |
| Master Event Calendar | `data/processed/event_calendar.csv` | CSV | 140 mapped rows |
| Events Data Dictionary | `data/processed/events_data_dictionary.md` | Markdown | Comprehensive |
| Supplement Template | `data/raw/events_supplement_TEMPLATE.csv` | CSV | Schema Template |
| Historical Figure (1994–2025) | `results/figures/aspi_with_elections_1994_2025.png` | PNG | 300 DPI |
| Proposal Period Figure (2009–2025) | `results/figures/aspi_with_elections_proposal_period_2009_2025.png` | PNG | 300 DPI |
| Campaign Durations Figure | `results/figures/election_campaign_durations.png` | PNG | 300 DPI |
| Market Reaction Gaps Figure | `results/figures/election_trading_day_gaps.png` | PNG | 300 DPI |
