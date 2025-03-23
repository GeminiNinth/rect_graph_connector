"""
Style configuration for bridge connection rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from .base_style import BaseStyle


class BridgeStyle(BaseStyle):
    """
    Style configuration for bridge connections.

    This class defines all visual properties for bridge connection rendering,
    including preview lines, highlights, and indicators.
    """

    def __init__(self):
        """Initialize bridge style with default values."""
        super().__init__()

        # Colors
        self.preview_color = self.get_color(
            "bridge.preview", "rgba(0,191,255,180)"
        )  # Deep sky blue
        self.highlight_color = self.get_color(
            "bridge.highlight", "rgba(255,215,0,180)"
        )  # Golden
        self.indicator_color = self.get_color(
            "bridge.indicator", "rgba(50,205,50,255)"
        )  # Lime green

        # Dimensions
        self.preview_width = self.get_dimension("bridge.preview_width", 2.0)
        self.highlight_width = self.get_dimension("bridge.highlight_width", 3.0)
        self.indicator_size = self.get_dimension("bridge.indicator_size", 8.0)

        # Line style configuration
        self.preview_style = Qt.DashLine
        self.highlight_style = Qt.SolidLine
        self.cap_style = Qt.RoundCap
        self.join_style = Qt.RoundJoin

        # Animation
        self.dash_pattern = self.get_constant("bridge.dash_pattern", [5, 5])

    def get_preview_pen(self):
        """
        Get the pen for drawing bridge preview lines.

        Returns:
            QPen: The configured pen for preview lines
        """
        pen = QPen(self.preview_color, self.preview_width)
        pen.setStyle(self.preview_style)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        pen.setDashPattern(self.dash_pattern)
        return pen

    def get_highlight_pen(self):
        """
        Get the pen for drawing highlighted groups.

        Returns:
            QPen: The configured pen for group highlighting
        """
        pen = QPen(self.highlight_color, self.highlight_width)
        pen.setStyle(self.highlight_style)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        return pen

    def get_indicator_pen(self):
        """
        Get the pen for drawing connection indicators.

        Returns:
            QPen: The configured pen for indicators
        """
        pen = QPen(self.indicator_color, 1.0)
        pen.setStyle(Qt.SolidLine)
        return pen
