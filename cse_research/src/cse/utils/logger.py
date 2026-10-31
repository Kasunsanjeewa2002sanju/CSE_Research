"""Structured logging utility for experiments and pipelines (Rule R6, R7)."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Format log records as structured JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_payload.update(record.extra)
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_payload)


def setup_logger(
    name: str = "cse",
    log_file: Optional[str] = "results/logs/cse_research.log",
    level: int = logging.INFO,
    structured_json: bool = True,
) -> logging.Logger:
    """Set up and configure a structured logger.

    Parameters
    ----------
    name : str
        Logger name identifier.
    log_file : Optional[str]
        Path to output log file. If provided, directory is automatically created.
    level : int
        Logging level (default: logging.INFO).
    structured_json : bool
        Whether file logging uses JSON lines format.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Avoid duplicate handlers if setup_logger is called repeatedly
    if logger.handlers:
        return logger

    # Console handler with clean readable formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            workspace_root = Path(__file__).resolve().parents[3]
            log_path = workspace_root / log_path
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
            file_handler.setLevel(level)
            if structured_json:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
        except Exception:
            # Fall back to console only if file logging fails
            pass

    return logger


def get_logger(name: str = "cse") -> logging.Logger:
    """Retrieve an existing logger or create default."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name=name)
    return logger
