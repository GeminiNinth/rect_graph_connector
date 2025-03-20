"""
Selection renderer for drawing selection rectangles and other selection-related visuals.
"""

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen

from ...config import config
from .base_renderer import BaseRenderer, parse_rgba


class SelectionRenderer(BaseRenderer):
    """
    Renderer for drawing selection-related visuals.
    Handles selection rectangles with different styles based on selection direction.
    """

    def draw(self, painter: QPainter, selection_rect_data=None, **kwargs):
        """
        Draw selection-related visuals.

        Args:
            painter (QPainter): The painter to use for drawing
            selection_rect_data (dict, optional): Dictionary containing 'start' and 'end' points
            **kwargs: Additional drawing parameters
        """
        # Only draw the selection rectangle during drag selection
        # Node and group selection styling is handled by node_renderer.py
        if selection_rect_data:
            self._draw_selection_rectangle(painter, selection_rect_data)

    def _draw_selection_rectangle(self, painter: QPainter, selection_rect_data):
        """
        Draw the selection rectangle during rectangle selection.
        The style changes based on selection direction:
        - Left-to-right: Blue, solid line (strict containment)
        - Right-to-left: Green, dashed line (intersection)

        Args:
            painter (QPainter): The painter to use for drawing
            selection_rect_data (dict): Dictionary containing 'start' and 'end' points
        """
        if (
            not selection_rect_data
            or "start" not in selection_rect_data
            or "end" not in selection_rect_data
        ):
            return

        start = selection_rect_data["start"]
        end = selection_rect_data["end"]

        # Determine the selection direction
        left_to_right = start.x() < end.x()

        # Calculate rectangle bounds
        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()

        # Create normalized rectangle (min_x, min_y, width, height)
        min_x = min(x1, x2)
        min_y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        # Set fill color based on selection direction
        if left_to_right:
            # Left-to-right selection (strict containment) - blue
            fill_color = config.get_color(
                "selection.rect.fill.strict", "rgba(0, 0, 255, 40)"
            )
        else:
            # Right-to-left selection (intersection) - green
            fill_color = config.get_color(
                "selection.rect.fill.intersect", "rgba(0, 255, 0, 40)"
            )

        # Set border color and style
        border_color = config.get_color("selection.rect.border", "#000000")

        # Convert to integers for QPainter
        min_x_int = int(min_x)
        min_y_int = int(min_y)
        width_int = int(width)
        height_int = int(height)

        # Fill rectangle with semi-transparent color
        painter.fillRect(
            min_x_int, min_y_int, width_int, height_int, parse_rgba(fill_color)
        )

        # Draw border
        pen = QPen(QColor(border_color))
        pen.setWidth(config.get_dimension("selection.rect.border_width", 1))

        # Use dashed line for right-to-left (intersection) selection
        if not left_to_right:
            pen.setStyle(Qt.DashLine)

        painter.setPen(pen)
        painter.drawRect(min_x_int, min_y_int, width_int, height_int)
