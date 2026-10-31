"""Unit tests for Event Study calculations, Brown-Warner tests, and FDR correction."""

import pytest
import numpy as np
import pandas as pd
from cse.events.event_study import EVENT_WINDOWS, EventStudyEngine, benjamini_hochberg
from cse.utils.config import find_project_root


@pytest.fixture
def cse_and_stages_data():
    root = find_project_root()
    cse_path = root / "data" / "processed" / "cse_clean.parquet"
    stages_path = root / "data" / "processed" / "events_stage_level.parquet"

    if not cse_path.exists() or not stages_path.exists():
        pytest.skip("Processed datasets not available.")

    df_cse = pd.read_parquet(cse_path)
    df_stages = pd.read_parquet(stages_path)
    return df_cse, df_stages


def test_benjamini_hochberg_correction() -> None:
    """Verify Benjamini-Hochberg FDR p-value adjustment."""
    raw_p = np.array([0.01, 0.04, 0.03, 0.20])
    adj_p = benjamini_hochberg(raw_p)

    assert len(adj_p) == len(raw_p)
    # Adjusted p-values must be greater than or equal to raw p-values
    assert np.all(adj_p >= raw_p)
    # Must be bounded in [0, 1]
    assert np.all((adj_p >= 0.0) & (adj_p <= 1.0))
    # Ranking order preserved
    assert adj_p[0] <= adj_p[2] <= adj_p[1] <= adj_p[3]


def test_event_windows_definitions() -> None:
    """Verify all 9 event windows are correctly defined."""
    expected_windows = [
        "[0,+2]", "[0,+7]", "[0,+15]", "[0,+30]",
        "[-7,-1]", "[-15,-1]", "[-30,-1]",
        "[-2,+2]", "[-7,+7]",
    ]
    for w in expected_windows:
        assert w in EVENT_WINDOWS
        w_start, w_end = EVENT_WINDOWS[w]
        assert w_start <= w_end


def test_event_study_engine_execution(cse_and_stages_data) -> None:
    """Verify EventStudyEngine runs and generates valid CARs and tests."""
    df_cse, df_stages = cse_and_stages_data

    # Use smaller permutation count for fast unit test
    engine = EventStudyEngine(
        df_cse=df_cse,
        df_stages=df_stages,
        estimation_window_len=15,
        model_type="mean_adjusted",
        n_permutations=200,
        seed=42,
    )

    df_pe = engine.run_per_event_analysis()
    assert len(df_pe) > 0
    assert "car" in df_pe.columns
    assert "bw_t_stat" in df_pe.columns
    assert "placebo_p_val" in df_pe.columns
    assert "placebo_percentile" in df_pe.columns

    # Verify Brown-Warner formula: t = CAR / BW_SE
    valid = df_pe[df_pe["bw_se"] > 0].iloc[0]
    expected_t = valid["car"] / valid["bw_se"]
    assert np.isclose(valid["bw_t_stat"], expected_t, rtol=1e-5)


def test_cross_event_aggregation(cse_and_stages_data) -> None:
    """Verify CAAR cross-event aggregation and small sample warning."""
    df_cse, df_stages = cse_and_stages_data

    engine = EventStudyEngine(
        df_cse=df_cse,
        df_stages=df_stages,
        estimation_window_len=15,
        model_type="mean_adjusted",
        n_permutations=100,
        seed=42,
    )
    df_pe = engine.run_per_event_analysis()
    agg = engine.aggregate_caar(df_pe, ["election_type", "window"], sample_scope="all")

    assert len(agg) > 0
    assert "caar" in agg.columns
    assert "n" in agg.columns
    assert "warn_small_sample" in agg.columns
    assert "t_stat" in agg.columns
    assert "sign_test_pval" in agg.columns

    # Small sample warning must flag n < 5
    for _, row in agg.iterrows():
        if row["n"] < 5:
            assert row["warn_small_sample"] is True
        else:
            assert row["warn_small_sample"] is False
