"""
Style configuration for selection rectangle rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPen

from .base_style import BaseStyle


class SelectionStyle(BaseStyle):
    """
    Style configuration for selection rectangle.

    This class defines visual properties for selection rectangle rendering,
    including fill color, border style, and transparency, supporting
    different styles based on selection direction (rightward vs. leftward).
    """

    def __init__(self):
        """Initialize selection style with default values from config."""
        super().__init__()

        # Colors for rightward selection (Using keys from colors.yaml)
        self.rightward_fill_color = QColor(
            self.get_color("selection.rightward_fill", "rgba(135, 206, 235, 80)")
        )
        self.rightward_border_color = QColor(
            self.get_color("selection.rightward_border", "rgba(70, 130, 180, 255)")
        )

        # Colors for leftward selection (Using keys from colors.yaml)
        self.leftward_fill_color = QColor(
            self.get_color("selection.leftward_fill", "rgba(144, 238, 144, 80)")
        )
        self.leftward_border_color = QColor(
            self.get_color("selection.leftward_border", "rgba(60, 179, 113, 255)")
        )

        # Dimensions
        self.border_width = self.get_dimension("selection.border_width", 1.0)

        # Border style configuration
        self.line_style = Qt.SolidLine  # Changed from DashLine for clarity
        self.cap_style = Qt.RoundCap
        self.join_style = Qt.RoundJoin

        # Animation (Dash pattern might not be needed with solid line)
        # self.dash_pattern = self.get_constant("selection.dash_pattern", [5, 5])

    def get_border_pen(self, direction: str = "rightward") -> QPen:
        """
        Get the pen for drawing the selection rectangle border based on direction.

        Args:
            direction (str): The selection direction ('rightward' or 'leftward').
                             Defaults to 'rightward'.

        Returns:
            QPen: The configured pen for the selection border.
        """
        if direction == "leftward":
            border_color = self.leftward_border_color
        else:  # Default to rightward
            border_color = self.rightward_border_color

        pen = QPen(border_color, self.border_width)
        pen.setStyle(self.line_style)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        # if self.line_style == Qt.DashLine:
        #     pen.setDashPattern(self.dash_pattern)
        return pen

    def get_fill_brush(self, direction: str = "rightward") -> QBrush:
        """
        Get the brush for filling the selection rectangle based on direction.

        Args:
            direction (str): The selection direction ('rightward' or 'leftward').
                             Defaults to 'rightward'.

        Returns:
            QBrush: The configured brush for the selection fill.
        """
        if direction == "leftward":
            fill_color = self.leftward_fill_color
        else:  # Default to rightward
            fill_color = self.rightward_fill_color

        return QBrush(fill_color)
