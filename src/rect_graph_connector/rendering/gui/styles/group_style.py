"""
Style configuration for group rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPen
from .base_style import BaseStyle


class GroupStyle(BaseStyle):
    """
    Style configuration for groups.

    This class defines all visual properties for group rendering,
    including background, border, and title styling.
    """

    def __init__(self):
        """Initialize group style with default values."""
        super().__init__()

        # Colors
        self.background_color = self.get_color(
            "group.background", "rgba(240,240,240,128)"
        )
        self.border_color = self.get_color("group.border", "rgba(180,180,180,255)")
        self.title_color = self.get_color("group.title", "rgba(100,100,100,255)")
        self.selected_color = self.get_color("group.selected", "rgba(200,220,240,128)")
        self.hover_color = self.get_color("group.hover", "rgba(230,230,230,128)")

        # Dimensions
        self.border_width = self.get_dimension("group.border_width", 2.0)
        self.title_height = self.get_dimension("group.title_height", 30.0)
        self.padding = self.get_dimension("group.padding", 20.0)
        self.corner_radius = self.get_dimension("group.corner_radius", 10.0)

        # Font configuration
        self.title_font = QFont()
        self.title_font.setFamily(self.get_constant("group.font_family", "Arial"))
        self.title_font.setPointSize(self.get_constant("group.font_size", 12))
        self.title_font.setBold(True)

        # Border style
        self.border_style = Qt.DashLine

    def get_background_color(self, is_selected: bool, is_hovered: bool):
        """
        Get the appropriate background color based on group state.

        Args:
            is_selected (bool): Whether the group is selected
            is_hovered (bool): Whether the group is being hovered over

        Returns:
            QColor: The appropriate background color
        """
        if is_selected:
            return self.selected_color
        if is_hovered:
            return self.hover_color
        return self.background_color

    def get_border_pen(self):
        """
        Get the pen for drawing group borders.

        Returns:
            QPen: Configured pen for group borders
        """
        pen = QPen(self.border_color, self.border_width)
        pen.setStyle(self.border_style)
        return pen
