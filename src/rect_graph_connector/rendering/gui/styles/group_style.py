"""
Style configuration for group rendering.
"""

from PyQt5.QtGui import QFont
from .base_style import BaseStyle
from .group_color_style import GroupColorStyle
from .group_border_style import GroupBorderStyle


class GroupStyle(BaseStyle):
    """
    Style configuration for groups.

    This class defines all visual properties for group rendering,
    integrating color and border styles with size and text configurations.
    """

    def __init__(self):
        """Initialize group style with default values."""
        super().__init__()

        # Initialize sub-styles
        self.color_style = GroupColorStyle()
        self.border_style = GroupBorderStyle()

        # Dimensions
        self.title_height = self.get_dimension("group.title_height", 30.0)
        self.padding = self.get_dimension("group.padding", 20.0)
        self.corner_radius = self.get_dimension("group.corner_radius", 10.0)

        # Font configuration
        self.title_font = QFont()
        self.title_font.setFamily(self.get_constant("group.font_family", "Arial"))
        self.title_font.setPointSize(self.get_constant("group.font_size", 12))
        self.title_font.setBold(True)

    def get_background_color(self, is_selected: bool):
        """
        Get the appropriate background color based on group state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QColor: The appropriate background color
        """
        return self.color_style.get_background_color(is_selected)

    def get_border_pen(self, is_selected: bool):
        """
        Get the pen for drawing group borders.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QPen: Configured pen for group borders
        """
        return self.border_style.get_pen(is_selected)

    def get_label_colors(self, is_selected: bool):
        """
        Get the appropriate label colors based on group state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            tuple[QColor, QColor]: A tuple of (text_color, background_color)
        """
        return self.color_style.get_label_colors(is_selected)
