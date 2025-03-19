"""
This module contains the renderer for the canvas, handling all drawing operations.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF
import re

from ..models.graph import Graph
from ..config import config


def parse_rgba(rgba_str):
    """
    Parse rgba string and return QColor object.
    Supports both hex and rgba() format.

    Args:
        rgba_str (str): Color string in format 'rgba(r,g,b,a)' or hex format
        where a can be integer (0-255) or float (0-1)

    Returns:
        QColor: QColor object with the specified color
    """
    if rgba_str.startswith("rgba"):
        # Parse rgba(r,g,b,a) format
        match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+|\d*\.\d+)\)", rgba_str)
        if match:
            r, g, b, a = match.groups()
            r, g, b = map(int, [r, g, b])
            # Convert alpha to 0-255 range if it's a float
            a = int(float(a) * 255) if "." in a else int(a)
            color = QColor()
            color.setRgb(r, g, b, a)
            return color
    # Default to direct QColor creation for hex format
    return QColor(rgba_str)


class CanvasRenderer:
    """
    A helper class to render the graph on the canvas.

    This class encapsulates all drawing operations, separating the rendering
    logic from the event handling and interactions in the Canvas class.
    """

    def __init__(self, canvas: QWidget, graph: Graph):
        """
        Initialize the renderer.

        Args:
            canvas (QWidget): The canvas widget to draw on
            graph (Graph): The graph model to render
        """
        self.canvas = canvas
        self.graph = graph

    def draw(
        self,
        painter: QPainter,
        mode: str,
        temp_edge_data=None,
        edit_target_group=None,
        edit_target_groups=None,
        knife_data=None,
        selected_edges=None,
        all_for_one_selected_nodes=None,
        selection_rect_data=None,
    ):
        """
        Draw the complete graph on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            mode (str): The current mode ("normal" or "edit")
            temp_edge_data (tuple, optional): Temporary edge data (start_node, end_point)
            edit_target_group: Deprecated. Use edit_target_groups instead.
            edit_target_groups: List of groups being edited in edit mode
            knife_data (dict, optional): Data for knife tool rendering
            selected_edges (list, optional): List of edges that are selected
            all_for_one_selected_nodes (list, optional): List of nodes selected in All-For-One connection mode
        """
        # Draw canvas border without scaling
        self._draw_canvas_border(painter, mode)

        # Save the painter state and apply zoom scaling for graph elements
        painter.save()

        # Apply pan offset and zoom scaling
        if hasattr(self.canvas, "pan_offset"):
            painter.translate(self.canvas.pan_offset)
        if hasattr(self.canvas, "zoom"):
            painter.scale(self.canvas.zoom, self.canvas.zoom)

        # Rendering order (visual context)：
        # 1. Background (most back)- canvas_border (Already drawn)
        # 2. Drawing edges that do not belong to a group (backmost)
        # 3. Drawing NodeGroup background
        # 4. Normal edges in groups (draw by group)
        # 5. Knife Tool Highlight Edge
        # 6. Temporary Edge (when creating a new Edge)
        # 7. Group nodes, borders, labels (in order of z-index)
        # 8. Independent nodes (nodes not belonging to a group)
        # 9. Knife Tool Path (Front)

        # Drawing edges that do not belong to a group (backmost)
        self._draw_standalone_edges(painter, selected_edges)

        # Drawing NodeGroup background
        self._draw_node_group_backgrounds(painter)

        # Draw normal edges in a group
        for group in sorted(self.graph.node_groups, key=lambda g: g.z_index):
            for source_id, target_id in self.graph.edges:
                # Skip if edge is selected (will be drawn later with highlight)
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

                        edge_color = config.get_color("edge.normal", "#000000")
                        pen = QPen(QColor(edge_color))
                        pen.setWidth(config.get_dimension("edge.width.normal", 1))
                        painter.setPen(pen)

                        # Calculate actual edge endpoints
                        start_point, end_point = self._calculate_edge_endpoints(
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

        # Draw selected edges
        if selected_edges:
            self._draw_selected_edges(painter, selected_edges)

        # Draw selected edges with the knife tool
        if knife_data and knife_data.get("highlighted_edges"):
            self._draw_highlighted_edges(painter, knife_data.get("highlighted_edges"))

        # Draw a temporary edge
        if temp_edge_data:
            self._draw_temp_edge(painter, temp_edge_data)

        # Draw group nodes, borders, and labels (in order of z-index)
        self._draw_nodes(painter, all_for_one_selected_nodes)

        # Draw the path of the Knife tool (front)
        if knife_data and knife_data.get("path"):
            self._draw_knife_path(painter, knife_data["path"])

        # Draw selection rectangle if active
        if selection_rect_data:
            self._draw_selection_rectangle(painter, selection_rect_data)

        # Restore painter state
        painter.restore()

    def _draw_canvas_border(self, painter: QPainter, mode: str):
        """
        Draw the canvas border with mode-specific color.

        Args:
            painter (QPainter): The painter to use for drawing
            mode (str): The current mode ("normal" or "edit")
        """
        # Set border color according to the mode from config
        if mode == "edit":
            border_color = config.get_color(
                "canvas.border.edit", "#FF6464"
            )  # Edit mode border
        else:
            border_color = config.get_color(
                "canvas.border.normal", "#000000"
            )  # Normal mode border

        pen = QPen(QColor(border_color))
        pen.setWidth(config.get_dimension("canvas.border_width", 2))
        painter.setPen(pen)
        painter.drawRect(0, 0, self.canvas.width() - 1, self.canvas.height() - 1)

    def _draw_highlighted_edges(self, painter: QPainter, highlighted_edges):
        """
        Draw highlighted edges for knife tool in a different color.
        These edges are drawn on top of all other elements for maximum visibility.

        Args:
            painter (QPainter): The painter to use for drawing
            highlighted_edges (List[Tuple[int, int]]): List of edge tuples to highlight
        """
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

                # Calculate actual edge endpoints
                start_point, end_point = self._calculate_edge_endpoints(
                    source_node, target_node
                )

                # Draw the highlighted edge
                painter.drawLine(
                    int(start_point.x()),
                    int(start_point.y()),
                    int(end_point.x()),
                    int(end_point.y()),
                )
            except StopIteration:
                continue

    def _draw_selected_edges(self, painter: QPainter, selected_edges):
        """
        Draw selected edges with a highlighted style.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_edges (List[Tuple[RectNode, RectNode]]): List of selected edges
        """
        if not selected_edges:
            return

        # Set up pen for selected edges
        edge_color = config.get_color("edge.highlighted", "#FF0000")
        edge_width = config.get_dimension("edge.width.highlighted", 2)
        painter.setPen(QPen(QColor(edge_color), edge_width))

        # Draw each selected edge
        for edge in selected_edges:
            try:
                source_node = edge[0]  # RectNode object
                target_node = edge[1]  # RectNode object

                # Calculate actual edge endpoints
                start_point, end_point = self._calculate_edge_endpoints(
                    source_node, target_node
                )

                # Draw the selected edge
                painter.drawLine(
                    int(start_point.x()),
                    int(start_point.y()),
                    int(end_point.x()),
                    int(end_point.y()),
                )
            except (IndexError, AttributeError):
                continue

    def _draw_knife_path(self, painter: QPainter, path_points):
        """
        Draw the knife tool path.

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

    def _draw_mode_indicator(
        self, painter: QPainter, mode: str, edit_target_group=None
    ):
        """
        Draw a mode indicator for debugging.

        Args:
            painter (QPainter): The painter to use for drawing
            mode (str): The current mode
            edit_target_group: The group being edited in edit mode
        """
        if mode == "edit" and edit_target_group:
            text = config.get_string(
                "main_window.mode.edit_with_target", "Mode: Edit - {group_names}"
            )
            text = text.format(group_names=edit_target_group.name)
        elif mode == "edit":
            text = config.get_string("main_window.mode.edit", "Mode: Edit")
        else:
            text = config.get_string("main_window.mode.normal", "Mode: Normal")

        text_color = config.get_color("mode_indicator.text", "#000000")
        painter.setPen(QColor(text_color))
        painter.drawText(10, 20, text)

    def _calculate_edge_endpoints(self, source_node, target_node):
        """
        Calculate the actual visual endpoints of an edge considering node sizes.

        Args:
            source_node: The source node
            target_node: The target node

        Returns:
            tuple: (start_point, end_point) as QPointF objects
        """
        # Get node centers
        start_center = QPointF(source_node.x, source_node.y)
        end_center = QPointF(target_node.x, target_node.y)

        # Calculate direction vector
        direction = end_center - start_center
        if direction.manhattanLength() == 0:
            return start_center, end_center

        # Normalize direction vector
        length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
        normalized_dir = QPointF(direction.x() / length, direction.y() / length)

        # Calculate actual endpoints considering node sizes
        start_point = QPointF(
            start_center.x() + normalized_dir.x() * source_node.size / 2,
            start_center.y() + normalized_dir.y() * source_node.size / 2,
        )
        end_point = QPointF(
            end_center.x() - normalized_dir.x() * target_node.size / 2,
            end_center.y() - normalized_dir.y() * target_node.size / 2,
        )

        return start_point, end_point

    def _draw_standalone_edges(self, painter: QPainter, selected_edges=None):
        """
        Draw edges between nodes that don't belong to any NodeGroup,
        or edges that connect nodes in different NodeGroups.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_edges (list, optional): List of edges that are selected
        """
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
            # Skip if edge is selected (will be drawn later with highlight)
            if selected_edges and (source_id, target_id) in [
                (e[0].id, e[1].id) for e in selected_edges
            ]:
                continue

            # Skip drawing if both nodes are in the same group
            # These will be drawn by _draw_nodes when rendering each group
            source_in_group = source_id in group_node_ids
            target_in_group = target_id in group_node_ids
            source_group = None
            target_group = None

            # Find which groups the nodes belong to
            for group in self.graph.node_groups:
                if source_id in group.node_ids:
                    source_group = group
                if target_id in group.node_ids:
                    target_group = group

            # Only draw if:
            # 1. Both nodes are in different groups, or
            # 2. At least one node is not in any group
            if source_group != target_group:
                try:
                    source_node = next(n for n in self.graph.nodes if n.id == source_id)
                    target_node = next(n for n in self.graph.nodes if n.id == target_id)
                except StopIteration:
                    continue

                # Calculate actual edge endpoints
                start_point, end_point = self._calculate_edge_endpoints(
                    source_node, target_node
                )

                painter.drawLine(
                    int(start_point.x()),
                    int(start_point.y()),
                    int(end_point.x()),
                    int(end_point.y()),
                )

    def _draw_edges(self, painter: QPainter):
        """
        Draw all edges in the graph.
        This method is kept for backward compatibility but is no longer used directly.
        Consider using _draw_standalone_edges instead.

        Args:
            painter (QPainter): The painter to use for drawing
        """
        edge_color = config.get_color("edge.normal", "#000000")
        pen = QPen(QColor(edge_color))
        pen.setWidth(config.get_dimension("edge.width.normal", 1))
        painter.setPen(pen)

        for source_id, target_id in self.graph.edges:
            # Skip if no node with the specified ID is found
            source_node = None
            target_node = None

            try:
                source_node = next(n for n in self.graph.nodes if n.id == source_id)
            except StopIteration:
                continue

            try:
                target_node = next(n for n in self.graph.nodes if n.id == target_id)
            except StopIteration:
                continue

            if source_node and target_node:
                painter.drawLine(
                    int(source_node.x),
                    int(source_node.y),
                    int(target_node.x),
                    int(target_node.y),
                )

    def _draw_temp_edge(self, painter: QPainter, temp_edge_data):
        """
        Draw temporary edge during edge creation.

        Args:
            painter (QPainter): The painter to use for drawing
            temp_edge_data (tuple): (start_node, end_point)
        """
        start_node, end_point = temp_edge_data
        if start_node and end_point:
            edge_color = config.get_color("edge.normal", "#000000")
            pen = QPen(QColor(edge_color))
            pen.setWidth(config.get_dimension("edge.width.normal", 1))
            painter.setPen(pen)

            # Calculate start point from node boundary
            start_center = QPointF(start_node.x, start_node.y)
            direction = QPointF(end_point) - start_center
            if direction.manhattanLength() > 0:
                # Normalize direction vector
                length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
                normalized_dir = QPointF(direction.x() / length, direction.y() / length)

                # Calculate start point at node boundary
                start_point = QPointF(
                    start_center.x() + normalized_dir.x() * start_node.size / 2,
                    start_center.y() + normalized_dir.y() * start_node.size / 2,
                )

                painter.drawLine(
                    int(start_point.x()),
                    int(start_point.y()),
                    int(end_point.x()),
                    int(end_point.y()),
                )

    def _draw_node_group_backgrounds(self, painter: QPainter):
        """
        Draw only the backgrounds of NodeGroups, ordered by z-index.
        Groups with lower z-index are drawn first, so they appear behind groups with higher z-index.

        Args:
            painter (QPainter): The painter to use for drawing
        """
        # Get selected group IDs
        selected_group_ids = [group.id for group in self.graph.selected_groups]

        # Sort groups by z-index (lowest to highest)
        # This ensures groups with higher z-index are drawn later and appear on top
        sorted_groups = sorted(self.graph.node_groups, key=lambda g: g.z_index)

        # Draw only the background for each group
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

    def _draw_nodes(self, painter: QPainter, all_for_one_selected_nodes=None):
        """
        Draw nodes, group borders, and labels (but not backgrounds).
        Uses z-index ordering to maintain proper visual layering.

        Args:
            painter (QPainter): The painter to use for drawing
            all_for_one_selected_nodes (list, optional): List of nodes selected in All-For-One connection mode
        """
        # Get selected group IDs
        selected_group_ids = [group.id for group in self.graph.selected_groups]

        # Sort groups by z-index (lowest to highest)
        # This ensures groups with higher z-index appear on top
        sorted_groups = sorted(self.graph.node_groups, key=lambda g: g.z_index)

        # Prepare standalone nodes (nodes not belonging to any group)
        standalone_nodes = [
            node
            for node in self.graph.nodes
            if not any(node.id in group.node_ids for group in self.graph.node_groups)
        ]

        # Important: Sort in ascending (lowest) z-index so that groups with higher z-indexes are drawn at the end
        # This will visually display correctly on the front
        sorted_groups_for_drawing = sorted(
            self.graph.node_groups, key=lambda g: g.z_index
        )

        # Draw each group's nodes, borders, and labels
        for group in sorted_groups_for_drawing:
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

            # Convert to integer positions as required
            min_x_int = int(min_x)
            min_y_int = int(min_y)
            group_width_int = int(group_width)
            group_height_int = int(group_height)

            # Draw nodes within the group
            for node in group_nodes:
                rect = QRectF(
                    node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
                )

                # Determine node selection state
                is_node_selected = node in self.graph.selected_nodes
                is_all_for_one_selected = (
                    all_for_one_selected_nodes and node in all_for_one_selected_nodes
                )

                # Fill color based on selection state
                if is_all_for_one_selected:
                    node_fill_color = config.get_color(
                        "node.fill.all_for_one_selected", "#FFA500"
                    )  # Orange for All-For-One connection selection
                elif is_node_selected:
                    node_fill_color = config.get_color(
                        "node.fill.selected", "#ADD8E6"
                    )  # Selected blue
                else:
                    node_fill_color = config.get_color(
                        "node.fill.normal", "skyblue"
                    )  # Normal blue

                node_color = QColor(node_fill_color)
                painter.fillRect(rect, node_color)

                # Draw border based on selection state
                if is_all_for_one_selected:
                    border_color = config.get_color(
                        "node.border.all_for_one_selected", "#FF6600"
                    )  # Dark orange for All-For-One connection selection
                    pen = QPen(QColor(border_color))
                    pen.setWidth(
                        config.get_dimension(
                            "node.border_width.all_for_one_selected", 3
                        )
                    )
                elif is_node_selected:
                    border_color = config.get_color("node.border.selected", "blue")
                    pen = QPen(QColor(border_color))
                    pen.setWidth(config.get_dimension("node.border_width.selected", 2))
                else:
                    border_color = config.get_color("node.border.normal", "gray")
                    pen = QPen(QColor(border_color))
                    pen.setWidth(config.get_dimension("node.border_width.normal", 1))
                painter.setPen(pen)
                painter.drawRect(rect)

                # Draw Node ID
                text_color = config.get_color("node.text", "#000000")
                painter.setPen(QColor(text_color))
                painter.drawText(rect, Qt.AlignCenter, str(node.id))

            # 2. Draw a group border
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

            # 3. Draw a label for the group name
            # Calculate label width (including margins)
            font_metrics = painter.fontMetrics()
            text_margin = config.get_dimension("group.label.text_margin", 10)
            text_width = font_metrics.width(group.name) + text_margin
            half_width = text_width // 2

            # Get label position (pass text width)
            label_x, label_y, alignment = self._get_label_position(
                group, group_nodes, text_width, half_width
            )

            # Set display width and text
            fixed_width = config.get_dimension("group.label.fixed_width", 100)

            if is_selected or group.label_position in [
                group.POSITION_TOP,
                group.POSITION_BOTTOM,
            ]:
                # Use the actual text width for the selected group or top and bottom labels
                display_width = text_width
                display_text = group.name
            else:
                # Fixed width and shortened text for unselected right-positioned labels
                display_width = fixed_width
                display_text = (
                    font_metrics.elidedText(group.name, Qt.ElideRight, fixed_width)
                    if text_width > fixed_width
                    else group.name
                )

            # Draw label background (semi-transparent)
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

            # label_x and label_y are already converted to integers with _get_label_position
            label_x_int = int(label_x)
            label_y_int = int(label_y)
            label_height = config.get_dimension("group.label.height", 20)
            painter.fillRect(
                label_x_int, label_y_int, display_width, label_height, label_bg
            )

            # Draw label border
            painter.setPen(pen_color)
            painter.drawRect(label_x_int, label_y_int, display_width, label_height)

            # Draw group name
            text_color = config.get_color("group.label.text", "#000000")
            painter.setPen(QColor(text_color))
            painter.drawText(
                label_x_int,
                label_y_int,
                display_width,
                label_height,
                Qt.AlignCenter,
                display_text,
            )

        # Draw standalone nodes (nodes not belonging to any group)
        for node in standalone_nodes:
            rect = QRectF(
                node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
            )

            # Determine node selection state
            is_node_selected = node in self.graph.selected_nodes
            is_all_for_one_selected = (
                all_for_one_selected_nodes and node in all_for_one_selected_nodes
            )

            # Fill color based on selection state
            if is_all_for_one_selected:
                node_fill_color = config.get_color(
                    "node.fill.all_for_one_selected", "#FFA500"
                )  # Orange for All-For-One connection selection
            elif is_node_selected:
                node_fill_color = config.get_color(
                    "node.fill.selected", "#ADD8E6"
                )  # Selected blue
            else:
                node_fill_color = config.get_color(
                    "node.fill.normal", "skyblue"
                )  # Normal blue

            node_color = QColor(node_fill_color)
            painter.fillRect(rect, node_color)

            # Draw border based on selection state
            if is_all_for_one_selected:
                border_color = config.get_color(
                    "node.border.all_for_one_selected", "#FF6600"
                )  # Dark orange for All-For-One connection selection
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
            painter.setPen(pen)
            painter.drawRect(rect)

            # ノードIDを描画
            text_color = config.get_color("node.text", "#000000")
            painter.setPen(QColor(text_color))
            painter.drawText(rect, Qt.AlignCenter, str(node.id))

    def _get_label_position(self, group, nodes=None, text_width=0, half_width=0):
        """
        Calculate the position for the group label based on the group's label_position.

        Args:
            group: The node group
            nodes: Optional list of nodes in the group. If not provided, will be retrieved from group.
            text_width: Width of the text in pixels
            half_width: Half of the text width in pixels

        Returns:
            Tuple[int, int, int]: x, y coordinates and alignment flag for the label
        """
        # Get nodes if not provided
        if nodes is None:
            nodes = group.get_nodes(self.graph.nodes)

        if not nodes:
            return (
                0,
                0,
                Qt.AlignCenter,
            )  # Default position if no nodes, now center-aligned

        # Find min/max coordinates of the group
        min_x = min(node.x - node.size / 2 for node in nodes)
        min_y = min(node.y - node.size / 2 for node in nodes)
        max_x = max(node.x + node.size / 2 for node in nodes)
        max_y = max(node.y + node.size / 2 for node in nodes)
        center_x = (min_x + max_x) / 2
        group_width = max_x - min_x

        # Default alignment is center-aligned
        alignment = Qt.AlignCenter

        # Margin to avoid overlapping with dotted lines
        margin = config.get_dimension("group.label.position_margin", 30)

        # Calculate position based on label_position
        if group.label_position == group.POSITION_RIGHT:
            # Calculate dynamic offset based on group width
            dynamic_offset = max(
                margin, group_width * 0.1
            )  # At least margin pixels, or 10% of group width
            return int(max_x + dynamic_offset), int((min_y + max_y) / 2 - 10), alignment
        elif group.label_position == group.POSITION_BOTTOM:
            # Always center the label for top/bottom positions
            return (
                int(center_x - text_width / 2),  # Center the label
                int(max_y + margin),
                alignment,
            )
        else:  # POSITION_TOP as default
            # Always center the label for top/bottom positions
            return (
                int(center_x - text_width / 2),  # Center the label
                int(min_y - margin),
                alignment,
            )

    def _draw_selection_rectangle(self, painter: QPainter, selection_rect_data):
        """
        Draw the selection rectangle during rectangle selection.

        Args:
            painter (QPainter): The painter to use for drawing
            selection_rect_data (dict): Dictionary containing 'start' and 'end' points
        """
        if (
            not selection_rect_data
            or "start" not in selection_rect_data
            or "end" not in selection_rect_data
        ):
            return

        start = selection_rect_data["start"]
        end = selection_rect_data["end"]

        # Determine the selection direction
        left_to_right = start.x() < end.x()

        # Calculate rectangle bounds
        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()

        # Create normalized rectangle (min_x, min_y, width, height)
        min_x = min(x1, x2)
        min_y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        # Set fill color based on selection direction
        if left_to_right:
            # Left-to-right selection (strict containment) - blue
            fill_color = config.get_color(
                "selection.rect.fill.strict", "rgba(0, 0, 255, 40)"
            )
        else:
            # Right-to-left selection (intersection) - green
            fill_color = config.get_color(
                "selection.rect.fill.intersect", "rgba(0, 255, 0, 40)"
            )

        # Set border color and style
        border_color = config.get_color("selection.rect.border", "#000000")

        # Convert to integers for QPainter
        min_x_int = int(min_x)
        min_y_int = int(min_y)
        width_int = int(width)
        height_int = int(height)

        # Fill rectangle with semi-transparent color
        painter.fillRect(
            min_x_int, min_y_int, width_int, height_int, parse_rgba(fill_color)
        )

        # Draw border
        pen = QPen(QColor(border_color))
        pen.setWidth(config.get_dimension("selection.rect.border_width", 1))

        # Use dashed line for right-to-left (intersection) selection
        if not left_to_right:
            pen.setStyle(Qt.DashLine)

        painter.setPen(pen)
        painter.drawRect(min_x_int, min_y_int, width_int, height_int)
