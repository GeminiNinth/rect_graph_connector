"""
Knife renderer for drawing knife tool path and highlights.
"""

from typing import List, Tuple
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QPainterPath

from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.knife_style import KnifeStyle


class KnifeRenderer(BaseRenderer):
    """
    Renderer for drawing the knife tool path and highlights.

    This class handles rendering of the knife tool's cutting path
    and highlighting of edges that will be cut.
    """

    def __init__(self, view_state: ViewStateModel, style: KnifeStyle = None):
        """
        Initialize the knife renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (KnifeStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or KnifeStyle())

    def draw(self, painter: QPainter, knife_data=None, **kwargs):
        """
        Draw the knife path and highlighted edges.

        Args:
            painter (QPainter): The painter to use for drawing
            knife_data (dict, optional): Knife tool data containing 'path' and
                                     'highlighted_edges'
            **kwargs: Additional drawing parameters
        """
        if not knife_data:
            return

        # Save painter state
        painter.save()

        # Apply view transformations
        self.apply_transform(painter)

        # Draw highlighted edges first
        self._draw_highlighted_edges(painter, knife_data.get("highlighted_edges", []))

        # Draw knife path
        self._draw_knife_path(painter, knife_data.get("path", []))

        # Restore painter state
        painter.restore()

    def _draw_knife_path(self, painter: QPainter, path_points: List[QPointF]):
        """
        Draw the knife tool's cutting path.

        Args:
            painter (QPainter): The painter to use for drawing
            path_points (List[QPointF]): List of points forming the path
        """
        if not path_points or len(path_points) < 2:
            return

        # Create path
        path = QPainterPath()
        path.moveTo(path_points[0])
        for point in path_points[1:]:
            path.lineTo(point)

        # Draw path
        painter.setPen(self.style.get_path_pen())
        painter.drawPath(path)

    def _draw_highlighted_edges(self, painter: QPainter, edges: List[Tuple]):
        """
        Draw highlighted edges that will be cut.

        Args:
            painter (QPainter): The painter to use for drawing
            edges (List[Tuple]): List of edges to highlight, each edge is a tuple
                              of (source_node, target_node)
        """
        if not edges:
            return

        # Set highlight pen
        painter.setPen(self.style.get_highlight_pen())

        # Draw each highlighted edge
        for edge in edges:
            source_node, target_node = edge
            # Calculate actual endpoints considering node sizes
            start_point, end_point = self.calculate_edge_endpoints(
                source_node, target_node
            )
            painter.drawLine(start_point, end_point)
