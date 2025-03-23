"""
Floating menu style definitions.
"""

from typing import Dict, Any
from PyQt5.QtGui import QColor, QPen, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QRectF

from .base_style import BaseStyle, STYLES, parse_color


class FloatingMenuStyle(BaseStyle):
    """
    Style class for floating menu components.

    This class provides styling for the floating menu used in bridge connection mode,
    including background, text, buttons, and borders.
    """

    def __init__(self, group_type: str = "source"):
        """
        Initialize the floating menu style.

        Args:
            group_type: The type of group ("source" or "target")
        """
        super().__init__()
        self.group_type = group_type

        # Initialize style cache
        self._background_color = None
        self._text_color = None
        self._button_bg_color = None
        self._button_hover_bg_color = None
        self._button_text_color = None
        self._border_color = None

    def get_background_color(self) -> QColor:
        """
        Get the background color.

        Returns:
            QColor: The background color
        """
        if self._background_color is None:
            bg_color_text = self.get_style("floating_menu", "background")
            self._background_color = parse_color(bg_color_text)
        return self._background_color

    def get_text_color(self) -> QColor:
        """
        Get the text color.

        Returns:
            QColor: The text color
        """
        if self._text_color is None:
            self._text_color = self.get_style_color("floating_menu", "text")
        return self._text_color

    def get_text_pen(self) -> QPen:
        """
        Get a pen for drawing text.

        Returns:
            QPen: The pen for drawing text
        """
        return QPen(self.get_text_color())

    def get_button_background_color(self, is_hover: bool = False) -> QColor:
        """
        Get the button background color.

        Args:
            is_hover: Whether the button is being hovered

        Returns:
            QColor: The button background color
        """
        if is_hover:
            if self._button_hover_bg_color is None:
                self._button_hover_bg_color = self.get_style_color(
                    "floating_menu", "button_hover"
                )
            return self._button_hover_bg_color
        else:
            if self._button_bg_color is None:
                self._button_bg_color = self.get_style_color(
                    "floating_menu", "button_background"
                )
            return self._button_bg_color

    def get_button_text_color(self) -> QColor:
        """
        Get the button text color.

        Returns:
            QColor: The button text color
        """
        if self._button_text_color is None:
            self._button_text_color = self.get_style_color(
                "floating_menu", "button_text"
            )
        return self._button_text_color

    def get_border_color(self) -> QColor:
        """
        Get the border color based on group type.

        Returns:
            QColor: The border color
        """
        if self._border_color is None:
            if self.group_type == "source":
                self._border_color = self.get_style_color(
                    "floating_menu", "source_border"
                )
            else:  # target or default
                self._border_color = self.get_style_color(
                    "floating_menu", "target_border"
                )
        return self._border_color

    def get_border_pen(self, width: float = 1.0) -> QPen:
        """
        Get a pen for drawing borders.

        Args:
            width: Line width for the pen

        Returns:
            QPen: The pen for drawing borders
        """
        return QPen(self.get_border_color(), width)

    def create_rounded_rect_path(self, rect: QRectF, radius: float) -> QPainterPath:
        """
        Create a path for a rounded rectangle.

        Args:
            rect: The rectangle
            radius: The corner radius

        Returns:
            QPainterPath: The path for the rounded rectangle
        """
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        return path


# Update STYLES dictionary with floating menu specific styles
STYLES.update(
    {
        "floating_menu": {
            "background": "rgba(60, 60, 60, 220)",
            "text": "#FFFFFF",
            "button_background": "#505050",
            "button_hover": "#606060",
            "button_text": "#FFFFFF",
            "source_border": "#FF5080",
            "target_border": "#FFA500",
        }
    }
)
