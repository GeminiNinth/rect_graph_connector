"""
Global configuration management for the rect_graph_connector application.

This module provides centralized configuration management for system-wide settings.
It handles loading and accessing various configuration values from YAML files including:
- UI dimensions (sizes, margins, etc.)
- Color schemes (with support for light/dark themes)
- UI strings (labels, button texts, etc.)
- Constants (flags, mode names, etc.)
- Language translations
"""

import os
import yaml
from typing import Dict, Any, Optional, Union


class Configuration:
    """
    Global configuration management class.

    This class manages system-wide settings and flags that affect the behavior
    of various components in the application.

    Attributes:
        allow_duplicate_names (bool): Flag to allow duplicate node group names
        node_id_start (int): Starting index for node IDs (0 or any positive integer)
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        language (str): Current language setting ('ja' or 'en')
        theme_mode (str): Current theme mode ('light' or 'dark')
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
            cls._instance._theme_mode = "light"  # Default theme mode
            cls._instance._translations = {"ja": {}, "en": {}}
            cls._instance._dimensions = {}
            cls._instance._colors = {"light": {}, "dark": {}}
            cls._instance._strings = {}
            cls._instance._constants = {}
            cls._instance._load_translations()
            cls._instance._load_config()
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

    def _load_config(self) -> None:
        """Load configuration from YAML files in the config directory."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_dir = os.path.join(base_dir, "config")

        # Load dimensions config
        dimensions_path = os.path.join(config_dir, "dimensions.yaml")
        if os.path.exists(dimensions_path):
            with open(dimensions_path, "r", encoding="utf-8") as f:
                self._dimensions = yaml.safe_load(f) or {}

        # Load colors config
        colors_path = os.path.join(config_dir, "colors.yaml")
        if os.path.exists(colors_path):
            with open(colors_path, "r", encoding="utf-8") as f:
                colors_data = yaml.safe_load(f) or {}
                if "light" in colors_data:
                    self._colors["light"] = colors_data["light"]
                if "dark" in colors_data:
                    self._colors["dark"] = colors_data["dark"]

        # Load strings config
        strings_path = os.path.join(config_dir, "strings.yaml")
        if os.path.exists(strings_path):
            with open(strings_path, "r", encoding="utf-8") as f:
                self._strings = yaml.safe_load(f) or {}

        # Load constants config
        constants_path = os.path.join(config_dir, "constants.yaml")
        if os.path.exists(constants_path):
            with open(constants_path, "r", encoding="utf-8") as f:
                self._constants = yaml.safe_load(f) or {}

    def _get_nested_value(self, data_dict: Dict, key_path: str, default=None) -> Any:
        """
        Get a nested value from a dictionary using a dot-separated key path.

        Args:
            data_dict: The dictionary to search in
            key_path: Dot-separated path to the key (e.g., 'canvas.border.width')
            default: Default value to return if key is not found

        Returns:
            The value at the specified key path, or default if not found
        """
        # Split the key path into parts
        keys = key_path.split(".")

        # Try to get the value from the dictionary
        current = data_dict
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

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

    def get_dimension(self, key_path: str, default=None) -> Any:
        """
        Get a dimension value from the configuration.

        Args:
            key_path: Dot-separated path to the dimension key (e.g., 'canvas.min_height')
            default: Default value to return if key is not found

        Returns:
            The dimension value at the specified key path, or default if not found
        """
        return self._get_nested_value(self._dimensions, key_path, default)

    def get_color(self, key_path: str, default=None) -> str:
        """
        Get a color value from the configuration.

        Args:
            key_path: Dot-separated path to the color key (e.g., 'canvas.border.normal')
            default: Default value to return if key is not found

        Returns:
            The color value at the specified key path, or default if not found
        """
        # Get colors for the current theme mode
        colors = self._colors.get(self._theme_mode, self._colors.get("light", {}))
        return self._get_nested_value(colors, key_path, default)

    def get_string(self, key_path: str, default=None) -> str:
        """
        Get a string value from the configuration.

        Args:
            key_path: Dot-separated path to the string key (e.g., 'main_window.title')
            default: Default value to return if key is not found

        Returns:
            The string value at the specified key path, or default if not found
        """
        return self._get_nested_value(self._strings, key_path, default)

    def get_constant(self, key_path: str, default=None) -> Any:
        """
        Get a constant value from the configuration.

        Args:
            key_path: Dot-separated path to the constant key (e.g., 'canvas_modes.normal')
            default: Default value to return if key is not found

        Returns:
            The constant value at the specified key path, or default if not found
        """
        return self._get_nested_value(self._constants, key_path, default)

    def get(self, config_type: str, key_path: str, default=None) -> Any:
        """
        General-purpose configuration getter.

        Args:
            config_type: Type of configuration ('dimension', 'color', 'string', 'constant')
            key_path: Dot-separated path to the key
            default: Default value to return if key is not found

        Returns:
            The value at the specified key path, or default if not found
        """
        if config_type == "dimension":
            return self.get_dimension(key_path, default)
        elif config_type == "color":
            return self.get_color(key_path, default)
        elif config_type == "string":
            return self.get_string(key_path, default)
        elif config_type == "constant":
            return self.get_constant(key_path, default)
        return default

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

    @property
    def theme_mode(self) -> str:
        """Get the current theme mode ('light' or 'dark')."""
        return self._theme_mode

    @theme_mode.setter
    def theme_mode(self, value: str) -> None:
        """
        Set the theme mode.

        Args:
            value (str): The theme mode ('light' or 'dark')
        """
        if value not in ["light", "dark"]:
            value = "light"  # Default to light mode if invalid
        self._theme_mode = value


# Global configuration instance
config = Configuration()
