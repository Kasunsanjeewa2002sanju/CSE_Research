# Events Data Dictionary (Stage 2)

**Authoritative Source:** `data/raw/Elections.csv` (SHA-256: `ac71d986fcbf121ed6eb1bd504cd573fbd711a5015e7188eb694d16c48cc043f`)  
**Trading Baseline:** `data/processed/cse_clean.parquet` (7,635 trading days, 1994-01-03 to 2025-12-31)  
**Permanent Rules Applied:** R1 (Real data only), R2 (Zero-lookahead), R11 (Sourced verification), R12 (Strict typing & validation).

---

## 1. Table: `events_event_level`
**Files:** `data/processed/events_event_level.parquet` | `data/processed/events_event_level.csv`  
**Grain:** One row per distinct election event ($N = 24$ rows). Multi-province Provincial Council elections sharing the same election date are consolidated with provincial detail preserved.

| Column Name | Data Type | Nullable | Source Field / Formula | Description | Example Values |
|:---|:---:|:---:|:---|:---|:---|
| `event_id` | String | No | Generated sequence | Unique canonical event identifier | `ELEC_01`, `ELEC_23` |
| `election_type` | String | No | `election_type` | Category of election: Presidential, Parliamentary, or Provincial Council | `Presidential`, `Parliamentary`, `Provincial Council` |
| `n_provinces` | Integer | No | Aggregated count | Number of provinces contested (1 for national; 1 to 6 for Provincial Council) | `1`, `6` |
| `province` | String | Yes | Grounded text extraction | Province name(s) for Provincial Council elections; null for national elections | `North Western`, `Central; North Central; Sabaragamuwa; Southern; Uva; Western` |
| `announcement_date_raw` | String (ISO) | No | `election_announcement_date` | Proclamation date in official gazette / announcement | `2024-07-26` |
| `announcement_date_mapped` | String (ISO) | No | Next trading day $\ge$ raw | First open CSE trading day on or after announcement | `2024-07-26` |
| `announcement_gap_days` | Integer | No | `mapped - raw` (calendar days) | Days between calendar announcement and market reaction day | `0`, `1`, `2` |
| `nomination_start_raw` | String (ISO) | Yes | `nomination_period_start` | First date of candidate nomination window | `2024-08-15` (Null for ELEC_04 & ELEC_10) |
| `nomination_start_mapped` | String (ISO) | Yes | Next trading day $\ge$ raw | First open CSE trading day on or after nomination start | `2024-08-15` |
| `nomination_start_gap_days` | Integer | Yes | `mapped - raw` | Calendar gap to market reaction day | `0`, `2` |
| `nomination_end_raw` | String (ISO) | Yes | `nomination_period_end` | Final nomination deadline | `2024-08-15` |
| `nomination_end_mapped` | String (ISO) | Yes | Next trading day $\ge$ raw | First open CSE trading day on or after nomination deadline | `2024-08-15` |
| `nomination_end_gap_days` | Integer | Yes | `mapped - raw` | Calendar gap to market reaction day | `0`, `2` |
| `polling_date_raw` | String (ISO) | No | `election_date` | Date citizens cast ballots (polling day) | `2024-09-21` |
| `polling_date_mapped` | String (ISO) | No | Next trading day $\ge$ raw | First open CSE trading day on or after polling day | `2024-09-23` |
| `polling_gap_days` | Integer | No | `mapped - raw` | Calendar gap (e.g. Saturday poll $\to$ Monday reaction = 2 days) | `0`, `1`, `2` |
| `result_date_raw` | String (ISO) | No | `election_result_date` | Official declaration of results | `2024-09-22` |
| `result_date_mapped` | String (ISO) | No | Next trading day $\ge$ raw | First open CSE trading day on or after result announcement | `2024-09-23` |
| `result_gap_days` | Integer | No | `mapped - raw` | Calendar gap to market reaction day | `0`, `1` |
| `government_formation_raw` | String (ISO) | No | `government_formation_date` | Date of swearing-in / cabinet or board of ministers appointment (earliest) | `2024-09-23` |
| `government_formation_mapped` | String (ISO) | No | Next trading day $\ge$ raw | First open CSE trading day on or after government formation | `2024-09-23` |
| `government_formation_gap_days` | Integer | No | `mapped - raw` | Calendar gap to market reaction day | `0` |
| `government_formation_latest_raw` | String (ISO) | Yes | Latest formation date | Latest formation date across provinces (for staggered multi-province councils) | `2012-09-24` |
| `government_formation_latest_mapped` | String (ISO) | Yes | Next trading day $\ge$ raw | Mapped trading day for latest formation date | `2012-09-24` |
| `government_formation_latest_gap_days` | Integer | Yes | `mapped - raw` | Calendar gap for latest formation date | `0` |
| `poll_trading_day_index` | Integer | No | CSE calendar index | Integer index of mapped polling date in `cse_clean` ($0 \dots 7634$) | `7329` |
| `sample_2009_2025` | Boolean | No | Polling date filter | True if polling date falls in proposal sample period (`2009-01-01` to `2025-12-31`) | `True`, `False` |
| `has_overlap_poll_30td` | Boolean | No | $\min \|t_i - t_j\| \le 30$ | True if polling day is within $\pm 30$ trading days of another distinct election poll | `True` (ELEC_03, ELEC_04), `False` |
| `min_dist_other_poll_td` | Integer | No | $\min \|t_i - t_j\|$ | Minimum trading days to the polling day of any other distinct election | `12`, `36`, `118` |
| `overlapping_events_poll_30td` | String | Yes | ID and distance list | IDs and trading day distances of overlapping elections | `ELEC_04(12td)` |
| `candidate_party_info` | String | No | Raw archive | Summary of contesting parties, major candidates, and seat totals | `"United National Front (109 seats)..."` |
| `event_significance` | String | No | Raw archive | Contextual description of electoral outcome and political significance | `"Snap election called following..."` |
| `source_of_information` | String | No | Raw archive | Authoritative documentary reference (Gazette, Election Commission, Handbook) | `"Parliament Handbook; Gazette..."` |
| `relevant_context` | String | No | Raw archive | Macro-political and historical contextual background | `"Fragile coalition collapsed..."` |
| `added_by_researcher` | Boolean | No | Metadata flag | False for primary records from `Elections.csv`; True for researcher supplement rows | `False` |

