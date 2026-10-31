"""Standardized model artifact serialization and metadata storage.

Adheres to:
- Rule R6: Save everything (models, predictions, configs, metrics).
- Rule R7: Reproducibility: seeds, library versions, hardware, data hash.
- Standard: models/<family>/<model>/<phase>/ containing model file, meta.json, and prediction pointer.
"""

from __future__ import annotations

import json
from pathlib import Path
import pickle
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd

from cse.utils.config import find_project_root
from cse.utils.device import get_device_info
from cse.utils.logger import get_logger

logger = get_logger("cse.models.artifact")


def save_model_artifact(
    model_obj: Any,
    family: str,
    model_name: str,
    phase: str,
    horizon: int,
    seed: int,
    train_date_range: Tuple[str, str],
    embargo_date_range: Tuple[str, str],
    val_date_range: Tuple[str, str],
    embargo_days: int,
    feature_set: str,
    raw_data_hash: str,
    runtime_seconds: float,
    prediction_file: str,
    hyperparameters: Optional[Dict[str, Any]] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """Save model artifact and standardized meta.json according to the project specification."""
    root = find_project_root()
    if output_dir is None:
        target_dir = root / "models" / family / model_name / phase
    else:
        target_dir = Path(output_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save model binary
    model_path = target_dir / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model_obj, f)

    # 2. Gather library versions
    import scipy
    import statsmodels
    lib_versions = {
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "statsmodels": statsmodels.__version__,
    }

    # 3. Create metadata dictionary
    meta = {
        "model": model_name,
        "family": family,
        "phase": phase,
        "horizon": horizon,
        "seed": seed,
        "train_date_range": list(train_date_range),
        "embargo_date_range": list(embargo_date_range),
        "val_date_range": list(val_date_range),
        "embargo_days": embargo_days,
        "feature_set": feature_set,
        "hyperparameters": hyperparameters or {},
        "raw_data_hash": raw_data_hash,
        "library_versions": lib_versions,
        "runtime_seconds": float(runtime_seconds),
        "hardware": get_device_info(),
        "prediction_file": prediction_file,
        "extra_meta": extra_meta or {},
    }

    meta_path = target_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info("Saved model artifact and metadata to %s", target_dir)
    return target_dir


def load_model_artifact(artifact_dir: Union[str, Path]) -> Tuple[Any, Dict[str, Any]]:
    """Load model binary and metadata from an artifact directory."""
    path = Path(artifact_dir)
    model_path = path / "model.pkl"
    meta_path = path / "meta.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")

    with open(model_path, "rb") as f:
        model_obj = pickle.load(f)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    return model_obj, meta
