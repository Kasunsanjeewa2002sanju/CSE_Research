"""Lookback selection on the inner-validation split (Rule R2: Zero Lookahead)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import torch

from cse.features.pipeline import PhaseDataManager
from cse.models.deep.architectures import build_deep_model
from cse.models.deep.trainer import DeepSequenceTrainer, get_device
from cse.utils.logger import get_logger

logger = get_logger("cse.models.deep.tuner")

CANDIDATE_LOOKBACKS = [20, 60, 120]


def select_best_lookback(
    mgr: PhaseDataManager,
    phase: str,
    horizon: int,
    feature_set: str,
    model_type: str,
    use_revin: bool = False,
    device: Optional[torch.device] = None,
    seed: int = 42,
) -> Tuple[int, Dict[int, float]]:
    """Select optimal lookback L in {20, 60, 120} strictly using inner-validation loss."""
    best_loss = float("inf")
    best_l = 20
    scores: Dict[int, float] = {}
    dev = device if device is not None else get_device()

    for L in CANDIDATE_LOOKBACKS:
        try:
            seq_data = mgr.get_sequence_windows(
                phase=phase,
                horizon=horizon,
                feature_set=feature_set,
                lookback=L,
            )
            in_features = seq_data.train.X_seq.shape[2]
            model = build_deep_model(
                model_type=model_type,
                in_features=in_features,
                lookback=L,
                use_revin=use_revin,
            )
            # Lightweight probe trial: max 5 epochs with patience 2 on inner-val
            trainer = DeepSequenceTrainer(
                model=model,
                device=dev,
                lr=1e-3,
                patience=2,
                max_epochs=5,
                time_budget_seconds=3.0,
                seed=seed,
            )
            fit_res = trainer.fit(seq_data.train, seq_data.inner_val, batch_size=128)
            val_loss = fit_res["best_val_loss"]
            scores[L] = val_loss

            if val_loss < best_loss:
                best_loss = val_loss
                best_l = L
        except Exception as e:
            logger.warning("Lookback tuning failed for L=%d (%s): %s", L, model_type, e)
            scores[L] = float("inf")

    logger.info("Selected Lookback L=%d for %s %s h%d (scores: %s)", best_l, model_type, phase, horizon, scores)
    return best_l, scores
