"""
Bridge connection renderer for visualizing bridge connections between node groups.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath

from ...config import config
from ...models.graph import Graph
from .base_renderer import BaseRenderer, parse_rgba


class BridgeRenderer(BaseRenderer):
    """
    Renderer for bridge connection visualization elements.

    This includes rendering bridge preview lines, highlighting edge nodes for bridge
    connections, and floating menus for bridge mode.
    """

    def __init__(self, canvas, graph: Graph):
        """
        Initialize the bridge renderer.

        Args:
            canvas: The canvas widget to draw on
            graph (Graph): The graph model to render
        """
        super().__init__(canvas, graph)

    def draw(self, painter: QPainter, bridge_data=None, **kwargs):
        """
        Draw bridge connection visualization elements.

        Args:
            painter (QPainter): The painter to use for drawing
            bridge_data (dict, optional): Data for bridge connection rendering
                - floating_menus (dict): Dict of floating menus for selected groups
                - preview_lines (list): List of (start_point, end_point) tuples for preview lines
                - selected_groups (list): List of selected groups for bridge connection
                - edge_nodes (dict): Dict mapping group ID to list of highlighted edge nodes
            **kwargs: Additional drawing parameters
        """
        if not bridge_data:
            return

        # Extract bridge data
        floating_menus = bridge_data.get("floating_menus", {})
        preview_lines = bridge_data.get("preview_lines", [])
        selected_groups = bridge_data.get("selected_groups", [])
        edge_nodes_dict = bridge_data.get("edge_nodes", {})

        # Draw preview lines for bridge connections
        self._draw_preview_lines(painter, preview_lines)

        # Draw highlighted edge nodes
        self._draw_highlighted_edge_nodes(painter, edge_nodes_dict)

        # Draw floating menus
        self._draw_floating_menus(painter, floating_menus, selected_groups)

    def _draw_preview_lines(self, painter: QPainter, preview_lines):
        """
        Draw preview lines for bridge connections.

        Args:
            painter (QPainter): The painter to use for drawing
            preview_lines (list): List of (start_point, end_point) tuples for preview lines
        """
        if not preview_lines:
            return

        # Save painter state
        painter.save()

        # Set preview line style
        # theme = "dark" if self._is_dark_mode() else "light"
        bridge_pen_color_text = config.get_color(
            "edge.bridge_preview", "rgba(100, 100, 255, 150)"
        )
        bridge_pen_color = parse_rgba(bridge_pen_color_text)
        bridge_pen = QPen(
            bridge_pen_color,
            1.5,
            Qt.DashLine,
        )
        painter.setPen(bridge_pen)

        # Draw each preview line
        for start_point, end_point in preview_lines:
            painter.drawLine(start_point, end_point)

        # Restore painter state
        painter.restore()

    def _draw_highlighted_edge_nodes(self, painter: QPainter, edge_nodes_dict):
        """
        Draw highlighted edge nodes for bridge connections.

        Args:
            painter (QPainter): The painter to use for drawing
            edge_nodes_dict (dict): Dict mapping group ID to list of highlighted edge nodes
        """
        if not edge_nodes_dict:
            return

        # Save painter state
        painter.save()

        # Get node highlight style
        # theme = "dark" if self._is_dark_mode() else "light"
        fill_color_text = config.get_color(
            "node.fill.bridge_highlighted", "rgba(255, 165, 0, 200)"
        )
        fill_color = parse_rgba(fill_color_text)
        border_color = QColor(
            config.get_color("node.border.bridge_highlighted", "#FF8C00")
        )

        # Draw each highlighted node
        for group_id, nodes in edge_nodes_dict.items():
            for node in nodes:
                # Draw the highlighted node
                radius = config.get_dimension("node.default_size", 30.0)

                # Draw the node with highlight
                painter.setBrush(QBrush(fill_color))

                painter.setPen(QPen(border_color, 2.0))
                painter.drawEllipse(QPointF(node.x, node.y), radius, radius)

        # Restore painter state
        painter.restore()

    def _draw_floating_menus(self, painter: QPainter, floating_menus, selected_groups):
        """
        Draw floating menus for bridge connections.

        Args:
            painter (QPainter): The painter to use for drawing
            floating_menus (dict): Dict of floating menus for selected groups
            selected_groups (list): List of selected groups for bridge connection
        """
        if not floating_menus or not selected_groups:
            return

        # Draw each floating menu
        for group_id, menu in floating_menus.items():
            # Find the group object
            group = None
            for g in selected_groups:
                if g.id == group_id:
                    group = g
                    break

            if group:
                # Get node positions for this group
                nodes = group.get_nodes(self.graph.nodes)
                node_positions = [(node.x, node.y) for node in nodes]

                # Get menu position
                menu_pos = menu.get_position(node_positions)

                # Draw the menu
                menu.draw(painter, menu_pos)
                # Store the last position in the menu
                menu.last_position = menu_pos

    # def _is_dark_mode(self):
    #     """Check if the canvas is in dark mode."""
    #     # You might implement this based on your application's theme management
    #     if hasattr(self.canvas, "theme"):
    #         return self.canvas.theme == "dark"
    #     return False
