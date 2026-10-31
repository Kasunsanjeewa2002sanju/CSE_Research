"""Configuration loader and schema validator."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


def find_project_root(anchor_file: str = "RULES.md") -> Path:
    """Locate the root directory of the cse_research project.

    Searches upward from source file location first, then current working directory.
    """
    # Search upward from source file location
    file_path = Path(__file__).resolve()
    for parent in [file_path.parent] + list(file_path.parents):
        if (parent / anchor_file).exists():
            return parent
        if (parent / "cse_research" / anchor_file).exists():
            return parent / "cse_research"

    # Search upward from current working directory
    current = Path.cwd().resolve()
    if (current / anchor_file).exists():
        return current
    if (current / "cse_research" / anchor_file).exists():
        return current / "cse_research"
    for parent in current.parents:
        if (parent / anchor_file).exists():
            return parent
        if (parent / "cse_research" / anchor_file).exists():
            return parent / "cse_research"

    return current


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load and parse the project configuration YAML.

    Parameters
    ----------
    config_path : Optional[str]
        Explicit path to config.yaml. If None, auto-locates inside config/config.yaml.

    Returns
    -------
    Dict[str, Any]
        Parsed configuration dictionary.
    """
    if config_path is None:
        root = find_project_root()
        candidate = root / "config" / "config.yaml"
        if candidate.exists():
            config_path = str(candidate)
        else:
            # Fallback relative
            config_path = "config/config.yaml"

    target_file = Path(config_path)
    if not target_file.exists():
        raise FileNotFoundError(f"Configuration file not found at: {target_file.resolve()}")

    with open(target_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"Invalid configuration format in {target_file}; expected YAML dictionary.")

    return config
