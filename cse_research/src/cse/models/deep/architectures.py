"""Deep sequence model architectures in PyTorch.

Includes:
    - MLP
    - LSTM
    - GRU
    - BiLSTM (bidirectional strictly over the past lookback window)
    - 1D-CNN
    - TCN (Temporal Convolutional Network with causal dilated convolutions)
    - CNN-LSTM hybrid
    - Transformer Encoder
    - PatchTST (Patch-based channel-independent transformer)
    - DLinear (Trend and seasonal decomposition linear projections)
    - N-BEATS (Neural basis expansion analysis with doubly residual stacking)

Adheres strictly to:
    - Rule R1: Real data only.
    - Rule R2: Zero lookahead. Sequence operations process past lookback window [t-L+1, ..., t].
    - Multitask output: y_ret (Huber loss) and y_dir (BCE loss).
    - Compact parameters: hidden dims 32-64, dropout 0.1-0.2, weight decay.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

from cse.models.deep.revin import RevIN


class BaseSequenceModel(nn.Module):
    """Base class for deep sequence models with dual return and direction prediction heads."""

    def __init__(self, in_features: int, lookback: int, repr_dim: int, use_revin: bool = False):
        super().__init__()
        self.in_features = in_features
        self.lookback = lookback
        self.repr_dim = repr_dim
        self.use_revin = use_revin
        self.revin = RevIN(in_features, affine=True) if use_revin else None

        # Multitask prediction heads
        self.head_ret = nn.Linear(repr_dim, 1)
        self.head_dir = nn.Linear(repr_dim, 1)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract latent representation vector z of shape (batch, repr_dim)."""
        raise NotImplementedError

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, lookback, in_features).
            
        Returns:
            Tuple of (y_ret_pred, y_dir_logits).
        """
        if self.use_revin and self.revin is not None:
            x = self.revin(x, mode="norm")

        z = self.extract_features(x)
        y_ret = self.head_ret(z).squeeze(-1)
        logits_dir = self.head_dir(z).squeeze(-1)

        return y_ret, logits_dir

    def count_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# =========================================================================
# 1. MLP MODEL
# =========================================================================

class MLPModel(BaseSequenceModel):
    """Multilayer Perceptron operating on flattened sequence windows."""

    def __init__(self, in_features: int, lookback: int, hidden_dim: int = 32, dropout: float = 0.2, use_revin: bool = False):
        repr_dim = 16
        super().__init__(in_features, lookback, repr_dim, use_revin=use_revin)
        flat_dim = in_features * lookback
        self.net = nn.Sequential(
            nn.Linear(flat_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, repr_dim),
            nn.LayerNorm(repr_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.size(0)
        flat = x.view(batch_size, -1)
        return self.net(flat)


# =========================================================================
# 2. LSTM MODEL
# =========================================================================

class LSTMModel(BaseSequenceModel):
    """Compact 1-layer LSTM sequence encoder."""

    def __init__(self, in_features: int, lookback: int, hidden_dim: int = 24, num_layers: int = 1, dropout: float = 0.15, use_revin: bool = False):
        super().__init__(in_features, lookback, repr_dim=hidden_dim, use_revin=use_revin)
        self.lstm = nn.LSTM(
            input_size=in_features,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        out, (h_n, c_n) = self.lstm(x)
        last_h = h_n[-1]
        return self.dropout(self.norm(last_h))


# =========================================================================
# 3. GRU MODEL
# =========================================================================

class GRUModel(BaseSequenceModel):
    """Compact 1-layer Gated Recurrent Unit sequence encoder."""

    def __init__(self, in_features: int, lookback: int, hidden_dim: int = 24, num_layers: int = 1, dropout: float = 0.15, use_revin: bool = False):
        super().__init__(in_features, lookback, repr_dim=hidden_dim, use_revin=use_revin)
        self.gru = nn.GRU(
            input_size=in_features,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        out, h_n = self.gru(x)
        last_h = h_n[-1]
        return self.dropout(self.norm(last_h))


# =========================================================================
# 4. BiLSTM MODEL (Bidirectional strictly over PAST lookback window)
# =========================================================================

class BiLSTMModel(BaseSequenceModel):
    """Bidirectional LSTM processing historical context forward and backward within [t-L+1, ..., t]."""

    def __init__(self, in_features: int, lookback: int, hidden_dim: int = 16, num_layers: int = 1, dropout: float = 0.15, use_revin: bool = False):
        repr_dim = hidden_dim * 2
        super().__init__(in_features, lookback, repr_dim=repr_dim, use_revin=use_revin)
        self.bilstm = nn.LSTM(
            input_size=in_features,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.norm = nn.LayerNorm(repr_dim)
        self.dropout = nn.Dropout(dropout)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        out, (h_n, c_n) = self.bilstm(x)
        h_forward = h_n[-2]
        h_backward = h_n[-1]
        cat_h = torch.cat([h_forward, h_backward], dim=-1)
        return self.dropout(self.norm(cat_h))


# =========================================================================
# 5. 1D-CNN MODEL
# =========================================================================

class CNN1DModel(BaseSequenceModel):
    """Temporal 1D Convolutional Neural Network."""

    def __init__(self, in_features: int, lookback: int, channels: int = 24, dropout: float = 0.15, use_revin: bool = False):
        super().__init__(in_features, lookback, repr_dim=channels, use_revin=use_revin)
        self.conv1 = nn.Conv1d(in_channels=in_features, out_channels=channels, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(in_channels=channels, out_channels=channels, kernel_size=3, padding=1)
        self.conv3 = nn.Conv1d(in_channels=channels, out_channels=channels, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.norm = nn.LayerNorm(channels)
        self.dropout = nn.Dropout(dropout)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        x_t = x.transpose(1, 2)
        h = F.gelu(self.conv1(x_t))
        h = F.gelu(self.conv2(h))
        h = F.gelu(self.conv3(h))
        pooled = self.pool(h).squeeze(-1)
        return self.dropout(self.norm(pooled))


# =========================================================================
# 6. TCN MODEL (Temporal Convolutional Network with causal dilated convs)
# =========================================================================

class Chomp1d(nn.Module):
    """Chomp right padding to guarantee causal convolutions with zero future leakage."""
    def __init__(self, chomp_size: int):
        super().__init__()
        self.chomp_size = chomp_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x[:, :, :-self.chomp_size].contiguous() if self.chomp_size > 0 else x


class TemporalBlock(nn.Module):
    def __init__(self, n_inputs: int, n_outputs: int, kernel_size: int, stride: int, dilation: int, padding: int, dropout: float = 0.2):
        super().__init__()
        self.conv1 = nn.Conv1d(n_inputs, n_outputs, kernel_size, stride=stride, padding=padding, dilation=dilation)
        self.chomp1 = Chomp1d(padding)
        self.relu1 = nn.GELU()
        self.dropout1 = nn.Dropout(dropout)

        self.conv2 = nn.Conv1d(n_outputs, n_outputs, kernel_size, stride=stride, padding=padding, dilation=dilation)
        self.chomp2 = Chomp1d(padding)
        self.relu2 = nn.GELU()
        self.dropout2 = nn.Dropout(dropout)

        self.downsample = nn.Conv1d(n_inputs, n_outputs, 1) if n_inputs != n_outputs else None
        self.init_weights()

    def init_weights(self):
        self.conv1.weight.data.normal_(0, 0.01)
        self.conv2.weight.data.normal_(0, 0.01)
        if self.downsample is not None:
            self.downsample.weight.data.normal_(0, 0.01)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv1(x)
        out = self.chomp1(out)
        out = self.relu1(out)
        out = self.dropout1(out)

        out = self.conv2(out)
        out = self.chomp2(out)
        out = self.relu2(out)
        out = self.dropout2(out)

        res = x if self.downsample is None else self.downsample(x)
        return F.gelu(out + res)


class TCNModel(BaseSequenceModel):
    """Causal Dilated Temporal Convolutional Network (Bai et al., 2018)."""

    def __init__(self, in_features: int, lookback: int, num_channels: Optional[List[int]] = None, kernel_size: int = 3, dropout: float = 0.15, use_revin: bool = False):
        if num_channels is None:
            num_channels = [24, 24, 24]
        repr_dim = num_channels[-1]
        super().__init__(in_features, lookback, repr_dim=repr_dim, use_revin=use_revin)

        layers = []
        num_levels = len(num_channels)
        for i in range(num_levels):
            dilation_size = 2 ** i
            in_ch = in_features if i == 0 else num_channels[i - 1]
            out_ch = num_channels[i]
            padding = (kernel_size - 1) * dilation_size
            layers.append(TemporalBlock(in_ch, out_ch, kernel_size, stride=1, dilation=dilation_size, padding=padding, dropout=dropout))

        self.network = nn.Sequential(*layers)
        self.norm = nn.LayerNorm(repr_dim)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        x_t = x.transpose(1, 2)
        out = self.network(x_t)
        last_step = out[:, :, -1]
        return self.norm(last_step)


# =========================================================================
# 7. CNN-LSTM HYBRID MODEL
# =========================================================================

class CNNLSTMModel(BaseSequenceModel):
    """Hybrid model: 1D-CNN local feature extraction followed by LSTM sequence aggregation."""

    def __init__(self, in_features: int, lookback: int, cnn_channels: int = 24, lstm_hidden: int = 24, dropout: float = 0.15, use_revin: bool = False):
        super().__init__(in_features, lookback, repr_dim=lstm_hidden, use_revin=use_revin)
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels=in_features, out_channels=cnn_channels, kernel_size=3, padding=1),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.lstm = nn.LSTM(
            input_size=cnn_channels,
            hidden_size=lstm_hidden,
            num_layers=1,
            batch_first=True,
        )
        self.norm = nn.LayerNorm(lstm_hidden)
        self.dropout = nn.Dropout(dropout)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        x_t = x.transpose(1, 2)
        conv_out = self.conv(x_t).transpose(1, 2)
        lstm_out, (h_n, c_n) = self.lstm(conv_out)
        return self.dropout(self.norm(h_n[-1]))


# =========================================================================
# 8. TRANSFORMER ENCODER MODEL
# =========================================================================

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 500):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1), :]


class TransformerEncoderModel(BaseSequenceModel):
    """Multi-Head Self-Attention Transformer encoder for financial sequences."""

    def __init__(self, in_features: int, lookback: int, d_model: int = 24, nhead: int = 2, num_layers: int = 1, dim_feedforward: int = 48, dropout: float = 0.1, use_revin: bool = False):
        super().__init__(in_features, lookback, repr_dim=d_model, use_revin=use_revin)
        self.input_proj = nn.Linear(in_features, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len=max(lookback + 10, 200))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d_model)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        h = self.input_proj(x)
        h = self.pos_encoder(h)
        out = self.transformer(h)
        pooled = torch.mean(out, dim=1)
        return self.norm(pooled)


# =========================================================================
# 9. PatchTST MODEL (Patch-based channel-independent transformer)
# =========================================================================

class PatchTSTModel(BaseSequenceModel):
    """PatchTST: Patch Time Series Transformer (Nie et al., ICLR 2023)."""

    def __init__(self, in_features: int, lookback: int, num_channels: int = 8, patch_len: int = 8, stride: int = 4, d_model: int = 24, nhead: int = 2, num_layers: int = 1, dropout: float = 0.1, use_revin: bool = False):
        super().__init__(in_features, lookback, repr_dim=d_model, use_revin=use_revin)
        self.num_channels = num_channels
        self.patch_len = patch_len
        self.stride = stride
        self.d_model = d_model

        # Project multivariate feature dimension to compact channel subspace
        self.channel_proj = nn.Linear(in_features, num_channels)

        # Calculate number of patches
        self.num_patches = max(1, (lookback - patch_len) // stride + 1)
        self.patch_proj = nn.Linear(patch_len, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len=self.num_patches + 10)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 2,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers, enable_nested_tensor=False)
        self.channel_combine = nn.Linear(num_channels, 1)
        self.norm = nn.LayerNorm(d_model)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        B, L, D = x.shape
        # Project features to compact channels
        x_proj = self.channel_proj(x)  # (B, L, num_channels)
        num_ch = x_proj.size(-1)

        # Pad along sequence dimension if shorter than patch_len
        if L < self.patch_len:
            pad = self.patch_len - L
            x_proj = F.pad(x_proj, (0, 0, pad, 0))
            L = self.patch_len

        # Unfold patches: shape (B, num_ch, num_patches, patch_len)
        x_perm = x_proj.permute(0, 2, 1)  # (B, num_ch, L)
        patches = x_perm.unfold(dimension=-1, size=self.patch_len, step=self.stride)
        actual_num_patches = patches.size(2)

        # Reshape to (B * num_ch, num_patches, patch_len)
        patches = patches.contiguous().view(B * num_ch, actual_num_patches, self.patch_len)
        h = self.patch_proj(patches)
        h = self.pos_encoder(h)
        out = self.transformer(h)

        # Pool over patches
        pooled_patch = torch.mean(out, dim=1)  # (B * num_ch, d_model)
        pooled_patch = pooled_patch.view(B, num_ch, self.d_model)
        # Combine channels: (B, d_model, num_ch) @ (num_ch, 1) -> (B, d_model)
        combined = self.channel_combine(pooled_patch.transpose(1, 2)).squeeze(-1)
        return self.norm(combined)


# =========================================================================
# 10. DLinear MODEL (Trend and Seasonal Decomposition)
# =========================================================================

class MovingAvg(nn.Module):
    """Moving average block to extract trend component."""
    def __init__(self, kernel_size: int, stride: int = 1):
        super().__init__()
        self.kernel_size = kernel_size
        self.avg = nn.AvgPool1d(kernel_size=kernel_size, stride=stride, padding=0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        front = x[:, :, 0:1].repeat(1, 1, (self.kernel_size - 1) // 2)
        end = x[:, :, -1:].repeat(1, 1, self.kernel_size // 2)
        x_pad = torch.cat([front, x, end], dim=-1)
        return self.avg(x_pad)


class DLinearModel(BaseSequenceModel):
    """DLinear: Series decomposition into trend and seasonal components (Zeng et al., AAAI 2023)."""

    def __init__(self, in_features: int, lookback: int, repr_dim: int = 24, kernel_size: int = 5, use_revin: bool = False):
        super().__init__(in_features, lookback, repr_dim=repr_dim, use_revin=use_revin)
        self.decomposition = MovingAvg(kernel_size=kernel_size)
        self.linear_seasonal = nn.Linear(lookback * in_features, repr_dim)
        self.linear_trend = nn.Linear(lookback * in_features, repr_dim)
        self.norm = nn.LayerNorm(repr_dim)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        B, L, D = x.shape
        x_t = x.transpose(1, 2)
        trend = self.decomposition(x_t).transpose(1, 2)
        seasonal = x - trend

        trend_flat = trend.contiguous().view(B, -1)
        seasonal_flat = seasonal.contiguous().view(B, -1)

        z_trend = self.linear_trend(trend_flat)
        z_season = self.linear_seasonal(seasonal_flat)
        z = z_trend + z_season
        return self.norm(z)


# =========================================================================
# 11. N-BEATS MODEL (Neural Basis Expansion Analysis)
# =========================================================================

class NBEATSBlock(nn.Module):
    def __init__(self, in_features: int, hidden_dim: int = 32, dropout: float = 0.15):
        super().__init__()
        self.fc1 = nn.Linear(in_features, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.backcast_proj = nn.Linear(hidden_dim, in_features)
        self.forecast_proj = nn.Linear(hidden_dim, hidden_dim // 2)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = F.gelu(self.fc1(x))
        h = self.dropout(h)
        h = F.gelu(self.fc2(h))
        h = self.dropout(h)
        h = F.gelu(self.fc3(h))

        backcast = self.backcast_proj(h)
        forecast = self.forecast_proj(h)
        return backcast, forecast


class NBEATSModel(BaseSequenceModel):
    """N-BEATS: Neural Basis Expansion Analysis with Doubly Residual Stacking (Oreshkin et al., ICLR 2020)."""

    def __init__(self, in_features: int, lookback: int, num_blocks: int = 2, hidden_dim: int = 32, dropout: float = 0.15, use_revin: bool = False):
        repr_dim = hidden_dim // 2
        super().__init__(in_features, lookback, repr_dim=repr_dim, use_revin=use_revin)
        flat_in = in_features * lookback
        self.blocks = nn.ModuleList([
            NBEATSBlock(flat_in, hidden_dim=hidden_dim, dropout=dropout) for _ in range(num_blocks)
        ])
        self.norm = nn.LayerNorm(repr_dim)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        B = x.size(0)
        x_flat = x.contiguous().view(B, -1)

        residual = x_flat
        forecast_total = torch.zeros(B, self.repr_dim, device=x.device)

        for block in self.blocks:
            backcast, forecast = block(residual)
            residual = residual - backcast
            forecast_total = forecast_total + forecast

        return self.norm(forecast_total)


# Registry of available model builders
MODEL_REGISTRY: Dict[str, Any] = {
    "mlp": MLPModel,
    "lstm": LSTMModel,
    "gru": GRUModel,
    "bilstm": BiLSTMModel,
    "cnn1d": CNN1DModel,
    "tcn": TCNModel,
    "cnn_lstm": CNNLSTMModel,
    "transformer": TransformerEncoderModel,
    "patch_tst": PatchTSTModel,
    "dlinear": DLinearModel,
    "nbeats": NBEATSModel,
}


def build_deep_model(
    model_type: str,
    in_features: int,
    lookback: int,
    use_revin: bool = False,
    **kwargs: Any,
) -> BaseSequenceModel:
    """Build a deep sequence model by name with optional RevIN."""
    model_type_clean = model_type.lower()
    if model_type_clean not in MODEL_REGISTRY:
        raise ValueError(
            f"Model type '{model_type}' not recognized. Available: {list(MODEL_REGISTRY.keys())}"
        )
    cls = MODEL_REGISTRY[model_type_clean]
    return cls(in_features=in_features, lookback=lookback, use_revin=use_revin, **kwargs)
