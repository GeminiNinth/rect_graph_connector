"""
Border renderer for drawing the canvas border.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor

from ...models.view_state_model import ViewStateModel
from ...config import config
from .base_renderer import BaseRenderer


class BorderRenderer(BaseRenderer):
    """
    Renderer for drawing the canvas border.

    This class handles rendering of the canvas border based on the current mode.
    """

    def __init__(self, view_state: ViewStateModel, style=None):
        """
        Initialize the border renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (BaseStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style)

    def draw(self, painter: QPainter, mode="normal", **kwargs):
        """
        Draw the canvas border.

        Args:
            painter (QPainter): The painter to use for drawing
            mode (str): The current mode ("normal" or "edit")
            **kwargs: Additional drawing parameters
        """
        # Save painter state
        painter.save()

        # Get canvas size
        canvas_width = painter.device().width()
        canvas_height = painter.device().height()

        # Set up border pen based on mode
        if mode == "edit":
            border_color = config.get_color(
                "canvas.border.edit", "#FF0000"
            )  # Red for edit mode
        else:
            border_color = config.get_color(
                "canvas.border.normal", "#000000"
            )  # Black for normal mode

        border_width = config.get_dimension("canvas.border_width", 2)

        pen = QPen(QColor(border_color))
        pen.setWidth(border_width)
        painter.setPen(pen)

        # Draw border rectangle
        painter.drawRect(0, 0, canvas_width - 1, canvas_height - 1)

        # Restore painter state
        painter.restore()
