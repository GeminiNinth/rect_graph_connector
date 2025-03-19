"""
Logging utilities for the rect_graph_connector application.

This module provides centralized logging configuration and initialization.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import config


def setup_logging(log_dir: str = ".log") -> None:
    """
    Set up logging configuration for the application.

    Args:
        log_dir (str): Directory where log files will be stored. Defaults to ".log".
    """
    # Create base log directory if it doesn't exist
    log_base_path = Path(log_dir)
    log_base_path.mkdir(exist_ok=True)

    # Create datetime-based directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_base_path / timestamp
    log_path.mkdir(exist_ok=True)

    # Create/Update symlink to latest log directory
    latest_link = log_base_path / "latest"
    if latest_link.exists():
        latest_link.unlink()
    # Use the directory name only for the symlink target
    latest_link.symlink_to(timestamp, target_is_directory=True)

    # Set up logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Create handlers
    # File handler for all logs
    file_handler = logging.FileHandler(
        os.path.join(log_path, "rect_graph_connector.log"), encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    file_handler.setLevel(getattr(logging, config.log_level))

    # File handler for errors only
    error_handler = logging.FileHandler(
        os.path.join(log_path, "error.log"), encoding="utf-8"
    )
    error_handler.setFormatter(logging.Formatter(log_format, date_format))
    error_handler.setLevel(logging.ERROR)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    console_handler.setLevel(getattr(logging, config.log_level))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level))

    # Remove any existing handlers
    root_logger.handlers = []

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name (Optional[str]): The name of the logger. If None, returns the root logger.

    Returns:
        logging.Logger: A configured logger instance.
    """
    return logging.getLogger(name)
