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
from .canvas_renderer import CanvasRenderer
from .context_menus.normal_menu import NormalContextMenu
from .context_menus.edit_menu import EditContextMenu
from ..models.connectivity import delete_edge_at_position


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

        # Initialize renderer
        self.renderer = CanvasRenderer(self, self.graph)

        # Initialize zoom parameters for zoom functionality
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

        # Initialize pan parameters for panning functionality
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
        self.edit_context_menu = EditContextMenu(self)
        self.normal_context_menu = NormalContextMenu(self)

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

    def paintEvent(self, event):
        """
        Handle the paint event to render the graph.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Use the renderer to draw the graph
        temp_edge_data = None
        if self.current_edge_start and self.temp_edge_end:
            temp_edge_data = (self.current_edge_start, self.temp_edge_end)

        self.renderer.draw(
            painter, self.current_mode, temp_edge_data, self.edit_target_group
        )

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
                # Right-click in normal mode - show context menu
                self.normal_context_menu.popup(self.mapToGlobal(widget_point))

        elif self.current_mode == self.EDIT_MODE:
            # Edit mode
            if event.button() == Qt.LeftButton:
                if self.edit_submode == self.EDIT_SUBMODE_CONNECT:
                    # Edge connection mode - start connecting edges
                    node = self.graph.find_node_at_position(graph_point)
                    if node:
                        # Check if node belongs to target group
                        if (
                            self.edit_target_group
                            and node
                            in self.edit_target_group.get_nodes(self.graph.nodes)
                        ):
                            # Use for edge creation in edit mode
                            self.current_edge_start = node
                            self.temp_edge_end = graph_point
                            # Change cursor during edit mode
                            self.setCursor(Qt.CrossCursor)

                elif self.edit_submode == self.EDIT_SUBMODE_ERASER:
                    # Eraser mode - delete edge at click point
                    delete_edge_at_position(
                        self.graph, graph_point.x(), graph_point.y()
                    )
                    self.update()

            elif event.button() == Qt.RightButton:
                # Right-click in edit mode - show context menu
                if self.edit_target_group:
                    # Prepare the menu before showing it
                    self.edit_context_menu.prepare_for_display()
                    # Show context menu
                    self.edit_context_menu.popup(self.mapToGlobal(widget_point))

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
