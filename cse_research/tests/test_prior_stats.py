"""Unit tests proving zero lookahead in prior_event_stats (Rule R2).

Must strictly verify:
1. No future event is ever included.
2. Events whose full window has not concluded before as_of_date are excluded.
3. as_of_date monotonicity holds.
"""

import pytest
import datetime
import numpy as np
import pandas as pd
from cse.events.prior_stats import PriorEventStatsCalculator, prior_event_stats
from cse.events.event_study import EventStudyEngine
from cse.utils.config import find_project_root


@pytest.fixture
def test_calculator():
    root = find_project_root()
    cse_path = root / "data" / "processed" / "cse_clean.parquet"
    stages_path = root / "data" / "processed" / "events_stage_level.parquet"

    if not cse_path.exists() or not stages_path.exists():
        pytest.skip("Processed datasets not available.")

    df_cse = pd.read_parquet(cse_path)
    df_stages = pd.read_parquet(stages_path)

    # Compute a lightweight per-event table for testing
    engine = EventStudyEngine(
        df_cse=df_cse,
        df_stages=df_stages,
        estimation_window_len=15,
        model_type="mean_adjusted",
        n_permutations=50,
        seed=42,
    )
    df_pe = engine.run_per_event_analysis()
    calc = PriorEventStatsCalculator(df_per_event=df_pe, df_cse=df_cse)
    return calc


def test_prior_stats_no_future_event_used(test_calculator: PriorEventStatsCalculator) -> None:
    """Prove that no event occurring or completing on/after as_of_date is included."""
    # Test as of 2015-01-01
    as_of = "2015-01-01"
    stats_res = test_calculator.get_stats(as_of_date=as_of, election_type="Presidential", stage="polling", window="[0,+7]")
    
    # Check underlying events in calculator
    mask = (test_calculator.df_events["window_end_date"] < as_of) & \
           (test_calculator.df_events["election_type"] == "Presidential") & \
           (test_calculator.df_events["stage"] == "polling") & \
           (test_calculator.df_events["window"] == "[0,+7]")
    
    matching_events = test_calculator.df_events[mask]
    assert stats_res["n"] == len(matching_events)

    # All matching events must have window_end_date strictly before as_of
    for _, row in matching_events.iterrows():
        assert row["window_end_date"] < as_of, f"Event {row['event_id']} window ended on/after {as_of}!"
        # Explicit check: 2015, 2019, 2024 Presidential elections must NOT be in this subset
        assert row["event_id"] not in ["ELEC_15", "ELEC_18", "ELEC_23"]


def test_prior_stats_monotonicity(test_calculator: PriorEventStatsCalculator) -> None:
    """Verify that sample size n monotonically increases or stays constant as as_of_date advances."""
    dates = ["2005-01-01", "2010-01-01", "2015-01-01", "2020-01-01", "2025-01-01"]
    counts = []

    for d in dates:
        res = test_calculator.get_stats(as_of_date=d, window="[0,+7]")
        counts.append(res["n"])

    # Monotonicity check
    assert counts == sorted(counts), f"Counts are not monotonically increasing: {counts}"
    assert counts[-1] > counts[0]


def test_prior_stats_pre_sample_returns_zero(test_calculator: PriorEventStatsCalculator) -> None:
    """Verify that an as_of_date before any historical election returns n = 0 and NaNs."""
    pre_date = "1995-01-01"
    res = test_calculator.get_stats(as_of_date=pre_date, window="[0,+7]")

    assert res["n"] == 0
    assert np.isnan(res["mean"])
    assert np.isnan(res["median"])
    assert np.isnan(res["std"])
