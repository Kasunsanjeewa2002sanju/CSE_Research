"""Unit tests for evaluation metrics and statistical tests."""

import pytest
import numpy as np
from cse.eval.metrics import (
    calc_mae,
    calc_rmse,
    calc_oos_r2,
    calc_theils_u,
    calc_level_mae,
    calc_level_rmse,
    calc_level_mape,
    calc_direction_accuracy,
    calc_balanced_accuracy,
    calc_precision,
    calc_recall,
    calc_f1,
    calc_mcc,
    calc_roc_auc,
    get_non_overlapping_indices,
)
from cse.eval.tests_stat import (
    diebold_mariano,
    binomial_accuracy_test,
    pesaran_timmermann,
    newey_west_variance,
)


def test_basic_magnitude_metrics() -> None:
    """Verify MAE, RMSE, OOS R2, and Theil's U."""
    y_true = np.array([0.02, -0.01, 0.03, -0.02, 0.01])
    y_pred = np.array([0.01, -0.01, 0.02, -0.01, 0.00])
    y_bench = np.zeros_like(y_true)

    # MAE should be mean(0.01, 0, 0.01, 0.01, 0.01) = 0.008
    mae = calc_mae(y_true, y_pred)
    assert np.isclose(mae, 0.008)

    # RMSE
    rmse = calc_rmse(y_true, y_pred)
    assert rmse > 0.0

    # OOS R2 vs zero benchmark
    r2 = calc_oos_r2(y_true, y_pred, y_bench)
    assert r2 > 0.0  # y_pred is strictly closer to y_true than 0 is

    # Theil's U
    u = calc_theils_u(y_true, y_pred, y_bench)
    assert 0.0 < u < 1.0


def test_level_metrics() -> None:
    """Verify reconstructed price level metrics."""
    level_true = np.array([1000.0, 1020.0, 1010.0])
    level_pred = np.array([1005.0, 1015.0, 1012.0])

    mae = calc_level_mae(level_true, level_pred)
    assert np.isclose(mae, (5.0 + 5.0 + 2.0) / 3.0)

    mape = calc_level_mape(level_true, level_pred)
    assert mape > 0.0


def test_classification_metrics() -> None:
    """Verify directional accuracy, balanced accuracy, MCC, F1, and ROC-AUC."""
    y_true_dir = np.array([1, 1, 0, 0, 1, 0])
    y_pred_dir = np.array([1, 0, 0, 0, 1, 1])

    acc = calc_direction_accuracy(y_true_dir, y_pred_dir)
    assert np.isclose(acc, 4.0 / 6.0)

    bal_acc = calc_balanced_accuracy(y_true_dir, y_pred_dir)
    assert 0.0 <= bal_acc <= 1.0

    mcc = calc_mcc(y_true_dir, y_pred_dir)
    assert -1.0 <= mcc <= 1.0

    # ROC AUC
    p_up = np.array([0.9, 0.4, 0.2, 0.1, 0.8, 0.6])
    auc = calc_roc_auc(y_true_dir, p_up)
    assert auc is not None
    assert 0.5 <= auc <= 1.0


def test_diebold_mariano_test() -> None:
    """Verify Diebold-Mariano test with HLN correction."""
    np.random.seed(42)
    T = 100
    # Candidate model has smaller errors than benchmark
    e_candidate = np.random.normal(0, 0.01, size=T)
    e_benchmark = np.random.normal(0, 0.03, size=T)

    dm_res = diebold_mariano(e_candidate, e_benchmark, h=1, power=2, alternative="two-sided")
    assert dm_res["df"] == T - 1
    # Candidate loss is smaller, so mean loss diff is negative
    assert dm_res["mean_loss_diff"] < 0
    assert dm_res["dm_hln_stat"] < 0
    assert dm_res["p_value"] < 0.01


def test_binomial_test() -> None:
    """Verify binomial test of directional accuracy."""
    y_true = np.array([1] * 65 + [0] * 35)
    y_pred = np.array([1] * 65 + [0] * 35)

    res = binomial_accuracy_test(y_true, y_pred, p_null=0.5, alternative="greater")
    assert res["successes"] == 100
    assert res["accuracy"] == 1.0
    assert res["p_value"] < 1e-10


def test_pesaran_timmermann_test() -> None:
    """Verify Pesaran-Timmermann test rejects independence when predictions are perfect."""
    y_true = np.array([1, 0, 1, 1, 0, 0, 1, 0] * 10)
    y_pred = y_true.copy()

    pt = pesaran_timmermann(y_true, y_pred)
    assert pt["pt_stat"] > 5.0
    assert pt["p_value"] < 1e-5


def test_non_overlapping_indices() -> None:
    """Verify non-overlapping subsampling indices."""
    idx = get_non_overlapping_indices(25, step=5)
    assert list(idx) == [0, 5, 10, 15, 20]
