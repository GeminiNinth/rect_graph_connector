"""
Grid renderer for drawing the background grid.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen

from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer


class GridRenderer(BaseRenderer):
    """
    Renderer for drawing the background grid.

    This class handles rendering of the grid lines based on the view state.

    Attributes:
        grid_size (float): The size of the grid cells
    """

    def __init__(self, view_state: ViewStateModel, style=None, grid_size=20):
        """
        Initialize the grid renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (BaseStyle, optional): The style object for this renderer
            grid_size (float): The size of the grid cells
        """
        super().__init__(view_state, style)
        self.grid_size = grid_size

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

        # Apply pan offset but not zoom (grid should scale with zoom)
        painter.translate(self.view_state.pan_offset)

        # Get canvas size
        canvas_width = painter.device().width()
        canvas_height = painter.device().height()

        # Calculate grid bounds in view coordinates
        left = -self.view_state.pan_offset.x() / self.view_state.zoom
        top = -self.view_state.pan_offset.y() / self.view_state.zoom
        right = (canvas_width - self.view_state.pan_offset.x()) / self.view_state.zoom
        bottom = (canvas_height - self.view_state.pan_offset.y()) / self.view_state.zoom

        # Calculate grid spacing in view coordinates
        grid_spacing = self.grid_size * self.view_state.zoom

        # Set up grid pen
        grid_pen = QPen(Qt.lightGray)
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)

        # Draw vertical grid lines
        x = left - (left % self.grid_size)
        while x < right:
            x_pos = x * self.view_state.zoom
            painter.drawLine(
                x_pos, top * self.view_state.zoom, x_pos, bottom * self.view_state.zoom
            )
            x += self.grid_size

        # Draw horizontal grid lines
        y = top - (top % self.grid_size)
        while y < bottom:
            y_pos = y * self.view_state.zoom
            painter.drawLine(
                left * self.view_state.zoom, y_pos, right * self.view_state.zoom, y_pos
            )
            y += self.grid_size

        # Restore painter state
        painter.restore()
