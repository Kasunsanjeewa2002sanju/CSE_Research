"""Monitoring and observability package for CSE news prediction system."""

from cse.monitoring.prediction_logger import (
    PredictionLogger,
    get_prediction_logger,
)

__all__ = ["PredictionLogger", "get_prediction_logger"]
