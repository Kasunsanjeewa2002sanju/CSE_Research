from pathlib import Path
from typing import Dict, Any, List, Optional
import joblib
import pandas as pd
import numpy as np

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.stock_loader import StockDataLoader
from backend.app.data.event_loader import EventDataLoader
from backend.app.ml.features import FeatureEngineer
from backend.app.ml.analogues import HistoricalAnaloguePredictor

class UnifiedPredictor:
    """
    Executes unified event-driven stock market impact predictions for
    Government Policy and Political Arrest scenarios.
    Combines:
      - Model 1: Historical Analogue Predictor (Primary explainable precedent engine)
      - Model 2: L2-Logistic Regression (Calibrated direction probability)
      - Model 3: Ridge Regression (Cumulative Abnormal Return point estimate)
      - Empirical Uncertainty Intervals (+/- 1.96 Residual Std)
    """
    def __init__(self):
        self.stock_loader = StockDataLoader()
        self.event_loader = EventDataLoader(self.stock_loader)
        self.calendar = self.stock_loader.get_trading_calendar()
        self.stock_df = self.stock_loader.load_stock_data()
        self.feature_engineer = FeatureEngineer(self.stock_df, self.calendar)
        self.analogue_predictor = HistoricalAnaloguePredictor(self.event_loader)
        self.models_dir = settings.ARTIFACT_DIR / "models"
        
        self._policy_model = None
        self._arrest_model = None

    def _load_model(self, event_family: str):
        slug = "policy" if "policy" in event_family.lower() else "arrest"
        model_path = self.models_dir / f"{slug}_model.joblib"
        if not model_path.exists():
            from backend.app.ml.train import ModelTrainer
            trainer = ModelTrainer()
            trainer.train_all_models()
        return joblib.load(model_path)

    def predict(
        self,
        event_family: str,
        event_subtype: str,
        headline_or_title: str,
        event_date: str,
        affected_sectors: Optional[List[str]] = None,
        target_symbol: str = "ASPI",
        forecast_horizon: int = 5,
        historical_cutoff: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates full predictive response matching Section 15 specifications.
        """
        # Align date to trading calendar
        aligned_date, align_type, lag_days = self.calendar.align_to_trading_day(event_date)
        
        # Load trained model artifact
        model_artifact = self._load_model(event_family)
        feature_cols = model_artifact["feature_columns"]
        clf_pipe = model_artifact["clf_pipeline"]
        reg_pipe = model_artifact["reg_pipeline"]
        residual_std = model_artifact["residual_std"]
        n_samples = model_artifact["n_samples"]
        eval_metrics = model_artifact["eval_metrics"]

        # Generate feature vector strictly up to pre-event session
        raw_feats = self.feature_engineer.build_feature_vector(
            event_family=event_family,
            event_subtype=event_subtype,
            date_str=aligned_date,
            text_description=headline_or_title,
            additional_metadata=additional_metadata or {}
        )

        df_input = pd.DataFrame([raw_feats])
        # Ensure all training feature columns exist
        for col in feature_cols:
            if col not in df_input.columns:
                df_input[col] = 0.0
        X_infer = df_input[feature_cols].fillna(0.0)

        # 1. Continuous CAR prediction (Ridge Regression)
        pred_car = float(reg_pipe.predict(X_infer)[0])
        # Horizon scaling factor: model trained on 5d CAR, scale proportionally by sqrt(horizon / 5)
        scale_factor = np.sqrt(forecast_horizon / 5.0)
        scaled_car = pred_car * scale_factor

        # 2. Direction probabilities (Logistic Regression)
        prob_up = float(clf_pipe.predict_proba(X_infer)[0, 1])
        prob_down = 1.0 - prob_up

        # 3. Prediction Intervals (+/- 1.96 * scaled_std)
        scaled_std = residual_std * scale_factor
        interval_lower = scaled_car - (1.96 * scaled_std)
        interval_upper = scaled_car + (1.96 * scaled_std)

        # 4. Impact direction classification
        if prob_up >= 0.55 and scaled_car > 0.003:
            direction = "Positive"
        elif prob_down >= 0.55 and scaled_car < -0.003:
            direction = "Negative"
        else:
            direction = "Neutral / Mixed"

        # 5. Historical Analogues
        analogues = self.analogue_predictor.find_analogues(
            event_family=event_family,
            event_subtype=event_subtype,
            query_text=headline_or_title,
            market_volatility=raw_feats.get("market_vol_20d", 0.18),
            historical_cutoff=historical_cutoff,
            top_k=4
        )

        # 6. Model Confidence Formulation
        top_sim = analogues[0]["similarity_score"] if analogues else 50.0
        if top_sim >= 75.0 and n_samples >= 50 and raw_feats.get("market_vol_20d", 0.18) < 0.35:
            confidence_level = "High"
        elif top_sim >= 60.0 and n_samples >= 25:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"

        # 7. Horizon Breakdown (1d, 5d, 10d, 20d)
        horizons_breakdown = {}
        for h in [1, 5, 10, 20]:
            h_scale = np.sqrt(h / 5.0)
            h_car = pred_car * h_scale
            h_std = residual_std * h_scale
            horizons_breakdown[f"{h}d"] = {
                "expected_car_pct": round(h_car * 100.0, 2),
                "lower_bound_pct": round((h_car - 1.96 * h_std) * 100.0, 2),
                "upper_bound_pct": round((h_car + 1.96 * h_std) * 100.0, 2),
            }

        # 8. Main Feature Drivers
        reg_coefs = reg_pipe.named_steps["reg"].coef_
        feature_importance = []
        for feat_name, coef in zip(feature_cols, reg_coefs):
            val = float(X_infer.iloc[0][feat_name])
            contrib = float(coef * val)
            feature_importance.append({
                "feature": feat_name,
                "value": round(val, 4),
                "contribution": round(contrib * 100.0, 3)
            })
        feature_importance.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        main_drivers = feature_importance[:5]

        # 9. Plain-language explanation
        explanation = (
            f"Based on {n_samples} historical {event_family.lower()} events, the model estimates a {direction.lower()} "
            f"market tendency ({horizons_breakdown['5d']['expected_car_pct']:+.2f}% 5-day CAR, 95% CI: "
            f"[{horizons_breakdown['5d']['lower_bound_pct']:+.2f}%, {horizons_breakdown['5d']['upper_bound_pct']:+.2f}%]). "
            f"Closest precedent '{analogues[0]['title'] if analogues else 'N/A'}' registered a "
            f"{analogues[0]['car_5d']:+.2f}% 5-day abnormal return."
        )

        return {
            "event_family": event_family,
            "event_subtype": event_subtype,
            "target_symbol": target_symbol,
            "prediction_date": aligned_date,
            "calendar_alignment": {
                "input_date": event_date,
                "aligned_trading_date": aligned_date,
                "alignment_type": align_type,
                "lag_days": lag_days
            },
            "historical_cutoff": historical_cutoff,
            "forecast_horizon": f"{forecast_horizon} trading days",
            "predicted_direction": direction,
            "probability_up": round(prob_up, 4),
            "probability_down": round(prob_down, 4),
            "expected_return_pct": round(scaled_car * 100.0, 2),
            "interval_lower_pct": round(interval_lower * 100.0, 2),
            "interval_upper_pct": round(interval_upper * 100.0, 2),
            "confidence_level": confidence_level,
            "horizons_breakdown": horizons_breakdown,
            "similar_events": analogues,
            "main_drivers": main_drivers,
            "sample_size": n_samples,
            "model_version": "1.0.0",
            "training_data_cutoff": model_artifact.get("cutoff_date", "2025-02-17"),
            "validation_summary": eval_metrics,
            "explanation": explanation,
            "limitations": [
                "Political events often overlap with macroeconomic trends and external shocks.",
                "Sample sizes are modest (Sri Lankan market history 2000-2025).",
                "Predictions reflect empirical correlation, not certified monocausality."
            ]
        }
