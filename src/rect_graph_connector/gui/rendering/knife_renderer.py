"""
Knife tool renderer for drawing the knife path and related visuals.
"""

from PyQt5.QtGui import QPainter, QColor, QPen

from .base_renderer import BaseRenderer
from ...config import config


class KnifeRenderer(BaseRenderer):
    """
    Renderer for drawing knife tool related visuals.
    Handles the knife path and any associated visual elements.
    """

    def draw(self, painter: QPainter, knife_data=None, **kwargs):
        """
        Draw knife tool related visuals.

        Args:
            painter (QPainter): The painter to use for drawing
            knife_data (dict, optional): Data for knife tool rendering
            **kwargs: Additional drawing parameters
        """
        if knife_data and knife_data.get("path"):
            self._draw_knife_path(painter, knife_data["path"])

    def _draw_knife_path(self, painter: QPainter, path_points):
        """
        Draw the knife tool path.
        The path is drawn as a series of connected lines in a distinct color.

        Args:
            painter (QPainter): The painter to use for drawing
            path_points (List[Tuple[float, float]]): List of points forming the path
        """
        if len(path_points) < 2:
            return

        # Set up the pen for the knife path
        knife_color = config.get_color("knife.path", "#C80000")
        pen = QPen(QColor(knife_color))
        pen.setWidth(config.get_dimension("knife.path_width", 2))
        painter.setPen(pen)

        # Draw lines connecting all points in the path
        for i in range(len(path_points) - 1):
            x1, y1 = path_points[i]
            x2, y2 = path_points[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
