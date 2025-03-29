"""
Style configuration for node rendering.
"""

from PyQt5.QtGui import QFont

from .base_style import BaseStyle
from .node_border_style import NodeBorderStyle
from .node_color_style import NodeColorStyle


class NodeStyle(BaseStyle):
    """
    Style configuration for nodes.

    This class defines all visual properties for node rendering,
    integrating color and border styles with size and text configurations.
    """

    def __init__(self):
        """Initialize node style with default values."""
        super().__init__()

        # Initialize sub-styles
        self.color_style = NodeColorStyle()
        self.border_style = NodeBorderStyle(self.color_style)

        # Node dimensions
        self.default_size = self.get_dimension("node.default_size", 30.0)
        self.padding = self.get_dimension("node.padding", 5)
        self.corner_radius = self.get_dimension("node.corner_radius", 3)

        # Font configuration
        self.font = QFont()
        self.font.setFamily(self.get_constant("font.family", "Arial"))
        self.font.setPointSize(self.get_constant("font.size", 10))

        # Hover effect
        self.hover_opacity = self.get_dimension("hover.opacity", 0.3)

    def get_background_color(
        self,
        is_selected: bool = False,
        is_all_for_one_selected: bool = False,
        is_parallel_selected: bool = False,
        is_bridge_source: bool = False,
        is_bridge_target: bool = False,
        is_hovered: bool = False,
        is_edit_target: bool = False,  # Add is_edit_target
    ):
        """
        Get the appropriate background color based on node state.

        Args:
            is_selected (bool): Whether the node is selected
            is_all_for_one_selected (bool): Whether the node is selected in All-For-One mode
            is_parallel_selected (bool): Whether the node is selected in Parallel mode
            is_bridge_source (bool): Whether the node is a bridge source
            is_bridge_target (bool): Whether the node is a bridge target
            is_hovered (bool): Whether the node is being hovered over

        Returns:
            QColor: The appropriate background color
        """
        color = self.color_style.get_fill_color(
            is_selected,
            is_all_for_one_selected,
            is_parallel_selected,
            is_bridge_source,
            is_bridge_target,
            is_hovered,
            is_edit_target,  # Pass is_edit_target
        )

        # No opacity adjustment needed for hovered nodes
        return color

    def get_border_pen(
        self,
        is_selected: bool = False,
        is_all_for_one_selected: bool = False,
        is_parallel_selected: bool = False,
        is_bridge_source: bool = False,
        is_bridge_target: bool = False,
        is_hovered: bool = False,
        is_edit_target: bool = False,  # Add is_edit_target
    ):
        """
        Get the appropriate border pen based on node state.

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
        return self.border_style.get_pen(
            is_selected,
            is_all_for_one_selected,
            is_parallel_selected,
            is_bridge_source,
            is_bridge_target,
            is_edit_target,  # Pass is_edit_target
        )

    def get_text_color(self):
        """
        Get the color for node text.

        Returns:
            QColor: The text color
        """
        return self.color_style.text_color

    def get_hover_opacity(self):
        """
        Get the opacity value for hover effect.

        Returns:
            float: The opacity value
        """
        return self.hover_opacity
