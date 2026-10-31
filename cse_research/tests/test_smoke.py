"""Smoke test suite verifying package imports, config loading, and runtime utilities."""

import pytest
from pathlib import Path
import cse
from cse.utils.config import load_config, find_project_root
from cse.utils.seed import seed_everything
from cse.utils.device import get_device, get_device_info
from cse.utils.logger import get_logger, setup_logger


def test_import_package() -> None:
    """Verify cse package can be imported and has version string."""
    assert hasattr(cse, "__version__")
    assert isinstance(cse.__version__, str)
    assert len(cse.__version__) > 0


def test_load_config() -> None:
    """Verify config.yaml can be located, loaded, and contains required schema keys."""
    config = load_config()
    assert isinstance(config, dict)
    
    # Required top-level sections
    required_keys = [
        "project",
        "seed",
        "paths",
        "inputs",
        "phases",
        "horizons",
        "windows",
        "models",
        "evaluation",
        "hardware",
        "logging",
    ]
    for key in required_keys:
        assert key in config, f"Missing required configuration key: {key}"

    # Verify seed
    assert isinstance(config["seed"], int)
    assert config["seed"] == 42

    # Verify horizons
    assert "h1" in config["horizons"]
    assert "h5" in config["horizons"]
    assert "h20" in config["horizons"]

    # Verify models
    for family in ["statistical", "shallow", "deep", "foundation", "hybrid"]:
        assert family in config["models"], f"Missing model family: {family}"
        assert len(config["models"][family]) > 0


def test_seed_reproducibility() -> None:
    """Verify seed_everything applies successfully."""
    seed_val = seed_everything(42)
    assert seed_val == 42


def test_device_detection() -> None:
    """Verify get_device and get_device_info return valid hardware descriptors."""
    device = get_device()
    assert isinstance(device, str)
    assert device in ["cpu", "cuda"]

    info = get_device_info()
    assert isinstance(info, dict)
    assert "device_type" in info
    assert "device_name" in info
    assert "is_cuda_available" in info


def test_structured_logger() -> None:
    """Verify structured logger instantiates and handles log records."""
    logger = get_logger("cse.test")
    assert logger is not None
    logger.info("Smoke test structured logging verification message.")


def test_raw_data_presence() -> None:
    """Verify raw input files exist in data/raw without alteration (Rule R1)."""
    root = find_project_root()
    raw_dir = root / "data" / "raw"
    assert raw_dir.exists(), f"Raw data directory does not exist: {raw_dir}"

    cse_file = raw_dir / "CSE_data.csv"
    elections_file = raw_dir / "Elections.csv"
    proposal_file = raw_dir / "Predicting Stock Market Movements Using Government_Changes_updated.pdf"

    assert cse_file.exists(), f"Missing required file: {cse_file}"
    assert elections_file.exists(), f"Missing required file: {elections_file}"
    assert proposal_file.exists(), f"Missing proposal PDF: {proposal_file}"

    assert cse_file.stat().st_size > 0
    assert elections_file.stat().st_size > 0
    assert proposal_file.stat().st_size > 0
