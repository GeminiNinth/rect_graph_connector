"""
This module contains the Canvas widget for graph visualization.
"""

from PyQt5.QtWidgets import QWidget, QMenu, QAction, QInputDialog
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor
from PyQt5.QtCore import Qt, QRectF, QPointF, QMimeData, pyqtSignal

from ..models.graph import Graph
from ..models.rect_node import RectNode
from ..utils.file_handler import FileHandler
from .import_dialog import ImportModeDialog


class Canvas(QWidget):
    """
    A custom widget for visualizing and interacting with the graph.

    This widget handles the rendering of nodes and edges, as well as
    user interactions such as dragging nodes and creating edges.
    It supports multiple interaction modes for different editing operations.
    """

    # Define mode constants
    NORMAL_MODE = "normal"
    EDIT_MODE = "edit"

    # Define edit sub-modes
    EDIT_SUBMODE_CONNECT = "connect"  # Default edit submode for edge connection
    EDIT_SUBMODE_ERASER = "eraser"  # Eraser submode for edge deletion

    # Signal to notify mode changes
    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        Initialize the canvas widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.graph = Graph()
        # Initialize zoom parameters for zoom functionality
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        # Initialize pan parameters for panning functionality
        from PyQt5.QtCore import QPointF

        self.pan_offset = QPointF(0, 0)
        self.panning = False
        self.pan_start = None
        self.pan_offset_start = QPointF(0, 0)

        # Interaction state
        self.dragging = False
        self.drag_start = None
        self.current_edge_start = None
        self.temp_edge_end = None
        self._pending_deselect = False
        self._press_pos = None

        # Mode management
        self.current_mode = self.NORMAL_MODE
        self.edit_target_group = None  # Target group in edit mode
        self.edit_submode = self.EDIT_SUBMODE_CONNECT  # Default edit submode

        # Context menus
        self.edit_context_menu = None
        self.normal_context_menu = None
        self._create_context_menus()

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Set minimum size for better usability
        self.setMinimumHeight(500)

        # Enable keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)

    def set_mode(self, mode):
        """
        Set the current interaction mode.

        Args:
            mode (str): The mode to set (NORMAL_MODE or EDIT_MODE)
        """
        if mode not in [self.NORMAL_MODE, self.EDIT_MODE]:
            return

        old_mode = self.current_mode
        self.current_mode = mode

        # カーソルをモードに合わせて変更
        if mode == self.EDIT_MODE:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        # モード変更通知
        if old_mode != mode:
            self.mode_changed.emit(mode)

        # 再描画
        self.update()

    def _create_context_menus(self):
        """
        Create context menus for both normal and edit modes.
        """
        # Edit mode context menu
        self.edit_context_menu = QMenu(self)

        # Connect all nodes in 4 directions action
        self.connect_4_directions_action = QAction(
            "Connect all nodes in 4 directions", self
        )
        self.connect_4_directions_action.triggered.connect(
            self._connect_nodes_in_4_directions
        )
        self.edit_context_menu.addAction(self.connect_4_directions_action)

        self.edit_context_menu.addSeparator()

        # Toggle eraser mode action
        self.toggle_eraser_action = QAction("Eraser Mode (Delete Edges)", self)
        self.toggle_eraser_action.setCheckable(True)
        self.toggle_eraser_action.triggered.connect(self._toggle_eraser_mode)
        self.edit_context_menu.addAction(self.toggle_eraser_action)

        # Normal mode context menu
        self.normal_context_menu = QMenu(self)

        # Set node ID start index action
        self.set_node_id_start_action = QAction("Set Node ID Starting Index", self)
        self.set_node_id_start_action.triggered.connect(self._set_node_id_start_index)
        self.normal_context_menu.addAction(self.set_node_id_start_action)

    def _set_node_id_start_index(self):
        """
        Display a dialog to set the node ID starting index.
        The change will apply to all nodes in the graph.
        """
        from ..config import config

        # Get the current node ID starting index
        current_start = config.node_id_start

        # Show an input dialog to get the new starting index
        new_start, ok = QInputDialog.getInt(
            self,
            "Set Node ID Starting Index",
            "Enter the starting index for node IDs (0 or higher):",
            value=current_start,
            min=0,
            max=1000000,  # Arbitrary high limit
        )

        if ok:
            # Update the node ID start in the graph
            self.graph.set_node_id_start(new_start)
            self.update()  # Redraw the canvas to show new IDs

    def toggle_edit_mode(self, target_group=None):
        """
        Toggle between normal and edit modes.

        Args:
            target_group (NodeGroup, optional): The group to be edited in edit mode
        """
        if self.current_mode == self.NORMAL_MODE:
            self.edit_target_group = target_group
            self.edit_submode = (
                self.EDIT_SUBMODE_CONNECT
            )  # Reset to default connect submode
            self.set_mode(self.EDIT_MODE)
        else:
            self.edit_target_group = None
            self.set_mode(self.NORMAL_MODE)

    def set_edit_submode(self, submode):
        """
        Set the edit submode and update the cursor.

        Args:
            submode (str): The submode to set (EDIT_SUBMODE_CONNECT or EDIT_SUBMODE_ERASER)
        """
        self.edit_submode = submode

        # Update cursor based on submode
        if submode == self.EDIT_SUBMODE_ERASER:
            # Eraser cursor
            self.setCursor(Qt.ForbiddenCursor)
        else:
            # Default edit mode cursor
            self.setCursor(Qt.CrossCursor)

        # Emit mode changed signal to update the UI
        self.mode_changed.emit(self.current_mode)

    def _toggle_eraser_mode(self, checked):
        """
        Toggle between eraser mode and normal edit mode.

        Args:
            checked (bool): Whether the eraser mode is enabled
        """
        if checked:
            self.set_edit_submode(self.EDIT_SUBMODE_ERASER)
        else:
            self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)

    def _connect_nodes_in_4_directions(self):
        """
        Connect all nodes in the current edit target group in 4 directions.
        Each node gets connected to its adjacent neighbors in 4 directions (up, down, left, right)
        based on their row and column positions in the grid.
        """
        if not self.edit_target_group:
            return

        # Get all nodes in the target group
        group_nodes = self.edit_target_group.get_nodes(self.graph.nodes)
        if not group_nodes:
            return

        # Create a grid structure: store nodes with row and col as keys
        grid = {}
        for node in group_nodes:
            grid[(node.row, node.col)] = node

        # For each node, connects to adjacent nodes in four directions (up, down, left, right)
        for node in group_nodes:
            # Calculate the coordinates of adjacent cells in four directions
            neighbors = [
                (node.row - 1, node.col),  # up
                (node.row + 1, node.col),  # down
                (node.row, node.col - 1),  # right
                (node.row, node.col + 1),  # left
            ]

            # Connecting with adjacent nodes
            for neighbor_pos in neighbors:
                if neighbor_pos in grid:
                    neighbor_node = grid[neighbor_pos]
                    # Added only if the connection does not already exist
                    if not self.graph.has_edge(node, neighbor_node):
                        self.graph.add_edge(node, neighbor_node)

        # Update display
        self.update()

    def paintEvent(self, event):
        """
        Handle the paint event to render the graph.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw canvas border without scaling
        self._draw_canvas_border(painter)

        # Save the painter state and apply zoom scaling for graph elements
        painter.save()
        painter.translate(self.pan_offset)
        painter.scale(self.zoom, self.zoom)

        # Draw edges
        self._draw_edges(painter)

        # Draw temporary edge if one is being created
        self._draw_temp_edge(painter)

        # Draw nodes
        self._draw_nodes(painter)
        painter.restore()

        # Mode display (for debugging)
        # self._draw_mode_indicator(painter)

    def _draw_canvas_border(self, painter: QPainter):
        """Draw the canvas border with mode-specific color."""
        # Set border color according to the mode
        if self.current_mode == self.EDIT_MODE:
            pen = QPen(QColor(255, 100, 100))  # Edit mode is reddish
        else:
            pen = QPen(QColor("black"))

        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def _draw_mode_indicator(self, painter: QPainter):
        """Draw a mode indicator for debugging."""
        text = f"Mode: {self.current_mode}"
        if self.current_mode == self.EDIT_MODE and self.edit_target_group:
            text += f" (Editing: {self.edit_target_group.name})"

        painter.setPen(QColor("black"))
        painter.drawText(10, 20, text)

    def _draw_edges(self, painter: QPainter):
        """Draw all edges in the graph."""
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
        # Identify the selected group
        selected_group_id = None
        if self.graph.selected_group:
            selected_group_id = self.graph.selected_group.id

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

            # Selected groups are displayed in special display
            is_selected = group.id == selected_group_id

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
            fixed_width = 100  # Fixed web

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
            # label_x and label_y have already been converted to int using the _get_label_position method, but just to be safe
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

        # Draw a node
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

    def find_group_at_position(self, point):
        """
        Find a node group that contains the given point in graph coordinates.

        Args:
            point (QPointF): The point in graph coordinates.

        Returns:
            The node group if found, otherwise None.
        """
        for group in self.graph.node_groups:
            group_nodes = group.get_nodes(self.graph.nodes)
            if not group_nodes:
                continue
            # Calculate group bounding rectangle with a margin of 5 pixels (converted to graph units).
            effective_margin = 5 / self.zoom
            min_x = (
                min(node.x - node.size / 2 for node in group_nodes) - effective_margin
            )
            min_y = (
                min(node.y - node.size / 2 for node in group_nodes) - effective_margin
            )
            max_x = (
                max(node.x + node.size / 2 for node in group_nodes) + effective_margin
            )
            max_y = (
                max(node.y + node.size / 2 for node in group_nodes) + effective_margin
            )
            if min_x <= point.x() <= max_x and min_y <= point.y() <= max_y:
                return group
        return None

    def keyPressEvent(self, event):
        """
        Handle keyboard events for mode switching.

        Args:
            event: Keyboard event
        """
        if event.key() == Qt.Key_Escape:
            # Clear NodeGroup selection and, if in edit mode, switch to normal mode.
            self.graph.selected_group = None
            self.graph.selected_nodes = []
            if self.current_mode == self.EDIT_MODE:
                self.toggle_edit_mode()
            self.update()
        elif event.key() == Qt.Key_E and self.graph.selected_group:
            self.toggle_edit_mode(self.graph.selected_group)

    def mousePressEvent(self, event):
        """
        Handle mouse press events for node selection and edge creation.

        Args:
            event: Mouse event
        """
        widget_point = event.pos()
        graph_point = (QPointF(widget_point) - self.pan_offset) / self.zoom

        # Process based on operation mode
        if self.current_mode == self.NORMAL_MODE:
            # Normal mode - Node selection and movement
            if event.button() == Qt.LeftButton:
                clicked_point = graph_point
                node = self.graph.find_node_at_position(clicked_point)
                if node:
                    group = self.graph.get_group_for_node(node)
                    if group and group == self.graph.selected_group:
                        # Instead of immediate toggle, set pending deselect flag and record press position.
                        self._pending_deselect = True
                        self._press_pos = clicked_point
                    else:
                        self.dragging = True
                        self.drag_start = clicked_point
                        if group:
                            self.graph.selected_group = group
                            self.graph.selected_nodes = group.get_nodes(
                                self.graph.nodes
                            )
                        else:
                            self.graph.selected_group = None
                            self.graph.selected_nodes = [node]
                        self.update()
                else:
                    # If no node is found, check if click is within a NodeGroup boundary.
                    group = self.find_group_at_position(clicked_point)
                    if group:
                        self.graph.selected_group = group
                        self.graph.selected_nodes = group.get_nodes(self.graph.nodes)
                        self.update()
                    else:
                        # Start panning if nothing is clicked.
                        self.panning = True
                        self.pan_start = event.pos()
                        self.pan_offset_start = self.pan_offset
                        self.setCursor(Qt.ClosedHandCursor)

            elif event.button() == Qt.RightButton:
                # Right-click in normal mode - show context menu with node ID options
                self.normal_context_menu.popup(self.mapToGlobal(point))

        elif self.current_mode == self.EDIT_MODE:
            # Edit mode
            if event.button() == Qt.LeftButton:
                if self.edit_submode == self.EDIT_SUBMODE_CONNECT:
                    # Edge connection mode - start connecting edges
                    node = self.graph.find_node_at_position(point)
                    if node:
                        # Check if node belongs to target group
                        if (
                            self.edit_target_group
                            and node
                            in self.edit_target_group.get_nodes(self.graph.nodes)
                        ):
                            # Use for edge creation in edit mode
                            self.current_edge_start = node
                            self.temp_edge_end = point
                            # Change cursor during edit mode
                            self.setCursor(Qt.CrossCursor)

                elif self.edit_submode == self.EDIT_SUBMODE_ERASER:
                    # Eraser mode - delete edge at click point
                    self._delete_edge_at_position(point)

            elif event.button() == Qt.RightButton:
                # Right-click in edit mode - show context menu
                if self.edit_target_group:
                    # Update toggle eraser action state
                    self.toggle_eraser_action.setChecked(
                        self.edit_submode == self.EDIT_SUBMODE_ERASER
                    )
                    # Show context menu
                    self.edit_context_menu.popup(self.mapToGlobal(point))

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events for node dragging and edge preview.

        Args:
            event: Mouse event
        """
        widget_point = event.pos()
        graph_point = (widget_point - self.pan_offset) / self.zoom
        if self.current_mode == self.NORMAL_MODE:
            if self._pending_deselect:
                # If movement exceeds threshold, cancel pending deselect and start dragging.
                if (graph_point - self._press_pos).manhattanLength() > 5:
                    self._pending_deselect = False
                    self.dragging = True
                    self.drag_start = self._press_pos
            # Normal mode - You can drag nodes or pan the view
            if self.dragging and self.drag_start:
                dx = graph_point.x() - self.drag_start.x()
                dy = graph_point.y() - self.drag_start.y()
                for node in self.graph.selected_nodes:
                    node.move(dx, dy)
                self.drag_start = graph_point
                self.update()
            elif self.panning:
                dx = widget_point.x() - self.pan_start.x()
                dy = widget_point.y() - self.pan_start.y()
                self.pan_offset = self.pan_offset_start + QPointF(dx, dy)
                self.update()
        elif self.current_mode == self.EDIT_MODE:
            # Edit Mode - NodeGroups are fixed and cannot be moved
            # ドラッグ操作を無視するだけで良い
            pass

        # Update edge previews in both modes
        if self.current_edge_start:
            self.temp_edge_end = graph_point
            self.update()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events to complete dragging or edge creation.

        Args:
            event: Mouse event
        """
        widget_point = event.pos()
        graph_point = (widget_point - self.pan_offset) / self.zoom

        if self.current_mode == self.NORMAL_MODE:
            # Normal mode - Only handle dragging
            if event.button() == Qt.LeftButton:
                if self._pending_deselect:
                    # Deselect NodeGroup on a short click.
                    self.graph.selected_group = None
                    self.graph.selected_nodes = []
                    self._pending_deselect = False
                    self.update()
                    return
                self.dragging = False
                self.drag_start = None
                if self.panning:
                    self.panning = False
                    self.setCursor(Qt.ArrowCursor)

            # Edge creation in normal mode is disabled
            elif event.button() == Qt.RightButton:
                # Clear any accidentally started edge (shouldn't happen with updated code)
                self.current_edge_start = None
                self.temp_edge_end = None
                self.update()

        elif self.current_mode == self.EDIT_MODE:
            # Edit mode - Support left-click edge creation
            if event.button() == Qt.LeftButton and self.current_edge_start:
                # In edit mode, create edge with left-click
                self._complete_edge_creation(graph_point)

            elif event.button() == Qt.RightButton:
                # Right-click will be used for context menu in the future
                # Currently no action
                pass

    def wheelEvent(self, event):
        """
        Handle mouse wheel events for zooming in and out.
        Zoom in when scrolling up and zoom out when scrolling down.
        The maximum zoom in is set such that three nodes nearly fill the canvas,
        and the maximum zoom out is determined by the span of all NodeGroups.
        Text and other canvas elements scale accordingly.
        """
        delta = event.angleDelta().y()
        zoom_factor = 1.0 + delta / 1200.0  # Adjust sensitivity as needed
        new_zoom = self.zoom * zoom_factor
        if new_zoom > self.max_zoom:
            new_zoom = self.max_zoom
        if new_zoom < self.min_zoom:
            new_zoom = self.min_zoom
        self.zoom = new_zoom
        self.update()

    def _complete_edge_creation(self, point):
        """
        Complete the edge creation process by connecting to a target node.

        Args:
            point (QPointF): The point where the mouse was released
        """
        target_node = self.graph.find_node_at_position(point)
        if target_node and target_node != self.current_edge_start:
            # Edit mode specific processing
            if self.current_mode == self.EDIT_MODE:
                # Edit mode allows connections only if the target node does not belong to the edited group
                # This allows nodes within the group to not connect, but only allow connections to nodes outside the group.
                source_group = self.graph.get_group_for_node(self.current_edge_start)
                target_group = self.graph.get_group_for_node(target_node)

                # In edit mode, the node group is fixed so the selection group is not changed
            elif self.current_mode == self.NORMAL_MODE:
                # Before creating an edge, check if both nodes belong to the same group
                source_group = self.graph.get_group_for_node(self.current_edge_start)
                target_group = self.graph.get_group_for_node(target_node)

                # Select groups with priority
                if source_group and target_group:
                    self.graph.selected_group = source_group
                elif source_group:
                    # If only the starting point belongs to the group
                    self.graph.selected_group = source_group
                elif target_group:
                    # If only the endpoint belongs to the group
                    self.graph.selected_group = target_group

            # Add Edge
            self.graph.add_edge(self.current_edge_start, target_node)

            # Update selection status (only in normal mode)
            if self.current_mode == self.NORMAL_MODE:
                if self.graph.selected_group:
                    self.graph.selected_nodes = self.graph.selected_group.get_nodes(
                        self.graph.nodes
                    )
                else:
                    # If neither of them belongs to a group, select both nodes
                    self.graph.selected_nodes = [self.current_edge_start, target_node]

        # After the edge creation is complete, the cursor is returned in edit mode.
        if self.current_mode == self.EDIT_MODE:
            self.setCursor(Qt.CrossCursor)

        # Reset
        self.current_edge_start = None
        self.temp_edge_end = None
        self.update()

    def dragEnterEvent(self, event):
        """
        Handle drag enter events for file drag and drop.

        Args:
            event: Drag enter event
        """
        # Check if the drag contains URLs (files)
        if event.mimeData().hasUrls():
            # Only accept if there's at least one file with .yaml extension
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".yaml"):
                    event.acceptProposedAction()
                    return

    def dragMoveEvent(self, event):
        """
        Handle drag move events for file drag and drop.

        Args:
            event: Drag move event
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """
        Handle drop events for file drag and drop.

        Args:
            event: Drop event
        """
        if event.mimeData().hasUrls():
            # Get the first YAML file from the dropped files
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(".yaml"):
                    self._handle_file_drop(file_path)
                    event.acceptProposedAction()
                    break

    def _delete_edge_at_position(self, point):
        """
        Delete an edge near the given point.

        Args:
            point (QPoint): The point to check for nearby edges
        """
        # Threshold distance for edge detection
        threshold = 10.0

        # Find the closest edge
        closest_edge = None
        min_distance = float("inf")

        for source_id, target_id in self.graph.edges:
            # Get source and target nodes
            source_node = None
            target_node = None

            try:
                source_node = next(n for n in self.graph.nodes if n.id == source_id)
                target_node = next(n for n in self.graph.nodes if n.id == target_id)
            except StopIteration:
                continue

            if source_node and target_node:
                # Calculate distance from point to line segment (edge)
                distance = self._point_to_line_distance(
                    point.x(),
                    point.y(),
                    source_node.x,
                    source_node.y,
                    target_node.x,
                    target_node.y,
                )

                if distance < min_distance:
                    min_distance = distance
                    closest_edge = (source_id, target_id)

        # Delete the edge if it's close enough
        if closest_edge and min_distance <= threshold:
            self.graph.edges.remove(closest_edge)
            self.update()

    def _point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """
        Calculate the minimum distance from a point to a line segment.

        Args:
            px, py: Point coordinates
            x1, y1: Line segment start coordinates
            x2, y2: Line segment end coordinates

        Returns:
            float: The minimum distance from the point to the line segment
        """
        # Line length squared
        line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2

        # If the line is actually a point
        if line_length_sq == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

        # Calculate projection of point onto line
        t = max(
            0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq)
        )

        # Calculate closest point on line segment
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)

        # Return distance to closest point
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5

    def _handle_file_drop(self, file_path):
        """
        Handle the dropped file by showing import mode dialog and importing the file.

        Args:
            file_path (str): Path to the dropped file
        """
        try:
            # Import graph data from the selected file
            imported_data = FileHandler.import_graph_from_yaml(file_path)

            # Show custom import mode dialog
            dialog = ImportModeDialog(self)
            if dialog.exec_():
                mode = dialog.get_selected_mode()
                # Import graph data with the selected mode
                self.graph.import_graph(imported_data, mode)
                # Update the parent window's group list
                if hasattr(self.parent(), "_update_group_list"):
                    self.parent()._update_group_list()
                elif hasattr(self.parent().parent(), "_update_group_list"):
                    self.parent().parent()._update_group_list()
                self.update()

        except IOError as e:
            print(f"Failed to import graph: {e}")
