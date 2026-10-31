"""Data ingestion, validation, and preprocessing modules (Rule R1, R4)."""

from cse.data.ingest import ingest_cse_raw, compute_file_sha256
from cse.data.audit import (
    compute_calendar_gaps,
    compute_trading_days_per_year,
    compute_missingness_by_year,
    compute_column_summaries,
    investigate_large_returns,
    check_consistency_and_outliers,
    run_stationarity_tests,
    generate_figures,
)
from cse.data.events import (
    parse_elections_raw,
    build_event_level_table,
    build_stage_level_table,
    build_event_calendar,
    load_and_merge_events,
    generate_election_figures,
    extract_province_from_row,
    map_date_to_trading_day,
)

__all__ = [
    "ingest_cse_raw",
    "compute_file_sha256",
    "compute_calendar_gaps",
    "compute_trading_days_per_year",
    "compute_missingness_by_year",
    "compute_column_summaries",
    "investigate_large_returns",
    "check_consistency_and_outliers",
    "run_stationarity_tests",
    "generate_figures",
    "parse_elections_raw",
    "build_event_level_table",
    "build_stage_level_table",
    "build_event_calendar",
    "load_and_merge_events",
    "generate_election_figures",
    "extract_province_from_row",
    "map_date_to_trading_day",
]
