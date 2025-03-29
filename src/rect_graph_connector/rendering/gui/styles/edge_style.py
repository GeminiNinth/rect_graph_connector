"""
Style configuration for edge rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen

from .base_style import BaseStyle


class EdgeStyle(BaseStyle):
    """
    Style configuration for edges.

    This class defines all visual properties for edge rendering,
    including line styles, colors, and arrow configurations.
    """

    def __init__(self):
        """Initialize edge style with default values."""
        super().__init__()

        # Colors
        self.line_color = self.get_color("edge.line", "rgba(100,100,100,255)")
        self.selected_color = self.get_color("edge.selected", "rgba(0,120,215,255)")
        self.hover_color = self.get_color("edge.hover", "rgba(150,150,150,255)")
        self.arrow_color = self.get_color("edge.arrow", "rgba(100,100,100,255)")

        # Dimensions
        self.line_width = self.get_dimension("edge.line_width", 2.0)
        self.selected_width = self.get_dimension("edge.selected_width", 3.0)
        self.arrow_size = self.get_dimension("edge.arrow_size", 10.0)

        # Line style configuration
        self.line_style = Qt.SolidLine
        self.cap_style = Qt.RoundCap
        self.join_style = Qt.RoundJoin

        # Animation parameters
        self.animation_speed = self.get_constant("edge.animation_speed", 1.0)
        self.dash_pattern = self.get_constant("edge.dash_pattern", [5, 5])

        # Hover effect
        self.hover_opacity = self.get_dimension("hover.opacity", 0.3)

    def get_pen(self, is_selected: bool, is_hovered: bool):
        """
        Get the appropriate pen based on edge state.

        Args:
            is_selected (bool): Whether the edge is selected
            is_hovered (bool): Whether the edge is being hovered over

        Returns:
            QPen: The configured pen for edge drawing
        """
        if is_selected:
            pen = QPen(self.selected_color, self.selected_width)
        elif is_hovered:
            pen = QPen(self.hover_color, self.line_width)
        else:
            pen = QPen(self.line_color, self.line_width)

        pen.setStyle(self.line_style)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        return pen

    def get_temporary_edge_pen(self):
        """
        Get the pen for drawing the temporary edge during creation.

        Returns:
            QPen: The configured pen for temporary edge drawing
        """
        # Use a distinct style, e.g., dashed line
        pen = QPen(self.line_color, self.line_width)
        pen.setStyle(Qt.DashLine)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        return pen

    def get_arrow_pen(self):
        """
        Get the pen for drawing edge arrows.

        Returns:
            QPen: The configured pen for arrow drawing
        """
        pen = QPen(self.arrow_color, self.line_width)
        pen.setCapStyle(self.cap_style)
        pen.setJoinStyle(self.join_style)
        return pen
