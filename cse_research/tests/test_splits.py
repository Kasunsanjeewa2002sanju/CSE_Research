"""Unit tests for walk-forward expanding window cross-validation splits and embargo gaps."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from cse.splits import ExpandingWindowSplitter, PhaseSplit
from cse.utils.config import find_project_root, load_config


@pytest.fixture
def clean_cse_df() -> pd.DataFrame:
    """Fixture providing clean historical CSE data."""
    root = find_project_root()
    df_path = root / "data" / "processed" / "cse_clean.parquet"
    if not df_path.exists():
        pytest.skip(f"Processed file {df_path} does not exist.")
    return pd.read_parquet(df_path)


def test_expanding_window_splitter_initialization(clean_cse_df: pd.DataFrame) -> None:
    """Verify splitter initializes all 5 phases correctly."""
    splitter = ExpandingWindowSplitter(clean_cse_df)
    assert len(splitter.splits) == 5
    for p in ["P1", "P2", "P3", "P4", "P5"]:
        assert p in splitter.splits


def test_embargo_gap_enforcement(clean_cse_df: pd.DataFrame) -> None:
    """Verify that every phase has an embargo gap of exactly 10 trading days."""
    splitter = ExpandingWindowSplitter(clean_cse_df, embargo_days=10)
    for phase_name, split in splitter.splits.items():
        # Embargo must have exactly 10 trading days
        assert split.embargo.n_days == 10, f"Embargo not 10 days for {phase_name}"
        
        # Chronological order: train end < embargo start <= embargo end < val start
        assert split.train.end_idx < split.embargo.start_idx
        assert split.embargo.start_idx <= split.embargo.end_idx
        assert split.embargo.end_idx < split.val.start_idx
        
        # Embargo gap strictly separates train from val
        assert split.embargo.start_idx == split.train.end_idx + 1
        assert split.val.start_idx == split.embargo.end_idx + 1
        
        # Dates must be strictly increasing
        assert split.train.end_date < split.embargo.start_date
        assert split.embargo.end_date < split.val.start_date


def test_inner_tuning_split(clean_cse_df: pd.DataFrame) -> None:
    """Verify inner chronological tuning split within training window."""
    splitter = ExpandingWindowSplitter(clean_cse_df, inner_tune_ratio=0.15, inner_embargo_days=10)
    for phase_name, split in splitter.splits.items():
        n_train = split.train.n_days
        n_inner_val = split.inner_val.n_days
        n_inner_emb = split.inner_embargo.n_days
        n_inner_tr = split.inner_train.n_days

        # Inner val is approximately 15% of train
        expected_inner_val = int(np.floor(n_train * 0.15))
        assert n_inner_val == expected_inner_val
        assert n_inner_emb == 10

        # Total partition of training set
        assert n_inner_tr + n_inner_emb + n_inner_val == n_train

        # Chronology of inner splits
        assert split.inner_train.end_idx + 1 == split.inner_embargo.start_idx
        assert split.inner_embargo.end_idx + 1 == split.inner_val.start_idx
        assert split.inner_val.end_idx == split.train.end_idx


def test_summary_table(clean_cse_df: pd.DataFrame) -> None:
    """Verify summary table generation."""
    splitter = ExpandingWindowSplitter(clean_cse_df)
    table = splitter.summary_table()
    assert len(table) == 5
    assert "phase" in table.columns
    assert "train_days" in table.columns
    assert "val_days" in table.columns
    assert "embargo_days" in table.columns

    # Verify expanding property: train_days must increase monotonically
    train_counts = table["train_days"].tolist()
    assert train_counts == sorted(train_counts)
    assert len(set(train_counts)) == 5
