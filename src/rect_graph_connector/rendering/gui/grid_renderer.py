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

        # Apply view transformations
        self.apply_transform(painter)

        # Get visible area in scene coordinates
        visible_rect = self._calculate_visible_rect(painter)

        # Check if grid should be shown at current zoom level
        if self.style.should_show_grid(self.view_state.zoom):
            # Draw minor grid lines if zoom level is sufficient
            if self.style.should_show_minor_lines(self.view_state.zoom):
                self._draw_grid_lines(
                    painter,
                    visible_rect,
                    self.style.minor_spacing,
                    self.style.get_minor_pen(),
                )

            # Draw major grid lines
            self._draw_grid_lines(
                painter,
                visible_rect,
                self.style.major_spacing,
                self.style.get_major_pen(),
            )

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
        self, painter: QPainter, visible_rect: QRectF, spacing: float, pen: QPen
    ):
        """
        Draw grid lines with specified spacing and style.

        Args:
            painter (QPainter): The painter to use for drawing
            visible_rect (QRectF): The visible rectangle in scene coordinates
            spacing (float): The spacing between grid lines
            pen (QPen): The pen to use for drawing the lines
        """
        # Set the pen for drawing
        painter.setPen(pen)

        # Calculate grid line positions
        left = int(visible_rect.left() / spacing) * spacing
        right = int(visible_rect.right() / spacing + 1) * spacing
        top = int(visible_rect.top() / spacing) * spacing
        bottom = int(visible_rect.bottom() / spacing + 1) * spacing

        # Draw vertical lines
        x = left
        while x <= right:
            painter.drawLine(
                QPointF(x, visible_rect.top()), QPointF(x, visible_rect.bottom())
            )
            x += spacing

        # Draw horizontal lines
        y = top
        while y <= bottom:
            painter.drawLine(
                QPointF(visible_rect.left(), y), QPointF(visible_rect.right(), y)
            )
            y += spacing
