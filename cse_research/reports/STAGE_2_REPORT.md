# STAGE 2 REPORT: Event Calendar Construction, Normalization & Trading Day Alignment

**Date**: 2026-10-11  
**Project**: Impact of Sri Lankan Political Events and News on the Colombo Stock Exchange (CSE) ASPI  
**Stage**: 2 (Electoral Event Calendar, Stage-Level Extraction, and Trading Day Mapping)  
**Status**: COMPLETE  

---

## 1. Executive Summary & Verification of Rules

Prior to initiating Stage 2, all twelve permanent research rules in [`RULES.md`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/RULES.md) were re-read, and sections 3.2 and 3.3 of the research proposal report (`Predicting Stock Market Movements Using Government_Changes_updated.pdf`) were reviewed:
- **Rule R1 (Real Data Only)**: All dates, event details, candidate information, and significance notes are parsed directly from `data/raw/Elections.csv` (SHA-256: `ac71d986fcbf121ed6eb1bd504cd573fbd711a5015e7188eb694d16c48cc043f`). Zero dates or event outcomes were simulated or hardcoded.
- **Rule R2 (Zero-Lookahead)**: Every market reaction date is strictly mapped forward ($M \ge D$) to the first open CSE trading session on or after the event date. Invariant verified: no mapped date is earlier than the raw event date.
- **Rule R6 (Save Everything to Disk)**: Event-level tables, stage-level tables, master event calendar, coverage reports, high-resolution figures, and data dictionaries are saved to disk in `data/processed/`, `results/tables/`, and `results/figures/`.
- **Rule R7 (Reproducibility)**: Exact SHA-256 hashes logged; all outputs reproducible via `python -m cse.run --stage 2` or `pytest tests/test_event_calendar.py`.
- **Rule R10 (Stage Discipline)**: Completed only Stage 2 tasks; generated this report and stopped.
- **Rule R11 (No Memory-Based Facts)**: Missing events referenced in the proposal (Local Government elections, Cabinet reshuffles) were not invented from memory. A standardized template (`data/raw/events_supplement_TEMPLATE.csv`) was created for researcher sourcing, with automated loader merging support.
- **Rule R12 (Code Quality)**: Typed modular implementation in [`src/cse/data/events.py`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/src/cse/data/events.py), unit tests in [`tests/test_event_calendar.py`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/tests/test_event_calendar.py) (9/9 passed, 21/21 full suite passing).

---

## 2. Key Metrics & Findings Summary

| Metric / Dimension | Value | Methodological / Research Implication |
|:---|:---:|:---|
| **Raw Records in Elections.csv** | 36 rows | 5 Presidential, 7 Parliamentary, 24 Provincial Council rows |
| **Distinct Election Events** | **24 events** | Multi-province elections sharing dates consolidated into single distinct events |
| **Presidential Elections** | 5 | 2005, 2010, 2015, 2019, 2024 (all national, $province = \text{NaN}$) |
| **Parliamentary Elections** | 7 | 2000, 2001, 2004, 2010, 2015, 2020, 2024 (all national, $province = \text{NaN}$) |
| **Provincial Council Events** | 12 | 6 single-province, 6 multi-province (contesting 1 to 6 provinces simultaneously) |
| **Proposal Sample Period (2009–2025)** | **16 events (66.7%)** | 4 Presidential, 4 Parliamentary, 8 Provincial Council |
| **Pre-Sample Baseline Period (2000–2008)** | **8 events (33.3%)** | 1 Presidential, 3 Parliamentary, 4 Provincial Council |
| **Total Stage Observations** | 146 records | 6 stages per election (announcement, nom_start, nom_end, poll, result, gov_formation) |
| **Mapped Trading Day Stages** | **142 stages** | 4 nomination stages marked 'Not Available' in raw archive left unmapped |
| **Reaction Day Gap = 0 (Trading Day)** | 148 dates (69.8%) | Event occurred directly on an open market session |
| **Reaction Day Gap = 1 Day (Sunday)** | 31 dates (14.6%) | Sunday result/formation mapped to Monday market open |
| **Reaction Day Gap = 2 Days (Saturday)** | 30 dates (14.2%) | Saturday poll/announcement mapped to Monday market open |
| **Reaction Day Gap = 3 Days (Holidays)** | 3 dates (1.4%) | Saturday/Sunday followed by public holiday market closure |
| **Severe Event Overlap ( $\le 30$ Trading Days)** | 2 events | ELEC_03 (2004 Parliamentary) and ELEC_04 (2004 Wayamba PC) are only **12 trading days** apart |
| **Sequential Stage Overlap** | ELEC_23 & ELEC_24 | 2024 Presidential formation (Sept 23) followed immediately by 2024 Parliamentary announcement (Sept 24, gap = 1 TD) |

