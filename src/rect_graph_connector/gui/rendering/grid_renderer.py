"""
Grid renderer for drawing the canvas grid.
"""

from PyQt5.QtGui import QPainter, QColor, QPen

from .base_renderer import BaseRenderer
from ...config import config


class GridRenderer(BaseRenderer):
    """
    Renderer for drawing grid lines across the canvas.
    Grid spacing is controlled by the grid.spacing configuration value.
    """

    def draw(self, painter: QPainter, **kwargs):
        """
        Draw grid lines across the canvas when grid visibility is enabled.
        Grid uses half the node spacing for a finer grid.

        Args:
            painter (QPainter): The painter to use for drawing
            **kwargs: Additional drawing parameters (not used)
        """
        if not hasattr(self.canvas, "grid_visible") or not self.canvas.grid_visible:
            return

        # Set grid line color and style
        grid_color = config.get_color("grid.line", "#DDDDDD")
        pen = QPen(QColor(grid_color))
        pen.setWidth(1)
        painter.setPen(pen)

        # Apply pan offset but not zoom for grid (grid should move with pan)
        painter.save()
        if hasattr(self.canvas, "pan_offset"):
            painter.translate(self.canvas.pan_offset)

        # Get grid spacing from config (using half the standard spacing as per requirements)
        standard_spacing = config.get_dimension("grid.spacing", 40.0)
        grid_spacing = standard_spacing / 2  # Half the node spacing for finer grid

        # Calculate visible area in graph coordinates
        visible_rect = self.canvas.rect()

        # Get the maximum canvas dimensions for determining grid coverage
        max_width = config.get_dimension("main_window.initial.width", 800)
        max_height = config.get_dimension("main_window.initial.height", 600)

        # Apply a safety margin to ensure grid covers viewport when panned or zoomed
        margin_factor = 10  # Increase this for larger grid coverage

        left = (
            -self.canvas.pan_offset.x() / self.canvas.zoom - max_width * margin_factor
        )
        top = (
            -self.canvas.pan_offset.y() / self.canvas.zoom - max_height * margin_factor
        )
        right = (
            visible_rect.width() - self.canvas.pan_offset.x()
        ) / self.canvas.zoom + max_width * margin_factor
        bottom = (
            visible_rect.height() - self.canvas.pan_offset.y()
        ) / self.canvas.zoom + max_height * margin_factor

        # Calculate grid line positions
        start_x = int(left / grid_spacing) * grid_spacing
        start_y = int(top / grid_spacing) * grid_spacing

        # Calculate grid coverage
        grid_width = int(
            visible_rect.width() + 2 * max_width * margin_factor * self.canvas.zoom
        )
        grid_height = int(
            visible_rect.height() + 2 * max_height * margin_factor * self.canvas.zoom
        )

        # Draw vertical grid lines
        x = start_x
        while x <= right:
            scaled_x = x * self.canvas.zoom
            painter.drawLine(
                int(scaled_x), -grid_height, int(scaled_x), grid_height * 2
            )
            x += grid_spacing

        # Draw horizontal grid lines
        y = start_y
        while y <= bottom:
            scaled_y = y * self.canvas.zoom
            painter.drawLine(-grid_width, int(scaled_y), grid_width * 2, int(scaled_y))
            y += grid_spacing

        painter.restore()
