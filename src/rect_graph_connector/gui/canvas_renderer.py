"""
This module contains the renderer for the canvas, handling all drawing operations.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF

from ..models.graph import Graph


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
    ):
        """
        Draw the complete graph on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            mode (str): The current mode ("normal" or "edit")
            temp_edge_data (tuple, optional): Temporary edge data (start_node, end_point)
            edit_target_group: The group being edited in edit mode (for backwards compatibility)
            edit_target_groups: List of groups being edited in edit mode (for multi-selection)
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

        # Draw edges
        self._draw_edges(painter)

        # Draw temporary edge if provided
        if temp_edge_data:
            self._draw_temp_edge(painter, temp_edge_data)

        # Draw nodes
        self._draw_nodes(painter)

        # Restore painter state
        painter.restore()

        # Draw mode indicator if needed
        # self._draw_mode_indicator(painter, mode, edit_target_group)

    def _draw_canvas_border(self, painter: QPainter, mode: str):
        """
        Draw the canvas border with mode-specific color.

        Args:
            painter (QPainter): The painter to use for drawing
            mode (str): The current mode ("normal" or "edit")
        """
        # Set border color according to the mode
        if mode == "edit":
            pen = QPen(QColor(255, 100, 100))  # Edit mode is reddish
        else:
            pen = QPen(QColor("black"))

        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.canvas.width() - 1, self.canvas.height() - 1)

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
        text = f"Mode: {mode}"
        if mode == "edit" and edit_target_group:
            text += f" (Editing: {edit_target_group.name})"

        painter.setPen(QColor("black"))
        painter.drawText(10, 20, text)

    def _draw_edges(self, painter: QPainter):
        """
        Draw all edges in the graph.

        Args:
            painter (QPainter): The painter to use for drawing
        """
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
        # Add from single selection (for backwards compatibility)
        if self.graph.selected_group:
            selected_group_ids.append(self.graph.selected_group.id)
        # Add from multi-selection
        for group in self.graph.selected_groups:
            if group.id not in selected_group_ids:
                selected_group_ids.append(group.id)

        # Draw group frames and labels
        for group in self.graph.node_groups:
            group_nodes = group.get_nodes(self.graph.nodes)
            if not group_nodes:
                continue

            # Calculate group boundaries
            min_x = min(node.x - node.size / 2 for node in group_nodes) - 5
            min_y = min(node.y - node.size / 2 for node in group_nodes) - 5
            max_x = max(node.x + node.size / 2 for node in group_nodes) + 5
            max_y = max(node.y + node.size / 2 for node in group_nodes) + 5
            group_width = max_x - min_x
            group_height = max_y - min_y

            # Selected groups are displayed with special styling
            is_selected = group.id in selected_group_ids

            # Draw group background (semi-transparent)
            bg_color = (
                QColor(230, 230, 255, 40) if is_selected else QColor(245, 245, 245, 20)
            )
            # The position must be specified as an integer
            min_x_int = int(min_x)
            min_y_int = int(min_y)
            group_width_int = int(group_width)
            group_height_int = int(group_height)
            painter.fillRect(
                min_x_int, min_y_int, group_width_int, group_height_int, bg_color
            )

            # Draw a group frame
            pen_color = QColor(100, 100, 255) if is_selected else QColor(200, 200, 200)
            pen = QPen(pen_color)
            pen.setWidth(2 if is_selected else 1)
            pen.setStyle(Qt.DashLine if not is_selected else Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(min_x_int, min_y_int, group_width_int, group_height_int)

            # Calculate the width of the group name (gives some room)
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.width(group.name) + 10  # 10px margin
            half_width = text_width // 2

            # Get label position (pass text width)
            label_x, label_y, alignment = self._get_label_position(
                group, group_nodes, text_width, half_width
            )

            # Get group width
            group_width_int = int(group_width)

            # Set the display width
            # Fixed width (100px) when not selected
            # When selected, the width is based on the number of characters (minimum width is 100px)
            fixed_width = 100  # Fixed width

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
            label_bg = (
                QColor(240, 240, 255, 200)
                if is_selected
                else QColor(240, 240, 240, 180)
            )
            # label_x and label_y have already been converted to int using the _get_label_position method
            label_x_int = int(label_x)
            label_y_int = int(label_y)
            painter.fillRect(label_x_int, label_y_int, display_width, 20, label_bg)

            # Draw label frame
            painter.setPen(pen_color)
            painter.drawRect(label_x_int, label_y_int, display_width, 20)

            # Draw group name
            painter.setPen(QColor("black"))
            painter.drawText(
                label_x_int,
                label_y_int,
                display_width,
                20,
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
            node_color = QColor(173, 216, 230) if is_selected else QColor("skyblue")
            painter.fillRect(rect, node_color)

            # Draw a frame
            if is_selected:
                pen = QPen(QColor("blue"))
                pen.setWidth(2)
            else:
                pen = QPen(QColor("gray"))
                pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Draw Node ID
            painter.setPen(QColor("black"))
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
        margin = 30

        # Calculate position based on label_position
        if group.label_position == group.POSITION_RIGHT:
            # Normally displayed on the right of NodeGroups
            return int(max_x + margin), int((min_y + max_y) / 2 - 10), alignment
        elif group.label_position == group.POSITION_BOTTOM:
            # Place directly below the group (fixed position)
            return (
                int(center_x - 50),
                int(max_y + margin),
                alignment,
            )  # Draw half of the fixed width (50px)
        else:  # POSITION_TOP as default
            # Displays in the same position when selected or not selected
            return (
                int(center_x - 50),
                int(min_y - margin),
                alignment,
            )  # Draw half of the fixed width (50px)
