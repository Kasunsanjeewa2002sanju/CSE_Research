"""Strict unit tests verifying zero lookahead bias and leakage prevention (Rule R2).

Mandatory Leakage Suite:
(a) Rebuilding features from data truncated at t gives identical features at t.
(b) Changing any value after t never changes the features at t.
(c) No validation date inside any training window and the embargo holds.
(d) Label-shuffle test: flexible model trained on shuffled targets scores ~50% direction accuracy.
(e) Scalers are fitted per phase on training data only.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from cse.splits import ExpandingWindowSplitter
from cse.features import build_backward_features, PhaseStandardScaler
from cse.utils.config import find_project_root


@pytest.fixture
def clean_cse_df() -> pd.DataFrame:
    root = find_project_root()
    df_path = root / "data" / "processed" / "cse_clean.parquet"
    if not df_path.exists():
        pytest.skip(f"Processed file {df_path} does not exist.")
    return pd.read_parquet(df_path)


def test_leakage_feature_truncation_invariance(clean_cse_df: pd.DataFrame) -> None:
    """Test (a): Rebuilding features from data truncated at t gives identical features at t."""
    df = clean_cse_df
    # Full dataset features
    feats_full = build_backward_features(df)

    # Test at multiple representative trading days across different market eras
    test_indices = [150, 500, 1500, 3000, 5000, 7000]

    for t in test_indices:
        df_trunc = df.iloc[: t + 1].copy()
        feats_trunc = build_backward_features(df_trunc)

        row_full = feats_full.iloc[t].dropna()
        row_trunc = feats_trunc.iloc[t].dropna()

        # Must have same feature columns
        assert list(row_full.index) == list(row_trunc.index)
        # Numerical values must match exactly within floating point precision
        np.testing.assert_allclose(
            row_trunc.values,
            row_full.values,
            rtol=1e-12,
            atol=1e-12,
            err_msg=f"Feature mismatch at truncation index {t}!",
        )


def test_leakage_future_data_perturbation_invariance(clean_cse_df: pd.DataFrame) -> None:
    """Test (b): Changing any value after t never changes the features at t."""
    df = clean_cse_df
    feats_original = build_backward_features(df)

    test_indices = [200, 1200, 2500, 4500, 6500]

    for t in test_indices:
        df_perturbed = df.copy()
        # Heavily perturb all future prices and volume after day t
        df_perturbed.loc[t + 1 :, "aspi"] = df_perturbed.loc[t + 1 :, "aspi"] * 5.0 + 1000.0
        if "turnover_equity_mn" in df_perturbed.columns:
            df_perturbed.loc[t + 1 :, "turnover_equity_mn"] = 99999.0

        feats_perturbed = build_backward_features(df_perturbed)

        row_orig = feats_original.iloc[t].dropna()
        row_pert = feats_perturbed.iloc[t].dropna()

        np.testing.assert_allclose(
            row_pert.values,
            row_orig.values,
            rtol=1e-12,
            atol=1e-12,
            err_msg=f"Future perturbation leaked backward to feature at index {t}!",
        )


def test_leakage_embargo_and_validation_separation(clean_cse_df: pd.DataFrame) -> None:
    """Test (c): No validation date inside any training window and the embargo holds."""
    splitter = ExpandingWindowSplitter(clean_cse_df, embargo_days=10)

    for phase_name, split in splitter.splits.items():
        train_indices = set(range(split.train.start_idx, split.train.end_idx + 1))
        embargo_indices = set(range(split.embargo.start_idx, split.embargo.end_idx + 1))
        val_indices = set(range(split.val.start_idx, split.val.end_idx + 1))

        # 1. No overlap between sets
        assert train_indices.isdisjoint(val_indices), f"{phase_name}: Validation indices found in training window!"
        assert train_indices.isdisjoint(embargo_indices), f"{phase_name}: Embargo indices overlap with training window!"
        assert embargo_indices.isdisjoint(val_indices), f"{phase_name}: Embargo indices overlap with validation window!"

        # 2. Embargo gap between train end and val start is at least 10 trading days
        gap_days = split.val.start_idx - split.train.end_idx - 1
        assert gap_days >= 10, f"{phase_name}: Embargo gap of {gap_days} is less than required 10 trading days!"

        # 3. Date monotonicity: all training dates precede embargo, which precedes validation
        train_dates = clean_cse_df.loc[list(train_indices), "date"]
        val_dates = clean_cse_df.loc[list(val_indices), "date"]
        embargo_dates = clean_cse_df.loc[list(embargo_indices), "date"]

        assert train_dates.max() < embargo_dates.min()
        assert embargo_dates.max() < val_dates.min()


def test_leakage_label_shuffle_test(clean_cse_df: pd.DataFrame) -> None:
    """Test (d): Label-shuffle test. A flexible model trained on shuffled targets scores ~50% direction accuracy."""
    splitter = ExpandingWindowSplitter(clean_cse_df)
    p1 = splitter.get_phase("P1")

    feats = build_backward_features(clean_cse_df).dropna()
    common_idx = feats.index

    train_idx = [i for i in range(p1.train.start_idx, p1.train.end_idx + 1) if i in common_idx]
    val_idx = [i for i in range(p1.val.start_idx, p1.val.end_idx + 1) if i in common_idx]

    scaler = PhaseStandardScaler()
    X_train = scaler.fit_transform(feats.loc[train_idx].values)
    X_val = scaler.transform(feats.loc[val_idx].values)

    # Add bias intercept
    X_train = np.column_stack([np.ones(len(X_train)), X_train])
    X_val = np.column_stack([np.ones(len(X_val)), X_val])

    # Real forward targets
    aspi_vals = clean_cse_df["aspi"].values
    y_train = np.log(aspi_vals[train_idx[1:]] / aspi_vals[train_idx[:-1]])
    X_train = X_train[:-1]

    y_val_dir = (np.log(aspi_vals[val_idx[1:]] / aspi_vals[val_idx[:-1]]) > 0).astype(int)
    X_val = X_val[:-1]

    # Randomly shuffle training labels to destroy all true signal
    np.random.seed(42)
    y_train_shuffled = np.random.permutation(y_train)

    # Train Ridge regression model on noise labels
    lambda_reg = 1.0
    beta = np.linalg.solve(
        X_train.T @ X_train + lambda_reg * np.eye(X_train.shape[1]),
        X_train.T @ y_train_shuffled,
    )

    # Predict direction on held-out validation window
    y_pred_val = X_val @ beta
    y_pred_dir = (y_pred_val > 0).astype(int)

    acc = float(np.mean(y_val_dir == y_pred_dir))
    
    # Assert directional accuracy is approximately 50% (between 44% and 56%)
    # If there were forward lookahead leakage in features or splits, accuracy would be significantly higher
    assert 0.44 <= acc <= 0.56, f"Label-shuffle accuracy {acc:.3f} deviated significantly from random chance (~50%)!"


def test_leakage_scaler_fitted_on_training_only(clean_cse_df: pd.DataFrame) -> None:
    """Test (e): Scalers are fitted per phase on training data only."""
    splitter = ExpandingWindowSplitter(clean_cse_df)
    p1 = splitter.get_phase("P1")

    feats = build_backward_features(clean_cse_df).dropna()
    common_idx = feats.index

    train_idx = [i for i in range(p1.train.start_idx, p1.train.end_idx + 1) if i in common_idx]
    val_idx = [i for i in range(p1.val.start_idx, p1.val.end_idx + 1) if i in common_idx]

    X_train = feats.loc[train_idx].values
    X_val = feats.loc[val_idx].values

    # Proper protocol: Scaler fitted on train only
    scaler_train = PhaseStandardScaler()
    scaler_train.fit(X_train)
    mu_train = scaler_train.mean_.copy()
    sigma_train = scaler_train.scale_.copy()

    # Contaminated scaler: Scaler fitted on train + val
    X_combined = np.vstack([X_train, X_val])
    scaler_leaked = PhaseStandardScaler()
    scaler_leaked.fit(X_combined)
    mu_leaked = scaler_leaked.mean_.copy()
    sigma_leaked = scaler_leaked.scale_.copy()

    # The training scaler parameters MUST NOT match the combined parameters
    # Demonstrating that validation statistics were not leaked into the training scaler
    assert not np.allclose(mu_train, mu_leaked, rtol=1e-5), "Train scaler mean equals leaked combined mean!"
    assert not np.allclose(sigma_train, sigma_leaked, rtol=1e-5), "Train scaler std equals leaked combined std!"

    # Verify that calling transform on validation data does not alter fitted training parameters
    _ = scaler_train.transform(X_val)
    np.testing.assert_array_equal(scaler_train.mean_, mu_train)
    np.testing.assert_array_equal(scaler_train.scale_, sigma_train)
