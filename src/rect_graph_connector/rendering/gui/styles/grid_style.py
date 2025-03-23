"""
Style configuration for grid rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from .base_style import BaseStyle


class GridStyle(BaseStyle):
    """
    Style configuration for grid.

    This class defines all visual properties for grid rendering,
    including colors, line styles, and spacing.
    """

    def __init__(self):
        """Initialize grid style with default values."""
        super().__init__()

        # Colors
        self.major_line_color = self.get_color(
            "grid.major_line", "rgba(200,200,200,128)"
        )
        self.minor_line_color = self.get_color(
            "grid.minor_line", "rgba(220,220,220,64)"
        )

        # Dimensions
        self.major_line_width = self.get_dimension("grid.major_line_width", 1.0)
        self.minor_line_width = self.get_dimension("grid.minor_line_width", 0.5)
        self.major_spacing = self.get_dimension("grid.major_spacing", 100.0)
        self.minor_spacing = self.get_dimension("grid.minor_spacing", 20.0)

        # Zoom thresholds
        self.min_zoom_visible = self.get_constant("grid.min_zoom_visible", 0.1)
        self.minor_line_zoom_threshold = self.get_constant(
            "grid.minor_line_zoom_threshold", 0.5
        )

    def get_major_pen(self):
        """
        Get the pen for drawing major grid lines.

        Returns:
            QPen: The configured pen for major grid lines
        """
        pen = QPen(self.major_line_color, self.major_line_width)
        pen.setStyle(Qt.SolidLine)
        return pen

    def get_minor_pen(self):
        """
        Get the pen for drawing minor grid lines.

        Returns:
            QPen: The configured pen for minor grid lines
        """
        pen = QPen(self.minor_line_color, self.minor_line_width)
        pen.setStyle(Qt.DotLine)
        return pen

    def should_show_minor_lines(self, zoom: float) -> bool:
        """
        Determine if minor grid lines should be shown at current zoom level.

        Args:
            zoom (float): Current zoom level

        Returns:
            bool: True if minor lines should be shown
        """
        return zoom >= self.minor_line_zoom_threshold

    def should_show_grid(self, zoom: float) -> bool:
        """
        Determine if grid should be shown at current zoom level.

        Args:
            zoom (float): Current zoom level

        Returns:
            bool: True if grid should be shown
        """
        return zoom >= self.min_zoom_visible
