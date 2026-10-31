"""Deep sequence models package (Stage 7).

PyTorch architectures:
    - MLP
    - LSTM
    - GRU
    - BiLSTM (bidirectional strictly over the past lookback window)
    - 1D-CNN
    - TCN (Temporal Convolutional Network with causal dilated convolutions)
    - CNN-LSTM hybrid
    - Transformer Encoder
    - PatchTST (Patch Time Series Transformer)
    - DLinear (Trend and seasonal decomposition linear projections)
    - N-BEATS (Neural basis expansion analysis with doubly residual stacking)
    - RevIN (Reversible Instance Normalization)
"""

from cse.models.deep.revin import RevIN
from cse.models.deep.architectures import (
    BaseSequenceModel,
    MLPModel,
    LSTMModel,
    GRUModel,
    BiLSTMModel,
    CNN1DModel,
    TCNModel,
    CNNLSTMModel,
    TransformerEncoderModel,
    PatchTSTModel,
    DLinearModel,
    NBEATSModel,
    build_deep_model,
    MODEL_REGISTRY,
)
from cse.models.deep.dataset import SequenceDataset, create_dataloader
from cse.models.deep.trainer import DeepSequenceTrainer, get_device, get_hardware_info, set_seed
from cse.models.deep.tuner import select_best_lookback

__all__ = [
    "RevIN",
    "BaseSequenceModel",
    "MLPModel",
    "LSTMModel",
    "GRUModel",
    "BiLSTMModel",
    "CNN1DModel",
    "TCNModel",
    "CNNLSTMModel",
    "TransformerEncoderModel",
    "PatchTSTModel",
    "DLinearModel",
    "NBEATSModel",
    "build_deep_model",
    "MODEL_REGISTRY",
    "SequenceDataset",
    "create_dataloader",
    "DeepSequenceTrainer",
    "get_device",
    "get_hardware_info",
    "set_seed",
    "select_best_lookback",
]
