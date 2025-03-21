"""
Edge renderer for drawing various types of edges in the graph.
"""

from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QPointF

from .base_renderer import BaseRenderer
from ...config import config


class EdgeRenderer(BaseRenderer):
    """
    Renderer for drawing all types of edges in the graph.
    Handles normal edges, temporary edges, selected edges, and highlighted edges.
    """

    def draw(
        self,
        painter: QPainter,
        selected_edges=None,
        temp_edge_data=None,
        knife_data=None,
        all_for_one_selected_nodes=None,
        parallel_data=None,
        **kwargs,
    ):
        """
        Draw all types of edges in the graph.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_edges (list, optional): List of edges that are selected
            temp_edge_data (tuple, optional): Temporary edge data (start_node, end_point)
            knife_data (dict, optional): Data for knife tool rendering
            all_for_one_selected_nodes (list, optional): List of nodes selected in All-For-One mode
            parallel_data (dict, optional): Data for parallel connection mode
            **kwargs: Additional drawing parameters
        """
        # Draw standalone edges first (backmost)
        self._draw_standalone_edges(painter, selected_edges)

        # Draw edges within groups
        self._draw_group_edges(painter, selected_edges)

        # Draw selected edges
        if selected_edges:
            self._draw_selected_edges(painter, selected_edges)

        # Draw knife tool highlighted edges
        if knife_data and knife_data.get("highlighted_edges"):
            self._draw_highlighted_edges(painter, knife_data["highlighted_edges"])

        # Draw temporary edge during edge creation
        if temp_edge_data:
            self._draw_temp_edge(painter, temp_edge_data)

        # Draw All-For-One connection edges
        if temp_edge_data and all_for_one_selected_nodes:
            self._draw_all_for_one_edges(
                painter, temp_edge_data, all_for_one_selected_nodes
            )

        # Draw parallel connection edges
        if (
            parallel_data
            and "edge_endpoints" in parallel_data
            and parallel_data["edge_endpoints"]
        ):
            self._draw_parallel_edges(painter, parallel_data)

    def _draw_standalone_edges(self, painter: QPainter, selected_edges=None):
        """Draw edges between nodes that don't belong to any NodeGroup."""
        # Set up pen for normal edges
        edge_color = config.get_color("edge.normal", "#000000")
        pen = QPen(QColor(edge_color))
        pen.setWidth(config.get_dimension("edge.width.normal", 1))
        painter.setPen(pen)

        # Collect all node IDs that belong to any group
        group_node_ids = set()
        for group in self.graph.node_groups:
            group_node_ids.update(group.node_ids)

        # Draw edges that connect nodes not in the same group
        for source_id, target_id in self.graph.edges:
            # Skip if edge is selected
            if selected_edges and (source_id, target_id) in [
                (e[0].id, e[1].id) for e in selected_edges
            ]:
                continue

            # Find which groups the nodes belong to
            source_group = next(
                (g for g in self.graph.node_groups if source_id in g.node_ids), None
            )
            target_group = next(
                (g for g in self.graph.node_groups if target_id in g.node_ids), None
            )

            # Only draw if nodes are in different groups or at least one is not in any group
            if source_group != target_group:
                try:
                    source_node = next(n for n in self.graph.nodes if n.id == source_id)
                    target_node = next(n for n in self.graph.nodes if n.id == target_id)

                    # Calculate and draw edge
                    start_point, end_point = self.calculate_edge_endpoints(
                        source_node, target_node
                    )
                    painter.drawLine(
                        int(start_point.x()),
                        int(start_point.y()),
                        int(end_point.x()),
                        int(end_point.y()),
                    )
                except StopIteration:
                    continue

    def _draw_group_edges(self, painter: QPainter, selected_edges=None):
        """Draw edges between nodes within the same group."""
        edge_color = config.get_color("edge.normal", "#000000")
        pen = QPen(QColor(edge_color))
        pen.setWidth(config.get_dimension("edge.width.normal", 1))
        painter.setPen(pen)

        # Draw edges for each group in z-index order
        for group in sorted(self.graph.node_groups, key=lambda g: g.z_index):
            for source_id, target_id in self.graph.edges:
                # Skip if edge is selected
                if selected_edges and (source_id, target_id) in [
                    (e[0].id, e[1].id) for e in selected_edges
                ]:
                    continue

                # Only draw edges where both nodes belong to this group
                if source_id in group.node_ids and target_id in group.node_ids:
                    try:
                        source_node = next(
                            n for n in self.graph.nodes if n.id == source_id
                        )
                        target_node = next(
                            n for n in self.graph.nodes if n.id == target_id
                        )

                        # Calculate and draw edge
                        start_point, end_point = self.calculate_edge_endpoints(
                            source_node, target_node
                        )
                        painter.drawLine(
                            int(start_point.x()),
                            int(start_point.y()),
                            int(end_point.x()),
                            int(end_point.y()),
                        )
                    except StopIteration:
                        continue

    def _draw_selected_edges(self, painter: QPainter, selected_edges):
        """Draw selected edges with a highlighted style."""
        if not selected_edges:
            return

        # Set up pen for selected edges
        edge_color = config.get_color("edge.highlighted", "#FF0000")
        edge_width = config.get_dimension("edge.width.highlighted", 2)
        painter.setPen(QPen(QColor(edge_color), edge_width))

        # Draw each selected edge
        for edge in selected_edges:
            try:
                source_node, target_node = edge[0], edge[1]
                start_point, end_point = self.calculate_edge_endpoints(
                    source_node, target_node
                )
                painter.drawLine(
                    int(start_point.x()),
                    int(start_point.y()),
                    int(end_point.x()),
                    int(end_point.y()),
                )
            except (IndexError, AttributeError):
                continue

    def _draw_highlighted_edges(self, painter: QPainter, highlighted_edges):
        """Draw highlighted edges for knife tool."""
        if not highlighted_edges:
            return

        # Set up pen for highlighted edges
        edge_color = config.get_color("edge.highlighted", "#FF0000")
        edge_width = config.get_dimension("edge.width.highlighted", 2)
        painter.setPen(QPen(QColor(edge_color), edge_width))

        # Draw each highlighted edge
        for edge in highlighted_edges:
            try:
                source_node = next(n for n in self.graph.nodes if n.id == edge[0])
                target_node = next(n for n in self.graph.nodes if n.id == edge[1])

                start_point, end_point = self.calculate_edge_endpoints(
                    source_node, target_node
                )
                painter.drawLine(
                    int(start_point.x()),
                    int(start_point.y()),
                    int(end_point.x()),
                    int(end_point.y()),
                )
            except StopIteration:
                continue

    def _draw_temp_edge(self, painter: QPainter, temp_edge_data):
        """Draw temporary edge during edge creation."""
        start_node, end_point = temp_edge_data
        if not (start_node and end_point):
            return

        # Set up pen for temporary edge
        edge_color = config.get_color("edge.normal", "#000000")
        pen = QPen(QColor(edge_color))
        pen.setWidth(config.get_dimension("edge.width.normal", 1))
        painter.setPen(pen)

        # Calculate start point from node boundary using shape-specific calculation if available
        if hasattr(start_node, "calculate_edge_connection_point"):
            start_x, start_y = start_node.calculate_edge_connection_point(
                end_point.x(), end_point.y()
            )
            start_point = QPointF(start_x, start_y)
        else:
            # Fallback to the old calculation method
            start_center = QPointF(start_node.x, start_node.y)
            direction = QPointF(end_point) - start_center
            if direction.manhattanLength() == 0:
                return

            length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
            normalized_dir = QPointF(direction.x() / length, direction.y() / length)
            start_point = QPointF(
                start_center.x() + normalized_dir.x() * start_node.size / 2,
                start_center.y() + normalized_dir.y() * start_node.size / 2,
            )

        # Draw the line from start_point to end_point
        painter.drawLine(
            int(start_point.x()),
            int(start_point.y()),
            int(end_point.x()),
            int(end_point.y()),
        )

    def _draw_all_for_one_edges(
        self, painter: QPainter, temp_edge_data, all_for_one_selected_nodes
    ):
        """Draw temporary virtual edges from all selected nodes in All-For-One connection mode."""
        if not (temp_edge_data and all_for_one_selected_nodes):
            return

        start_node, end_point = temp_edge_data

        # Set up pen for virtual edges
        edge_color = config.get_color("edge.normal", "#000000")
        pen = QPen(QColor(edge_color))
        pen.setWidth(config.get_dimension("edge.width.normal", 1))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        # Draw virtual edges from all selected nodes except the start node
        for node in all_for_one_selected_nodes:
            if node != start_node:
                # Calculate start point using shape-specific calculation if available
                if hasattr(node, "calculate_edge_connection_point"):
                    start_x, start_y = node.calculate_edge_connection_point(
                        end_point.x(), end_point.y()
                    )
                    start_point = QPointF(start_x, start_y)
                else:
                    # Fallback to the old calculation method
                    start_center = QPointF(node.x, node.y)
                    direction = QPointF(end_point) - start_center

                    if direction.manhattanLength() == 0:
                        continue

                    length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
                    normalized_dir = QPointF(
                        direction.x() / length, direction.y() / length
                    )
                    start_point = QPointF(
                        start_center.x() + normalized_dir.x() * node.size / 2,
                        start_center.y() + normalized_dir.y() * node.size / 2,
                    )

                # Draw the line from start_point to end_point for all cases
                painter.drawLine(
                    int(start_point.x()),
                    int(start_point.y()),
                    int(end_point.x()),
                    int(end_point.y()),
                )

    def _draw_parallel_edges(self, painter: QPainter, parallel_data):
        """Draw temporary virtual edges for parallel connection mode."""
        if not parallel_data or "edge_endpoints" not in parallel_data:
            return

        selected_nodes = parallel_data.get("selected_nodes", [])
        edge_endpoints = parallel_data["edge_endpoints"]

        # Set up pen for virtual edges
        edge_color = config.get_color("edge.normal", "#000000")
        pen = QPen(QColor(edge_color))
        pen.setWidth(config.get_dimension("edge.width.normal", 1))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        # Draw each virtual edge
        for node, endpoint in zip(selected_nodes, edge_endpoints):
            if node and endpoint:
                end_point = QPointF(endpoint[0], endpoint[1])

                # Calculate start point using shape-specific calculation if available
                if hasattr(node, "calculate_edge_connection_point"):
                    start_x, start_y = node.calculate_edge_connection_point(
                        end_point.x(), end_point.y()
                    )
                    start_point = QPointF(start_x, start_y)
                else:
                    # Fallback to the old calculation method
                    start_center = QPointF(node.x, node.y)
                    direction = end_point - start_center

                    if direction.manhattanLength() == 0:
                        continue

                    length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
                    normalized_dir = QPointF(
                        direction.x() / length, direction.y() / length
                    )
                    start_point = QPointF(
                        start_center.x() + normalized_dir.x() * node.size / 2,
                        start_center.y() + normalized_dir.y() * node.size / 2,
                    )

                # Draw the line from start_point to end_point for all cases
                painter.drawLine(
                    int(start_point.x()),
                    int(start_point.y()),
                    int(end_point.x()),
                    int(end_point.y()),
                )

    def calculate_edge_endpoints(self, source_node, target_node):
        """
        Calculate the start and end points for an edge between two nodes.
        The points are on the boundaries of the nodes, not at their centers.
        Uses the node's shape-specific edge connection point calculation.

        Args:
            source_node: The source node
            target_node: The target node

        Returns:
            tuple: (start_point, end_point) as QPointF objects
        """
        # Use the node's shape-specific edge connection point calculation if available
        if hasattr(source_node, "calculate_edge_connection_point") and hasattr(
            target_node, "calculate_edge_connection_point"
        ):
            # Calculate source connection point
            source_x, source_y = source_node.calculate_edge_connection_point(
                target_node.x, target_node.y
            )
            # Calculate target connection point
            target_x, target_y = target_node.calculate_edge_connection_point(
                source_node.x, source_node.y
            )

            return QPointF(source_x, source_y), QPointF(target_x, target_y)
        else:
            # Fallback to the old calculation method for backward compatibility
            # Get node centers
            source_center = QPointF(source_node.x, source_node.y)
            target_center = QPointF(target_node.x, target_node.y)

            # Calculate direction vector
            direction = target_center - source_center
            if direction.manhattanLength() == 0:
                return source_center, target_center

            # Normalize direction
            length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
            normalized_dir = QPointF(direction.x() / length, direction.y() / length)

            # Calculate points on node boundaries
            start_point = QPointF(
                source_center.x() + normalized_dir.x() * source_node.size / 2,
                source_center.y() + normalized_dir.y() * source_node.size / 2,
            )
            end_point = QPointF(
                target_center.x() - normalized_dir.x() * target_node.size / 2,
                target_center.y() - normalized_dir.y() * target_node.size / 2,
            )

            return start_point, end_point
