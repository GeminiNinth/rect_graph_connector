"""
Style configuration for group rendering.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPen, QColor
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

        # Colors - using specific state keys from config
        self.background_color = self.get_color(
            "group.background.normal", "rgba(245, 245, 245, 100)"
        )
        self.selected_background_color = self.get_color(
            "group.background.selected", "rgba(230, 230, 255, 120)"
        )
        self.border_color = self.get_color("group.border.normal", "#C8C8C8")
        self.selected_border_color = self.get_color("group.border.selected", "#6464FF")
        self.label_text_color = self.get_color("group.label.text", "#000000")
        self.label_background_color = self.get_color(
            "group.label.background.normal", "rgba(240, 240, 240, 180)"
        )
        self.label_background_selected_color = self.get_color(
            "group.label.background.selected", "rgba(240, 240, 255, 200)"
        )

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

    def get_background_color(self, is_selected: bool) -> QColor:
        """
        Get the appropriate background color based on group state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QColor: The appropriate background color
        """
        return self.selected_background_color if is_selected else self.background_color

    def get_border_pen(self, is_selected: bool) -> QPen:
        """
        Get the pen for drawing group borders.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QPen: Configured pen for group borders
        """
        color = self.selected_border_color if is_selected else self.border_color
        pen = QPen(color, self.border_width)
        pen.setStyle(self.border_style)
        return pen

    def get_label_colors(self, is_selected: bool) -> tuple[QColor, QColor]:
        """
        Get the appropriate label colors based on group state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            tuple[QColor, QColor]: A tuple of (text_color, background_color)
        """
        bg_color = (
            self.label_background_selected_color
            if is_selected
            else self.label_background_color
        )
        return self.label_text_color, bg_color
