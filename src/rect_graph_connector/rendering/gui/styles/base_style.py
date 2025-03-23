"""
Base style class for rendering components.
"""

from abc import ABC
from typing import Any, Dict, Optional, Union
from PyQt5.QtGui import QColor

from ....config import config
from ....utils.logging_utils import get_logger

logger = get_logger(__name__)

# Default value when `config/colors.yaml` cannot be loaded
STYLES: Dict[str, Dict[str, str]] = {
    "node": {
        "fill": "skyblue",
        "border": "gray",
        "selected_fill": "#FFA500",
        "selected_border": "#FF4500",
        "hover_fill": "#87CEEB",
        "hover_border": "#4682B4",
        "bridge_target_highlighted_fill": "#50FCC0",
        "bridge_target_highlighted_border": "#10DDFF",
    },
    "group": {
        "fill": "rgba(200,200,200,128)",
        "border": "#808080",
        "selected_fill": "rgba(255,200,100,128)",
        "selected_border": "#FF8C00",
    },
    "edge": {
        "normal": "#6495ED",
        "selected": "#FF4500",
        "hover": "#4169E1",
    },
    "bridge_window": {
        "node_area_background": "#F5F5F5",
        "node_area_connection_line": "#6495ED",
        "background_light": "rgba(255, 255, 255, 240)",
        "background_dark": "rgba(40, 40, 40, 240)",
        "button_background_dark": "#555555",
        "button_text_dark": "#FFFFFF",
    },
}


def parse_color(color_str):
    """
    Parse color string and return QColor object.
    Supports hex, rgba(), and named color formats.

    Args:
        color_str (str): Color string in one of the following formats:
            - Hex: "#RRGGBB" or "#RRGGBBAA"
            - RGBA: "rgba(r,g,b,a)" where r,g,b are 0-255 and a is 0-255 or 0-1
            - Named color: e.g., "red", "skyblue", etc.

    Returns:
        QColor: QColor object with the specified color

    Raises:
        ValueError: If the color string format is invalid
    """
    import re

    # Handle empty or invalid input
    if not color_str or not isinstance(color_str, str):
        raise ValueError(f"Invalid color string: {color_str}")

    # Handle rgba format
    if color_str.startswith("rgba"):
        match = re.match(
            r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+|\d*\.\d+)\)", color_str
        )
        if not match:
            raise ValueError(f"Invalid rgba format: {color_str}")

        r, g, b, a = match.groups()
        r, g, b = map(int, [r, g, b])
        # Convert alpha to 0-255 range if it's a float
        a = int(float(a) * 255) if "." in a else int(a)

        # Validate ranges
        if not all(0 <= x <= 255 for x in [r, g, b, a]):
            raise ValueError(f"Color values out of range in: {color_str}")

        color = QColor()
        color.setRgb(r, g, b, a)
        return color

    # Handle hex format
    if color_str.startswith("#"):
        # Remove '#' and validate length
        hex_str = color_str[1:]
        if len(hex_str) not in [6, 8]:  # RRGGBB or RRGGBBAA
            raise ValueError(f"Invalid hex color format: {color_str}")

        try:
            # Parse hex values
            if len(hex_str) == 6:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                return QColor(r, g, b)
            else:  # len == 8, includes alpha
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                a = int(hex_str[6:8], 16)
                return QColor(r, g, b, a)
        except ValueError:
            raise ValueError(f"Invalid hex color values in: {color_str}")

    # Handle named colors
    color = QColor(color_str)
    if not color.isValid():
        raise ValueError(f"Invalid color name: {color_str}")
    return color


def apply_style(widget: Any, style_key: str) -> None:
    """
    Apply predefined style to a widget.

    Args:
        widget: The widget object to style.
        style_key: The key identifying the style in the STYLES dictionary.
    """
    style: Dict[str, str] = STYLES.get(style_key, {})
    for attr, value in style.items():
        setattr(widget, attr, value)


class BaseStyle(ABC):
    """
    Abstract base class for all rendering styles.

    This class provides common functionality for styles used by renderers.
    Concrete style classes should inherit from this class and implement
    specific styling properties.
    """

    def __init__(self):
        """Initialize the base style."""
        pass

    def get_color(self, key: str, default: Optional[str] = None) -> QColor:
        """
        Get a color from the configuration.

        Args:
            key: The configuration key for the color
            default: Default color value if not found in config

        Returns:
            QColor: The color as a QColor object
        """
        color_str = config.get_color(key, default)
        try:
            return parse_color(color_str)
        except ValueError as e:
            # Log error and return a fallback color (black) to prevent crashes
            logger.error(f"Error parsing color for key '{key}': {e}")
            return QColor(0, 0, 0)

    def get_dimension(self, key: str, default: Optional[float] = None) -> float:
        """
        Get a dimension value from the configuration.

        Args:
            key: The configuration key for the dimension
            default: Default dimension value if not found in config

        Returns:
            float: The dimension value
        """
        return config.get_dimension(key, default)

    def get_constant(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a constant value from the configuration.

        Args:
            key: The configuration key for the constant
            default: Default constant value if not found in config

        Returns:
            Any: The constant value
        """
        return config.get_constant(key, default)

    def get_style(
        self, category: str, style_type: str, default: Optional[str] = None
    ) -> str:
        """
        Get a style value from the centralized style dictionary.

        Args:
            category: The category in the STYLES dictionary (e.g., 'node', 'edge')
            style_type: The style type within the category (e.g., 'fill', 'border')
            default: Default style value if not found

        Returns:
            str: The style value
        """
        if category in STYLES and style_type in STYLES[category]:
            return STYLES[category][style_type]
        return default

    def get_style_color(
        self, category: str, style_type: str, default: Optional[str] = None
    ) -> QColor:
        """
        Get a style color from the centralized style dictionary as QColor.

        Args:
            category: The category in the STYLES dictionary (e.g., 'node', 'edge')
            style_type: The style type within the category (e.g., 'fill', 'border')
            default: Default color value if not found

        Returns:
            QColor: The color as a QColor object
        """
        color_str = self.get_style(category, style_type, default)
        try:
            return parse_color(color_str)
        except ValueError as e:
            # Log error and return a fallback color (black) to prevent crashes
            logger.error(
                f"Error parsing color for style '{category}.{style_type}': {e}"
            )
            return QColor(0, 0, 0)
