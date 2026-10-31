"""Hardware device detection with automatic GPU detection and CPU fallback."""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class DeviceInfo:
    """Hardware device diagnostic metadata."""
    device_type: str
    device_name: str
    is_cuda_available: bool
    cuda_device_count: int
    total_memory_mb: Optional[float] = None
    cuda_version: Optional[str] = None


def get_device(preferred_device: Optional[str] = None) -> str:
    """Determine the optimal compute device.

    Parameters
    ----------
    preferred_device : Optional[str]
        Explicit device override (e.g. 'cpu', 'cuda', 'cuda:0').
        If None, automatically detects CUDA GPU with CPU fallback.

    Returns
    -------
    str
        Device identifier string ('cuda', 'cuda:0', or 'cpu').
    """
    if preferred_device:
        return preferred_device

    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass

    return "cpu"


def get_device_info() -> Dict[str, Any]:
    """Retrieve full hardware device metadata for reproducibility logs.

    Returns
    -------
    Dict[str, Any]
        Structured dictionary of hardware diagnostics.
    """
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        count = torch.cuda.device_count() if cuda_avail else 0
        name = torch.cuda.get_device_name(0) if cuda_avail and count > 0 else "CPU"
        total_mem = None
        if cuda_avail and count > 0:
            total_mem = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2), 2)
        
        info = DeviceInfo(
            device_type="cuda" if cuda_avail else "cpu",
            device_name=name,
            is_cuda_available=cuda_avail,
            cuda_device_count=count,
            total_memory_mb=total_mem,
            cuda_version=torch.version.cuda if cuda_avail else None,
        )
        return asdict(info)
    except ImportError:
        return asdict(DeviceInfo(
            device_type="cpu",
            device_name="CPU (torch not installed)",
            is_cuda_available=False,
            cuda_device_count=0,
            total_memory_mb=None,
            cuda_version=None,
        ))
