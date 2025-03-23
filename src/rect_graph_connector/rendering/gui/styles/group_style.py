"""
Group style class for node group rendering.
"""

from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt

from .base_style import BaseStyle


class GroupStyle(BaseStyle):
    """
    Style class for node group rendering.

    This class provides styling properties for node groups, including background colors,
    border colors, and label styles for different group states (normal, selected, etc.).
    """

    def __init__(self):
        """Initialize the group style."""
        super().__init__()

    def get_background_color(self, is_selected=False):
        """
        Get the background color for a node group based on its state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QColor: The background color
        """
        if is_selected:
            return self.get_color(
                "group.background.selected", "rgba(230, 230, 255, 40)"
            )
        else:
            return self.get_color("group.background.normal", "rgba(245, 245, 245, 20)")

    def get_border_pen(self, is_selected=False):
        """
        Get the border pen for a node group based on its state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QPen: The border pen
        """
        if is_selected:
            color = self.get_color("group.border.selected", "#6464FF")
            width = self.get_dimension("group.border_width.selected", 2)
            style = Qt.SolidLine
        else:
            color = self.get_color("group.border.normal", "#C8C8C8")
            width = self.get_dimension("group.border_width.normal", 1)
            style = Qt.DashLine

        pen = QPen(color)
        pen.setWidth(int(width))
        pen.setStyle(style)
        return pen

    def get_label_background_color(self, is_selected=False):
        """
        Get the background color for a group label based on its state.

        Args:
            is_selected (bool): Whether the group is selected

        Returns:
            QColor: The label background color
        """
        if is_selected:
            return self.get_color(
                "group.label.background.selected", "rgba(240, 240, 255, 200)"
            )
        else:
            return self.get_color(
                "group.label.background.normal", "rgba(240, 240, 240, 180)"
            )

    def get_label_text_color(self):
        """
        Get the text color for group labels.

        Returns:
            QColor: The label text color
        """
        return self.get_color("group.label.text", "#000000")

    def get_label_text_pen(self):
        """
        Get the pen for group label text.

        Returns:
            QPen: The label text pen
        """
        return QPen(self.get_label_text_color(), 1)

    def get_border_margin(self):
        """
        Get the margin between the group border and its nodes.

        Returns:
            float: The border margin
        """
        return self.get_dimension("group.border_margin", 5)

    def get_label_dimensions(self):
        """
        Get the dimensions for group labels.

        Returns:
            tuple: (padding, height, max_width) for the label
        """
        padding = self.get_dimension("group.label_padding", 2)
        height = self.get_dimension("group.label_height", 20)
        max_width = self.get_dimension("group.label_max_width", 150)
        return padding, height, max_width
