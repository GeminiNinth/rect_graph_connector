"""
Base style class for rendering components.
"""

from abc import ABC
from PyQt5.QtGui import QColor

from ....config import config


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

    def get_color(self, key, default=None):
        """
        Get a color from the configuration.

        Args:
            key (str): The configuration key for the color
            default (str, optional): Default color value if not found in config

        Returns:
            QColor: The color as a QColor object
        """
        color_str = config.get_color(key, default)
        try:
            return parse_color(color_str)
        except ValueError as e:
            # Log error and return a fallback color (black) to prevent crashes
            print(f"Error parsing color for key '{key}': {e}")
            return QColor(0, 0, 0)

    def get_dimension(self, key, default=None):
        """
        Get a dimension value from the configuration.

        Args:
            key (str): The configuration key for the dimension
            default (float, optional): Default dimension value if not found in config

        Returns:
            float: The dimension value
        """
        return config.get_dimension(key, default)

    def get_constant(self, key, default=None):
        """
        Get a constant value from the configuration.

        Args:
            key (str): The configuration key for the constant
            default (any, optional): Default constant value if not found in config

        Returns:
            any: The constant value
        """
        return config.get_constant(key, default)
