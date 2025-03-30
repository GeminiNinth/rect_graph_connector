"""
Style configuration for canvas border rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen

from .base_style import BaseStyle


class BorderStyle(BaseStyle):
    """
    Style configuration for canvas border.

    This class defines all visual properties for border rendering,
    including color, width, and pattern.
    """

    def __init__(self):
        """Initialize border style with default values."""
        super().__init__()

        # Colors (Using new keys from colors.yaml)
        self.border_color = self.get_color(
            "canvas.border.default", "rgba(180,180,180,255)"
        )
        self.background_color = self.get_color(
            "canvas.background", "rgba(255,255,255,255)"
        )

        # Dimensions
        self.border_width = self.get_dimension(
            "canvas.border_width", 1.0
        )  # Use canvas.border_width
        # self.margin = self.get_dimension("border.margin", 10.0) # Margin no longer used for border rect

        # Border style configuration
        self.line_style = Qt.SolidLine
        self.cap_style = Qt.SquareCap
        self.join_style = Qt.MiterJoin

    def get_border_pen(self):
        """
        Get the pen for drawing the border.

        Returns:
            QPen: The configured pen for border drawing
        """
        pen = QPen(self.border_color, self.border_width)
        pen.setStyle(self.line_style)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        return pen
