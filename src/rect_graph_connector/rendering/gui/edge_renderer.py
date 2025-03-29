"""
Edge renderer for drawing graph edges.
"""

from math import atan2, cos, pi, sin

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPainterPath

from ...config import config  # Import config
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
        temp_edge_data=None,  # Add temp_edge_data parameter
        **kwargs,
    ):
        """
        Draw all edges and the temporary edge (if creating one) on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_edges (list, optional): List of selected edges
            hover_edge (list, optional): Currently hovered edges
            **kwargs: Additional drawing parameters
        """
        selected_edges = selected_edges or []
        hover_node = kwargs.get("hover_node", None)
        hovered_edges = hover_edge or []

        # If we have a hover node but no hovered edges, we can get connected edges
        if hover_node and not hovered_edges:
            # This is a fallback if hover_edge is not provided
            # Note: get_connected_edges returns List[Tuple[BaseNode, BaseNode]]
            hovered_edges = self.graph.get_connected_edges(hover_node)

        # Create a node map for quick lookup
        node_map = {node.id: node for node in self.graph.nodes}

        # Draw all edges
        for src_id, tgt_id in self.graph.edges:  # Iterate through ID tuples
            source_node = node_map.get(src_id)
            target_node = node_map.get(tgt_id)

            if not source_node or not target_node:
                continue  # Skip if nodes not found

            # Check selection/hover status using node objects
            # Assuming selected_edges and hovered_edges contain tuples of NODE OBJECTS
            current_edge_tuple = (source_node, target_node)
            is_selected = (
                current_edge_tuple in selected_edges
                or (target_node, source_node) in selected_edges
            )
            is_hovered = (
                current_edge_tuple in hovered_edges
                or (target_node, source_node) in hovered_edges
            )

            # Apply opacity based on hover state
            opacity = 1.0
            if hover_node and not is_hovered:
                # Apply reduced opacity to non-highlighted edges when hovering
                opacity = self.style.hover_opacity

            # Pass node objects to _draw_edge
            self._draw_edge(
                painter, source_node, target_node, is_selected, is_hovered, opacity
            )

        # Temporary edge drawing is now handled by CompositeRenderer

    def _draw_edge(
        self,
        painter: QPainter,
        source_node,  # Changed: Accept source_node
        target_node,  # Changed: Accept target_node
        is_selected: bool,
        is_hovered: bool,
        opacity: float = 1.0,
    ):
        """
        Draw a single edge with its line and optional arrow.

        Args:
            painter (QPainter): The painter to use for drawing
            source_node: The source node object
            target_node: The target node object
            is_selected (bool): Whether the edge is selected
            is_hovered (bool): Whether the edge is being hovered over
            opacity (float): Opacity level for the edge (0.0-1.0)
        """
        # Calculate edge endpoints considering node sizes
        start_point, end_point = self.calculate_edge_endpoints(
            source_node, target_node
        )  # Use node objects

        # Save painter state
        painter.save()

        # Set edge pen based on state
        pen = self.style.get_pen(is_selected, is_hovered)

        # Apply opacity if needed
        if opacity < 1.0:
            pen_color = pen.color()
            pen_color.setAlphaF(pen_color.alphaF() * opacity)
            pen.setColor(pen_color)

        painter.setPen(pen)

        # Draw the edge line
        painter.drawLine(start_point, end_point)

        # Draw arrow if configured to do so
        if config.get_constant("edge.draw_arrow", False):
            # For arrow, we need to use a potentially modified pen
            arrow_pen = self.style.get_arrow_pen()
            if opacity < 1.0:
                arrow_color = arrow_pen.color()
                arrow_color.setAlphaF(arrow_color.alphaF() * opacity)
                arrow_pen.setColor(arrow_color)
            painter.setPen(arrow_pen)
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
