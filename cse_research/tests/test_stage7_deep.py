"""Unit tests for Stage 7 deep sequence models and training pipeline."""

import pytest
import torch
import numpy as np

from cse.models.deep.revin import RevIN
from cse.models.deep.architectures import build_deep_model, MODEL_REGISTRY
from cse.models.deep.dataset import SequenceDataset, create_dataloader
from cse.features.pipeline import SequenceSplitData


def test_revin_reversibility():
    """Verify RevIN normalizes along sequence dim and accurately de-normalizes."""
    B, L, D = 8, 20, 10
    x = torch.randn(B, L, D) * 5.0 + 3.0
    revin = RevIN(num_features=D, affine=True)

    x_norm = revin(x, mode="norm")
    assert x_norm.shape == (B, L, D)
    # Check approximately zero mean along time dim
    mean = torch.mean(x_norm, dim=1)
    assert torch.allclose(mean, torch.zeros_like(mean), atol=1e-4)

    x_denorm = revin(x_norm, mode="denorm")
    assert x_denorm.shape == (B, L, D)
    assert torch.allclose(x_denorm, x, atol=1e-4)


@pytest.mark.parametrize("model_type", list(MODEL_REGISTRY.keys()))
def test_all_deep_models_forward(model_type: str):
    """Verify each deep sequence model executes forward pass and produces dual heads."""
    B, L, D = 4, 20, 12
    x = torch.randn(B, L, D)

    # Test without RevIN
    model = build_deep_model(model_type=model_type, in_features=D, lookback=L, use_revin=False)
    y_ret, logits_dir = model(x)

    assert y_ret.shape == (B,)
    assert logits_dir.shape == (B,)
    assert not torch.isnan(y_ret).any()
    assert not torch.isnan(logits_dir).any()

    # Parameter count assertion (Rule: keep models compact, < 250k parameters)
    n_params = model.count_parameters()
    assert 50 < n_params < 250_000, f"{model_type} has {n_params} parameters!"

    # Test with RevIN
    model_revin = build_deep_model(model_type=model_type, in_features=D, lookback=L, use_revin=True)
    y_ret_r, logits_dir_r = model_revin(x)
    assert y_ret_r.shape == (B,)
    assert logits_dir_r.shape == (B,)


def test_deep_model_gradient_backward():
    """Verify loss calculation and backpropagation for multitask heads."""
    B, L, D = 8, 20, 10
    x = torch.randn(B, L, D)
    y_ret = torch.randn(B) * 0.02
    y_dir = torch.randint(0, 2, (B,)).float()

    model = build_deep_model("lstm", in_features=D, lookback=L, use_revin=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

    pred_ret, logits_dir = model(x)
    loss = torch.nn.functional.huber_loss(pred_ret, y_ret) + 0.5 * torch.nn.functional.binary_cross_entropy_with_logits(logits_dir, y_dir)

    loss.backward()
    optimizer.step()

    assert not torch.isnan(loss)
    assert loss.item() > 0.0
