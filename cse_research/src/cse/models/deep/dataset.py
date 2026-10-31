"""PyTorch Dataset and DataLoader for sequence tensors."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from cse.features.pipeline import SequenceSplitData


class SequenceDataset(Dataset):
    """PyTorch Dataset for historical lookback windows and forward returns."""

    def __init__(self, seq_data: SequenceSplitData, aspi_levels: Optional[np.ndarray] = None):
        self.X = torch.tensor(seq_data.X_seq, dtype=torch.float32)
        self.y_ret = torch.tensor(seq_data.y_ret, dtype=torch.float32)
        self.y_dir = torch.tensor(seq_data.y_dir, dtype=torch.float32)
        self.dates = list(seq_data.dates)
        self.aspi_levels = (
            torch.tensor(aspi_levels, dtype=torch.float32)
            if aspi_levels is not None
            else torch.ones(len(self.dates), dtype=torch.float32)
        )

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]:
        return self.X[idx], self.y_ret[idx], self.y_dir[idx], idx


def create_dataloader(
    seq_data: SequenceSplitData,
    batch_size: int = 64,
    shuffle: bool = True,
    aspi_levels: Optional[np.ndarray] = None,
) -> DataLoader:
    """Create PyTorch DataLoader for sequence training/inference."""
    dataset = SequenceDataset(seq_data, aspi_levels=aspi_levels)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=False,
    )
