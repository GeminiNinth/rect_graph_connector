"""
Border renderer for drawing the canvas border.
"""

from PyQt5.QtGui import QPainter, QColor, QPen

from .base_renderer import BaseRenderer
from ...config import config


class BorderRenderer(BaseRenderer):
    """
    Renderer for drawing the canvas border.
    The border style changes based on the current mode.
    """

    def draw(self, painter: QPainter, mode: str = "normal", **kwargs):
        """
        Draw the canvas border with mode-specific color.

        Args:
            painter (QPainter): The painter to use for drawing
            mode (str): The current mode ("normal" or "edit")
            **kwargs: Additional drawing parameters
        """
        # Set border color according to the mode from config
        if mode == "edit":
            border_color = config.get_color(
                "canvas.border.edit", "#FF6464"
            )  # Edit mode border
        else:
            border_color = config.get_color(
                "canvas.border.normal", "#000000"
            )  # Normal mode border

        pen = QPen(QColor(border_color))
        pen.setWidth(config.get_dimension("canvas.border_width", 2))
        painter.setPen(pen)

        # Draw border rectangle without scaling
        painter.drawRect(0, 0, self.canvas.width() - 1, self.canvas.height() - 1)
