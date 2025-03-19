"""
Global configuration management for the rect_graph_connector application.

This module provides centralized configuration management for system-wide settings.
"""


class Configuration:
    """
    Global configuration management class.

    This class manages system-wide settings and flags that affect the behavior
    of various components in the application.

    Attributes:
        allow_duplicate_names (bool): Flag to allow duplicate node group names
        node_id_start (int): Starting index for node IDs (0 or any positive integer)
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Configuration, cls).__new__(cls)
            # Initialize default settings
            cls._instance._allow_duplicate_names = True
            cls._instance._node_id_start = 0
            cls._instance._log_level = "INFO"  # Default log level
        return cls._instance

    @property
    def allow_duplicate_names(self) -> bool:
        """Get the current duplicate names allowance setting."""
        return self._allow_duplicate_names

    @allow_duplicate_names.setter
    def allow_duplicate_names(self, value: bool) -> None:
        """
        Set the duplicate names allowance setting.

        Args:
            value (bool): True to allow duplicate names, False to enforce uniqueness
        """
        self._allow_duplicate_names = value

    @property
    def node_id_start(self) -> int:
        """Get the starting node ID."""
        return self._node_id_start

    @node_id_start.setter
    def node_id_start(self, value: int) -> None:
        """
        Set the starting node ID.

        Args:
            value (int): The starting node ID (must be a natural number including 0)
        """
        if value < 0:
            value = 0  # Ensure it's a natural number including 0
        self._node_id_start = value

    @property
    def log_level(self) -> str:
        """Get the current logging level."""
        return self._log_level

    @log_level.setter
    def log_level(self, value: str) -> None:
        """
        Set the logging level.

        Args:
            value (str): The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value.upper() not in valid_levels:
            value = "INFO"  # Default to INFO if invalid level is provided
        self._log_level = value.upper()


# Global configuration instance
config = Configuration()
