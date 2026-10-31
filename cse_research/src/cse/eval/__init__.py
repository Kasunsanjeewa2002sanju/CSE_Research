"""Evaluation harness, metrics, and statistical hypothesis testing."""

from cse.eval.harness import EvaluationHarness, PREDICTION_SCHEMA
from cse.eval.metrics import (
    calc_all_metrics,
    calc_balanced_accuracy,
    calc_direction_accuracy,
    calc_f1,
    calc_level_mae,
    calc_level_mape,
    calc_level_rmse,
    calc_mae,
    calc_mcc,
    calc_oos_r2,
    calc_precision,
    calc_recall,
    calc_rmse,
    calc_roc_auc,
    calc_theils_u,
    get_non_overlapping_indices,
)
from cse.eval.tests_stat import (
    binomial_accuracy_test,
    diebold_mariano,
    newey_west_variance,
    pesaran_timmermann,
)

__all__ = [
    "EvaluationHarness",
    "PREDICTION_SCHEMA",
    "calc_mae",
    "calc_rmse",
    "calc_oos_r2",
    "calc_theils_u",
    "calc_level_mae",
    "calc_level_rmse",
    "calc_level_mape",
    "calc_direction_accuracy",
    "calc_balanced_accuracy",
    "calc_precision",
    "calc_recall",
    "calc_f1",
    "calc_mcc",
    "calc_roc_auc",
    "calc_all_metrics",
    "get_non_overlapping_indices",
    "diebold_mariano",
    "binomial_accuracy_test",
    "pesaran_timmermann",
    "newey_west_variance",
]
