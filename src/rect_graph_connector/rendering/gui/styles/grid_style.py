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

        # Colors (Using keys from colors.yaml)
        self.major_line_color = self.get_color(
            "grid.major_line", "rgba(200,200,200,128)"
        )
        self.minor_line_color = self.get_color(
            "grid.minor_line", "rgba(220,220,220,64)"
        )
        self.axis_x_color = self.get_color("grid.axis_x", "rgba(255,0,0,128)")
        self.axis_y_color = self.get_color("grid.axis_y", "rgba(0,255,0,128)")

        # Dimensions
        node_to_node_distance = self.get_dimension(
            "node.node_to_node_distance", 50  # Use the new key
        )
        self.minor_spacing = (
            node_to_node_distance / 2.0
        )  # Grid lines are half the node distance
        self.major_spacing = self.minor_spacing * 5  # Major lines every 5 minor lines

        self.major_line_width = self.get_dimension("grid.major_line_width", 1.0)
        self.minor_line_width = self.get_dimension("grid.minor_line_width", 0.5)

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

    def get_axis_x_pen(self):
        """Get the pen for drawing the X=0 axis."""
        pen = QPen(self.axis_x_color, self.major_line_width)  # Use major width for axis
        pen.setStyle(Qt.SolidLine)
        return pen

    def get_axis_y_pen(self):
        """Get the pen for drawing the Y=0 axis."""
        pen = QPen(self.axis_y_color, self.major_line_width)  # Use major width for axis
        pen.setStyle(Qt.SolidLine)
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
