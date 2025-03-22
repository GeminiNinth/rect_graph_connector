"""
Node and group renderer for drawing nodes and their containing groups.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen

from ...config import config
from .base_renderer import BaseRenderer, parse_rgba


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
                )

            # Draw standalone nodes
            for node in standalone_nodes:
                self._draw_node(
                    painter,
                    node,
                    all_for_one_selected_nodes,
                    parallel_selected_nodes,
                    is_bridge_highlighted=False,
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
                )

            # Draw standalone nodes
            for node in standalone_nodes:
                self._draw_node(
                    painter,
                    node,
                    all_for_one_selected_nodes,
                    parallel_selected_nodes,
                    is_bridge_highlighted=False,
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
    ):
        """
        Draw a single node with its fill, border, and label.

        Args:
            painter (QPainter): The painter to use for drawing
            node: The node to draw
            all_for_one_selected_nodes: List of nodes selected in All-For-One mode
            parallel_selected_nodes: List of nodes selected in Parallel mode
            is_bridge_highlighted (bool): Whether this node is highlighted in bridge mode
        """
        rect = QRectF(
            node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
        )

        # Save painter state before drawing
        painter.save()

        # Determine node selection state
        is_node_selected = node in self.graph.selected_nodes
        is_all_for_one_selected = (
            all_for_one_selected_nodes and node in all_for_one_selected_nodes
        )
        is_parallel_selected = (
            parallel_selected_nodes and node in parallel_selected_nodes
        )

        # Fill color based on selection state
        if is_bridge_highlighted:
            # Bridge highlighting takes precedence
            node_fill_color = config.get_color(
                "node.fill.bridge_highlighted", "#10DDFF"
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
        if is_bridge_highlighted:
            # Bridge highlighting takes precedence
            border_color = config.get_color(
                "node.border.bridge_highlighted", "#50FCC0"
            )  # Emerald green
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
        text_color = config.get_color("node.text", "#000000")
        painter.setPen(QColor(text_color))
        painter.drawText(rect, Qt.AlignCenter, str(node.id))

        # 描画後にpainterの状態を復元
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
        """Draw the label for a node group."""
        # Calculate label width (including margins)
        font_metrics = painter.fontMetrics()
        text_margin = config.get_dimension("group.label.text_margin", 10)
        text_width = font_metrics.width(group.name) + text_margin
        half_width = text_width // 2

        # Calculate label position
        center_x = (min_x + max_x) / 2
        margin = config.get_dimension("group.label.position_margin", 30)
        label_height = config.get_dimension("group.label.height", 20)
        fixed_width = config.get_dimension("group.label.fixed_width", 100)

        # Determine label position and width based on group settings
        if group.label_position == group.POSITION_RIGHT:
            # Right position with dynamic offset
            dynamic_offset = max(margin, (max_x - min_x) * 0.1)
            label_x = int(max_x + dynamic_offset)
            label_y = int((min_y + max_y) / 2 - 10)
            display_width = text_width if is_selected else min(fixed_width, text_width)
            display_text = (
                group.name
                if is_selected or text_width <= fixed_width
                else font_metrics.elidedText(group.name, Qt.ElideRight, fixed_width)
            )
        else:  # POSITION_TOP or POSITION_BOTTOM
            # Center the label
            label_x = int(center_x - text_width / 2)
            label_y = (
                int(min_y - margin)
                if group.label_position == group.POSITION_TOP
                else int(max_y + margin)
            )
            display_width = text_width
            display_text = group.name

        # Draw label background
        label_bg_value = (
            config.get_color(
                "group.label.background.selected", "rgba(240, 240, 255, 200)"
            )
            if is_selected
            else config.get_color(
                "group.label.background.normal", "rgba(240, 240, 240, 180)"
            )
        )
        label_bg = parse_rgba(label_bg_value)
        painter.fillRect(label_x, label_y, display_width, label_height, label_bg)

        # Draw label border
        painter.setPen(pen_color)
        painter.drawRect(label_x, label_y, display_width, label_height)

        # Draw group name
        text_color = config.get_color("group.label.text", "#000000")
        painter.setPen(QColor(text_color))
        painter.drawText(
            label_x,
            label_y,
            display_width,
            label_height,
            Qt.AlignCenter,
            display_text,
        )
