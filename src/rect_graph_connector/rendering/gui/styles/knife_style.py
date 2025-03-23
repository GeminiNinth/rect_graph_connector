"""
Style configuration for knife tool rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from .base_style import BaseStyle


class KnifeStyle(BaseStyle):
    """
    Style configuration for knife tool.

    This class defines all visual properties for knife tool rendering,
    including path and highlight styles.
    """

    def __init__(self):
        """Initialize knife style with default values."""
        super().__init__()

        # Colors
        self.path_color = self.get_color(
            "knife.path", "rgba(255,0,0,200)"
        )  # Semi-transparent red
        self.highlight_color = self.get_color(
            "knife.highlight", "rgba(255,165,0,200)"
        )  # Semi-transparent orange

        # Dimensions
        self.path_width = self.get_dimension("knife.path_width", 2.0)
        self.highlight_width = self.get_dimension("knife.highlight_width", 3.0)

        # Path style configuration
        self.path_style = Qt.SolidLine
        self.cap_style = Qt.RoundCap
        self.join_style = Qt.RoundJoin

    def get_path_pen(self):
        """
        Get the pen for drawing the knife path.

        Returns:
            QPen: The configured pen for knife path
        """
        pen = QPen(self.path_color, self.path_width)
        pen.setStyle(self.path_style)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        return pen

    def get_highlight_pen(self):
        """
        Get the pen for drawing highlighted edges.

        Returns:
            QPen: The configured pen for edge highlighting
        """
        pen = QPen(self.highlight_color, self.highlight_width)
        pen.setStyle(self.path_style)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        return pen
