"""
Border style configuration for groups.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen
from .base_style import BaseStyle


class GroupBorderStyle(BaseStyle):
    """
    Border style configuration for groups.

    This class manages border widths and pen styles for different group states.
    """

    def __init__(self):
        """Initialize group border style with values from config."""
        super().__init__()

        # Border widths from dimensions config
        self.width_normal = self.get_dimension("group.border_width.normal", 1.0)
        self.width_selected = self.get_dimension("group.border_width.selected", 2.0)

        # Border colors
        self.color_normal = self.get_color("group.border.normal", "#C8C8C8")
        self.color_selected = self.get_color("group.border.selected", "#6464FF")

        # Border style
        self.style = Qt.DashLine

    def get_pen(self, is_selected: bool = False) -> QPen:
        """
        Get the appropriate pen for group border based on state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QPen: The configured pen for group border
        """
        # Get appropriate border color
        color = self.color_selected if is_selected else self.color_normal

        # Get appropriate border width
        width = self.width_selected if is_selected else self.width_normal

        # Create and return pen
        pen = QPen(color, width)
        pen.setStyle(self.style)
        return pen
