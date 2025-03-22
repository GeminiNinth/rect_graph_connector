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

from ...config import config
from ...models.graph import Graph, NodeGroup
from ...models.node import BaseNode
from ...models.special.bridge_connection import BridgeConnector, BridgeConnectionParams
from ...utils.logging_utils import get_logger

logger = get_logger(__name__)


class NodeView(QWidget):
    """
    A custom widget to render and interact with nodes in the bridge window.

    This widget displays nodes from both source and target NodeGroups and allows highlighting
    edge nodes for bridge connections in a unified view.
    """

    node_clicked = pyqtSignal(object)  # Signal emitted when a node is clicked

    def __init__(self, parent=None):
        """Initialize the node view widget."""
        super().__init__(parent)
        self.source_nodes = []  # List of source nodes to display
        self.target_nodes = []  # List of target nodes to display
        self.source_edge_nodes = []  # List of source edge nodes to highlight
        self.target_edge_nodes = []  # List of target edge nodes to highlight
        self.connections = []  # List of (source, target) connections to display
        self.node_size = 15  # Size of nodes in the view
        self.source_highlight_position = BridgeConnector.POS_ROW_FIRST
        self.target_highlight_position = BridgeConnector.POS_ROW_LAST
        self.theme = "light"  # Current theme
        self.source_group_name = ""  # Name of the source group
        self.target_group_name = ""  # Name of the target group

        # Enable mouse tracking
        self.setMouseTracking(True)

        # Set minimum size
        self.setMinimumSize(200, 300)

        # Colors
        self._update_colors()

    def _update_colors(self):
        """Update colors based on the current theme."""
        self.node_fill_color = QColor(config.get_color("node.fill.normal", "skyblue"))
        self.node_border_color = QColor(config.get_color("node.border.normal", "gray"))
        self.highlight_fill_color = QColor(
            config.get_color("node.fill.bridge_target_highlighted", "#50FCC0")
        )
        self.highlight_border_color = QColor(
            config.get_color("node.border.bridge_target_highlighted", "#10DDFF")
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

    def set_source_nodes(self, nodes: List[BaseNode], group_name: str):
        """
        Set the source nodes to display.

        Args:
            nodes: List of source nodes to display
            group_name: Name of the source node group
        """
        self.source_nodes = nodes
        self.source_group_name = group_name
        self.update()

    def set_target_nodes(self, nodes: List[BaseNode], group_name: str):
        """
        Set the target nodes to display.

        Args:
            nodes: List of target nodes to display
            group_name: Name of the target node group
        """
        self.target_nodes = nodes
        self.target_group_name = group_name
        self.update()

    def set_source_edge_nodes(
        self, edge_nodes: List[BaseNode], highlight_position: str
    ):
        """
        Set the source edge nodes to highlight.

        Args:
            edge_nodes: List of source edge nodes to highlight
            highlight_position: The highlight position used
        """
        self.source_edge_nodes = edge_nodes
        self.source_highlight_position = highlight_position
        self.update()

    def set_target_edge_nodes(
        self, edge_nodes: List[BaseNode], highlight_position: str
    ):
        """
        Set the target edge nodes to highlight.

        Args:
            edge_nodes: List of target edge nodes to highlight
            highlight_position: The highlight position used
        """
        self.target_edge_nodes = edge_nodes
        self.target_highlight_position = highlight_position
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

        # Draw group headers
        self._draw_group_headers(painter)

        # Draw connections
        self._draw_connections(painter)

        # Draw nodes
        self._draw_nodes(painter)

    def _draw_group_headers(self, painter: QPainter):
        """
        Draw the group headers.

        Args:
            painter: The painter to draw with
        """
        # Setup font for headers
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        # Get text color based on theme
        text_color = Qt.black if self.theme == "light" else Qt.white
        painter.setPen(QPen(text_color, 1))

        # Draw source group header
        source_header_text = f"Source Nodes\n{self.source_group_name}"
        source_header_rect = QRectF(0, 0, self.width() / 2, 30)
        painter.drawText(source_header_rect, Qt.AlignCenter, source_header_text)

        # Draw target group header
        target_header_text = f"Target Nodes\n{self.target_group_name}"
        target_header_rect = QRectF(self.width() / 2, 0, self.width() / 2, 30)
        painter.drawText(target_header_rect, Qt.AlignCenter, target_header_text)

    def _map_node_to_view_position(self, node_id, nodes, positions):
        """
        Map a node ID to its view position.

        Args:
            node_id: The ID of the node
            nodes: List of nodes
            positions: List of positions corresponding to nodes

        Returns:
            QPointF: The position in the view
        """
        for i, node in enumerate(nodes):
            if node.id == node_id and i < len(positions):
                return positions[i]
        return QPointF(0, 0)  # Default to origin if not found

    def _draw_connections(self, painter: QPainter):
        """
        Draw the direct connection lines between source and target nodes.

        Args:
            painter: The painter to draw with
        """
        # Get source and target node positions
        source_positions = self._get_source_node_positions()
        target_positions = self._get_target_node_positions()

        # Return if either set is empty
        if not source_positions or not target_positions:
            return

        # Set up pen for connections
        pen = QPen(self.connection_color, 2, Qt.SolidLine)
        painter.setPen(pen)

        # Draw connections directly from self.connections
        # which is set in _update_preview
        if self.connections:
            for src_pt, tgt_pt in self.connections:
                # Map node coordinates to view positions by finding matching nodes
                source_node_id = None
                target_node_id = None

                for node in self.source_nodes:
                    if (
                        abs(node.x - src_pt.x()) < 0.01
                        and abs(node.y - src_pt.y()) < 0.01
                    ):
                        source_node_id = node.id
                        break

                for node in self.target_nodes:
                    if (
                        abs(node.x - tgt_pt.x()) < 0.01
                        and abs(node.y - tgt_pt.y()) < 0.01
                    ):
                        target_node_id = node.id
                        break

                if source_node_id is not None and target_node_id is not None:
                    source_view_pos = self._map_node_to_view_position(
                        source_node_id, self.source_nodes, source_positions
                    )
                    target_view_pos = self._map_node_to_view_position(
                        target_node_id, self.target_nodes, target_positions
                    )
                    painter.drawLine(source_view_pos, target_view_pos)

    def _draw_nodes(self, painter: QPainter):
        """
        Draw both source and target nodes.

        Args:
            painter: The painter to draw with
        """
        # Draw source nodes
        self._draw_node_set(
            painter,
            self.source_nodes,
            self.source_edge_nodes,
            self._get_source_node_positions(),
        )

        # Draw target nodes
        self._draw_node_set(
            painter,
            self.target_nodes,
            self.target_edge_nodes,
            self._get_target_node_positions(),
        )

    def _draw_node_set(
        self,
        painter: QPainter,
        nodes: List[BaseNode],
        edge_nodes: List[BaseNode],
        positions: List[QPointF],
    ):
        """
        Draw a set of nodes.

        Args:
            painter: The painter to draw with
            nodes: List of nodes to draw
            edge_nodes: List of highlighted edge nodes
            positions: Positions for each node
        """
        if not nodes or not positions:
            return

        for i, node in enumerate(nodes):
            is_edge_node = node in edge_nodes

            # Set colors based on whether it's an edge node
            fill_color = (
                self.highlight_fill_color if is_edge_node else self.node_fill_color
            )
            border_color = (
                self.highlight_border_color if is_edge_node else self.node_border_color
            )

            # Draw the node
            center = positions[i]
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

    def _get_source_node_positions(self) -> List[QPointF]:
        """
        Calculate positions for all source nodes in the unified view.

        Returns:
            List of source node positions in view coordinates
        """
        if not self.source_nodes:
            return []

        # Add some margin
        top_margin = 40  # Extra space for headers
        side_margin = 20
        width = self.width() - 2 * side_margin
        height = self.height() - top_margin - side_margin

        # Position nodes in a vertical column on the left side
        positions = []
        node_count = len(self.source_nodes)

        if node_count > 0:
            # Calculate vertical spacing
            vertical_spacing = height / (node_count + 1)

            for i in range(node_count):
                # Position in a vertical column on the left side (25% of width)
                x = side_margin + (0.25 * width)
                y = top_margin + ((i + 1) * vertical_spacing)
                positions.append(QPointF(x, y))

        return positions

    def _get_target_node_positions(self) -> List[QPointF]:
        """
        Calculate positions for all target nodes in the unified view.

        Returns:
            List of target node positions in view coordinates
        """
        if not self.target_nodes:
            return []

        # Add some margin
        top_margin = 40  # Extra space for headers
        side_margin = 20
        width = self.width() - 2 * side_margin
        height = self.height() - top_margin - side_margin

        # Position nodes in a vertical column on the right side
        positions = []
        node_count = len(self.target_nodes)

        if node_count > 0:
            # Calculate vertical spacing
            vertical_spacing = height / (node_count + 1)

            for i in range(node_count):
                # Position in a vertical column on the right side (75% of width)
                x = side_margin + (0.75 * width)
                y = top_margin + ((i + 1) * vertical_spacing)
                positions.append(QPointF(x, y))

        return positions

    def mousePressEvent(self, event):
        """
        Handle mouse press events for node selection in the unified view.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            # Check source nodes
            source_positions = self._get_source_node_positions()
            for i, pos in enumerate(source_positions):
                if (pos - event.pos()).manhattanLength() <= self.node_size:
                    self.node_clicked.emit(self.source_nodes[i])
                    return

            # Check target nodes
            target_positions = self._get_target_node_positions()
            for i, pos in enumerate(target_positions):
                if (pos - event.pos()).manhattanLength() <= self.node_size:
                    self.node_clicked.emit(self.target_nodes[i])
                    return


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
        self.bridge_connection = BridgeConnector(graph)

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

        # Consolidated node connection control
        counts_layout = QHBoxLayout()

        # Single node connection control with increase/decrease buttons
        connection_layout = QHBoxLayout()
        self.node_connection_label = QLabel("Node Connection:")

        # Control section with value and buttons
        control_layout = QHBoxLayout()

        # Decrease button
        decrease_text = config.get_string(
            "bridge_connection.window.connection_counts.decrease", "-"
        )
        self.decrease_button = QPushButton(decrease_text)
        self.decrease_button.setFixedWidth(30)
        self.decrease_button.clicked.connect(self._decrease_connection_count)

        # Connection value display
        self.connection_value_label = QLabel("1")
        self.connection_value_label.setAlignment(Qt.AlignCenter)
        self.connection_value_label.setMinimumWidth(30)

        # Increase button
        increase_text = config.get_string(
            "bridge_connection.window.connection_counts.increase", "+"
        )
        self.increase_button = QPushButton(increase_text)
        self.increase_button.setFixedWidth(30)
        self.increase_button.clicked.connect(self._increase_connection_count)

        # Flip button
        flip_text = config.get_string("bridge_connection.window.flip_direction", "Flip")
        self.flip_button = QPushButton(flip_text)
        self.flip_button.setFixedWidth(50)
        self.flip_button.setCheckable(True)
        self.flip_button.clicked.connect(self._toggle_flip_direction)

        # Add widgets to control layout
        control_layout.addWidget(self.decrease_button)
        control_layout.addWidget(self.connection_value_label)
        control_layout.addWidget(self.increase_button)
        control_layout.addWidget(self.flip_button)

        # Add label and control to connection layout
        connection_layout.addWidget(self.node_connection_label)
        connection_layout.addLayout(control_layout)

        # Add connection layout to counts layout with centering
        counts_layout.addStretch()
        counts_layout.addLayout(connection_layout)
        counts_layout.addStretch()

        # Store the current connection count and flip direction
        self.connection_count = 1
        self.max_connection_count = 1  # Will be calculated based on edge nodes
        self.flip_direction = False

        main_layout.addLayout(counts_layout)

        # Unified node view
        self.unified_view = NodeView()

        # Add the unified view to the main layout
        main_layout.addWidget(self.unified_view, 1)

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
        # Update unified node view
        self.unified_view.set_theme(self.theme)

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

            # Update button and label styles for dark theme
            button_bg = QColor(
                config.get_color(
                    "bridge.window.controls.button.background", "#555555", theme="dark"
                )
            )
            button_text = QColor(
                config.get_color(
                    "bridge.window.controls.button.text", "#FFFFFF", theme="dark"
                )
            )

            # Update the buttons and label
            for button in [self.decrease_button, self.increase_button]:
                button_palette = button.palette()
                button_palette.setColor(QPalette.Button, button_bg)
                button_palette.setColor(QPalette.ButtonText, button_text)
                button.setPalette(button_palette)

            # Update connection value label
            label_palette = self.connection_value_label.palette()
            label_palette.setColor(QPalette.WindowText, text_color)
            self.connection_value_label.setPalette(label_palette)
        else:
            # Light theme (default)
            bg_color = QColor(
                config.get_color("bridge.window.background", "rgba(255, 255, 255, 240)")
            )
            text_color = Qt.black

            # Reset to default palette
            self.setPalette(QApplication.style().standardPalette())

    def _increase_connection_count(self):
        """Increase the connection count and update the UI."""
        if self.connection_count < self.max_connection_count:
            self.connection_count += 1
            self.connection_value_label.setText(str(self.connection_count))

            # Update the button state
            self.decrease_button.setEnabled(self.connection_count > 1)
            self.increase_button.setEnabled(
                self.connection_count < self.max_connection_count
            )

            self._update_preview()

    def _decrease_connection_count(self):
        """Decrease the connection count and update the UI."""
        if self.connection_count > 1:
            self.connection_count -= 1
            self.connection_value_label.setText(str(self.connection_count))

            # Update the button state
            self.decrease_button.setEnabled(self.connection_count > 1)
            self.increase_button.setEnabled(
                self.connection_count < self.max_connection_count
            )

            self._update_preview()

    def _toggle_flip_direction(self):
        """Toggle the flip direction for adjacent connections."""
        self.flip_direction = self.flip_button.isChecked()
        self._update_preview()

    def set_groups(
        self,
        source_group: NodeGroup,
        target_group: NodeGroup,
        source_highlight_pos=None,
        target_highlight_pos=None,
    ):
        """
        Set the node groups to configure bridge connections for.

        Args:
            source_group: The source node group
            target_group: The target node group
            source_highlight_pos: Position of highlighted nodes in source group
            target_highlight_pos: Position of highlighted nodes in target group
        """
        self.source_group = source_group
        self.target_group = target_group

        # Update highlight positions if provided
        if source_highlight_pos:
            self.params.source_highlight_pos = source_highlight_pos
        if target_highlight_pos:
            self.params.target_highlight_pos = target_highlight_pos

        # Initialize flip direction to False
        self.params.flip_direction = False
        self.flip_button.setChecked(False)
        self.flip_direction = False

        # Update labels
        source_label_text = config.get_string(
            "bridge_connection.window.source_group", "Source Group:"
        )
        self.source_label.setText(f"{source_label_text} {source_group.name}")

        target_label_text = config.get_string(
            "bridge_connection.window.target_group", "Target Group:"
        )
        self.target_label.setText(f"{target_label_text} {target_group.name}")

        # Update connection label with group names
        connection_label_text = (
            f"Node Connection: {source_group.name} ↔ {target_group.name}"
        )
        self.node_connection_label.setText(connection_label_text)

        # Get edge nodes based on highlight positions
        source_edge_nodes = self.bridge_connection._get_edge_nodes(
            source_group, self.params.source_highlight_pos
        )
        target_edge_nodes = self.bridge_connection._get_edge_nodes(
            target_group, self.params.target_highlight_pos
        )

        # Set source and target nodes in the unified view (only the edge nodes)
        self.unified_view.set_source_nodes(source_edge_nodes, source_group.name)
        self.unified_view.set_target_nodes(target_edge_nodes, target_group.name)

        # Set edge nodes
        self.unified_view.set_source_edge_nodes(
            source_edge_nodes, self.params.source_highlight_pos
        )
        self.unified_view.set_target_edge_nodes(
            target_edge_nodes, self.params.target_highlight_pos
        )

        # Calculate maximum possible connections for a complete graph
        source_count = len(source_edge_nodes)
        target_count = len(target_edge_nodes)
        if source_count > 0 and target_count > 0:
            # In a complete bipartite graph, every node in one set is connected to every node in the other set
            # For bidirectional connections, the max connections needed is min(source_count, target_count)
            self.max_connection_count = min(
                source_count,
                target_count,
                config.get_constant("bridge_connection.max_connections", 10),
            )
        else:
            self.max_connection_count = 1

        # Reset connection count to 1
        self.connection_count = 1
        self.connection_value_label.setText(str(self.connection_count))

        # Update button states
        self.decrease_button.setEnabled(self.connection_count > 1)
        self.increase_button.setEnabled(
            self.connection_count < self.max_connection_count
        )

        # Update preview
        self._update_preview()

    def _update_edge_nodes(self):
        """Update the edge nodes in the unified view based on highlight positions."""
        if not self.source_group or not self.target_group:
            return

        # Get edge nodes from both groups
        source_nodes = self.bridge_connection._get_edge_nodes(
            self.source_group, self.params.source_highlight_pos
        )
        target_nodes = self.bridge_connection._get_edge_nodes(
            self.target_group, self.params.target_highlight_pos
        )

        # Update the source and target nodes to only show edge nodes
        self.unified_view.set_source_nodes(source_nodes, self.source_group.name)
        self.unified_view.set_target_nodes(target_nodes, self.target_group.name)

        # Update the edge nodes highlighting
        self.unified_view.set_source_edge_nodes(
            source_nodes, self.params.source_highlight_pos
        )
        self.unified_view.set_target_edge_nodes(
            target_nodes, self.params.target_highlight_pos
        )

        # Update preview
        self._update_preview()

    def _update_preview(self):
        """Update the connection preview based on current settings."""
        if not self.source_group or not self.target_group:
            return

        # Update parameters with the consolidated connection count and flip direction
        # Use the same value for both directions to create bidirectional connections
        self.params.source_to_target_count = self.connection_count
        self.params.target_to_source_count = self.connection_count
        self.params.flip_direction = self.flip_direction

        # Get the displayed nodes from the unified view
        source_displayed_nodes = self.unified_view.source_nodes
        target_displayed_nodes = self.unified_view.target_nodes

        if not source_displayed_nodes or not target_displayed_nodes:
            return

        # Get the edge nodes (selected nodes) from the unified view
        source_edge_nodes = self.unified_view.source_edge_nodes
        target_edge_nodes = self.unified_view.target_edge_nodes

        # If no edge nodes are selected, use all displayed nodes
        if not source_edge_nodes:
            source_edge_nodes = source_displayed_nodes
        if not target_edge_nodes:
            target_edge_nodes = target_displayed_nodes

        unique_edges = set()
        s2t = self.bridge_connection._generate_bipartite_mapping(
            source_edge_nodes,
            target_edge_nodes,
            self.connection_count,
            self.flip_direction,
        )
        for src_idx, tgt_set in s2t.items():
            for tgt_idx in tgt_set:
                unique_edges.add((src_idx, tgt_idx))

        connection_lines = []
        for src_idx, tgt_idx in unique_edges:
            source_node = source_edge_nodes[src_idx]
            target_node = target_edge_nodes[tgt_idx]
            connection_lines.append(
                (
                    QPointF(source_node.x, source_node.y),
                    QPointF(target_node.x, target_node.y),
                )
            )
        self.unified_view.set_connections(connection_lines)

    def _apply_connections(self):
        """Apply the configured bridge connections to the graph."""
        if not self.source_group or not self.target_group:
            return

        # Update parameters with the consolidated connection count and flip direction
        self.params.source_to_target_count = self.connection_count
        self.params.target_to_source_count = self.connection_count
        self.params.flip_direction = self.flip_direction

        # Get the edge nodes (selected nodes) from the unified view
        source_edge_nodes = self.unified_view.source_edge_nodes
        target_edge_nodes = self.unified_view.target_edge_nodes

        # Get the displayed nodes from the unified view as fallback
        source_displayed_nodes = self.unified_view.source_nodes
        target_displayed_nodes = self.unified_view.target_nodes

        # If no edge nodes are selected, use all displayed nodes
        if not source_edge_nodes:
            source_edge_nodes = source_displayed_nodes
        if not target_edge_nodes:
            target_edge_nodes = target_displayed_nodes

        if not source_edge_nodes or not target_edge_nodes:
            logger.error("No nodes available for connection")
            return

        success = True

        # Instead of trying to recreate the connections from the preview lines,
        # use the same algorithm that generated the preview to create the actual connections
        # This ensures the preview and actual connections match exactly

        # Clear any existing connections between the two groups first
        # to avoid duplicate connections
        for source_node in source_edge_nodes:
            for target_node in target_edge_nodes:
                # Find and remove any existing edges between these nodes
                for edge in list(
                    self.graph.edges
                ):  # Create a copy to safely modify during iteration
                    if (edge[0] == source_node.id and edge[1] == target_node.id) or (
                        edge[0] == target_node.id and edge[1] == source_node.id
                    ):
                        self.graph.edges.remove(edge)

        # Generate source to target connections using the same mapping function
        # that was used for the preview
        unique_edges = set()
        s2t = self.bridge_connection._generate_bipartite_mapping(
            source_edge_nodes,
            target_edge_nodes,
            self.connection_count,
            self.flip_direction,
        )
        for src_idx, tgt_set in s2t.items():
            for tgt_idx in tgt_set:
                unique_edges.add((src_idx, tgt_idx))

        for src_idx, tgt_idx in unique_edges:
            source_node = source_edge_nodes[src_idx]
            target_node = target_edge_nodes[tgt_idx]
            self.graph.add_edge(source_node, target_node)

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
        source_highlight_pos=None,
        target_highlight_pos=None,
        parent=None,
    ) -> bool:
        """
        Show the bridge connection dialog.

        Args:
            graph: The graph to operate on
            source_group: The source node group
            target_group: The target node group
            source_highlight_pos: Position of highlighted nodes in source group
            target_highlight_pos: Position of highlighted nodes in target group
            parent: Parent widget

        Returns:
            True if connections were applied, False otherwise
        """
        dialog = cls(graph, parent)
        dialog.set_groups(
            source_group, target_group, source_highlight_pos, target_highlight_pos
        )

        # Show dialog and return result
        return dialog.exec_() == QDialog.Accepted
