"""
Edge renderer for drawing graph edges.
"""

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPainterPath
from math import atan2, cos, sin, pi

from ...models.graph import Graph
from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.edge_style import EdgeStyle


class EdgeRenderer(BaseRenderer):
    """
    Renderer for drawing edges between nodes.

    This class handles rendering of edges with different styles based on
    their states and configurations, including directional arrows.

    Attributes:
        graph (Graph): The graph model containing edges to render
    """

    def __init__(
        self, view_state: ViewStateModel, graph: Graph, style: EdgeStyle = None
    ):
        """
        Initialize the edge renderer.

        Args:
            view_state (ViewStateModel): The view state model
            graph (Graph): The graph model containing edges
            style (EdgeStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or EdgeStyle())
        self.graph = graph

    def draw(
        self,
        painter: QPainter,
        selected_edges=None,
        hover_edge=None,
        **kwargs,
    ):
        """
        Draw all edges on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_edges (list, optional): List of selected edges
            hover_edge (tuple, optional): Currently hovered edge as (source, target)
            **kwargs: Additional drawing parameters
        """
        selected_edges = selected_edges or []

        # Draw all edges
        for edge in self.graph.edges:
            is_selected = edge in selected_edges
            is_hovered = hover_edge and (
                (edge.source == hover_edge[0] and edge.target == hover_edge[1])
                or (edge.source == hover_edge[1] and edge.target == hover_edge[0])
            )
            self._draw_edge(painter, edge, is_selected, is_hovered)

    def _draw_edge(
        self,
        painter: QPainter,
        edge,
        is_selected: bool,
        is_hovered: bool,
    ):
        """
        Draw a single edge with its line and optional arrow.

        Args:
            painter (QPainter): The painter to use for drawing
            edge: The edge to draw
            is_selected (bool): Whether the edge is selected
            is_hovered (bool): Whether the edge is being hovered over
        """
        # Calculate edge endpoints considering node sizes
        start_point, end_point = self.calculate_edge_endpoints(edge.source, edge.target)

        # Save painter state
        painter.save()

        # Set edge pen based on state
        painter.setPen(self.style.get_pen(is_selected, is_hovered))

        # Draw the edge line
        painter.drawLine(start_point, end_point)

        # Draw arrow if edge is directed
        if getattr(edge, "directed", True):
            self._draw_arrow(painter, start_point, end_point)

        # Restore painter state
        painter.restore()

    def _draw_arrow(self, painter: QPainter, start_point: QPointF, end_point: QPointF):
        """
        Draw an arrow head at the end of the edge.

        Args:
            painter (QPainter): The painter to use for drawing
            start_point (QPointF): Start point of the edge
            end_point (QPointF): End point of the edge
        """
        # Calculate arrow direction
        dx = end_point.x() - start_point.x()
        dy = end_point.y() - start_point.y()
        angle = atan2(dy, dx)

        # Arrow head points
        arrow_size = self.style.arrow_size
        arrow_angle = pi / 6  # 30 degrees

        # Calculate arrow head points
        p1 = QPointF(
            end_point.x() - arrow_size * cos(angle - arrow_angle),
            end_point.y() - arrow_size * sin(angle - arrow_angle),
        )
        p2 = QPointF(
            end_point.x() - arrow_size * cos(angle + arrow_angle),
            end_point.y() - arrow_size * sin(angle + arrow_angle),
        )

        # Create arrow head path
        arrow_path = QPainterPath()
        arrow_path.moveTo(end_point)
        arrow_path.lineTo(p1)
        arrow_path.lineTo(p2)
        arrow_path.lineTo(end_point)

        # Draw arrow head
        painter.setPen(self.style.get_arrow_pen())
        painter.fillPath(arrow_path, self.style.arrow_color)
        painter.drawPath(arrow_path)
