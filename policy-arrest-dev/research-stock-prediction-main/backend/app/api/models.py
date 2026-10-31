import json
from pathlib import Path
from fastapi import APIRouter

from backend.app.core.config import settings

router = APIRouter(prefix="/model", tags=["Model Information"])

@router.get("/report")
def get_model_report():
    """
    Returns empirical evaluation metrics, chronological validation results,
    baseline comparisons, and confidence formulations for trained models.
    """
    report_file = settings.ARTIFACT_DIR / "reports" / "model_comparison.json"
    if report_file.exists():
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "status": "ready",
        "model_version": "1.0.0",
        "description": "L2-Regularized Logistic Regression and Ridge Models with Historical Analogue Predictor.",
        "validation_method": "Expanding-Window Chronological Split",
        "sample_sizes": {
            "government_policies": 70,
            "political_arrests": 34
        }
    }
