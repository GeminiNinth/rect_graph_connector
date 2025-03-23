"""
Color style configuration for nodes.
"""

from PyQt5.QtGui import QColor
from .base_style import BaseStyle


class NodeColorStyle(BaseStyle):
    """
    Color style configuration for nodes.

    This class manages fill and border colors for different node states.
    """

    def __init__(self):
        """Initialize node color style with values from config."""
        super().__init__()

        # Fill colors
        self.fill_normal = self.get_color("node.fill.normal", "skyblue")
        self.fill_selected = self.get_color("node.fill.selected", "#ADD8E6")
        self.fill_all_for_one = self.get_color(
            "node.fill.all_for_one_selected", "#FFA07A"
        )
        self.fill_parallel = self.get_color("node.fill.parallel_selected", "#90EE90")
        self.fill_bridge_target = self.get_color(
            "node.fill.bridge_target_highlighted", "#50FCC0"
        )
        self.fill_bridge_source = self.get_color(
            "node.fill.bridge_source_highlighted", "#FFD0E0"
        )

        # Border colors
        self.border_normal = self.get_color("node.border.normal", "gray")
        self.border_selected = self.get_color("node.border.selected", "blue")
        self.border_all_for_one = self.get_color(
            "node.border.all_for_one_selected", "#FF4500"
        )
        self.border_parallel = self.get_color(
            "node.border.parallel_selected", "#006400"
        )
        self.border_bridge_target = self.get_color(
            "node.border.bridge_target_highlighted", "#10DDFF"
        )
        self.border_bridge_source = self.get_color(
            "node.border.bridge_source_highlighted", "#FF80A0"
        )

        # Text color
        self.text_color = self.get_color("node.text", "#000000")

    def get_fill_color(
        self,
        is_selected: bool = False,
        is_all_for_one_selected: bool = False,
        is_parallel_selected: bool = False,
        is_bridge_source: bool = False,
        is_bridge_target: bool = False,
        is_hovered: bool = False,
    ) -> QColor:
        """
        Get the appropriate fill color based on node state.

        Args:
            is_selected (bool): Whether the node is selected
            is_all_for_one_selected (bool): Whether the node is selected in All-For-One mode
            is_parallel_selected (bool): Whether the node is selected in Parallel mode
            is_bridge_source (bool): Whether the node is a bridge source
            is_bridge_target (bool): Whether the node is a bridge target
            is_hovered (bool): Whether the node is being hovered over

        Returns:
            QColor: The appropriate fill color
        """
        if is_bridge_source:
            return self.fill_bridge_source
        if is_bridge_target:
            return self.fill_bridge_target
        if is_all_for_one_selected:
            return self.fill_all_for_one
        if is_parallel_selected:
            return self.fill_parallel
        if is_selected:
            return self.fill_selected
        return self.fill_normal

    def get_border_color(
        self,
        is_selected: bool = False,
        is_all_for_one_selected: bool = False,
        is_parallel_selected: bool = False,
        is_bridge_source: bool = False,
        is_bridge_target: bool = False,
        is_hovered: bool = False,
    ) -> QColor:
        """
        Get the appropriate border color based on node state.

        Args:
            is_selected (bool): Whether the node is selected
            is_all_for_one_selected (bool): Whether the node is selected in All-For-One mode
            is_parallel_selected (bool): Whether the node is selected in Parallel mode
            is_bridge_source (bool): Whether the node is a bridge source
            is_bridge_target (bool): Whether the node is a bridge target
            is_hovered (bool): Whether the node is being hovered over

        Returns:
            QColor: The appropriate border color
        """
        if is_bridge_source:
            return self.border_bridge_source
        if is_bridge_target:
            return self.border_bridge_target
        if is_all_for_one_selected:
            return self.border_all_for_one
        if is_parallel_selected:
            return self.border_parallel
        if is_selected:
            return self.border_selected
        return self.border_normal
