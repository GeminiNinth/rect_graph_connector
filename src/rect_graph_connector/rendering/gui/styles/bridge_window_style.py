"""
Bridge window style definitions.
"""

from typing import Dict, Any
from PyQt5.QtGui import QColor, QPen, QBrush
from PyQt5.QtCore import Qt

from .base_style import BaseStyle, STYLES


class BridgeWindowStyle(BaseStyle):
    """
    Style class for bridge window components.

    This class provides styling for the bridge connection window and its components,
    including node views, buttons, and other UI elements.
    """

    def __init__(self):
        """Initialize the bridge window style."""
        super().__init__()

        # Initialize style cache
        self._text_color = None
        self._node_fill_color = None
        self._node_border_color = None
        self._highlight_fill_color = None
        self._highlight_border_color = None
        self._connection_color = None
        self._background_color = None

    def get_text_color(self) -> QColor:
        """
        Get the text color based on the current theme.

        Returns:
            QColor: The text color
        """
        if self._text_color is None:
            self._text_color = self.get_style_color("bridge_window", "text_color")
        return self._text_color

    def get_text_pen(self, width: float = 1.0) -> QPen:
        """
        Get a pen for drawing text.

        Args:
            width: Line width for the pen

        Returns:
            QPen: The pen for drawing text
        """
        return QPen(self.get_text_color(), width)

    def get_node_fill_color(self, is_highlighted: bool = False) -> QColor:
        """
        Get the node fill color.

        Args:
            is_highlighted: Whether the node is highlighted

        Returns:
            QColor: The node fill color
        """
        if is_highlighted:
            if self._highlight_fill_color is None:
                self._highlight_fill_color = self.get_style_color(
                    "node", "fill_bridge_target_highlighted"
                )
            return self._highlight_fill_color
        else:
            if self._node_fill_color is None:
                self._node_fill_color = self.get_style_color("node", "fill_normal")
            return self._node_fill_color

    def get_node_border_color(self, is_highlighted: bool = False) -> QColor:
        """
        Get the node border color.

        Args:
            is_highlighted: Whether the node is highlighted

        Returns:
            QColor: The node border color
        """
        if is_highlighted:
            if self._highlight_border_color is None:
                self._highlight_border_color = self.get_style_color(
                    "node", "border_bridge_target_highlighted"
                )
            return self._highlight_border_color
        else:
            if self._node_border_color is None:
                self._node_border_color = self.get_style_color("node", "border_normal")
            return self._node_border_color

    def get_node_fill_brush(self, is_highlighted: bool = False) -> QBrush:
        """
        Get a brush for filling nodes.

        Args:
            is_highlighted: Whether the node is highlighted

        Returns:
            QBrush: The brush for filling nodes
        """
        return QBrush(self.get_node_fill_color(is_highlighted))

    def get_node_border_pen(
        self, is_highlighted: bool = False, width: float = 1.5
    ) -> QPen:
        """
        Get a pen for drawing node borders.

        Args:
            is_highlighted: Whether the node is highlighted
            width: Line width for the pen

        Returns:
            QPen: The pen for drawing node borders
        """
        return QPen(self.get_node_border_color(is_highlighted), width)

    def get_connection_color(self) -> QColor:
        """
        Get the connection line color.

        Returns:
            QColor: The connection line color
        """
        if self._connection_color is None:
            self._connection_color = self.get_style_color(
                "bridge_window", "node_area_connection_line"
            )
        return self._connection_color

    def get_connection_pen(self, width: float = 2.0) -> QPen:
        """
        Get a pen for drawing connection lines.

        Args:
            width: Line width for the pen

        Returns:
            QPen: The pen for drawing connection lines
        """
        return QPen(self.get_connection_color(), width, Qt.SolidLine)

    def get_background_color(self) -> QColor:
        """
        Get the background color.

        Returns:
            QColor: The background color
        """
        if self._background_color is None:
            self._background_color = self.get_style_color(
                "bridge_window", "node_area_background"
            )
        return self._background_color


# Update STYLES dictionary with bridge window specific styles
STYLES.update(
    {
        "bridge_window": {
            "text_color_light": "#000000",
            "text_color_dark": "#FFFFFF",
            "node_area_background": "#F5F5F5",
            "node_area_connection_line": "#6495ED",
            "background": "rgba(255, 255, 255, 240)",
            "border": "#A0A0A0",
            "title_bar": "#E6E6FA",
        }
    }
)
