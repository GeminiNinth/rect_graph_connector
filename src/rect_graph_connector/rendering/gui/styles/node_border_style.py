"""
Border style configuration for nodes.
"""

from PyQt5.QtGui import QPen
from .base_style import BaseStyle
from .node_color_style import NodeColorStyle


class NodeBorderStyle(BaseStyle):
    """
    Border style configuration for nodes.

    This class manages border widths and pen styles for different node states.
    """

    def __init__(self, color_style: NodeColorStyle = None):
        """
        Initialize node border style with values from config.

        Args:
            color_style (NodeColorStyle, optional): Color style for borders
        """
        super().__init__()
        self.color_style = color_style or NodeColorStyle()

        # Border widths from dimensions config
        self.width_normal = self.get_dimension("node.border_width.normal", 1.0)
        self.width_selected = self.get_dimension("node.border_width.selected", 2.0)
        self.width_all_for_one = self.get_dimension(
            "node.border_width.all_for_one_selected", 3.0
        )
        self.width_parallel = self.get_dimension(
            "node.border_width.parallel_selected", 3.0
        )
        self.width_bridge = self.get_dimension(
            "node.border_width.bridge_highlighted", 2.0
        )

    def get_pen(
        self,
        is_selected: bool = False,
        is_all_for_one_selected: bool = False,
        is_parallel_selected: bool = False,
        is_bridge_source: bool = False,
        is_bridge_target: bool = False,
        is_hovered: bool = False,
    ) -> QPen:
        """
        Get the appropriate pen for node border based on state.

        Args:
            is_selected (bool): Whether the node is selected
            is_all_for_one_selected (bool): Whether the node is selected in All-For-One mode
            is_parallel_selected (bool): Whether the node is selected in Parallel mode
            is_bridge_source (bool): Whether the node is a bridge source
            is_bridge_target (bool): Whether the node is a bridge target
            is_hovered (bool): Whether the node is being hovered over

        Returns:
            QPen: The configured pen for node border
        """
        # Get appropriate border color
        color = self.color_style.get_border_color(
            is_selected,
            is_all_for_one_selected,
            is_parallel_selected,
            is_bridge_source,
            is_bridge_target,
            is_hovered,
        )

        # Get appropriate border width
        if is_bridge_source or is_bridge_target:
            width = self.width_bridge
        elif is_all_for_one_selected:
            width = self.width_all_for_one
        elif is_parallel_selected:
            width = self.width_parallel
        elif is_selected:
            width = self.width_selected
        else:
            width = self.width_normal

        # Create and return pen
        pen = QPen(color, width)
        return pen
