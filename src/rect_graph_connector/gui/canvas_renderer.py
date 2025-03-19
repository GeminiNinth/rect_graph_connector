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

        # 新しい描画順序（視覚的な前後関係）：
        # 1. 背景（最背面）- canvas_border (すでに描画済み)
        # 2. グループに属さないエッジを描画（最背面）
        # 3. NodeGroupごとに以下を描画（z-indexの低い順）
        #    a. グループの背景
        #    b. グループ内の通常エッジ (グループごとに分けて描画)
        #    c. グループのノード、枠線、ラベル
        # 4. 独立したノード（グループに属さないノード）
        # 5. ナイフツールのハイライトエッジ (最前面に表示するため、他の要素より後に描画)
        # 6. 一時的なエッジ (新規エッジ作成時)
        # 7. Knifeツールのパス (最前面)

        # グループに属さないエッジを描画（最背面）
        self._draw_standalone_edges(painter)

        # NodeGroupの背景を描画
        self._draw_node_group_backgrounds(painter)

        # グループのノード、枠線、ラベルを描画（z-indexの順）- ハイライトエッジは描画しない
        self._draw_nodes(painter)

        # ナイフツールで選択されたエッジを描画（最前面の手前）
        if knife_data and knife_data.get("highlighted_edges"):
            self._draw_highlighted_edges(painter, knife_data.get("highlighted_edges"))

        # 一時的なエッジを描画
        if temp_edge_data:
            self._draw_temp_edge(painter, temp_edge_data)

        # Knifeツールのパスを描画（最前面）
        if knife_data and knife_data.get("path"):
            self._draw_knife_path(painter, knife_data["path"])

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
        pen.setWidth(
            config.get_dimension("canvas.border_width", 2)
        )  # 設定ファイルから取得
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
        for source_id, target_id in highlighted_edges:
            try:
                source_node = next(n for n in self.graph.nodes if n.id == source_id)
                target_node = next(n for n in self.graph.nodes if n.id == target_id)

                # Draw the highlighted edge
                painter.drawLine(
                    int(source_node.x),
                    int(source_node.y),
                    int(target_node.x),
                    int(target_node.y),
                )
            except StopIteration:
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

    def _draw_standalone_edges(self, painter: QPainter):
        """
        Draw edges between nodes that don't belong to any NodeGroup,
        or edges that connect nodes in different NodeGroups.

        Args:
            painter (QPainter): The painter to use for drawing
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

                painter.drawLine(
                    int(source_node.x),
                    int(source_node.y),
                    int(target_node.x),
                    int(target_node.y),
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

            painter.drawLine(
                int(start_node.x),
                int(start_node.y),
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

    def _draw_nodes(self, painter: QPainter):
        """
        Draw nodes, group borders, and labels (but not backgrounds).
        Uses z-index ordering to maintain proper visual layering.

        Args:
            painter (QPainter): The painter to use for drawing
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

        # 重要: z-indexの昇順（低い順）にソートして、高いz-indexのグループが最後に描画されるようにする
        # これにより視覚的に正しく前面に表示される
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

            # Draw normal edges within the group
            edge_color = config.get_color("edge.normal", "#000000")
            pen = QPen(QColor(edge_color))
            pen.setWidth(config.get_dimension("edge.width.normal", 1))
            painter.setPen(pen)

            for source_id, target_id in self.graph.edges:
                # Only draw edges where both nodes belong to this group
                if source_id in group.node_ids and target_id in group.node_ids:
                    try:
                        source_node = next(
                            n for n in self.graph.nodes if n.id == source_id
                        )
                        target_node = next(
                            n for n in self.graph.nodes if n.id == target_id
                        )

                        painter.drawLine(
                            int(source_node.x),
                            int(source_node.y),
                            int(target_node.x),
                            int(target_node.y),
                        )
                    except StopIteration:
                        continue

            # 1. Draw nodes within the group (they appear on top)
            for node in group_nodes:
                rect = QRectF(
                    node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
                )

                # 選択されたノードは異なる色で表示
                is_node_selected = node in self.graph.selected_nodes
                node_fill_color = (
                    config.get_color("node.fill.selected", "#ADD8E6")
                    if is_node_selected
                    else config.get_color("node.fill.normal", "skyblue")
                )
                node_color = QColor(node_fill_color)
                painter.fillRect(rect, node_color)

                # 枠線を描画
                if is_node_selected:
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

            # 2. グループの枠線を描画
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

            # 3. グループ名のラベルを描画
            # ラベルの幅を計算（余白を含む）
            font_metrics = painter.fontMetrics()
            text_margin = config.get_dimension("group.label.text_margin", 10)
            text_width = font_metrics.width(group.name) + text_margin
            half_width = text_width // 2

            # ラベル位置を取得（テキスト幅を渡す）
            label_x, label_y, alignment = self._get_label_position(
                group, group_nodes, text_width, half_width
            )

            # 表示幅とテキストを設定
            fixed_width = config.get_dimension("group.label.fixed_width", 100)

            if is_selected or group.label_position in [
                group.POSITION_TOP,
                group.POSITION_BOTTOM,
            ]:
                # 選択されたグループまたは上下のラベルには実際のテキスト幅を使用
                display_width = text_width
                display_text = group.name
            else:
                # 固定幅と短縮テキストを未選択の右配置ラベルに使用
                display_width = fixed_width
                display_text = (
                    font_metrics.elidedText(group.name, Qt.ElideRight, fixed_width)
                    if text_width > fixed_width
                    else group.name
                )

            # ラベルの背景を描画（半透明）
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

            # label_xとlabel_yはすでに_get_label_positionで整数に変換されている
            label_x_int = int(label_x)
            label_y_int = int(label_y)
            label_height = config.get_dimension("group.label.height", 20)
            painter.fillRect(
                label_x_int, label_y_int, display_width, label_height, label_bg
            )

            # ラベルの枠線を描画
            painter.setPen(pen_color)
            painter.drawRect(label_x_int, label_y_int, display_width, label_height)

            # グループ名を描画
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

        # グループに属さないノードを描画（最前面）
        for node in standalone_nodes:
            rect = QRectF(
                node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
            )

            # 選択されたノードは異なる色で表示
            is_selected = node in self.graph.selected_nodes
            node_fill_color = (
                config.get_color("node.fill.selected", "#ADD8E6")
                if is_selected
                else config.get_color("node.fill.normal", "skyblue")
            )
            node_color = QColor(node_fill_color)
            painter.fillRect(rect, node_color)

            # 枠線を描画
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
