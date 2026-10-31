"""Reproducibility utilities for random state management (Rule R7)."""

import os
import random
from typing import Optional


def seed_everything(seed: int = 42) -> int:
    """Set global seeds across python random, numpy, and torch (if installed).

    Parameters
    ----------
    seed : int
        Integer seed value to enforce reproducibility.

    Returns
    -------
    int
        The seed value that was applied.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    return seed
