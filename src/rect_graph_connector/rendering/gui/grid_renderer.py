"""
Grid renderer for drawing background grid.
"""

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen

from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.grid_style import GridStyle


class GridRenderer(BaseRenderer):
    """
    Renderer for drawing the background grid.

    This class handles rendering of the grid with major and minor lines,
    adjusting the display based on zoom level and view state.
    """

    def __init__(self, view_state: ViewStateModel, style: GridStyle = None):
        """
        Initialize the grid renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (GridStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or GridStyle())

    def draw(self, painter: QPainter, **kwargs):
        """
        Draw the grid on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            **kwargs: Additional drawing parameters
        """
        if not self.view_state.grid_visible:
            return

        # Save painter state
        painter.save()

        # Transformations are handled by CanvasView

        # Get visible area in scene coordinates
        visible_rect = self._calculate_visible_rect(painter)

        # Check if grid should be shown at current zoom level
        if self.style.should_show_grid(self.view_state.zoom):
            # Draw minor grid lines (these are now the base lines)
            self._draw_grid_lines(
                painter,
                visible_rect,
                self.style.minor_spacing,
                self.style.get_minor_pen(),
                self.style.get_major_pen(),
                5,  # Major lines every 5 minor lines
            )

            # Draw X=0 and Y=0 axes
            self._draw_axes(painter, visible_rect)

        # Restore painter state
        painter.restore()

    def _calculate_visible_rect(self, painter: QPainter) -> QRectF:
        """
        Calculate the visible rectangle in scene coordinates.

        Args:
            painter (QPainter): The current painter

        Returns:
            QRectF: The visible rectangle in scene coordinates
        """
        # Get widget size
        widget_rect = painter.viewport()

        # Convert to scene coordinates
        top_left = (
            painter.transform()
            .inverted()[0]
            .map(QPointF(widget_rect.left(), widget_rect.top()))
        )
        bottom_right = (
            painter.transform()
            .inverted()[0]
            .map(QPointF(widget_rect.right(), widget_rect.bottom()))
        )

        return QRectF(top_left, bottom_right)

    def _draw_grid_lines(
        self,
        painter: QPainter,
        visible_rect: QRectF,
        spacing: float,  # This is now minor spacing
        minor_pen: QPen,
        major_pen: QPen,
        major_multiple: int,
    ):
        """
            Draw grid lines, using major pen for lines at multiples of major_multiple.
        Args:
            painter (QPainter): The painter to use for drawing
            visible_rect (QRectF): The visible rectangle in scene coordinates
            spacing (float): The spacing between minor grid lines
            minor_pen (QPen): The pen for minor lines
            major_pen (QPen): The pen for major lines
            major_multiple (int): Interval for major lines (e.g., 5)
        """

        # Pen will be set inside the loop

        # Calculate grid line positions based on minor spacing
        left = int(visible_rect.left() / spacing) * spacing
        right = int(visible_rect.right() / spacing + 1) * spacing
        top = int(visible_rect.top() / spacing) * spacing
        bottom = int(visible_rect.bottom() / spacing + 1) * spacing

        # Draw vertical lines
        line_index = 0
        x = left
        while x <= right:
            # Determine if it's a major line (multiple of major_multiple, approximately)
            # Use a small tolerance for floating point comparisons
            is_major = (
                abs(
                    round(x / (spacing * major_multiple)) * (spacing * major_multiple)
                    - x
                )
                < spacing * 0.1
            )
            current_pen = major_pen if is_major else minor_pen
            # Skip drawing the Y-axis line here, it will be drawn separately
            if abs(x) > spacing * 0.1:  # Avoid drawing over Y-axis
                painter.setPen(current_pen)
                painter.drawLine(
                    QPointF(x, visible_rect.top()), QPointF(x, visible_rect.bottom())
                )
            x += spacing
            line_index += 1

        # Draw horizontal lines
        line_index = 0
        y = top
        while y <= bottom:
            # Determine if it's a major line
            is_major = (
                abs(
                    round(y / (spacing * major_multiple)) * (spacing * major_multiple)
                    - y
                )
                < spacing * 0.1
            )
            current_pen = major_pen if is_major else minor_pen
            # Skip drawing the X-axis line here
            if abs(y) > spacing * 0.1:  # Avoid drawing over X-axis
                painter.setPen(current_pen)
                painter.drawLine(
                    QPointF(visible_rect.left(), y), QPointF(visible_rect.right(), y)
                )
            y += spacing
            line_index += 1

    def _draw_axes(self, painter: QPainter, visible_rect: QRectF):
        """Draw the X=0 and Y=0 axes."""
        # Draw Y-axis (x=0)
        if visible_rect.left() <= 0 <= visible_rect.right():
            painter.setPen(self.style.get_axis_y_pen())
            painter.drawLine(
                QPointF(0, visible_rect.top()), QPointF(0, visible_rect.bottom())
            )

        # Draw X-axis (y=0)
        if visible_rect.top() <= 0 <= visible_rect.bottom():
            painter.setPen(self.style.get_axis_x_pen())
            painter.drawLine(
                QPointF(visible_rect.left(), 0), QPointF(visible_rect.right(), 0)
            )
