"""
Color style configuration for groups.
"""

from PyQt5.QtGui import QColor
from .base_style import BaseStyle


class GroupColorStyle(BaseStyle):
    """
    Color style configuration for groups.

    This class manages colors for different group states and elements.
    """

    def __init__(self):
        """Initialize group color style with values from config."""
        super().__init__()

        # Background colors
        self.background_normal = self.get_color(
            "group.background.normal", "rgba(245, 245, 245, 100)"
        )
        self.background_selected = self.get_color(
            "group.background.selected", "rgba(230, 230, 255, 120)"
        )

        # Label colors
        self.label_text = self.get_color("group.label.text", "#000000")
        self.label_background_normal = self.get_color(
            "group.label.background.normal", "rgba(240, 240, 240, 180)"
        )
        self.label_background_selected = self.get_color(
            "group.label.background.selected", "rgba(240, 240, 255, 200)"
        )

    def get_background_color(self, is_selected: bool) -> QColor:
        """
        Get the appropriate background color based on group state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QColor: The appropriate background color
        """
        return self.background_selected if is_selected else self.background_normal

    def get_label_colors(self, is_selected: bool) -> tuple[QColor, QColor]:
        """
        Get the appropriate label colors based on group state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            tuple[QColor, QColor]: A tuple of (text_color, background_color)
        """
        bg_color = (
            self.label_background_selected
            if is_selected
            else self.label_background_normal
        )
        return self.label_text, bg_color
