"""Unified logging configuration for the stock research data foundation.

Provides structured logging with file rotation and console output.
"""

import logging
import logging.handlers
import os
from pathlib import Path

from .config import config


def setup_logging(name: str = "stock_research", level: str | None = None) -> logging.Logger:
    """Set up and return a configured logger.

    Args:
        name: Logger name (used in log messages and file name)
        level: Log level override (defaults to config.log_level)
    """
    log_level = getattr(logging, (level or config.log_level).upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # File handler with rotation (10MB per file, keep 5 files)
    log_file = config.log_dir / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger


# Default logger instance
logger = setup_logging()
