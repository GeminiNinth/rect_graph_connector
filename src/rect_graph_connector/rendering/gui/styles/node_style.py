"""
Node style class for node rendering.
"""

from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt

from .base_style import BaseStyle


class NodeStyle(BaseStyle):
    """
    Style class for node rendering.

    This class provides styling properties for nodes, including fill colors,
    border colors, and border widths for different node states (normal, selected,
    hovered, etc.).
    """

    def __init__(self):
        """Initialize the node style."""
        super().__init__()

    def get_fill_color(
        self,
        is_selected=False,
        is_all_for_one_selected=False,
        is_parallel_selected=False,
        is_bridge_source=False,
        is_bridge_target=False,
    ):
        """
        Get the fill color for a node based on its state.

        Args:
            is_selected (bool): Whether the node is selected
            is_all_for_one_selected (bool): Whether the node is selected in All-For-One mode
            is_parallel_selected (bool): Whether the node is selected in Parallel mode
            is_bridge_source (bool): Whether the node is a source node in Bridge mode
            is_bridge_target (bool): Whether the node is a target node in Bridge mode

        Returns:
            QColor: The fill color
        """
        if is_bridge_source:
            return self.get_color("node.fill.bridge_source_highlighted", "#FFD0E0")
        elif is_bridge_target:
            return self.get_color("node.fill.bridge_target_highlighted", "#50FCC0")
        elif is_parallel_selected:
            return self.get_color("node.fill.parallel_selected", "#90EE90")
        elif is_all_for_one_selected:
            return self.get_color("node.fill.all_for_one_selected", "#FFA500")
        elif is_selected:
            return self.get_color("node.fill.selected", "#ADD8E6")
        else:
            return self.get_color("node.fill.normal", "skyblue")

    def get_border_pen(
        self,
        is_selected=False,
        is_all_for_one_selected=False,
        is_parallel_selected=False,
        is_bridge_source=False,
        is_bridge_target=False,
    ):
        """
        Get the border pen for a node based on its state.

        Args:
            is_selected (bool): Whether the node is selected
            is_all_for_one_selected (bool): Whether the node is selected in All-For-One mode
            is_parallel_selected (bool): Whether the node is selected in Parallel mode
            is_bridge_source (bool): Whether the node is a source node in Bridge mode
            is_bridge_target (bool): Whether the node is a target node in Bridge mode

        Returns:
            QPen: The border pen
        """
        if is_bridge_source:
            color = self.get_color("node.border.bridge_source_highlighted", "#FF80A0")
            width = self.get_dimension("node.border_width.bridge_highlighted", 2)
        elif is_bridge_target:
            color = self.get_color("node.border.bridge_target_highlighted", "#10DDFF")
            width = self.get_dimension("node.border_width.bridge_highlighted", 2)
        elif is_parallel_selected:
            color = self.get_color("node.border.parallel_selected", "#006400")
            width = self.get_dimension("node.border_width.parallel_selected", 3)
        elif is_all_for_one_selected:
            color = self.get_color("node.border.all_for_one_selected", "#FF6600")
            width = self.get_dimension("node.border_width.all_for_one_selected", 3)
        elif is_selected:
            color = self.get_color("node.border.selected", "blue")
            width = self.get_dimension("node.border_width.selected", 2)
        else:
            color = self.get_color("node.border.normal", "gray")
            width = self.get_dimension("node.border_width.normal", 1)

        pen = QPen(color)
        pen.setWidth(int(width))
        return pen

    def get_text_color(self):
        """
        Get the text color for node labels.

        Returns:
            QColor: The text color
        """
        return self.get_color("node.text", "#000000")

    def get_text_pen(self):
        """
        Get the pen for node label text.

        Returns:
            QPen: The text pen
        """
        return QPen(self.get_text_color(), 1)

    def get_hover_opacity(self):
        """
        Get the opacity for non-highlighted nodes when hovering.

        Returns:
            float: The opacity value (0.0-1.0)
        """
        return self.get_dimension("hover.opacity", 0.5)
