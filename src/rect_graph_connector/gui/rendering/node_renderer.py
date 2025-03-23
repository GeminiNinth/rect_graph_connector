"""
Node and group renderer for drawing nodes and their containing groups.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen

from ...config import config
from .base_renderer import BaseRenderer, parse_rgba
from ...utils.logging_utils import get_logger

logger = get_logger(__name__)


class NodeRenderer(BaseRenderer):
    """
    Renderer for drawing nodes and their containing groups.
    Handles node shapes, colors, labels, and group backgrounds/borders.
    """

    def draw(
        self,
        painter: QPainter,
        all_for_one_selected_nodes=None,
        draw_only_backgrounds=False,
        draw_only_nodes=False,
        test_mode=False,
        hover_data=None,
        **kwargs,
    ):
        """
        Draw nodes and their containing groups.

        Args:
            painter (QPainter): The painter to use for drawing
            all_for_one_selected_nodes (list, optional): List of nodes selected in All-For-One mode
            draw_only_backgrounds (bool): If True, only draw group backgrounds
            draw_only_nodes (bool): If True, only draw nodes and borders (no backgrounds)
            test_mode (bool): If True, only draw nodes without groups (for testing)
            **kwargs: Additional drawing parameters
        """
        # Get nodes selected in parallel connection mode from canvas
        parallel_selected_nodes = []
        if hasattr(self.canvas, "parallel_selected_nodes"):
            parallel_selected_nodes = self.canvas.parallel_selected_nodes

        # Special case for test mode - just draw all nodes directly
        if test_mode:
            for node in self.graph.nodes:
                self._draw_node(
                    painter,
                    node,
                    all_for_one_selected_nodes,
                    parallel_selected_nodes,
                    is_bridge_highlighted=False,
                )
            return

        # Get selected group IDs
        selected_group_ids = [group.id for group in self.graph.selected_groups]

        # Sort groups by z-index (lowest to highest)
        sorted_groups = sorted(self.graph.node_groups, key=lambda g: g.z_index)

        # Prepare standalone nodes (nodes not belonging to any group)
        standalone_nodes = [
            node
            for node in self.graph.nodes
            if not any(node.id in group.node_ids for group in self.graph.node_groups)
        ]

        if draw_only_backgrounds:
            # Draw only group backgrounds
            self._draw_node_group_backgrounds(painter)
        elif draw_only_nodes:
            # Draw each group's nodes, borders, and labels (without backgrounds)
            for group in sorted_groups:
                self._draw_group(
                    painter,
                    group,
                    selected_group_ids,
                    all_for_one_selected_nodes,
                    parallel_selected_nodes,
                    skip_background=True,
                    hover_data=hover_data,
                )

            # Draw standalone nodes
            for node in standalone_nodes:
                self._draw_node(
                    painter,
                    node,
                    all_for_one_selected_nodes,
                    parallel_selected_nodes,
                    is_bridge_highlighted=False,
                    hover_data=hover_data,
                )
        else:
            # Draw everything (backwards compatibility)
            self._draw_node_group_backgrounds(painter)

            for group in sorted_groups:
                self._draw_group(
                    painter,
                    group,
                    selected_group_ids,
                    all_for_one_selected_nodes,
                    parallel_selected_nodes,
                    hover_data=hover_data,
                )

            # Draw standalone nodes
            for node in standalone_nodes:
                self._draw_node(
                    painter,
                    node,
                    all_for_one_selected_nodes,
                    parallel_selected_nodes,
                    is_bridge_highlighted=False,
                    hover_data=hover_data,
                )

    def _draw_node_group_backgrounds(self, painter: QPainter):
        """Draw the background rectangles for all node groups."""
        # Get selected group IDs
        selected_group_ids = [group.id for group in self.graph.selected_groups]

        # Sort groups by z-index (lowest to highest)
        sorted_groups = sorted(self.graph.node_groups, key=lambda g: g.z_index)

        # Draw background for each group
        for group in sorted_groups:
            group_nodes = group.get_nodes(self.graph.nodes)
            if not group_nodes:
                continue

            # Calculate group boundary
            border_margin = config.get_dimension("group.border_margin", 5)
            min_x = min(node.x - node.size / 2 for node in group_nodes) - border_margin
            min_y = min(node.y - node.size / 2 for node in group_nodes) - border_margin
            max_x = max(node.x + node.size / 2 for node in group_nodes) + border_margin
            max_y = max(node.y + node.size / 2 for node in group_nodes) + border_margin
            group_width = max_x - min_x
            group_height = max_y - min_y

            # Special style for selected groups
            is_selected = group.id in selected_group_ids

            # Draw group background (semi-transparent)
            bg_color_value = (
                config.get_color("group.background.selected", "rgba(230, 230, 255, 40)")
                if is_selected
                else config.get_color(
                    "group.background.normal", "rgba(245, 245, 245, 20)"
                )
            )
            bg_color = parse_rgba(bg_color_value)

            # Convert to integer positions as required
            min_x_int = int(min_x)
            min_y_int = int(min_y)
            group_width_int = int(group_width)
            group_height_int = int(group_height)
            painter.fillRect(
                min_x_int, min_y_int, group_width_int, group_height_int, bg_color
            )

    def _draw_group(
        self,
        painter: QPainter,
        group,
        selected_group_ids,
        all_for_one_selected_nodes,
        parallel_selected_nodes,
        skip_background=False,
        hover_data=None,
    ):
        """
        Draw a single group including its nodes, border, and label.

        Args:
            painter (QPainter): The painter to use for drawing
            group: The group to draw
            selected_group_ids: List of selected group IDs
            all_for_one_selected_nodes: List of nodes selected in All-For-One mode
            parallel_selected_nodes: List of nodes selected in Parallel mode
            skip_background (bool): If True, skip drawing the background
        """
        group_nodes = group.get_nodes(self.graph.nodes)
        if not group_nodes:
            return

        # Calculate group boundary
        border_margin = config.get_dimension("group.border_margin", 5)
        min_x = min(node.x - node.size / 2 for node in group_nodes) - border_margin
        min_y = min(node.y - node.size / 2 for node in group_nodes) - border_margin
        max_x = max(node.x + node.size / 2 for node in group_nodes) + border_margin
        max_y = max(node.y + node.size / 2 for node in group_nodes) + border_margin
        group_width = max_x - min_x
        group_height = max_y - min_y

        # Special style for selected groups
        is_selected = group.id in selected_group_ids

        # Convert to integer positions
        min_x_int = int(min_x)
        min_y_int = int(min_y)
        group_width_int = int(group_width)
        group_height_int = int(group_height)

        # Draw nodes within the group
        for node in group_nodes:
            self._draw_node(
                painter,
                node,
                all_for_one_selected_nodes,
                parallel_selected_nodes,
                is_bridge_highlighted=False,
                hover_data=hover_data,
            )

        # Draw group border
        border_color_value = (
            config.get_color("group.border.selected", "#6464FF")
            if is_selected
            else config.get_color("group.border.normal", "#C8C8C8")
        )
        pen_color = QColor(border_color_value)

        pen = QPen(pen_color)
        border_width = (
            config.get_dimension("group.border_width.selected", 2)
            if is_selected
            else config.get_dimension("group.border_width.normal", 1)
        )
        pen.setWidth(border_width)
        pen.setStyle(Qt.DashLine if not is_selected else Qt.SolidLine)
        painter.setPen(pen)
        painter.drawRect(min_x_int, min_y_int, group_width_int, group_height_int)

        # Draw group label
        self._draw_group_label(
            painter,
            group,
            group_nodes,
            is_selected,
            pen_color,
            min_x_int,
            min_y_int,
            max_x,
            max_y,
        )

    def _draw_node(
        self,
        painter: QPainter,
        node,
        all_for_one_selected_nodes=None,
        parallel_selected_nodes=None,
        is_bridge_highlighted=False,
        is_bridge_source_highlighted=False,
        hover_data=None,
    ):
        """
        Draw a single node with its fill, border, and label.

        Args:
            painter (QPainter): The painter to use for drawing
            node: The node to draw
            all_for_one_selected_nodes: List of nodes selected in All-For-One mode
            parallel_selected_nodes: List of nodes selected in Parallel mode
            is_bridge_highlighted (bool): Whether this node is highlighted as a target node in bridge mode
            is_bridge_source_highlighted (bool): Whether this node is highlighted as a source node in bridge mode
        """
        rect = QRectF(
            node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
        )

        # Save painter state before drawing
        painter.save()

        # Check if node should be highlighted based on hover state
        is_highlighted = False
        if hover_data:
            # Highlights only the nodes that are hovered or directly connected to that node
            is_highlighted = False
            if node.id == hover_data["node"].id:
                is_highlighted = True
            else:
                # Check for directly connected edges from the hovered node
                for edge in hover_data["edges"]:
                    if (
                        edge[0].id == hover_data["node"].id and edge[1].id == node.id
                    ) or (
                        edge[1].id == hover_data["node"].id and edge[0].id == node.id
                    ):
                        is_highlighted = True
                        break
            logger.debug(f"Node {node.id}: highlighted={is_highlighted}")

        # Apply transparency for non-highlighted nodes in edit mode when hovering
        if hover_data and not is_highlighted:
            opacity = config.get_dimension("hover.opacity", 0.5)
            logger.debug(f"Node {node.id}: applying opacity={opacity}")
            painter.setOpacity(opacity)

        # Determine node selection state
        is_node_selected = node in self.graph.selected_nodes
        is_all_for_one_selected = (
            all_for_one_selected_nodes and node in all_for_one_selected_nodes
        )
        is_parallel_selected = (
            parallel_selected_nodes and node in parallel_selected_nodes
        )

        # Fill color based on selection state
        if is_bridge_source_highlighted:
            # Source node highlighting takes precedence
            node_fill_color = config.get_color(
                "node.fill.bridge_source_highlighted", "#FFD0E0"
            )  # Light pink
        elif is_bridge_highlighted:
            # Target node highlighting takes precedence
            node_fill_color = config.get_color(
                "node.fill.bridge_target_highlighted", "#50FCC0"
            )  # Light blue
        elif is_parallel_selected:
            node_fill_color = config.get_color(
                "node.fill.parallel_selected", "#90EE90"
            )  # Light green
        elif is_all_for_one_selected:
            node_fill_color = config.get_color(
                "node.fill.all_for_one_selected", "#FFA500"
            )  # Orange
        elif is_node_selected:
            node_fill_color = config.get_color(
                "node.fill.selected", "#ADD8E6"
            )  # Selected blue
        else:
            node_fill_color = config.get_color(
                "node.fill.normal", "skyblue"
            )  # Normal blue

        node_color = QColor(node_fill_color)

        # Set up border pen based on selection state
        if is_bridge_source_highlighted:
            # Source node highlighting takes precedence
            border_color = config.get_color(
                "node.border.bridge_source_highlighted", "#FF80A0"
            )  # Pink
            pen = QPen(QColor(border_color))
            pen.setWidth(
                int(config.get_dimension("node.border_width.bridge_highlighted", 2))
            )
        elif is_bridge_highlighted:
            # Target node highlighting takes precedence
            border_color = config.get_color(
                "node.border.bridge_target_highlighted", "#10DDFF"
            )  # Turquoise
            pen = QPen(QColor(border_color))
            pen.setWidth(
                int(config.get_dimension("node.border_width.bridge_highlighted", 2))
            )
        elif is_parallel_selected:
            border_color = config.get_color(
                "node.border.parallel_selected", "#006400"
            )  # Dark green
            pen = QPen(QColor(border_color))
            pen.setWidth(config.get_dimension("node.border_width.parallel_selected", 3))
        elif is_all_for_one_selected:
            border_color = config.get_color(
                "node.border.all_for_one_selected", "#FF6600"
            )  # Dark orange
            pen = QPen(QColor(border_color))
            pen.setWidth(
                config.get_dimension("node.border_width.all_for_one_selected", 3)
            )
        elif is_node_selected:
            border_color = config.get_color("node.border.selected", "blue")
            pen = QPen(QColor(border_color))
            pen.setWidth(config.get_dimension("node.border_width.selected", 2))
        else:
            border_color = config.get_color("node.border.normal", "gray")
            pen = QPen(QColor(border_color))
            pen.setWidth(config.get_dimension("node.border_width.normal", 1))

        # Draw the node based on its shape
        shape = getattr(node, "shape", "rectangle")

        if shape == "circle":
            # Draw circular node
            painter.setBrush(node_color)
            painter.setPen(pen)
            painter.drawEllipse(rect)
        else:
            # Draw rectangular node (default)
            painter.fillRect(rect, node_color)
            painter.setPen(pen)
            painter.drawRect(rect)

        # Draw node ID
        painter.setPen(QPen(QColor(config.get_color("node.text", "#000000")), 1))
        painter.drawText(rect, Qt.AlignCenter, str(node.id))

        # Restore painter state
        painter.restore()

    def _draw_group_label(
        self,
        painter: QPainter,
        group,
        group_nodes,
        is_selected,
        pen_color,
        min_x,
        min_y,
        max_x,
        max_y,
    ):
        """
        Draw the label for a node group.

        Args:
            painter (QPainter): The painter to use for drawing
            group: The group to draw the label for
            group_nodes: List of nodes in the group
            is_selected: Whether the group is selected
            pen_color: Color for the label text
            min_x, min_y: Top-left corner of the group
            max_x, max_y: Bottom-right corner of the group
        """
        if not group.name:
            return

        # Set up label background
        label_bg_color_value = (
            config.get_color(
                "group.label.background.selected", "rgba(240, 240, 255, 200)"
            )
            if is_selected
            else config.get_color(
                "group.label.background.normal", "rgba(240, 240, 240, 180)"
            )
        )
        label_bg_color = parse_rgba(label_bg_color_value)

        # Set up label text color
        label_text_color = QColor(config.get_color("group.label.text", "#000000"))

        # Calculate label position (centered at the top of the group)
        label_padding = config.get_dimension("group.label_padding", 2)
        label_height = config.get_dimension("group.label_height", 20)
        label_width = min(
            config.get_dimension("group.label_max_width", 150),
            max_x - min_x,
        )
        label_x = min_x + (max_x - min_x - label_width) / 2
        label_y = min_y - label_height - label_padding

        # Draw label background
        label_rect = QRectF(label_x, label_y, label_width, label_height)
        painter.fillRect(label_rect, label_bg_color)

        # Draw label border
        painter.setPen(pen_color)
        painter.drawRect(label_rect)

        # Draw label text
        painter.setPen(label_text_color)
        painter.drawText(label_rect, Qt.AlignCenter, group.name)