---

## 2. Table: `events_stage_level`
**Files:** `data/processed/events_stage_level.parquet` | `data/processed/events_stage_level.csv`  
**Grain:** One row per election event per electoral stage ($N = 146$ rows).

| Column Name | Data Type | Nullable | Description | Example Values |
|:---|:---:|:---:|:---|:---|
| `event_id` | String | No | Canonical event identifier | `ELEC_01` |
| `election_type` | String | No | Presidential, Parliamentary, or Provincial Council | `Presidential` |
| `stage` | String | No | Electoral stage: `announcement`, `nomination_start`, `nomination_end`, `polling`, `result`, `government_formation` | `announcement`, `polling` |
| `raw_date` | String (ISO) | Yes | Original calendar date from archive (`YYYY-MM-DD`). Null if marked 'Not Available' | `2024-09-21` |
| `mapped_date` | String (ISO) | Yes | First open CSE trading day on or after `raw_date`. Null if `raw_date` is missing | `2024-09-23` |
| `gap_days` | Float/Int | Yes | Calendar days elapsed between `raw_date` and `mapped_date` | `0.0`, `2.0` |
| `raw_weekday` | String | Yes | Day of the week for `raw_date` | `Sat`, `Sun`, `Fri` |
| `mapped_weekday` | String | Yes | Day of the week for `mapped_date` (guaranteed Monday–Friday) | `Mon`, `Tue` |
| `is_trading_day_raw` | Boolean | No | True if `raw_date` occurred directly on an open trading day (`gap_days == 0`) | `True`, `False` |
| `trading_day_index` | Integer | No | Integer trading day index in `cse_clean` (-1 if unmapped) | `7329` |
| `n_provinces` | Integer | No | Number of provinces contested | `1`, `6` |
| `province` | String | Yes | Province name(s) | `Western`, `Central` |
| `sample_2009_2025` | Boolean | No | True if polling date $\in [2009-01-01, 2025-12-31]$ | `True` |
| `is_overlapping_30td` | Boolean | No | True if this stage date is within $\pm 30$ trading days of any stage of another election | `True`, `False` |
| `nearest_other_event_stage_td` | Integer | Yes | Minimum trading days to any stage of another distinct election | `1`, `12` |
| `overlapping_stage_details` | String | Yes | Semicolon-separated details of stages within $\pm 30$ trading days | `ELEC_24:announcement(1td)` |
| `candidate_party_info` | String | No | Contesting parties and candidates | Text |
| `event_significance` | String | No | Significance text | Text |
| `source_of_information` | String | No | Source citation | Text |
| `relevant_context` | String | No | Context narrative | Text |
| `added_by_researcher` | Boolean | No | False for `Elections.csv` rows; True for supplemental events | `False` |

---

## 3. Table: `event_calendar.csv`
**File:** `data/processed/event_calendar.csv`  
**Grain:** Master trading day reaction timeline ($N = 142$ mapped rows). Sorted strictly chronologically by `mapped_date`.  
**Purpose:** Ready for direct time-series joining against `cse_clean` trading panel on `mapped_date == cse_clean.date` for Stage 3 Event Study AR/CAR computations.
