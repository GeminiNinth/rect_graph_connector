"""
This module contains the bridge connection settings window.

The window allows the user to configure the bridge connections between
two node groups, including connection counts and edge node selection.
"""

from typing import Dict, List, Optional, Set, Tuple, Callable

from PyQt5.QtCore import Qt, QPointF, QRectF, QSize, pyqtSignal, pyqtProperty, QPoint
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QFont,
    QFontMetrics,
    QPalette,
    QBrush,
    QLinearGradient,
)
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
    QScrollArea,
    QFrame,
    QApplication,
)

from ..config import config
from ..models.graph import Graph, NodeGroup
from ..models.node import BaseNode
from ..models.bridge_connector import BridgeConnector, BridgeConnectionParams
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


class NodeView(QWidget):
    """
    A custom widget to render and interact with nodes in the bridge window.

    This widget displays nodes from a NodeGroup and allows highlighting
    edge nodes for bridge connections.
    """

    node_clicked = pyqtSignal(object)  # Signal emitted when a node is clicked

    def __init__(self, parent=None):
        """Initialize the node view widget."""
        super().__init__(parent)
        self.nodes = []  # List of nodes to display
        self.edge_nodes = []  # List of edge nodes to highlight
        self.connections = []  # List of (source, target) connections to display
        self.node_size = 15  # Size of nodes in the view
        self.highlight_position = BridgeConnector.POS_ROW_FIRST
        self.theme = "light"  # Current theme

        # Enable mouse tracking
        self.setMouseTracking(True)

        # Set minimum size
        self.setMinimumSize(200, 200)

        # Colors
        self._update_colors()

    def _update_colors(self):
        """Update colors based on the current theme."""
        if self.theme == "dark":
            self.node_fill_color = QColor(
                config.get_color("node.fill.normal", "#3399CC", theme="dark")
            )
            self.node_border_color = QColor(
                config.get_color("node.border.normal", "#999999", theme="dark")
            )
            self.highlight_fill_color = QColor(
                config.get_color(
                    "node.fill.bridge_highlighted",
                    "rgba(255, 165, 0, 220)",
                    theme="dark",
                )
            )
            self.highlight_border_color = QColor(
                config.get_color(
                    "node.border.bridge_highlighted", "#FFA500", theme="dark"
                )
            )
            self.connection_color = QColor(
                config.get_color(
                    "bridge.window.node_area.connection_line", "#6495ED", theme="dark"
                )
            )
            self.bg_color = QColor(
                config.get_color(
                    "bridge.window.node_area.background", "#303030", theme="dark"
                )
            )
        else:
            self.node_fill_color = QColor(
                config.get_color("node.fill.normal", "skyblue")
            )
            self.node_border_color = QColor(
                config.get_color("node.border.normal", "gray")
            )
            self.highlight_fill_color = QColor(
                config.get_color(
                    "node.fill.bridge_highlighted", "rgba(255, 165, 0, 200)"
                )
            )
            self.highlight_border_color = QColor(
                config.get_color("node.border.bridge_highlighted", "#FF8C00")
            )
            self.connection_color = QColor(
                config.get_color("bridge.window.node_area.connection_line", "#6495ED")
            )
            self.bg_color = QColor(
                config.get_color("bridge.window.node_area.background", "#F5F5F5")
            )

    def set_theme(self, theme: str):
        """
        Set the color theme for the node view.

        Args:
            theme: The theme to use ('light' or 'dark')
        """
        self.theme = theme
        self._update_colors()
        self.update()

    def set_nodes(self, nodes: List[BaseNode]):
        """
        Set the nodes to display.

        Args:
            nodes: List of nodes to display
        """
        self.nodes = nodes
        self.update()

    def set_edge_nodes(self, edge_nodes: List[BaseNode], highlight_position: str):
        """
        Set the edge nodes to highlight.

        Args:
            edge_nodes: List of edge nodes to highlight
            highlight_position: The highlight position used
        """
        self.edge_nodes = edge_nodes
        self.highlight_position = highlight_position
        self.update()

    def set_connections(self, connections: List[Tuple[QPointF, QPointF]]):
        """
        Set the connections to display.

        Args:
            connections: List of (source, target) point pairs for connections
        """
        self.connections = connections
        self.update()

    def paintEvent(self, event):
        """
        Handle the paint event to render nodes and connections.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), self.bg_color)

        # Draw connections
        self._draw_connections(painter)

        # Draw nodes
        self._draw_nodes(painter)

    def _draw_connections(self, painter: QPainter):
        """
        Draw the connection lines.

        Args:
            painter: The painter to draw with
        """
        if not self.connections:
            return

        # Set up pen for connections
        pen = QPen(self.connection_color, 1.5, Qt.DashLine)
        painter.setPen(pen)

        # Get node positions in view coordinates
        node_positions = self._get_node_positions()

        # Draw each connection
        for source_point, target_point in self.connections:
            # Map the graph coordinates to view coordinates
            source_view_pos = self._map_to_view(source_point)
            target_view_pos = self._map_to_view(target_point)

            painter.drawLine(source_view_pos, target_view_pos)

    def _draw_nodes(self, painter: QPainter):
        """
        Draw the nodes.

        Args:
            painter: The painter to draw with
        """
        if not self.nodes:
            return

        # Get node positions in view coordinates
        node_positions = self._get_node_positions()

        # Draw each node
        for i, node in enumerate(self.nodes):
            is_edge_node = node in self.edge_nodes

            # Set colors based on whether it's an edge node
            fill_color = (
                self.highlight_fill_color if is_edge_node else self.node_fill_color
            )
            border_color = (
                self.highlight_border_color if is_edge_node else self.node_border_color
            )

            # Draw the node
            center = node_positions[i]
            radius = self.node_size / 2

            # Fill circle
            painter.setBrush(QBrush(fill_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)

            # Draw border
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(border_color, 1.5))
            painter.drawEllipse(center, radius, radius)

            # Draw node ID
            painter.setPen(QPen(Qt.black if self.theme == "light" else Qt.white, 1))
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            id_text = str(node.id)
            text_rect = QRectF(
                center.x() - radius, center.y() - radius, radius * 2, radius * 2
            )
            painter.drawText(text_rect, Qt.AlignCenter, id_text)

    def _get_node_positions(self) -> List[QPointF]:
        """
        Calculate positions for all nodes in view coordinates.

        Returns:
            List of node positions in view coordinates
        """
        if not self.nodes:
            return []

        # Calculate the bounds of all nodes in graph coordinates
        min_x = min(node.x for node in self.nodes)
        max_x = max(node.x for node in self.nodes)
        min_y = min(node.y for node in self.nodes)
        max_y = max(node.y for node in self.nodes)

        # Add some margin
        margin = 20
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin

        # Calculate scale factors
        graph_width = max(max_x - min_x, 1)
        graph_height = max(max_y - min_y, 1)

        scale_x = width / graph_width
        scale_y = height / graph_height

        # Use the smaller scale to maintain aspect ratio
        scale = min(scale_x, scale_y)

        # Calculate positions
        positions = []
        for node in self.nodes:
            x = margin + (node.x - min_x) * scale
            y = margin + (node.y - min_y) * scale
            positions.append(QPointF(x, y))

        return positions

    def _map_to_view(self, point: QPointF) -> QPointF:
        """
        Map a point from graph coordinates to view coordinates.

        Args:
            point: Point in graph coordinates

        Returns:
            Point in view coordinates
        """
        if not self.nodes:
            return QPointF(0, 0)

        # Calculate the bounds of all nodes in graph coordinates
        min_x = min(node.x for node in self.nodes)
        max_x = max(node.x for node in self.nodes)
        min_y = min(node.y for node in self.nodes)
        max_y = max(node.y for node in self.nodes)

        # Add some margin
        margin = 20
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin

        # Calculate scale factors
        graph_width = max(max_x - min_x, 1)
        graph_height = max(max_y - min_y, 1)

        scale_x = width / graph_width
        scale_y = height / graph_height

        # Use the smaller scale to maintain aspect ratio
        scale = min(scale_x, scale_y)

        # Map the point
        x = margin + (point.x() - min_x) * scale
        y = margin + (point.y() - min_y) * scale

        return QPointF(x, y)

    def mousePressEvent(self, event):
        """
        Handle mouse press events for node selection.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            # Get node positions
            node_positions = self._get_node_positions()

            # Check if a node was clicked
            for i, pos in enumerate(node_positions):
                # Check if click is within node radius
                if (pos - event.pos()).manhattanLength() <= self.node_size:
                    # Emit signal with the clicked node
                    self.node_clicked.emit(self.nodes[i])
                    break


