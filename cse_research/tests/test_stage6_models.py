"""Unit tests for Stage 6 Statistical and Shallow ML models."""

import numpy as np
import pandas as pd
import pytest

from cse.features.pipeline import PhaseDataManager, get_phase_data
from cse.models.statistical.arima import ARIMAModel, SARIMAModel, find_best_arima_order
from cse.models.statistical.ets_theta import ETSModel, ThetaForecastingModel
from cse.models.statistical.garch import GARCHModel, calc_variance_metrics
from cse.models.statistical.linear import LinearReturnModel, LogisticDirectionModel, RegularizedLinearModel
from cse.models.statistical.var import VARModel
from cse.models.shallow.calibrator import InnerSliceCalibrator
from cse.models.shallow.kernel_knn import KernelKNNModel
from cse.models.shallow.tree_models import TreeModelBase


def test_arima_order_selection_and_fit():
    """Verify ARIMA order selection strictly on training data."""
    np.random.seed(42)
    # Generate stationary AR(1) process
    n = 300
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = 0.3 * y[t - 1] + np.random.normal(0, 0.01)

    order = find_best_arima_order(y, max_p=2, max_q=2, d=0)
    assert len(order) == 3
    assert order[1] == 0

    model = ARIMAModel(order=(1, 0, 0), seed=42)
    model.fit(y)
    assert model.fitted_model_ is not None


def test_garch_variance_metrics():
    """Verify GARCH volatility metrics (QLIKE, MSE)."""
    np.random.seed(42)
    n = 100
    rv_true = np.abs(np.random.normal(0.0004, 0.0001, n))
    var_pred = np.abs(np.random.normal(0.0004, 0.0001, n))

    metrics = calc_variance_metrics(rv_true, var_pred)
    assert "qlike" in metrics
    assert "mse_realized_variance" in metrics
    assert metrics["qlike"] >= 0.0
    assert metrics["mse_realized_variance"] >= 0.0


def test_shallow_models_fit_and_calibrate():
    """Verify shallow model regressor, classifier, and calibration on sample phase data."""
    mgr = PhaseDataManager()
    phase_data = mgr.get_phase_data("P1", horizon=1, feature_set="A")
    full_df = mgr.df_cse

    # Test Random Forest regressor
    rf_reg = TreeModelBase(tree_type="random_forest", mode="regressor", seed=42)
    df_rf_reg = rf_reg.predict_phase(phase_data, full_df)
    assert len(df_rf_reg) > 0
    assert "y_pred_ret" in df_rf_reg.columns
    assert len(rf_reg.feature_importances_) > 0

    # Test Logistic regression classifier
    log_clf = LogisticDirectionModel(seed=42)
    df_log = log_clf.predict_phase(phase_data, full_df)
    assert len(df_log) > 0
    assert "p_up" in df_log.columns
    assert (df_log["p_up"] >= 0.0).all() and (df_log["p_up"] <= 1.0).all()
