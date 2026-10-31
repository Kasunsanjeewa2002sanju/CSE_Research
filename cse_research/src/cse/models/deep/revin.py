"""Reversible Instance Normalization (RevIN) for PyTorch.

Reference:
    Kim et al. (ICLR 2022): "Reversible Instance Normalization for Accurate Time-Series
    Forecasting against Distribution Shift".
    https://openreview.net/forum?id=cGDAkQo1C0p

Adheres strictly to:
    - Rule R1: Real data only.
    - Rule R2: Zero lookahead. Instance statistics computed strictly across the lookback window.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class RevIN(nn.Module):
    """Reversible Instance Normalization layer.

    Normalizes input sequence along the time dimension to zero mean and unit variance,
    with optional affine learnable scaling parameters.
    """

    def __init__(self, num_features: int, eps: float = 1e-5, affine: bool = True):
        super().__init__()
        self.num_features = num_features
        self.eps = eps
        self.affine = affine
        if self.affine:
            self.affine_weight = nn.Parameter(torch.ones(1, 1, num_features))
            self.affine_bias = nn.Parameter(torch.zeros(1, 1, num_features))
        else:
            self.register_parameter("affine_weight", None)
            self.register_parameter("affine_bias", None)

        self.mean: torch.Tensor = torch.empty(0)
        self.stdev: torch.Tensor = torch.empty(0)

    def forward(self, x: torch.Tensor, mode: str = "norm") -> torch.Tensor:
        """Forward pass for normalization or de-normalization.

        Args:
            x: Input tensor of shape (batch_size, seq_len, num_features).
            mode: 'norm' to normalize, 'denorm' to invert.

        Returns:
            Normalized or de-normalized tensor of identical shape.
        """
        if mode == "norm":
            self._get_statistics(x)
            x_norm = (x - self.mean) / self.stdev
            if self.affine:
                x_norm = x_norm * self.affine_weight + self.affine_bias
            return x_norm
        elif mode == "denorm":
            if self.mean is None or self.stdev is None or self.mean.numel() == 0:
                return x
            x_denorm = x
            if self.affine:
                x_denorm = (x_denorm - self.affine_bias) / (self.affine_weight + self.eps)
            x_denorm = x_denorm * self.stdev + self.mean
            return x_denorm
        else:
            raise NotImplementedError(f"RevIN mode '{mode}' not supported. Use 'norm' or 'denorm'.")

    def _get_statistics(self, x: torch.Tensor) -> None:
        # Compute mean and standard deviation along the sequence dimension (dim=1)
        self.mean = torch.mean(x, dim=1, keepdim=True).detach()
        self.stdev = torch.sqrt(torch.var(x, dim=1, keepdim=True, unbiased=False) + self.eps).detach()