class BridgeConnectionWindow(QDialog):
    """
    Dialog window for configuring bridge connections between two node groups.

    This window allows the user to set connection counts and preview the connections
    before applying them to the graph.
    """

    def __init__(self, graph: Graph, parent=None):
        """
        Initialize the bridge connection window.

        Args:
            graph: The graph to operate on
            parent: Parent widget
        """
        super().__init__(parent)
        self.graph = graph
        self.bridge_connector = BridgeConnector(graph)

        # Initialize parameters
        self.source_group = None
        self.target_group = None
        self.params = BridgeConnectionParams()

        # Initialize UI
        self._setup_ui()

        # Set window properties
        title = config.get_string(
            "bridge_connection.window.title", "Bridge Connection Settings"
        )
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)

        # Set theme based on system
        self.theme = "light"
        self._update_theme()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)

        # Add a title label
        title_label = QLabel(self.windowTitle())
        title_font = title_label.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Node groups info
        groups_layout = QHBoxLayout()

        # Source group label
        source_label_text = config.get_string(
            "bridge_connection.window.source_group", "Source Group:"
        )
        self.source_label = QLabel(f"{source_label_text} N/A")
        groups_layout.addWidget(self.source_label)

        groups_layout.addStretch()

        # Target group label
        target_label_text = config.get_string(
            "bridge_connection.window.target_group", "Target Group:"
        )
        self.target_label = QLabel(f"{target_label_text} N/A")
        groups_layout.addWidget(self.target_label)

        main_layout.addLayout(groups_layout)

        # Connection counts
        counts_layout = QHBoxLayout()

        # Source to target count
        self.source_to_target_layout = QHBoxLayout()
        self.source_to_target_label = QLabel("Source → Target connections:")
        self.source_to_target_spinbox = QSpinBox()
        self.source_to_target_spinbox.setMinimum(
            config.get_constant("bridge_connection.min_connections", 1)
        )
        self.source_to_target_spinbox.setMaximum(
            config.get_constant("bridge_connection.max_connections", 10)
        )
        self.source_to_target_spinbox.setValue(1)
        self.source_to_target_spinbox.valueChanged.connect(self._update_preview)

        self.source_to_target_layout.addWidget(self.source_to_target_label)
        self.source_to_target_layout.addWidget(self.source_to_target_spinbox)
        counts_layout.addLayout(self.source_to_target_layout)

        counts_layout.addStretch()

        # Target to source count
        self.target_to_source_layout = QHBoxLayout()
        self.target_to_source_label = QLabel("← Target → Source connections:")
        self.target_to_source_spinbox = QSpinBox()
        self.target_to_source_spinbox.setMinimum(
            config.get_constant("bridge_connection.min_connections", 1)
        )
        self.target_to_source_spinbox.setMaximum(
            config.get_constant("bridge_connection.max_connections", 10)
        )
        self.target_to_source_spinbox.setValue(1)
        self.target_to_source_spinbox.valueChanged.connect(self._update_preview)

        self.target_to_source_layout.addWidget(self.target_to_source_label)
        self.target_to_source_layout.addWidget(self.target_to_source_spinbox)
        counts_layout.addLayout(self.target_to_source_layout)

        main_layout.addLayout(counts_layout)

        # Node views
        views_layout = QHBoxLayout()

        # Source node view
        self.source_view = NodeView()
        source_view_label = QLabel(
            config.get_string(
                "bridge_connection.window.node_selection.source_title", "Source Nodes"
            )
        )
        source_view_label.setAlignment(Qt.AlignCenter)

        source_view_container = QVBoxLayout()
        source_view_container.addWidget(source_view_label)
        source_view_container.addWidget(self.source_view)

        views_layout.addLayout(source_view_container)

        # Target node view
        self.target_view = NodeView()
        target_view_label = QLabel(
            config.get_string(
                "bridge_connection.window.node_selection.target_title", "Target Nodes"
            )
        )
        target_view_label.setAlignment(Qt.AlignCenter)

        target_view_container = QVBoxLayout()
        target_view_container.addWidget(target_view_label)
        target_view_container.addWidget(self.target_view)

        views_layout.addLayout(target_view_container)

        main_layout.addLayout(views_layout, 1)

        # Buttons
        button_layout = QHBoxLayout()

        # Apply button
        apply_text = config.get_string("bridge_connection.window.apply", "Apply")
        self.apply_button = QPushButton(apply_text)
        self.apply_button.clicked.connect(self._apply_connections)

        # Cancel button
        cancel_text = config.get_string("bridge_connection.window.cancel", "Cancel")
        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def _update_theme(self):
        """Update UI elements based on current theme."""
        # Update node views
        self.source_view.set_theme(self.theme)
        self.target_view.set_theme(self.theme)

        # Update labels and backgrounds based on theme
        if self.theme == "dark":
            bg_color = QColor(
                config.get_color(
                    "bridge.window.background", "rgba(40, 40, 40, 240)", theme="dark"
                )
            )
            text_color = Qt.white

            # Set window background
            self.setAutoFillBackground(True)
            palette = self.palette()
            palette.setColor(QPalette.Window, bg_color)
            palette.setColor(QPalette.WindowText, text_color)
            palette.setColor(QPalette.Text, text_color)
            self.setPalette(palette)

            # Update spinbox colors
            spinbox_bg = QColor(
                config.get_color(
                    "bridge.window.controls.counter.background", "#404040", theme="dark"
                )
            )
            spinbox_text = QColor(
                config.get_color(
                    "bridge.window.controls.counter.text", "#FFFFFF", theme="dark"
                )
            )

            for spinbox in [
                self.source_to_target_spinbox,
                self.target_to_source_spinbox,
            ]:
                spinbox_palette = spinbox.palette()
                spinbox_palette.setColor(QPalette.Base, spinbox_bg)
                spinbox_palette.setColor(QPalette.Text, spinbox_text)
                spinbox.setPalette(spinbox_palette)
        else:
            # Light theme (default)
            bg_color = QColor(
                config.get_color("bridge.window.background", "rgba(255, 255, 255, 240)")
            )
            text_color = Qt.black

            # Reset to default palette
            self.setPalette(QApplication.style().standardPalette())

    def set_groups(self, source_group: NodeGroup, target_group: NodeGroup):
        """
        Set the node groups to configure bridge connections for.

        Args:
            source_group: The source node group
            target_group: The target node group
        """
        self.source_group = source_group
        self.target_group = target_group

        # Update labels
        source_label_text = config.get_string(
            "bridge_connection.window.source_group", "Source Group:"
        )
        self.source_label.setText(f"{source_label_text} {source_group.name}")

        target_label_text = config.get_string(
            "bridge_connection.window.target_group", "Target Group:"
        )
        self.target_label.setText(f"{target_label_text} {target_group.name}")

        # Update connection count labels with group names
        source_to_target_text = config.get_string(
            "bridge_connection.window.connection_counts.source_to_target_label",
            "{source} → {target} connections:",
        )
        source_to_target_text = source_to_target_text.format(
            source=source_group.name, target=target_group.name
        )
        self.source_to_target_label.setText(source_to_target_text)

        target_to_source_text = config.get_string(
            "bridge_connection.window.connection_counts.target_to_source_label",
            "← {target} → {source} connections:",
        )
        target_to_source_text = target_to_source_text.format(
            source=source_group.name, target=target_group.name
        )
        self.target_to_source_label.setText(target_to_source_text)

        # Set nodes in views
        source_nodes = source_group.get_nodes(self.graph.nodes)
        target_nodes = target_group.get_nodes(self.graph.nodes)

        self.source_view.set_nodes(source_nodes)
        self.target_view.set_nodes(target_nodes)

        # Set initial edge nodes
        self._update_edge_nodes()

        # Update preview
        self._update_preview()

    def _update_edge_nodes(self):
        """Update the edge nodes in the views based on highlight positions."""
        if not self.source_group or not self.target_group:
            return

        # Get edge nodes
        source_nodes = self.bridge_connector._get_edge_nodes(
            self.source_group, self.params.source_highlight_pos
        )
        target_nodes = self.bridge_connector._get_edge_nodes(
            self.target_group, self.params.target_highlight_pos
        )

        # Update views
        self.source_view.set_edge_nodes(source_nodes, self.params.source_highlight_pos)
        self.target_view.set_edge_nodes(target_nodes, self.params.target_highlight_pos)

        # Update preview
        self._update_preview()

    def _update_preview(self):
        """Update the connection preview based on current settings."""
        if not self.source_group or not self.target_group:
            return

        # Update parameters
        self.params.source_to_target_count = self.source_to_target_spinbox.value()
        self.params.target_to_source_count = self.target_to_source_spinbox.value()

        # Get connection preview
        preview_lines = self.bridge_connector.get_connection_preview(
            self.source_group, self.target_group, self.params
        )

        # Update views
        self.source_view.set_connections(preview_lines)
        self.target_view.set_connections(preview_lines)

    def _apply_connections(self):
        """Apply the configured bridge connections to the graph."""
        if not self.source_group or not self.target_group:
            return

        # Update parameters
        self.params.source_to_target_count = self.source_to_target_spinbox.value()
        self.params.target_to_source_count = self.target_to_source_spinbox.value()

        # Create bridge connections
        success = self.bridge_connector.create_bridge_connection(
            self.source_group, self.target_group, self.params
        )

        if success:
            # Accept the dialog (will close it)
            self.accept()
        else:
            # Log error but keep dialog open
            logger.error("Failed to create bridge connection")

    @classmethod
    def show_dialog(
        cls, graph: Graph, source_group: NodeGroup, target_group: NodeGroup, parent=None
    ) -> bool:
        """
        Show the bridge connection dialog.

        Args:
            graph: The graph to operate on
            source_group: The source node group
            target_group: The target node group
            parent: Parent widget

        Returns:
            True if connections were applied, False otherwise
        """
        dialog = cls(graph, parent)
        dialog.set_groups(source_group, target_group)

        # Show dialog and return result
        return dialog.exec_() == QDialog.Accepted
