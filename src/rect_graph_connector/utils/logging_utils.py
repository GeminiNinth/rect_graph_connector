"""
Logging utilities for the rect_graph_connector application.

This module provides centralized logging configuration and initialization.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from ..config import config


def setup_logging(log_dir: str = ".log") -> None:
    """
    Set up logging configuration for the application.

    Args:
        log_dir (str): Directory where log files will be stored. Defaults to ".log".
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Set up logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # File handler for all logs
            logging.FileHandler(
                os.path.join(log_dir, "rect_graph_connector.log"), encoding="utf-8"
            ),
            # File handler for errors only
            logging.FileHandler(
                os.path.join(log_dir, "error.log"),
                encoding="utf-8",
                level=logging.ERROR,
            ),
            # Console handler
            logging.StreamHandler(),
        ],
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name (Optional[str]): The name of the logger. If None, returns the root logger.

    Returns:
        logging.Logger: A configured logger instance.
    """
    return logging.getLogger(name)
