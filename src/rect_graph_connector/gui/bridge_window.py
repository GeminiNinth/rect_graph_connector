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
        self.node_fill_color = QColor(config.get_color("node.fill.normal", "skyblue"))
        self.node_border_color = QColor(config.get_color("node.border.normal", "gray"))
        self.highlight_fill_color = QColor(
            config.get_color("node.fill.bridge_highlighted", "rgba(255, 165, 0, 200)")
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

        Only displays edge nodes (first/last row, first/last column) to create
        a simplified view with just input and output layers.

        Args:
            nodes: List of nodes to display
        """
        # Filter to only show edge nodes (first/last row, first/last column)
        if nodes:
            # Group nodes by row and column
            rows = {}
            cols = {}

            for node in nodes:
                if node.row not in rows:
                    rows[node.row] = []
                if node.col not in cols:
                    cols[node.col] = []

                rows[node.row].append(node)
                cols[node.col].append(node)

            # Sort nodes within each row/column
            for r in rows:
                rows[r].sort(key=lambda n: n.col)

            for c in cols:
                cols[c].sort(key=lambda n: n.row)

            # Get edge nodes using a list instead of a set to avoid hashability issues
            edge_nodes = []

            # Helper function to add a node if it's not already in the list
            def add_unique_node(node):
                for existing_node in edge_nodes:
                    if existing_node.id == node.id:
                        return
                edge_nodes.append(node)

            # First and last row
            sorted_rows = sorted(rows.keys())
            if sorted_rows:
                first_row = sorted_rows[0]
                last_row = sorted_rows[-1]

                # Add first and last node in first row
                if rows[first_row]:
                    add_unique_node(rows[first_row][0])  # First node in first row
                    add_unique_node(rows[first_row][-1])  # Last node in first row

                # Add first and last node in last row
                if rows[last_row] and last_row != first_row:
                    add_unique_node(rows[last_row][0])  # First node in last row
                    add_unique_node(rows[last_row][-1])  # Last node in last row

            # First and last column
            sorted_cols = sorted(cols.keys())
            if sorted_cols:
                first_col = sorted_cols[0]
                last_col = sorted_cols[-1]

                # Add first and last node in first column
                if cols[first_col]:
                    add_unique_node(cols[first_col][0])  # First node in first column
                    add_unique_node(cols[first_col][-1])  # Last node in first column

                # Add first and last node in last column
                if cols[last_col] and last_col != first_col:
                    add_unique_node(cols[last_col][0])  # First node in last column
                    add_unique_node(cols[last_col][-1])  # Last node in last column

            self.nodes = edge_nodes
        else:
            self.nodes = []

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

        Creates a simplified layout with source nodes on the left and target nodes on the right,
        arranged vertically regardless of their original positions.

        Returns:
            List of node positions in view coordinates
        """
        if not self.nodes:
            return []

        # Determine if this is a source or target view based on the first node's presence in edge_nodes
        is_source_view = False
        if self.edge_nodes and self.nodes:
            # Check if any node in self.nodes is in self.edge_nodes and has highlight_position
            # that matches a source position (ROW_FIRST, ROW_LAST, COL_FIRST, COL_LAST)
            source_positions = [
                BridgeConnector.POS_ROW_FIRST,
                BridgeConnector.POS_ROW_LAST,
                BridgeConnector.POS_COL_FIRST,
                BridgeConnector.POS_COL_LAST,
            ]
            is_source_view = self.highlight_position in source_positions

        # Add some margin
        margin = 20
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin

        # For simplified layout, position nodes in a vertical column
        # Source nodes on the left side, target nodes on the right side
        positions = []
        node_count = len(self.nodes)

        if node_count > 0:
            # Calculate vertical spacing
            vertical_spacing = height / (node_count + 1)

            for i, node in enumerate(self.nodes):
                # Position in a vertical column
                # Source nodes on left (25% of width), target nodes on right (75% of width)
                x = margin + (0.25 * width if is_source_view else 0.75 * width)
                y = margin + ((i + 1) * vertical_spacing)
                positions.append(QPointF(x, y))

        return positions

    def _map_to_view(self, point: QPointF) -> QPointF:
        """
        Map a point from graph coordinates to view coordinates.

        In the simplified layout, this is primarily used for connection endpoints.
        Since we're using a virtual layout, we need to find the closest node
        and use its position in the simplified layout.

        Args:
            point: Point in graph coordinates

        Returns:
            Point in view coordinates
        """
        if not self.nodes:
            return QPointF(0, 0)

        # For the simplified layout, we need to find which node this point belongs to
        # and return that node's position in our virtual layout

        # Find the node closest to this point
        closest_node = None
        min_distance = float("inf")

        for node in self.nodes:
            # Calculate distance to this node
            dx = node.x - point.x()
            dy = node.y - point.y()
            distance = dx * dx + dy * dy  # Square of distance is enough for comparison

            if distance < min_distance:
                min_distance = distance
                closest_node = node

        # If we found a node, use its position in our layout
        if closest_node:
            # Get all node positions in our virtual layout
            positions = self._get_node_positions()

            # Find the position of our closest node
            for i, node in enumerate(self.nodes):
                if node.id == closest_node.id:
                    return positions[i]

        # Fallback to center of view
        return QPointF(self.width() / 2, self.height() / 2)

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

        # Get the displayed nodes from each view
        source_displayed_nodes = self.source_view.nodes
        target_displayed_nodes = self.target_view.nodes

        if not source_displayed_nodes or not target_displayed_nodes:
            return

        # Get the edge nodes (selected nodes) from each view
        source_edge_nodes = self.source_view.edge_nodes
        target_edge_nodes = self.target_view.edge_nodes

        # If no edge nodes are selected, use all displayed nodes
        if not source_edge_nodes:
            source_edge_nodes = source_displayed_nodes
        if not target_edge_nodes:
            target_edge_nodes = target_displayed_nodes

        # Create preview lines between edge nodes only
        source_preview_lines = []
        target_preview_lines = []

        # For source to target connections
        if self.params.source_to_target_count > 0:
            # Use bridge connector's bipartite mapping logic but only for edge nodes
            connections = self.bridge_connector._generate_bipartite_mapping(
                source_edge_nodes,
                target_edge_nodes,
                self.params.source_to_target_count,
            )

            for source_idx, target_indices in connections.items():
                source_node = source_edge_nodes[source_idx]
                for target_idx in target_indices:
                    target_node = target_edge_nodes[target_idx]
                    # Create connection points for both views
                    source_preview_lines.append(
                        (
                            QPointF(source_node.x, source_node.y),
                            QPointF(target_node.x, target_node.y),
                        )
                    )
                    target_preview_lines.append(
                        (
                            QPointF(source_node.x, source_node.y),
                            QPointF(target_node.x, target_node.y),
                        )
                    )

        # For target to source connections
        if self.params.target_to_source_count > 0:
            # Use bridge connector's bipartite mapping logic but only for edge nodes
            connections = self.bridge_connector._generate_bipartite_mapping(
                target_edge_nodes,
                source_edge_nodes,
                self.params.target_to_source_count,
            )

            for target_idx, source_indices in connections.items():
                target_node = target_edge_nodes[target_idx]
                for source_idx in source_indices:
                    source_node = source_edge_nodes[source_idx]
                    # Create connection points for both views
                    source_preview_lines.append(
                        (
                            QPointF(target_node.x, target_node.y),
                            QPointF(source_node.x, source_node.y),
                        )
                    )
                    target_preview_lines.append(
                        (
                            QPointF(target_node.x, target_node.y),
                            QPointF(source_node.x, source_node.y),
                        )
                    )

        # Update views with their respective connection lines
        self.source_view.set_connections(source_preview_lines)
        self.target_view.set_connections(target_preview_lines)

    def _apply_connections(self):
        """Apply the configured bridge connections to the graph."""
        if not self.source_group or not self.target_group:
            return

        # Update parameters
        self.params.source_to_target_count = self.source_to_target_spinbox.value()
        self.params.target_to_source_count = self.target_to_source_spinbox.value()

        # Get the edge nodes (selected nodes) from each view
        source_edge_nodes = self.source_view.edge_nodes
        target_edge_nodes = self.target_view.edge_nodes

        # Get the displayed nodes from each view as fallback
        source_displayed_nodes = self.source_view.nodes
        target_displayed_nodes = self.target_view.nodes

        # If no edge nodes are selected, use all displayed nodes
        if not source_edge_nodes:
            source_edge_nodes = source_displayed_nodes
        if not target_edge_nodes:
            target_edge_nodes = target_displayed_nodes

        if not source_edge_nodes or not target_edge_nodes:
            logger.error("No nodes available for connection")
            return

        success = True

        # For source to target connections
        if self.params.source_to_target_count > 0:
            # Use bridge connector's bipartite connection logic but only for edge nodes
            connections = self.bridge_connector._generate_bipartite_mapping(
                source_edge_nodes,
                target_edge_nodes,
                self.params.source_to_target_count,
            )

            for source_idx, target_indices in connections.items():
                source_node = source_edge_nodes[source_idx]
                for target_idx in target_indices:
                    target_node = target_edge_nodes[target_idx]
                    self.graph.add_edge(source_node, target_node)

        # For target to source connections
        if self.params.target_to_source_count > 0:
            # Use bridge connector's bipartite connection logic but only for edge nodes
            connections = self.bridge_connector._generate_bipartite_mapping(
                target_edge_nodes,
                source_edge_nodes,
                self.params.target_to_source_count,
            )

            for target_idx, source_indices in connections.items():
                target_node = target_edge_nodes[target_idx]
                for source_idx in source_indices:
                    source_node = source_edge_nodes[source_idx]
                    self.graph.add_edge(target_node, source_node)

            if success:
                # Accept the dialog (will close it)
                self.accept()
            else:
                # Log error but keep dialog open
                logger.error("Failed to create bridge connection")

    @classmethod
    def show_dialog(
        cls,
        graph: Graph,
        source_group: NodeGroup,
        target_group: NodeGroup,
        parent=None,
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
