"""
This module contains the Canvas widget for graph visualization.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF

from ..models.graph import Graph
from ..models.rect_node import RectNode


class Canvas(QWidget):
    """
    A custom widget for visualizing and interacting with the graph.

    This widget handles the rendering of nodes and edges, as well as
    user interactions such as dragging nodes and creating edges.
    """

    def __init__(self, parent=None):
        """
        Initialize the canvas widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.graph = Graph()

        # Interaction state
        self.dragging = False
        self.drag_start = None
        self.current_edge_start = None
        self.temp_edge_end = None

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # Set minimum size for better usability
        self.setMinimumHeight(500)

    def paintEvent(self, event):
        """
        Handle the paint event to render the graph.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw canvas border
        self._draw_canvas_border(painter)

        # Draw edges
        self._draw_edges(painter)

        # Draw temporary edge if one is being created
        self._draw_temp_edge(painter)

        # Draw nodes
        self._draw_nodes(painter)

    def _draw_canvas_border(self, painter: QPainter):
        """Draw the canvas border."""
        pen = QPen(QColor("black"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def _draw_edges(self, painter: QPainter):
        """Draw all edges in the graph."""
        for source_id, target_id in self.graph.edges:
            source_node = next(n for n in self.graph.nodes if n.id == source_id)
            target_node = next(n for n in self.graph.nodes if n.id == target_id)
            painter.drawLine(
                int(source_node.x),
                int(source_node.y),
                int(target_node.x),
                int(target_node.y),
            )

    def _draw_temp_edge(self, painter: QPainter):
        """Draw temporary edge during edge creation."""
        if self.current_edge_start and self.temp_edge_end:
            painter.drawLine(
                int(self.current_edge_start.x),
                int(self.current_edge_start.y),
                int(self.temp_edge_end.x()),
                int(self.temp_edge_end.y()),
            )

    def _draw_nodes(self, painter: QPainter):
        """Draw all nodes in the graph."""
        # Draw group labels first
        for i, group in enumerate(self.graph.node_groups):
            if group.nodes:
                # Find the position for the label based on the group's label_position
                label_x, label_y, alignment = self._get_label_position(group)

                # Draw group name
                painter.setPen(QColor("black"))
                painter.drawText(
                    label_x,
                    label_y,
                    100,
                    20,
                    alignment,
                    group.name,
                )

        # Draw nodes
        for node in self.graph.nodes:
            rect = QRectF(
                node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
            )

            # Fill rectangle
            painter.fillRect(rect, QColor("skyblue"))

            # Draw border
            if node in self.graph.selected_nodes:
                pen = QPen(QColor("black"))
                pen.setWidth(2)
            else:
                pen = QPen(QColor("gray"))
                pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Draw node ID
            painter.drawText(rect, Qt.AlignCenter, str(node.id))

    def _get_label_position(self, group):
        """
        Calculate the position for the group label based on the group's label_position.

        Args:
            group: The node group

        Returns:
            Tuple[int, int, int]: x, y coordinates and alignment flag for the label
        """
        # Find min/max coordinates of the group
        min_x = min(node.x - node.size / 2 for node in group.nodes)
        min_y = min(node.y - node.size / 2 for node in group.nodes)
        max_x = max(node.x + node.size / 2 for node in group.nodes)
        max_y = max(node.y + node.size / 2 for node in group.nodes)
        center_x = (min_x + max_x) / 2

        # Default alignment is left-aligned
        alignment = Qt.AlignLeft

        # Calculate position based on label_position
        if group.label_position == group.POSITION_TOP_LEFT:
            return int(min_x), int(min_y - 20), alignment
        elif group.label_position == group.POSITION_TOP_CENTER:
            return int(center_x - 50), int(min_y - 20), Qt.AlignCenter
        elif group.label_position == group.POSITION_TOP_RIGHT:
            return int(max_x - 100), int(min_y - 20), Qt.AlignRight
        elif group.label_position == group.POSITION_BOTTOM_LEFT:
            return int(min_x), int(max_y + 5), alignment
        elif group.label_position == group.POSITION_BOTTOM_CENTER:
            return int(center_x - 50), int(max_y + 5), Qt.AlignCenter
        elif group.label_position == group.POSITION_BOTTOM_RIGHT:
            return int(max_x - 100), int(max_y + 5), Qt.AlignRight
        else:
            # Default to top-left
            return int(min_x), int(min_y - 20), alignment

    def mousePressEvent(self, event):
        """
        Handle mouse press events for node selection and edge creation.

        Args:
            event: Mouse event
        """
        point = event.pos()

        if event.button() == Qt.LeftButton:
            node = self.graph.find_node_at_position(point)
            if node:
                self.dragging = True
                self.drag_start = point
                group = self.graph.get_group_for_node(node)
                if group:
                    self.graph.selected_nodes = group.nodes
                    self.graph.selected_group = group
                self.update()
            else:
                # Deselect if clicking on empty space
                self.graph.selected_nodes = []
                self.graph.selected_group = None
                self.update()

        elif event.button() == Qt.RightButton:
            node = self.graph.find_node_at_position(point)
            if node:
                self.current_edge_start = node
                self.temp_edge_end = point

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events for node dragging and edge preview.

        Args:
            event: Mouse event
        """
        point = event.pos()

        if self.dragging and self.drag_start:
            dx = point.x() - self.drag_start.x()
            dy = point.y() - self.drag_start.y()

            for node in self.graph.selected_nodes:
                node.move(dx, dy)

            self.drag_start = point
            self.update()

        elif self.current_edge_start:
            self.temp_edge_end = point
            self.update()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events to complete dragging or edge creation.

        Args:
            event: Mouse event
        """
        point = event.pos()

        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.drag_start = None

        elif event.button() == Qt.RightButton and self.current_edge_start:
            target_node = self.graph.find_node_at_position(point)
            if target_node and target_node != self.current_edge_start:
                self.graph.add_edge(self.current_edge_start, target_node)

            self.current_edge_start = None
            self.temp_edge_end = None
            self.update()
