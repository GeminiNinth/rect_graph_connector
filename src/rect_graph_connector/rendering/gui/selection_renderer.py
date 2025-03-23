"""
Selection renderer for drawing selection rectangle.
"""

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainter, QBrush

from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.selection_style import SelectionStyle


class SelectionRenderer(BaseRenderer):
    """
    Renderer for drawing the selection rectangle.

    This class handles rendering of the selection rectangle during
    drag selection operations, including fill and border styles.
    """

    def __init__(self, view_state: ViewStateModel, style: SelectionStyle = None):
        """
        Initialize the selection renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (SelectionStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or SelectionStyle())

    def draw(self, painter: QPainter, selection_rect_data=None, **kwargs):
        """
        Draw the selection rectangle if selection is active.

        Args:
            painter (QPainter): The painter to use for drawing
            selection_rect_data (dict, optional): Selection rectangle data containing
                                               'start' and 'end' points
            **kwargs: Additional drawing parameters
        """
        if not selection_rect_data:
            return

        # Save painter state
        painter.save()

        # Apply view transformations
        self.apply_transform(painter)

        # Get selection rectangle points
        start_point = selection_rect_data["start"]
        end_point = selection_rect_data["end"]

        # Calculate selection rectangle
        rect = self._calculate_selection_rect(start_point, end_point)

        # Draw selection rectangle
        self._draw_selection_rect(painter, rect)

        # Restore painter state
        painter.restore()

    def _calculate_selection_rect(
        self, start_point: QPointF, end_point: QPointF
    ) -> QRectF:
        """
        Calculate the selection rectangle from start and end points.

        Args:
            start_point (QPointF): Starting point of selection
            end_point (QPointF): Ending point of selection

        Returns:
            QRectF: The calculated selection rectangle
        """
        # Calculate top-left and bottom-right points
        x1, y1 = start_point.x(), start_point.y()
        x2, y2 = end_point.x(), end_point.y()

        # Ensure correct rectangle orientation regardless of drag direction
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        return QRectF(left, top, width, height)

    def _draw_selection_rect(self, painter: QPainter, rect: QRectF):
        """
        Draw the selection rectangle with fill and border.

        Args:
            painter (QPainter): The painter to use for drawing
            rect (QRectF): The rectangle to draw
        """
        # Draw fill
        painter.fillRect(rect, QBrush(self.style.fill_color))

        # Draw border
        painter.setPen(self.style.get_border_pen())
        painter.drawRect(rect)
