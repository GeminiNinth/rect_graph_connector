"""
Edge renderer for drawing edges between nodes.
"""

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QPainterPath

from ...models.graph import Graph
from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.edge_style import EdgeStyle


class EdgeRenderer(BaseRenderer):
    """
    Renderer for drawing edges between nodes.

    This class handles rendering of edges, including normal edges, temporary edges,
    and special edge types for different modes.

    Attributes:
        graph (Graph): The graph model to render
    """

    def __init__(
        self, view_state: ViewStateModel, graph: Graph, style: EdgeStyle = None
    ):
        """
        Initialize the edge renderer.

        Args:
            view_state (ViewStateModel): The view state model
            graph (Graph): The graph model to render
            style (EdgeStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or EdgeStyle())
        self.graph = graph

    def draw(
        self,
        painter: QPainter,
        selected_edges=None,
        temp_edge_data=None,
        all_for_one_data=None,
        parallel_data=None,
        hover_data=None,
        **kwargs,
    ):
        """
        Draw edges on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_edges (list, optional): List of selected edges
            temp_edge_data (tuple, optional): Temporary edge data (start_node, end_point)
            all_for_one_data (list, optional): List of nodes selected in All-For-One mode
            parallel_data (dict, optional): Data for parallel connection mode
            hover_data (dict, optional): Data about hover state
            **kwargs: Additional drawing parameters
        """
        # Default empty collections if not provided
        selected_edges = selected_edges or []

        # Save painter state
        painter.save()

        # Draw normal edges
        self._draw_normal_edges(painter, selected_edges, hover_data)

        # Draw temporary edge if creating one
        if temp_edge_data:
            self._draw_temp_edge(painter, temp_edge_data)

        # Draw All-For-One mode edges
        if all_for_one_data:
            self._draw_all_for_one_edges(painter, all_for_one_data, temp_edge_data)

        # Draw Parallel mode edges
        if parallel_data:
            self._draw_parallel_edges(painter, parallel_data)

        # Restore painter state
        painter.restore()

    def _draw_normal_edges(self, painter: QPainter, selected_edges, hover_data):
        """
        Draw normal edges between nodes.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_edges (list): List of selected edges
            hover_data (dict, optional): Data about hover state
        """
        # Apply transparency for non-highlighted edges when hovering
        if hover_data and hover_data.get("edges"):
            painter.setOpacity(self.style.get_hover_opacity())

        # Draw all edges
        for edge in self.graph.edges:
            try:
                # Get the actual node objects
                source_node = next(n for n in self.graph.nodes if n.id == edge[0])
                target_node = next(n for n in self.graph.nodes if n.id == edge[1])

                # Check if this edge is selected
                is_selected = (source_node, target_node) in selected_edges

                # Check if this edge is highlighted due to hover
                is_highlighted = False
                if hover_data and hover_data.get("edges"):
                    for hover_edge in hover_data["edges"]:
                        if (
                            hover_edge[0].id == source_node.id
                            and hover_edge[1].id == target_node.id
                        ) or (
                            hover_edge[1].id == source_node.id
                            and hover_edge[0].id == target_node.id
                        ):
                            is_highlighted = True
                            break

                # If edge is highlighted, restore full opacity
                if is_highlighted and hover_data:
                    # Save current opacity
                    current_opacity = painter.opacity()
                    # Set full opacity for highlighted edge
                    painter.setOpacity(1.0)
                    # Draw the edge
                    self._draw_edge(
                        painter, source_node, target_node, is_selected, is_highlighted
                    )
                    # Restore previous opacity
                    painter.setOpacity(current_opacity)
                else:
                    # Draw the edge with current opacity
                    self._draw_edge(
                        painter, source_node, target_node, is_selected, is_highlighted
                    )

            except StopIteration:
                continue

    def _draw_edge(
        self,
        painter: QPainter,
        source_node,
        target_node,
        is_selected=False,
        is_highlighted=False,
    ):
        """
        Draw a single edge between two nodes.

        Args:
            painter (QPainter): The painter to use for drawing
            source_node: The source node
            target_node: The target node
            is_selected (bool): Whether the edge is selected
            is_highlighted (bool): Whether the edge is highlighted
        """
        # Calculate edge endpoints considering node sizes
        start_point, end_point = self.calculate_edge_endpoints(source_node, target_node)

        # Get the appropriate pen based on edge state
        pen = self.style.get_edge_pen(
            is_selected=is_selected, is_highlighted=is_highlighted
        )
        painter.setPen(pen)

        # Draw the edge line
        painter.drawLine(start_point, end_point)

        # Draw arrow at the end of the edge
        self._draw_arrow(painter, start_point, end_point)

    def _draw_temp_edge(self, painter: QPainter, temp_edge_data):
        """
        Draw a temporary edge during edge creation.

        Args:
            painter (QPainter): The painter to use for drawing
            temp_edge_data (tuple): Temporary edge data (start_node, end_point)
        """
        start_node, end_point = temp_edge_data

        # Calculate start point considering node size
        start_center = QPointF(start_node.x, start_node.y)
        direction = end_point - start_center

        if direction.manhattanLength() == 0:
            return

        # Normalize direction vector
        length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
        normalized_dir = QPointF(direction.x() / length, direction.y() / length)

        # Calculate actual start point at node boundary
        start_point = QPointF(
            start_center.x() + normalized_dir.x() * start_node.size / 2,
            start_center.y() + normalized_dir.y() * start_node.size / 2,
        )

        # Get the temporary edge pen
        pen = self.style.get_edge_pen(is_temporary=True)
        painter.setPen(pen)

        # Draw the temporary edge line
        painter.drawLine(start_point, end_point)

        # Draw arrow at the end of the edge
        self._draw_arrow(painter, start_point, end_point)

    def _draw_all_for_one_edges(
        self, painter: QPainter, all_for_one_nodes, temp_edge_data
    ):
        """
        Draw edges for All-For-One connection mode.

        Args:
            painter (QPainter): The painter to use for drawing
            all_for_one_nodes (list): List of nodes selected in All-For-One mode
            temp_edge_data (tuple, optional): Temporary edge data (start_node, end_point)
        """
        if not temp_edge_data or not all_for_one_nodes:
            return

        start_node, end_point = temp_edge_data

        # Get the All-For-One edge pen
        pen = self.style.get_edge_pen(is_all_for_one=True)
        painter.setPen(pen)

        # Draw temporary edges from all selected nodes to the end point
        for node in all_for_one_nodes:
            if node != start_node:  # Skip the start node as it's already drawn
                # Calculate start point considering node size
                start_center = QPointF(node.x, node.y)
                direction = end_point - start_center

                if direction.manhattanLength() == 0:
                    continue

                # Normalize direction vector
                length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
                normalized_dir = QPointF(direction.x() / length, direction.y() / length)

                # Calculate actual start point at node boundary
                start_point = QPointF(
                    start_center.x() + normalized_dir.x() * node.size / 2,
                    start_center.y() + normalized_dir.y() * node.size / 2,
                )

                # Draw the edge line
                painter.drawLine(start_point, end_point)

                # Draw arrow at the end of the edge
                self._draw_arrow(painter, start_point, end_point)

    def _draw_parallel_edges(self, painter: QPainter, parallel_data):
        """
        Draw edges for Parallel connection mode.

        Args:
            painter (QPainter): The painter to use for drawing
            parallel_data (dict): Data for parallel connection mode
        """
        selected_nodes = parallel_data.get("selected_nodes", [])
        edge_endpoints = parallel_data.get("edge_endpoints", [])

        if (
            not selected_nodes
            or not edge_endpoints
            or len(selected_nodes) != len(edge_endpoints)
        ):
            return

        # Get the Parallel edge pen
        pen = self.style.get_edge_pen(is_parallel=True)
        painter.setPen(pen)

        # Draw temporary edges from all selected nodes to their respective endpoints
        for i, node in enumerate(selected_nodes):
            if i < len(edge_endpoints):
                end_point = QPointF(*edge_endpoints[i])

                # Calculate start point considering node size
                start_center = QPointF(node.x, node.y)
                direction = end_point - start_center

                if direction.manhattanLength() == 0:
                    continue

                # Normalize direction vector
                length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
                normalized_dir = QPointF(direction.x() / length, direction.y() / length)

                # Calculate actual start point at node boundary
                start_point = QPointF(
                    start_center.x() + normalized_dir.x() * node.size / 2,
                    start_center.y() + normalized_dir.y() * node.size / 2,
                )

                # Draw the edge line
                painter.drawLine(start_point, end_point)

                # Draw arrow at the end of the edge
                self._draw_arrow(painter, start_point, end_point)

    def _draw_arrow(self, painter: QPainter, start_point, end_point):
        """
        Draw an arrow at the end of an edge.

        Args:
            painter (QPainter): The painter to use for drawing
            start_point (QPointF): The start point of the edge
            end_point (QPointF): The end point of the edge
        """
        # Get arrow size from style
        arrow_size = self.style.get_arrow_size()

        # Calculate direction vector
        direction = end_point - start_point

        if direction.manhattanLength() == 0:
            return

        # Normalize direction vector
        length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
        normalized_dir = QPointF(direction.x() / length, direction.y() / length)

        # Calculate perpendicular vector
        perp_dir = QPointF(-normalized_dir.y(), normalized_dir.x())

        # Calculate arrow points
        arrow_point1 = QPointF(
            end_point.x()
            - normalized_dir.x() * arrow_size
            + perp_dir.x() * arrow_size / 2,
            end_point.y()
            - normalized_dir.y() * arrow_size
            + perp_dir.y() * arrow_size / 2,
        )
        arrow_point2 = QPointF(
            end_point.x()
            - normalized_dir.x() * arrow_size
            - perp_dir.x() * arrow_size / 2,
            end_point.y()
            - normalized_dir.y() * arrow_size
            - perp_dir.y() * arrow_size / 2,
        )

        # Create arrow path
        arrow_path = QPainterPath()
        arrow_path.moveTo(end_point)
        arrow_path.lineTo(arrow_point1)
        arrow_path.lineTo(arrow_point2)
        arrow_path.closeSubpath()

        # Fill the arrow
        painter.fillPath(arrow_path, painter.pen().color())
