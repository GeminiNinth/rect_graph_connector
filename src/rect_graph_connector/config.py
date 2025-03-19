"""
Global configuration management for the rect_graph_connector application.

This module provides centralized configuration management for system-wide settings.
"""

import os
import yaml
from typing import Dict, Any, Optional


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
            cls._instance._language = "ja"  # Default language
            cls._instance._translations = {"ja": {}, "en": {}}
            cls._instance._load_translations()
        return cls._instance

    def _load_translations(self) -> None:
        """Load translations from YAML files."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        # Load Japanese translations
        ja_path = os.path.join(base_dir, "language", "ja.yaml")
        if os.path.exists(ja_path):
            with open(ja_path, "r", encoding="utf-8") as f:
                self._translations["ja"] = yaml.safe_load(f) or {}

        # Load English translations
        en_path = os.path.join(base_dir, "language", "en.yaml")
        if os.path.exists(en_path):
            with open(en_path, "r", encoding="utf-8") as f:
                self._translations["en"] = yaml.safe_load(f) or {}

    def get_text(self, key_path: str) -> str:
        """
        Get translated text for the given key path.

        Args:
            key_path: Dot-separated path to the translation key (e.g., 'import_dialog.window_title')

        Returns:
            str: Translated text in current language, falling back to English if not found
        """
        # Split the key path into parts
        keys = key_path.split(".")

        # Try to get translation in current language
        current = self._translations[self._language]
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                # If not found in current language, try English
                current = self._translations["en"]
                for k in keys:
                    if isinstance(current, dict) and k in current:
                        current = current[k]
                    else:
                        return key_path  # Return key path if translation not found
                break

        return current if isinstance(current, str) else key_path

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

    @property
    def language(self) -> str:
        """Get the current language setting."""
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        """
        Set the language.

        Args:
            value (str): The language code ('ja' or 'en')
        """
        if value not in ["ja", "en"]:
            value = "en"  # Default to English if invalid language is provided
        self._language = value


# Global configuration instance
config = Configuration()