---

## 3. What Was Built & Generated

### A. Modular Codebase
1. **[`src/cse/data/events.py`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/src/cse/data/events.py)**:
   - `parse_elections_raw`: Ingests and standardizes dates from raw `Elections.csv`, coercing `'Not Available'` to `NaN`.
   - `extract_province_from_row`: Grounded text-matching algorithm assigning each Provincial Council row to its exact Sri Lankan province.
   - `map_date_to_trading_day`: Maps calendar dates to the first open CSE session on or after the date using `cse_clean.parquet`.
   - `build_event_level_table`: Consolidates multi-province events, calculates `n_provinces`, extracts dates and summaries, and flags overlapping events and proposal sample inclusion.
   - `build_stage_level_table`: Generates one record per election per stage with trading day indexes and stage-level overlap diagnostics.
   - `build_event_calendar`: Produces the master chronological market reaction timeline.
   - `load_and_merge_events`: Unified loader supporting researcher supplement merging with `added_by_researcher = True`.
   - `generate_election_figures`: Produces 4 high-resolution diagnostic visualizations.
2. **CLI Integration in [`src/cse/run.py`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/src/cse/run.py)**:
   - `python -m cse.run --stage 2` runs the complete Stage 2 pipeline.
3. **Interactive Notebook [`notebooks/02_stage2_event_calendar.py`](file:///d:/SLIIT/YEAR%2004/Research/NEW%20Dev/cse_research/notebooks/02_stage2_event_calendar.py)**.

### B. Processed Datasets & Documentation
1. **`data/processed/events_event_level.parquet`** (24 rows, Parquet & CSV)
2. **`data/processed/events_stage_level.parquet`** (146 rows, Parquet & CSV)
3. **`data/processed/event_calendar.csv`** (142 rows, chronological trading day panel)
4. **`data/processed/events_data_dictionary.md`**: Complete schema, nullability, and definitions.
5. **`data/raw/events_supplement_TEMPLATE.csv`**: Standardized schema for user sourcing of missing events.
6. **`results/tables/election_event_coverage.md`**: Detailed coverage and gap analysis markdown table.

### C. Diagnostic Visualizations (300 DPI)
1. **`results/figures/aspi_with_elections_1994_2025.png`**: Full historical ASPI index (1994–2025) with election polling dates color-coded by election type.
2. **`results/figures/aspi_with_elections_proposal_period_2009_2025.png`**: Focused view of the proposal sample period (2009–2025) displaying shaded campaign windows (announcement to polling) and polling dates.
3. **`results/figures/election_campaign_durations.png`**: Horizontal bar chart comparing announcement-to-polling duration across all 24 elections.
4. **`results/figures/election_trading_day_gaps.png`**: Distribution of calendar day gaps to market reaction day.

---

## 4. Audit of Proposal-Referenced Events Missing from `Elections.csv`

In accordance with Rule R1 and Rule R11, we audited the research proposal report (`Predicting Stock Market Movements Using Government_Changes_updated.pdf`) against `Elections.csv` and identified that the following categories are **absent** from the raw CSV:

1. **Local Government Elections**:
   - *Proposal Reference:* Section 1.6 (page 12) cites the March 2025 local government poll announcement triggering market panic selling [29], and May 2025 polls where stocks declined 0.76% (119.99 basis points) as the ruling NPP failed to secure a majority [30][31][32][33].
   - *Historical Reference:* 2011 and February 2018 local government elections are also unlisted.
   - *Status in Elections.csv:* 0 rows.
2. **Ministry & Cabinet Transitions**:
   - *Proposal Reference:* Abstract (page 3) and Section 1.5 (page 12) discuss the 18 November 2024 21-member Cabinet formation, and the October 2025 cabinet reshuffle reorganizing the Lanka Electricity Company and energy sector state-owned enterprise (SOE) reforms.
   - *Status in Elections.csv:* 0 rows.
3. **Post-2024 Provincial Council Elections**:
   - *Proposal Reference:* Abstract (page 3) states 'Provincial Council elections, scheduled no later than end-2025'.
   - *Status in Elections.csv:* Delayed since 2018; 0 rows.

**Resolution Protocol**:
We did **not** inject any dates from memory. We created `data/raw/events_supplement_TEMPLATE.csv`. When the researcher provides a populated file at `data/raw/events_supplement.csv`, `cse.data.events.load_and_merge_events()` will automatically ingest and merge these rows with `added_by_researcher = True`.

---

## 5. Overlap & Confounding Windows (±30 Trading Days)

Event Study methodology requires identifying overlapping event windows to prevent abnormal return contamination:
1. **ELEC_03 (Parliamentary 2004-04-02) & ELEC_04 (Provincial Council Wayamba 2004-04-25)**:
   - Polling dates are only **12 trading days apart** (April 2 to April 26 mapped).
   - Parliamentary government formation occurred on April 22, just 3 calendar days before the Wayamba election.
2. **ELEC_23 (Presidential 2024-09-21) & ELEC_24 (Parliamentary 2024-11-14)**:
   - Presidential polling occurred on Saturday Sept 21 (mapped to Monday Sept 23).
   - Parliament was dissolved and new elections announced on Tuesday Sept 24 (just 1 trading day after presidential swearing-in).
   - Polling dates are 36 trading days apart, but their stage windows overlap continuously.

Both pairs are retained per Rule R1 and flagged with `has_overlap_poll_30td` and `is_overlapping_30td` to inform multi-event regression controls in Stage 3.

---

## 6. Verification of Unit Tests

Full test suite execution (`pytest tests/ -v`):
```
tests/test_data_ingest.py::test_parse_raw_date_century_mapping PASSED
tests/test_data_ingest.py::test_parse_numeric_cell PASSED
tests/test_data_ingest.py::test_no_duplicate_dates PASSED
tests/test_data_ingest.py::test_strictly_monotonic_dates PASSED
tests/test_data_ingest.py::test_sp20_no_backfill_and_has_sp20_flag PASSED
tests/test_data_ingest.py::test_aspi_log_returns PASSED
tests/test_event_calendar.py::test_raw_elections_parsing PASSED
tests/test_event_calendar.py::test_distinct_elections_count PASSED
tests/test_event_calendar.py::test_mapped_date_not_earlier_than_raw PASSED
tests/test_event_calendar.py::test_every_mapped_date_is_trading_day PASSED
tests/test_event_calendar.py::test_calendar_gaps_validity PASSED
tests/test_event_calendar.py::test_proposal_sample_period_flags PASSED
tests/test_event_calendar.py::test_overlap_detection PASSED
tests/test_event_calendar.py::test_provinces_assignment PASSED
tests/test_event_calendar.py::test_saved_artifacts_exist PASSED
tests/test_smoke.py::test_import_package PASSED
tests/test_smoke.py::test_load_config PASSED
tests/test_smoke.py::test_seed_reproducibility PASSED
tests/test_smoke.py::test_device_detection PASSED
tests/test_smoke.py::test_structured_logger PASSED
tests/test_smoke.py::test_raw_data_presence PASSED
============================== 21 passed in 4.84s ==============================
```

All 21 unit tests are passing.

---

## 7. Open Decisions & Next Stage Handoff

### Open Decisions Logged in `DECISIONS.md`:
1. **Consolidation Grain**: Grouped 36 raw rows into 24 distinct elections while retaining full provincial breakdown in `events_stage_level`.
2. **Trading Day Mapping Rule**: Next available CSE session ($M \ge D$) applied uniformly.
3. **Handling of Missing Dates**: Row 3 and Row 16 nomination dates kept strictly as `NaN` (no guessing).
4. **Researcher Supplement Handling**: Configured template and loader for `added_by_researcher = True`.

### Stage 3 Readiness:
Stage 2 is 100% complete and self-contained. The codebase is fully prepared for **Stage 3: Event Study Analysis & Abnormal Return Estimation (AR / CAR)** across 2, 7, 15, and 30-day windows.
