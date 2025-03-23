"""
Style configuration for selection rectangle rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from .base_style import BaseStyle


class SelectionStyle(BaseStyle):
    """
    Style configuration for selection rectangle.

    This class defines all visual properties for selection rectangle rendering,
    including fill color, border style, and transparency.
    """

    def __init__(self):
        """Initialize selection style with default values."""
        super().__init__()

        # Colors
        self.fill_color = self.get_color(
            "selection.fill", "rgba(135,206,235,64)"
        )  # Light blue with transparency
        self.border_color = self.get_color(
            "selection.border", "rgba(70,130,180,255)"
        )  # Steel blue

        # Dimensions
        self.border_width = self.get_dimension("selection.border_width", 1.0)

        # Border style configuration
        self.line_style = Qt.DashLine
        self.cap_style = Qt.RoundCap
        self.join_style = Qt.RoundJoin

        # Animation
        self.dash_pattern = self.get_constant("selection.dash_pattern", [5, 5])

    def get_border_pen(self):
        """
        Get the pen for drawing the selection rectangle border.

        Returns:
            QPen: The configured pen for selection border
        """
        pen = QPen(self.border_color, self.border_width)
        pen.setStyle(self.line_style)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        pen.setDashPattern(self.dash_pattern)
        return pen
