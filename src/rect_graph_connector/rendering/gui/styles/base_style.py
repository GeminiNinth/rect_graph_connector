"""
Base style class for rendering components.
"""

from abc import ABC
from PyQt5.QtGui import QColor

from ....config import config


def parse_rgba(rgba_str):
    """
    Parse rgba string and return QColor object.
    Supports both hex and rgba() format.

    Args:
        rgba_str (str): Color string in format 'rgba(r,g,b,a)' or hex format
        where a can be integer (0-255) or float (0-1)

    Returns:
        QColor: QColor object with the specified color
    """
    import re

    if rgba_str.startswith("rgba"):
        # Parse rgba(r,g,b,a) format
        match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+|\d*\.\d+)\)", rgba_str)
        if match:
            r, g, b, a = match.groups()
            r, g, b = map(int, [r, g, b])
            # Convert alpha to 0-255 range if it's a float
            a = int(float(a) * 255) if "." in a else int(a)
            color = QColor()
            color.setRgb(r, g, b, a)
            return color
    # Default to direct QColor creation for hex format
    return QColor(rgba_str)


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
        return parse_rgba(color_str)

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
