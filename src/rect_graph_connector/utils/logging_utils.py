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


def setup_logging(log_dir: str = None) -> None:
    """
    Set up logging configuration for the application.

    Args:
        log_dir (str, optional): Directory where log files will be stored.
                                If None, uses the value from config.
    """
    # Get log directory from config if not provided
    if log_dir is None:
        log_dir = config.get_constant("logging.directory", ".log")

    # Create base log directory if it doesn't exist
    log_base_path = Path(log_dir)
    log_base_path.mkdir(exist_ok=True)

    # Create datetime-based directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_base_path / timestamp
    log_path.mkdir(exist_ok=True)

    # Create/Update symlink to latest log directory using os module directly
    import os
    import shutil
    import platform
    import time

    latest_link_path = str(log_base_path / "latest")
    target_path = timestamp  # Just the timestamp string, not a Path object

    # Force remove the existing symlink or directory
    try:
        if os.path.islink(latest_link_path):
            os.unlink(latest_link_path)
        elif os.path.isdir(latest_link_path):
            shutil.rmtree(latest_link_path)
        elif os.path.exists(latest_link_path):
            os.remove(latest_link_path)
    except Exception as e:
        print(f"Warning: Failed to remove existing 'latest' link: {e}")

    # Handle platform-specific symlink creation
    if platform.system() == "Windows":
        # On Windows, create a text file with the path to the latest log directory
        # This is a workaround for the symlink permission issue on Windows
        try:
            with open(latest_link_path + ".txt", "w") as f:
                f.write(timestamp)
            print(f"Created latest.txt pointer to {timestamp} log directory")
        except Exception as e:
            print(f"Warning: Failed to create latest.txt pointer: {e}")
    else:
        # On Unix-like systems, create a proper symlink
        try:
            os.symlink(target_path, latest_link_path, target_is_directory=True)
        except FileExistsError:
            # If it still fails, try one more aggressive approach
            print(
                f"Warning: Failed to create symlink on first attempt, trying again..."
            )
            # Force remove again with different method
            try:
                if os.path.exists(latest_link_path):
                    os.unlink(latest_link_path)
            except Exception as e:
                print(f"Warning: Failed to remove link on second attempt: {e}")

            # Try again with a small delay
            time.sleep(0.1)
            os.symlink(target_path, latest_link_path, target_is_directory=True)

    # Set up logging format from config
    log_format = config.get_constant(
        "logging.formats.log", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    date_format = config.get_constant("logging.formats.date", "%Y-%m-%d %H:%M:%S")

    # Get log filenames from config
    main_log_filename = config.get_constant(
        "logging.filenames.main", "rect_graph_connector.log"
    )
    error_log_filename = config.get_constant("logging.filenames.error", "error.log")

    # Create handlers
    # File handler for all logs
    file_handler = logging.FileHandler(
        os.path.join(log_path, main_log_filename), encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    file_handler.setLevel(getattr(logging, config.log_level))

    # File handler for errors only
    error_handler = logging.FileHandler(
        os.path.join(log_path, error_log_filename), encoding="utf-8"
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
