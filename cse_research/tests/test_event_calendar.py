"""Unit tests for Stage 2 Event Calendar, Date Mapping & Invariants (Rules R1, R2, R11, R12)."""

import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cse.data.events import (
    extract_province_from_row,
    map_date_to_trading_day,
    parse_elections_raw,
    build_event_level_table,
    build_stage_level_table,
    build_event_calendar,
    load_and_merge_events,
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
RAW_ELECTIONS_PATH = WORKSPACE_ROOT / "data" / "raw" / "Elections.csv"
CLEAN_CSE_PATH = WORKSPACE_ROOT / "data" / "processed" / "cse_clean.parquet"


@pytest.fixture(scope="module")
def elections_data():
    """Load parsed raw elections and clean CSE trading days."""
    df_raw = parse_elections_raw(RAW_ELECTIONS_PATH)
    df_cse = pd.read_parquet(CLEAN_CSE_PATH)
    df_events = build_event_level_table(df_raw, df_cse)
    df_stages = build_stage_level_table(df_raw, df_cse)
    df_calendar = build_event_calendar(df_stages)
    return {
        "df_raw": df_raw,
        "df_cse": df_cse,
        "df_events": df_events,
        "df_stages": df_stages,
        "df_calendar": df_calendar,
        "trading_days_set": set(df_cse["date"]),
    }


def test_raw_elections_parsing(elections_data):
    """Assert exactly 36 raw rows, proper columns, and 'Not Available' coerced to NaN."""
    df_raw = elections_data["df_raw"]
    assert len(df_raw) == 36
    assert "election_type" in df_raw.columns
    assert "election_date" in df_raw.columns

    # Verify 'Not Available' was turned into NaN in nomination start/end
    assert df_raw["nomination_period_start"].isna().sum() == 2
    assert df_raw["nomination_period_end"].isna().sum() == 2


def test_distinct_elections_count(elections_data):
    """Assert exactly 24 distinct elections across the 36 raw records."""
    df_events = elections_data["df_events"]
    assert len(df_events) == 24

    # 5 Presidential, 7 Parliamentary, 12 Provincial Council
    type_counts = df_events["election_type"].value_counts().to_dict()
    assert type_counts.get("Presidential") == 5
    assert type_counts.get("Parliamentary") == 7
    assert type_counts.get("Provincial Council") == 12


def test_mapped_date_not_earlier_than_raw(elections_data):
    """CRITICAL INVARIANT: No mapped market reaction date may be earlier than the raw calendar date."""
    df_stages = elections_data["df_stages"]
    valid_stages = df_stages[df_stages["mapped_date"].notna()]

    for _, r in valid_stages.iterrows():
        raw_d = pd.to_datetime(r["raw_date"]).date()
        map_d = pd.to_datetime(r["mapped_date"]).date()
        assert map_d >= raw_d, f"Violation in {r['event_id']}:{r['stage']}: mapped {map_d} < raw {raw_d}"


def test_every_mapped_date_is_trading_day(elections_data):
    """CRITICAL INVARIANT: Every mapped date must be an open trading day in cse_clean."""
    td_set = elections_data["trading_days_set"]
    df_stages = elections_data["df_stages"]
    df_events = elections_data["df_events"]
    df_calendar = elections_data["df_calendar"]

    for d in df_stages["mapped_date"].dropna():
        assert d in td_set, f"Stage mapped date {d} not in CSE trading days!"

    for d in df_calendar["mapped_date"]:
        assert d in td_set, f"Calendar mapped date {d} not in CSE trading days!"

    for d in df_events["polling_date_mapped"]:
        assert d in td_set, f"Event polling date {d} not in CSE trading days!"


def test_calendar_gaps_validity(elections_data):
    """Verify gap_days calculation is non-negative and matches date arithmetic."""
    df_stages = elections_data["df_stages"]
    valid = df_stages[df_stages["mapped_date"].notna()]

    for _, r in valid.iterrows():
        raw_d = pd.to_datetime(r["raw_date"]).date()
        map_d = pd.to_datetime(r["mapped_date"]).date()
        expected_gap = (map_d - raw_d).days
        assert r["gap_days"] == expected_gap
        assert r["gap_days"] >= 0


def test_proposal_sample_period_flags(elections_data):
    """Verify proposal sample period (Jan 2009 - Dec 2025) contains exactly 16 elections."""
    df_events = elections_data["df_events"]
    in_sample = df_events[df_events["sample_2009_2025"]]
    pre_sample = df_events[~df_events["sample_2009_2025"]]

    assert len(in_sample) == 16
    assert len(pre_sample) == 8
    assert len(in_sample) + len(pre_sample) == 24

    for _, r in in_sample.iterrows():
        d = pd.to_datetime(r["polling_date_raw"]).date()
        assert datetime.date(2009, 1, 1) <= d <= datetime.date(2025, 12, 31)

    for _, r in pre_sample.iterrows():
        d = pd.to_datetime(r["polling_date_raw"]).date()
        assert d < datetime.date(2009, 1, 1)


def test_overlap_detection(elections_data):
    """Verify that closely-spaced elections (ELEC_03 and ELEC_04) are flagged as overlapping."""
    df_events = elections_data["df_events"]
    elec3 = df_events[df_events["event_id"] == "ELEC_03"].iloc[0]
    elec4 = df_events[df_events["event_id"] == "ELEC_04"].iloc[0]

    assert elec3["has_overlap_poll_30td"] is True or elec3["has_overlap_poll_30td"] == 1
    assert elec4["has_overlap_poll_30td"] is True or elec4["has_overlap_poll_30td"] == 1
    assert elec3["min_dist_other_poll_td"] == 12
    assert elec4["min_dist_other_poll_td"] == 12


def test_provinces_assignment(elections_data):
    """Verify province extraction: Provincial Council rows have valid provinces, national have None."""
    df_raw = elections_data["df_raw"]
    valid_provinces = {
        "Western", "Central", "Southern", "Northern", "Eastern",
        "North Western", "North Central", "Uva", "Sabaragamuwa"
    }

    pc_rows = df_raw[df_raw["election_type"] == "Provincial Council"]
    for _, r in pc_rows.iterrows():
        p = extract_province_from_row(r)
        assert p in valid_provinces, f"Invalid province '{p}' extracted for row:\n{r}"

    national_rows = df_raw[df_raw["election_type"].isin(["Presidential", "Parliamentary"])]
    for _, r in national_rows.iterrows():
        p = extract_province_from_row(r)
        assert p is None, f"National election should not have province, got: {p}"


def test_saved_artifacts_exist():
    """Verify that all processed files and figures required by Stage 2 exist on disk."""
    proc = WORKSPACE_ROOT / "data" / "processed"
    figs = WORKSPACE_ROOT / "results" / "figures"
    tabs = WORKSPACE_ROOT / "results" / "tables"

    assert (proc / "events_event_level.parquet").exists()
    assert (proc / "events_event_level.csv").exists()
    assert (proc / "events_stage_level.parquet").exists()
    assert (proc / "events_stage_level.csv").exists()
    assert (proc / "event_calendar.csv").exists()
    assert (proc / "events_data_dictionary.md").exists()

    assert (figs / "aspi_with_elections_1994_2025.png").exists()
    assert (figs / "aspi_with_elections_proposal_period_2009_2025.png").exists()
    assert (figs / "election_campaign_durations.png").exists()
    assert (figs / "election_trading_day_gaps.png").exists()

    assert (tabs / "election_event_coverage.md").exists()
    assert (WORKSPACE_ROOT / "data" / "raw" / "events_supplement_TEMPLATE.csv").exists()
