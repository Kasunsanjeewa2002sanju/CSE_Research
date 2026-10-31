import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, balanced_accuracy_score, mean_absolute_error, brier_score_loss, roc_auc_score

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.stock_loader import StockDataLoader
from backend.app.data.event_loader import EventDataLoader
from backend.app.ml.features import FeatureEngineer

class ModelTrainer:
    """
    Trains, evaluates, and persists machine-learning models for Government Policy
    and Political Arrest market reactions using strict chronological expanding-window splits.
    """
    def __init__(self):
        self.stock_loader = StockDataLoader()
        self.event_loader = EventDataLoader(self.stock_loader)
        self.calendar = self.stock_loader.get_trading_calendar()
        self.stock_df = self.stock_loader.load_stock_data()
        self.feature_engineer = FeatureEngineer(self.stock_df, self.calendar)
        self.models_dir = settings.ARTIFACT_DIR / "models"
        self.reports_dir = settings.ARTIFACT_DIR / "reports"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def prepare_dataset(self, event_family: str, target_horizon: str = "car_0_5") -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Builds feature matrix X, regression target y_reg (CAR), and binary target y_clf (CAR > 0).
        """
        study_df = self.event_loader.get_event_study_results().copy()
        events_df = self.event_loader.load_all_events()
        
        merged = pd.merge(study_df, events_df[["Event_ID", "summary"]], left_on="event_id", right_on="Event_ID", how="left")
        fam_df = merged[merged["event_family"].str.lower() == event_family.lower()].copy()
        fam_df = fam_df.sort_values("aligned_date").reset_index(drop=True)

        features_list = []
        for _, row in fam_df.iterrows():
            feats = self.feature_engineer.build_feature_vector(
                event_family=row["event_family"],
                event_subtype=row["event_subtype"],
                date_str=row["aligned_date"],
                text_description=str(row.get("title", "")),
                additional_metadata={"summary": row.get("summary")}
            )
            features_list.append(feats)

        df_feats = pd.DataFrame(features_list)
        
        # Select numeric feature columns
        numeric_cols = [c for c in df_feats.columns if c not in ["event_family", "event_subtype"]]
        X = df_feats[numeric_cols].fillna(0.0)

        y_reg = fam_df[target_horizon].astype(float)
        y_clf = (y_reg > 0.0).astype(int)

        return X, y_reg, y_clf, fam_df

    def evaluate_chronological(self, X: pd.DataFrame, y_reg: pd.Series, y_clf: pd.Series, min_train: int = 15) -> Dict[str, Any]:
        """
        Performs forward-chaining expanding window cross-validation to strictly
        prevent chronological lookahead leakage.
        """
        n = len(X)
        if n < min_train + 5:
            # Fallback for very small datasets
            min_train = max(5, n // 2)

        clf_preds = []
        clf_probs = []
        reg_preds = []
        y_clf_true = []
        y_reg_true = []
        
        # Baselines
        majority_preds = []
        mean_preds = []

        for split_idx in range(min_train, n):
            X_train, y_train_clf, y_train_reg = X.iloc[:split_idx], y_clf.iloc[:split_idx], y_reg.iloc[:split_idx]
            X_test, y_test_clf, y_test_reg = X.iloc[split_idx:split_idx+1], y_clf.iloc[split_idx:split_idx+1], y_reg.iloc[split_idx:split_idx+1]

            # Model 2: Logistic Regression (Classification)
            if len(np.unique(y_train_clf)) < 2:
                prob = float(y_train_clf.iloc[0])
                pred_class = int(prob >= 0.5)
            else:
                clf_pipe = Pipeline([
                    ("scaler", StandardScaler()),
                    ("clf", LogisticRegression(C=1.0, random_state=settings.MODEL_RANDOM_STATE, max_iter=200))
                ])
                clf_pipe.fit(X_train, y_train_clf)
                prob = float(clf_pipe.predict_proba(X_test)[0, 1])
                pred_class = int(prob >= 0.5)

            # Model 3: Ridge Regression (CAR magnitude)
            reg_pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("reg", Ridge(alpha=1.0, random_state=settings.MODEL_RANDOM_STATE))
            ])
            reg_pipe.fit(X_train, y_train_reg)
            pred_reg = float(reg_pipe.predict(X_test)[0])

            clf_preds.append(pred_class)
            clf_probs.append(prob)
            reg_preds.append(pred_reg)
            y_clf_true.append(int(y_test_clf.iloc[0]))
            y_reg_true.append(float(y_test_reg.iloc[0]))

            # Baselines
            maj_class = int(y_train_clf.mode()[0])
            majority_preds.append(maj_class)
            mean_preds.append(float(y_train_reg.mean()))

        # Calculate metrics
        acc = accuracy_score(y_clf_true, clf_preds)
        bal_acc = balanced_accuracy_score(y_clf_true, clf_preds)
        brier = brier_score_loss(y_clf_true, clf_probs)
        try:
            auc = roc_auc_score(y_clf_true, clf_probs)
        except Exception:
            auc = 0.5

        mae_model = mean_absolute_error(y_reg_true, reg_preds)
        mae_mean_baseline = mean_absolute_error(y_reg_true, mean_preds)
        mae_zero_baseline = mean_absolute_error(y_reg_true, [0.0] * len(y_reg_true))

        baseline_acc = accuracy_score(y_clf_true, majority_preds)

        return {
            "validation_method": "Expanding-Window Chronological Split",
            "eval_sample_count": len(y_clf_true),
            "classification": {
                "accuracy": round(float(acc), 4),
                "balanced_accuracy": round(float(bal_acc), 4),
                "brier_score": round(float(brier), 4),
                "roc_auc": round(float(auc), 4),
                "majority_baseline_accuracy": round(float(baseline_acc), 4),
                "outperforms_majority": bool(acc >= baseline_acc)
            },
            "regression": {
                "mae_model_pct": round(float(mae_model * 100), 2),
                "mae_mean_baseline_pct": round(float(mae_mean_baseline * 100), 2),
                "mae_zero_baseline_pct": round(float(mae_zero_baseline * 100), 2),
                "outperforms_mean_baseline": bool(mae_model <= mae_mean_baseline)
            }
        }

    def train_and_persist(self, event_family: str, cutoff_date: Optional[str] = None) -> Dict[str, Any]:
        """Trains final full pipeline on data up to cutoff_date and serializes model artifact."""
        X, y_reg, y_clf, fam_df = self.prepare_dataset(event_family)

        if cutoff_date:
            mask = fam_df["aligned_date"] <= cutoff_date
            X = X[mask].copy()
            y_reg = y_reg[mask].copy()
            y_clf = y_clf[mask].copy()
            fam_df = fam_df[mask].copy()

        n_samples = len(X)
        eval_metrics = self.evaluate_chronological(X, y_reg, y_clf)

        # Train final models on available dataset
        clf_pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, random_state=settings.MODEL_RANDOM_STATE))
        ])
        reg_pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("reg", Ridge(alpha=1.0, random_state=settings.MODEL_RANDOM_STATE))
        ])

        clf_pipe.fit(X, y_clf)
        reg_pipe.fit(X, y_reg)

        # Residual std for prediction intervals
        reg_preds = reg_pipe.predict(X)
        residuals = y_reg.values - reg_preds
        residual_std = float(np.std(residuals)) if len(residuals) > 0 else 0.025

        artifact_payload = {
            "event_family": event_family,
            "feature_columns": X.columns.tolist(),
            "clf_pipeline": clf_pipe,
            "reg_pipeline": reg_pipe,
            "residual_std": residual_std,
            "n_samples": n_samples,
            "cutoff_date": cutoff_date or str(fam_df["aligned_date"].max()),
            "eval_metrics": eval_metrics
        }

        fam_slug = "policy" if "policy" in event_family.lower() else "arrest"
        save_path = self.models_dir / f"{fam_slug}_model.joblib"
        joblib.dump(artifact_payload, save_path)
        logger.info(f"Trained & saved {event_family} model to {save_path} (N = {n_samples})")

        return {
            "event_family": event_family,
            "artifact_path": str(save_path),
            "sample_size": n_samples,
            "cutoff_date": artifact_payload["cutoff_date"],
            "eval_metrics": eval_metrics
        }

    def train_all_models(self) -> Dict[str, Any]:
        """Trains both Government Policy and Political Arrest models and exports evaluation report."""
        logger.info("Training PolitiTrade LK Machine Learning Pipeline...")
        res_policy = self.train_and_persist("Government Policy")
        res_arrest = self.train_and_persist("Political Arrest")

        comparison = {
            "model_version": "1.0.0",
            "evaluated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "models": {
                "government_policy": res_policy,
                "political_arrest": res_arrest
            },
            "scientific_interpretation": (
                "Due to sample sizes (70 policy events, 34 arrest events), models are regularized "
                "to prevent overfitting. Prediction intervals and historical analogues must always accompany point estimates."
            )
        }

        report_path = self.reports_dir / "model_comparison.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)

        meta_path = self.models_dir / "model_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)

        logger.info(f"Saved model evaluation report to {report_path}")
        return comparison
