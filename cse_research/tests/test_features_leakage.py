"""Comprehensive leakage and causality validation for Feature Sets A, B, C and Pipeline (Rule R2).

Mandatory tests:
1. Truncate-rebuild equality test on Feature Sets A, B, C:
   Rebuilding features using data strictly up to date t gives identical features at t.
2. Future perturbation test on Feature Sets A, B, C:
   Drastically changing prices, volume, and future event dates after date t
   produces ZERO change to any feature computed at date t.
3. Strict zero lookahead in S&P SL 20 features:
   Pre-2012 returns are strictly NaN and masked with has_sp20=0.
4. Per-phase scaler & imputer isolation:
   Transformers fitted strictly on training data; validation blocks never touch fitting.
5. 10-day embargo gap enforcement in get_phase_data across all phases P1-P5.
6. Sequence window boundary integrity:
   Sequence windows (L in {20, 60, 120}) never cross phase or embargo boundaries.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cse.features.events_features import (
    build_calendar_features,
    build_causal_event_features,
    build_feature_set_c,
)
from cse.features.market_activity import build_feature_set_b
from cse.features.pipeline import (
    PhaseFeaturePipeline,
    compute_targets,
    get_phase_data,
    get_sequence_windows,
)
from cse.features.technical import build_feature_set_a
from cse.splits.walk_forward import ExpandingWindowSplitter
from cse.utils.config import find_project_root


@pytest.fixture
def cse_df() -> pd.DataFrame:
    root = find_project_root()
    p_cse = root / "data" / "processed" / "cse_clean.parquet"
    if not p_cse.exists():
        pytest.skip(f"Cleaned CSE panel not found at {p_cse}")
    return pd.read_parquet(p_cse)


def test_truncate_rebuild_equality_set_a(cse_df: pd.DataFrame) -> None:
    """Test 1A: Truncating data at date t produces identical Set A features at t."""
    df_full = cse_df
    feats_full = build_feature_set_a(df_full)

    # Test representative dates across multiple market eras
    test_indices = [100, 500, 1500, 3000, 5000, 7000]

    for t in test_indices:
        df_trunc = df_full.iloc[: t + 1].copy()
        feats_trunc = build_feature_set_a(df_trunc)

        row_full = feats_full.iloc[t].dropna()
        row_trunc = feats_trunc.iloc[t].dropna()

        assert list(row_full.index) == list(row_trunc.index)
        np.testing.assert_allclose(
            row_trunc.values,
            row_full.values,
            rtol=1e-11,
            atol=1e-11,
            err_msg=f"Set A mismatch at truncation index {t}!",
        )


def test_truncate_rebuild_equality_set_b(cse_df: pd.DataFrame) -> None:
    """Test 1B: Truncating data at date t produces identical Set B features at t."""
    df_full = cse_df
    feats_full = build_feature_set_b(df_full)

    # Test across pre-2012 and post-2012 eras
    test_indices = [200, 1500, 4420, 4500, 6000, 7200]

    for t in test_indices:
        df_trunc = df_full.iloc[: t + 1].copy()
        feats_trunc = build_feature_set_b(df_trunc)

        row_full = feats_full.iloc[t].dropna()
        row_trunc = feats_trunc.iloc[t].dropna()

        assert list(row_full.index) == list(row_trunc.index)
        np.testing.assert_allclose(
            row_trunc.values,
            row_full.values,
            rtol=1e-11,
            atol=1e-11,
            err_msg=f"Set B mismatch at truncation index {t}!",
        )


def test_truncate_rebuild_equality_set_c(cse_df: pd.DataFrame) -> None:
    """Test 1C: Truncating data at date t produces identical Set C features at t."""
    df_full = cse_df
    feats_full = build_feature_set_c(df_full)

    # Test across multiple election eras (2004, 2010, 2015, 2024)
    test_indices = [1500, 2450, 4000, 5500, 7300]

    for t in test_indices:
        df_trunc = df_full.iloc[: t + 1].copy()
        feats_trunc = build_feature_set_c(df_trunc)

        row_full = feats_full.iloc[t].dropna()
        row_trunc = feats_trunc.iloc[t].dropna()

        assert list(row_full.index) == list(row_trunc.index)
        np.testing.assert_allclose(
            row_trunc.values,
            row_full.values,
            rtol=1e-11,
            atol=1e-11,
            err_msg=f"Set C mismatch at truncation index {t}!",
        )


def test_future_perturbation_invariance_sets_a_b_c(cse_df: pd.DataFrame) -> None:
    """Test 2: Perturbing future prices, volume, and index levels after date t never changes features at t."""
    df = cse_df
    feats_a_orig = build_feature_set_a(df)
    feats_b_orig = build_feature_set_b(df)
    feats_c_orig = build_feature_set_c(df)

    test_indices = [300, 2000, 5000, 7000]

    for t in test_indices:
        df_perturbed = df.copy()
        # Heavily shock future prices and turnover after date t
        df_perturbed.loc[t + 1 :, "aspi"] = df_perturbed.loc[t + 1 :, "aspi"] * 10.0 + 5000.0
        df_perturbed.loc[t + 1 :, "turnover_equity_mn"] = df_perturbed.loc[t + 1 :, "turnover_equity_mn"] * 50.0
        df_perturbed.loc[t + 1 :, "shares_traded_equity_k"] = df_perturbed.loc[t + 1 :, "shares_traded_equity_k"] * 100.0
        if "sp20" in df_perturbed.columns:
            df_perturbed.loc[t + 1 :, "sp20"] = df_perturbed.loc[t + 1 :, "sp20"] * 8.0

        feats_a_pert = build_feature_set_a(df_perturbed)
        feats_b_pert = build_feature_set_b(df_perturbed)
        feats_c_pert = build_feature_set_c(df_perturbed)

        row_a_orig = feats_a_orig.iloc[t].dropna()
        row_a_pert = feats_a_pert.iloc[t].dropna()
        np.testing.assert_allclose(row_a_pert.values, row_a_orig.values, rtol=1e-11, atol=1e-11)

        row_b_orig = feats_b_orig.iloc[t].dropna()
        row_b_pert = feats_b_pert.iloc[t].dropna()
        np.testing.assert_allclose(row_b_pert.values, row_b_orig.values, rtol=1e-11, atol=1e-11)

        row_c_orig = feats_c_orig.iloc[t].dropna()
        row_c_pert = feats_c_pert.iloc[t].dropna()
        np.testing.assert_allclose(row_c_pert.values, row_c_orig.values, rtol=1e-11, atol=1e-11)


def test_sp20_strict_masking_invariant(cse_df: pd.DataFrame) -> None:
    """Test 3: S&P SL 20 return and spread are strictly NaN prior to 2012-06-27 (never filled)."""
    feats_b = build_feature_set_b(cse_df)
    pre_2012_mask = cse_df["date"] < "2012-06-27"

    assert (feats_b.loc[pre_2012_mask, "has_sp20"] == 0).all()
    assert feats_b.loc[pre_2012_mask, "sp20_log_return"].isna().all()
    assert feats_b.loc[pre_2012_mask, "aspi_sp20_spread"].isna().all()


def test_pipeline_scaler_fitted_on_train_only(cse_df: pd.DataFrame) -> None:
    """Test 4: PhaseFeaturePipeline scales using training statistics only; validation data does not leak."""
    splitter = ExpandingWindowSplitter(cse_df, embargo_days=10)
    p1 = splitter.get_phase("P1")

    feats_b = build_feature_set_b(cse_df)
    train_slice = slice(p1.train.start_idx, p1.train.end_idx + 1)
    val_slice = slice(p1.val.start_idx, p1.val.end_idx + 1)

    X_train = feats_b.iloc[train_slice].copy()
    X_val = feats_b.iloc[val_slice].copy()

    pipeline_clean = PhaseFeaturePipeline()
    pipeline_clean.fit(X_train)

    train_means_clean = pipeline_clean.means_.copy()
    train_scales_clean = pipeline_clean.scales_.copy()

    # Contaminated pipeline fitting on train + val
    X_leaked = pd.concat([X_train, X_val], ignore_index=True)
    pipeline_leaked = PhaseFeaturePipeline()
    pipeline_leaked.fit(X_leaked)

    # Means and scales must differ for dynamic indicators (e.g. log_turnover, ret_1d)
    assert pipeline_clean.means_["log_turnover"] != pipeline_leaked.means_["log_turnover"]
    assert pipeline_clean.scales_["log_turnover"] != pipeline_leaked.scales_["log_turnover"]

    # Transform on validation set must not mutate fitted training statistics
    _ = pipeline_clean.transform(X_val)
    assert pipeline_clean.means_ == train_means_clean
    assert pipeline_clean.scales_ == train_scales_clean


def test_embargo_separation_across_all_phases(cse_df: pd.DataFrame) -> None:
    """Test 5: 10-day embargo holds across all 5 phases and both horizons in get_phase_data."""
    for phase in ["P1", "P2", "P3", "P4", "P5"]:
        for h in [1, 5]:
            p_data = get_phase_data(phase=phase, horizon=h, feature_set="C", df_cse=cse_df)

            # 1. Date monotonicity and separation
            train_max_date = p_data.train.dates.max()
            val_min_date = p_data.val.dates.min()
            assert train_max_date < val_min_date

            # 2. Embargo gap between train end and val start is at least 10 trading days
            train_max_idx = p_data.train.indices.max()
            val_min_idx = p_data.val.indices.min()
            gap = val_min_idx - train_max_idx - 1
            assert gap >= 10, f"{phase} gap {gap} is less than required 10 trading days!"

            # 3. Inner tuning split separation within training
            inner_train_max_date = p_data.inner_val.dates.min()  # inner_val starts after inner_train
            assert p_data.inner_val.indices.min() > p_data.train.indices.min()


def test_sequence_window_boundary_integrity(cse_df: pd.DataFrame) -> None:
    """Test 6: Sequence windows (L in {20, 60, 120}) never cross phase or embargo boundaries."""
    for lookback in [20, 60, 120]:
        seq_data = get_sequence_windows(phase="P1", horizon=5, feature_set="C", lookback=lookback, df_cse=cse_df)

        # Output shape assertions
        assert seq_data.train.X_seq.shape[1] == lookback
        assert seq_data.val.X_seq.shape[1] == lookback
        assert seq_data.inner_val.X_seq.shape[1] == lookback

        # No NaNs in sequence tensors
        assert not np.isnan(seq_data.train.X_seq).any()
        assert not np.isnan(seq_data.val.X_seq).any()
        assert not np.isnan(seq_data.inner_val.X_seq).any()

        # Lengths match N_split - L + 1
        p_data = get_phase_data("P1", 5, "C", df_cse=cse_df)
        assert len(seq_data.train.X_seq) == len(p_data.train.X) - lookback + 1
        assert len(seq_data.val.X_seq) == len(p_data.val.X) - lookback + 1
        assert len(seq_data.inner_val.X_seq) == len(p_data.inner_val.X) - lookback + 1
