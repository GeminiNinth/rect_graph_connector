"""
Edge style class for edge rendering.
"""

from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt

from .base_style import BaseStyle


class EdgeStyle(BaseStyle):
    """
    Style class for edge rendering.

    This class provides styling properties for edges, including colors and widths
    for different edge states (normal, selected, hovered, etc.).
    """

    def __init__(self):
        """Initialize the edge style."""
        super().__init__()

    def get_edge_pen(
        self,
        is_selected=False,
        is_highlighted=False,
        is_temporary=False,
        is_all_for_one=False,
        is_parallel=False,
        is_bridge=False,
    ):
        """
        Get the pen for an edge based on its state.

        Args:
            is_selected (bool): Whether the edge is selected
            is_highlighted (bool): Whether the edge is highlighted (e.g., by knife tool)
            is_temporary (bool): Whether the edge is a temporary preview
            is_all_for_one (bool): Whether the edge is part of All-For-One mode
            is_parallel (bool): Whether the edge is part of Parallel mode
            is_bridge (bool): Whether the edge is part of Bridge mode

        Returns:
            QPen: The edge pen
        """
        if is_bridge:
            color = self.get_color("edge.bridge", "#FF00FF")  # Magenta
            width = self.get_dimension("edge.width.bridge", 2)
            style = Qt.DashLine
        elif is_parallel:
            color = self.get_color("edge.parallel", "#008000")  # Green
            width = self.get_dimension("edge.width.parallel", 2)
            style = Qt.SolidLine
        elif is_all_for_one:
            color = self.get_color("edge.all_for_one", "#FFA500")  # Orange
            width = self.get_dimension("edge.width.all_for_one", 2)
            style = Qt.SolidLine
        elif is_temporary:
            color = self.get_color("edge.temporary", "#FF0000")  # Red
            width = self.get_dimension("edge.width.temporary", 2)
            style = Qt.DashLine
        elif is_highlighted:
            color = self.get_color("edge.highlighted", "#FF0000")  # Red
            width = self.get_dimension("edge.width.highlighted", 2)
            style = Qt.SolidLine
        elif is_selected:
            color = self.get_color("edge.selected", "#0000FF")  # Blue
            width = self.get_dimension("edge.width.selected", 2)
            style = Qt.SolidLine
        else:
            color = self.get_color("edge.normal", "#000000")  # Black
            width = self.get_dimension("edge.width.normal", 1)
            style = Qt.SolidLine

        pen = QPen(color)
        pen.setWidth(int(width))
        pen.setStyle(style)
        return pen

    def get_hover_edge_pen(self):
        """
        Get the pen for a hovered edge.

        Returns:
            QPen: The hover edge pen
        """
        color = self.get_color("edge.hover", "#FF6600")  # Orange
        width = self.get_dimension("edge.width.hover", 2)

        pen = QPen(color)
        pen.setWidth(int(width))
        return pen

    def get_arrow_size(self):
        """
        Get the size of edge arrows.

        Returns:
            float: The arrow size
        """
        return self.get_dimension("edge.arrow_size", 10)

    def get_edge_hit_tolerance(self):
        """
        Get the tolerance for edge hit detection.

        Returns:
            float: The edge hit tolerance
        """
        return self.get_dimension("edge.hit_tolerance", 5)

    def get_hover_opacity(self):
        """
        Get the opacity for non-highlighted edges when hovering.

        Returns:
            float: The opacity value (0.0-1.0)
        """
        return self.get_dimension("hover.opacity", 0.5)
