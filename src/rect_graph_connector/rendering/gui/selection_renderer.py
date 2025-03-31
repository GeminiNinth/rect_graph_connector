"""
Selection renderer for drawing selection rectangle.
"""

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainter

from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.selection_style import SelectionStyle


class SelectionRenderer(BaseRenderer):
    """
    Renderer for drawing the selection rectangle.

    This class handles rendering of the selection rectangle during
    drag selection operations, including fill and border styles that
    change based on the selection direction (rightward vs. leftward).
    """

    def __init__(self, view_state: ViewStateModel, style: SelectionStyle = None):
        """
        Initialize the selection renderer.

        Args:
            view_state (ViewStateModel): The view state model.
            style (SelectionStyle, optional): The style object for this renderer.
                                              Defaults to SelectionStyle().
        """
        # Ensure style is an instance of SelectionStyle
        actual_style = style or SelectionStyle()
        if not isinstance(actual_style, SelectionStyle):
            raise TypeError("Style must be an instance of SelectionStyle")
        super().__init__(view_state, actual_style)
        # Explicitly type hint self.style for clarity
        self.style: SelectionStyle = actual_style

    def draw(self, painter: QPainter, selection_rect_data=None, **kwargs):
        """
        Draw the selection rectangle if selection is active.

        Args:
            painter (QPainter): The painter to use for drawing.
            selection_rect_data (dict, optional): Selection rectangle data containing
                                               'start' and 'end' QPointF points.
            **kwargs: Additional drawing parameters (unused).
        """
        if (
            not selection_rect_data
            or "start" not in selection_rect_data
            or "end" not in selection_rect_data
        ):
            return

        # Save painter state
        painter.save()

        # Transformation is already applied by the painter passed from CanvasView
        # self.apply_transform(painter) # DO NOT apply transform again here

        # Get selection rectangle points
        start_point: QPointF = selection_rect_data["start"]
        end_point: QPointF = selection_rect_data["end"]

        # Determine selection direction
        direction = "leftward" if end_point.x() < start_point.x() else "rightward"

        # Calculate selection rectangle
        rect = self._calculate_selection_rect(start_point, end_point)

        # Draw selection rectangle using direction-specific style
        self._draw_selection_rect(painter, rect, direction)

        # Restore painter state
        painter.restore()

    def _calculate_selection_rect(
        self, start_point: QPointF, end_point: QPointF
    ) -> QRectF:
        """
        Calculate the selection rectangle from start and end points.

        Args:
            start_point (QPointF): Starting point of selection in view coordinates.
            end_point (QPointF): Ending point of selection in view coordinates.

        Returns:
            QRectF: The calculated selection rectangle in view coordinates.
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

    def _draw_selection_rect(self, painter: QPainter, rect: QRectF, direction: str):
        """
        Draw the selection rectangle with fill and border based on direction.

        Args:
            painter (QPainter): The painter to use for drawing.
            rect (QRectF): The rectangle to draw in view coordinates.
            direction (str): The selection direction ('rightward' or 'leftward').
        """
        # Get direction-specific brush and pen from the style object
        fill_brush = self.style.get_fill_brush(direction)
        border_pen = self.style.get_border_pen(direction)

        # Draw fill
        painter.fillRect(rect, fill_brush)

        # Draw border
        painter.setPen(border_pen)
        painter.drawRect(rect)
