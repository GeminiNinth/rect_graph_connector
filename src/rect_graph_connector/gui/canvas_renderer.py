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

        # Draw edges (with highlighting if in knife mode)
        if knife_data and knife_data.get("highlighted_edges"):
            self._draw_edges_with_highlight(painter, knife_data["highlighted_edges"])
        else:
            self._draw_edges(painter)

        # Draw temporary edge if provided
        if temp_edge_data:
            self._draw_temp_edge(painter, temp_edge_data)

        # Draw knife path if in knife mode
        if knife_data and knife_data.get("path"):
            self._draw_knife_path(painter, knife_data["path"])

        # Draw nodes
        self._draw_nodes(painter)

        # Restore painter state
        painter.restore()

        # Draw mode indicator if needed
        # self._draw_mode_indicator(painter, mode, edit_target_group)
        # Draw mode indicator if needed
        # self._draw_mode_indicator(painter, mode, edit_target_group)

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
        pen.setWidth(
            config.get_dimension("canvas.border_width", 2)
        )  # 設定ファイルから取得
        painter.setPen(pen)
        painter.drawRect(0, 0, self.canvas.width() - 1, self.canvas.height() - 1)

    def _draw_edges_with_highlight(self, painter: QPainter, highlighted_edges):
        """
        Draw all edges with highlighted edges in a different color.

        Args:
            painter (QPainter): The painter to use for drawing
            highlighted_edges (List[Tuple[str, str]]): List of edge tuples to highlight
        """
        # First draw all edges normally
        pen = painter.pen()
        for source_id, target_id in self.graph.edges:
            try:
                source_node = next(n for n in self.graph.nodes if n.id == source_id)
                target_node = next(n for n in self.graph.nodes if n.id == target_id)
            except StopIteration:
                continue

            if (source_id, target_id) in highlighted_edges:
                # Highlight edge in red
                edge_color = config.get_color("edge.highlighted", "#FF0000")
                edge_width = config.get_dimension("edge.width.highlighted", 2)
                painter.setPen(QPen(QColor(edge_color), edge_width))
            else:
                # Normal edge in black
                painter.setPen(pen)

            painter.drawLine(
                int(source_node.x),
                int(source_node.y),
                int(target_node.x),
                int(target_node.y),
            )

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

    def _draw_edges(self, painter: QPainter):
        """
        Draw all edges in the graph.

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

            painter.drawLine(
                int(start_node.x),
                int(start_node.y),
                int(end_point.x()),
                int(end_point.y()),
            )

    def _draw_nodes(self, painter: QPainter):
        """
        Draw all nodes and node groups in the graph.

        Args:
            painter (QPainter): The painter to use for drawing
        """
        # Identify the selected groups
        selected_group_ids = []
        # Add from multi-selection only
        for group in self.graph.selected_groups:
            if group.id not in selected_group_ids:
                selected_group_ids.append(group.id)

        # Draw group frames and labels
        for group in self.graph.node_groups:
            group_nodes = group.get_nodes(self.graph.nodes)
            if not group_nodes:
                continue

            # Calculate group boundaries
            border_margin = config.get_dimension("group.border_margin", 5)
            min_x = min(node.x - node.size / 2 for node in group_nodes) - border_margin
            min_y = min(node.y - node.size / 2 for node in group_nodes) - border_margin
            max_x = max(node.x + node.size / 2 for node in group_nodes) + border_margin
            max_y = max(node.y + node.size / 2 for node in group_nodes) + border_margin
            group_width = max_x - min_x
            group_height = max_y - min_y

            # Selected groups are displayed with special styling
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

            # The position must be specified as an integer
            min_x_int = int(min_x)
            min_y_int = int(min_y)
            group_width_int = int(group_width)
            group_height_int = int(group_height)
            painter.fillRect(
                min_x_int, min_y_int, group_width_int, group_height_int, bg_color
            )

            # Draw a group frame
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

            # Calculate the width of the group name (gives some room)
            font_metrics = painter.fontMetrics()
            text_margin = config.get_dimension("group.label.text_margin", 10)
            text_width = font_metrics.width(group.name) + text_margin
            half_width = text_width // 2

            # Get label position (pass text width)
            label_x, label_y, alignment = self._get_label_position(
                group, group_nodes, text_width, half_width
            )

            # Get group width
            group_width_int = int(group_width)

            # Set the display width
            # Fixed width when not selected
            # When selected, the width is based on the number of characters (minimum width is fixed width)
            fixed_width = config.get_dimension("group.label.fixed_width", 100)

            if is_selected:
                # When selected, the width is based on the number of characters (minimum width is fixed width)
                display_width = max(text_width, fixed_width)
            else:
                # Fixed width when not selected
                display_width = fixed_width

            # Determine the text to be displayed (whole displays when selected, omits if necessary)
            display_text = group.name
            if not is_selected and text_width > fixed_width:
                display_text = font_metrics.elidedText(
                    group.name, Qt.ElideRight, fixed_width
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

            # label_x and label_y have already been converted to int in _get_label_position
            label_x_int = int(label_x)
            label_y_int = int(label_y)
            label_height = config.get_dimension("group.label.height", 20)
            painter.fillRect(
                label_x_int, label_y_int, display_width, label_height, label_bg
            )

            # Draw label frame
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

        # Draw all nodes
        for node in self.graph.nodes:
            rect = QRectF(
                node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
            )

            # Selected nodes are displayed in different colors
            is_selected = node in self.graph.selected_nodes
            node_fill_color = (
                config.get_color("node.fill.selected", "#ADD8E6")
                if is_selected
                else config.get_color("node.fill.normal", "skyblue")
            )
            node_color = QColor(node_fill_color)
            painter.fillRect(rect, node_color)

            # Draw a frame
            if is_selected:
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

        # Default alignment is center-aligned
        alignment = Qt.AlignCenter

        # Margin to avoid overlapping with dotted lines
        margin = config.get_dimension("group.label.position_margin", 30)
        label_offset = config.get_dimension("group.label.position_offset", 50)

        # Calculate position based on label_position
        if group.label_position == group.POSITION_RIGHT:
            # Normally displayed on the right of NodeGroups
            return int(max_x + margin), int((min_y + max_y) / 2 - 10), alignment
        elif group.label_position == group.POSITION_BOTTOM:
            # Place directly below the group (fixed position)
            return (
                int(center_x - label_offset / 2),
                int(max_y + margin),
                alignment,
            )
        else:  # POSITION_TOP as default
            # Displays in the same position when selected or not selected
            return (
                int(center_x - label_offset / 2),
                int(min_y - margin),
                alignment,
            )
