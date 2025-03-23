"""
Selection renderer for drawing selection rectangles.
"""

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush

from ...models.view_state_model import ViewStateModel
from ...config import config
from .base_renderer import BaseRenderer


class SelectionRenderer(BaseRenderer):
    """
    Renderer for drawing selection rectangles.

    This class handles rendering of the selection rectangle during rectangle selection.
    """

    def __init__(self, view_state: ViewStateModel, style=None):
        """
        Initialize the selection renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (BaseStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style)

    def draw(self, painter: QPainter, selection_rect_data=None, **kwargs):
        """
        Draw the selection rectangle.

        Args:
            painter (QPainter): The painter to use for drawing
            selection_rect_data (dict, optional): Data for the selection rectangle
            **kwargs: Additional drawing parameters
        """
        if not selection_rect_data:
            return

        # Save painter state
        painter.save()

        # Get selection rectangle data
        start = selection_rect_data.get("start")
        end = selection_rect_data.get("end")

        if not start or not end:
            painter.restore()
            return

        # Calculate rectangle bounds
        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()

        # Create normalized rectangle
        rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

        # Set up selection rectangle appearance
        border_color = config.get_color("selection.border", "#0000FF")  # Blue
        fill_color = config.get_color(
            "selection.fill", "rgba(0, 0, 255, 30)"
        )  # Transparent blue

        # Draw selection rectangle
        painter.setPen(QPen(QColor(border_color), 1, Qt.DashLine))
        painter.setBrush(QBrush(QColor(fill_color)))
        painter.drawRect(rect)

        # Restore painter state
        painter.restore()
