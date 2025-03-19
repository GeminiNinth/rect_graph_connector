"""
This module contains the Canvas widget for graph visualization.
"""

from PyQt5.QtWidgets import QWidget, QMenu, QAction, QInputDialog, QMainWindow
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor
from PyQt5.QtCore import Qt, QRectF, QPointF, QMimeData, pyqtSignal

from ..models.graph import Graph
from ..models.rect_node import RectNode
from ..utils.file_handler import FileHandler
from ..utils.logging_utils import get_logger
from .import_dialog import ImportModeDialog
from .canvas_renderer import CanvasRenderer
from .context_menus.normal_menu import NormalContextMenu
from .context_menus.edit_menu import EditContextMenu
from ..models.connectivity import delete_edge_at_position, find_intersecting_edges


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
    EDIT_SUBMODE_KNIFE = "knife"  # Knife submode for edge deletion with path

    # Signal to notify mode changes
    mode_changed = pyqtSignal(str)

    # NodeGroup selection deselection methods flags
    # These flags control which deselection methods are enabled
    DESELECT_BY_ESCAPE = "escape"  # Deselect using ESC key
    DESELECT_BY_RECLICK = "reclick"  # Click the same NodeGroup again to deselect it
    DESELECT_BY_BACKGROUND = "background"  # Click on the background area to deselect it

    def __init__(self, parent=None):
        """
        Initialize the canvas widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.graph = Graph()

        # Initialize logger
        self.logger = get_logger(__name__)

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

        # Knife mode state
        self.knife_path = []  # List of points forming the knife path
        self.highlighted_edges = []  # List of edges intersecting with knife path
        self.is_cutting = False  # Flag to indicate active cutting operation

        # Mode management
        self.current_mode = self.NORMAL_MODE
        self.edit_target_groups = []  # Target groups in edit mode
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

        # Initialize flags for deselection methods
        # Enable all deselect methods
        self.enabled_deselect_methods = {
            self.DESELECT_BY_ESCAPE: True,
            self.DESELECT_BY_RECLICK: True,
            self.DESELECT_BY_BACKGROUND: True,
        }

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
            # Handle selection for edit mode
            if self.graph.selected_groups:
                # Use all selected groups for editing
                self.edit_target_groups = self.graph.selected_groups.copy()
            elif target_group:
                # Single selection case
                self.edit_target_groups = [target_group]
            else:
                self.edit_target_groups = []

            self.edit_submode = (
                self.EDIT_SUBMODE_CONNECT
            )  # Reset to default connect submode
            self.set_mode(self.EDIT_MODE)
        else:
            self.edit_target_groups = []
            self.set_mode(self.NORMAL_MODE)

    def set_deselect_method(self, method, enabled=True):
        """
        Enable/disable the deselection method.

        Args:
            method (str): methods to be set (DESELECT_BY_ESCAPE, DESELECT_BY_RECLICK, DESELECT_BY_BACKGROUND)
            enabled (bool): True to enable, False to disable
        """
        if method in [
            self.DESELECT_BY_ESCAPE,
            self.DESELECT_BY_RECLICK,
            self.DESELECT_BY_BACKGROUND,
        ]:
            self.enabled_deselect_methods[method] = enabled

    def set_edit_submode(self, submode):
        """
        Set the edit submode and update the cursor.

        Args:
            submode (str): The submode to set (EDIT_SUBMODE_CONNECT or EDIT_SUBMODE_KNIFE)
        """
        self.edit_submode = submode

        # Reset knife mode state
        self.knife_path = []
        self.highlighted_edges = []
        self.is_cutting = False

        # Update cursor based on submode
        if submode == self.EDIT_SUBMODE_KNIFE:
            # Knife cursor (using CrossCursor as a temporary solution)
            # TODO: Create a custom knife cursor image
            self.setCursor(Qt.CrossCursor)
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

        # Prepare temporary edge data
        temp_edge_data = None
        if self.current_edge_start and self.temp_edge_end:
            temp_edge_data = (self.current_edge_start, self.temp_edge_end)

        # Prepare knife data if in knife mode
        knife_data = None
        if (
            self.current_mode == self.EDIT_MODE
            and self.edit_submode == self.EDIT_SUBMODE_KNIFE
        ):
            knife_data = {
                "path": self.knife_path,
                "highlighted_edges": self.highlighted_edges,
            }

        # Use the renderer to draw the graph
        self.renderer.draw(
            painter,
            self.current_mode,
            temp_edge_data,
            None,  # edit_target_group parameter is deprecated
            self.edit_target_groups,
            knife_data,
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
            # Only when deselection using the ESC key is enabled
            if self.enabled_deselect_methods.get(self.DESELECT_BY_ESCAPE, True):
                # Clear NodeGroup selection and, if in edit mode, switch to normal mode.
                self.graph.selected_groups = []
                self.graph.selected_nodes = []
                if self.current_mode == self.EDIT_MODE:
                    self.toggle_edit_mode()
                self.update()
        elif event.key() == Qt.Key_E and self.graph.selected_groups:
            # When entering edit mode, use all selected groups
            self.toggle_edit_mode()
        elif (
            event.key() == Qt.Key_A
            and event.modifiers() & Qt.ControlModifier
            and self.current_mode == self.NORMAL_MODE
        ):
            # Ctrl+A: Select all NodeGroups
            if self.graph.node_groups:
                self.graph.selected_groups = list(
                    self.graph.node_groups
                )  # Make all NodeGroups selected as a list

                # Collect all nodes from the selected group
                self.graph.selected_nodes = []
                for group in self.graph.selected_groups:
                    self.graph.selected_nodes.extend(group.get_nodes(self.graph.nodes))
                self.update()
        elif event.key() == Qt.Key_Delete and self.current_mode == self.NORMAL_MODE:
            # Delete key: Delete selected groups
            if self.graph.selected_groups and len(self.graph.selected_groups) > 0:
                # Create a copy of the list since we're modifying it during iteration
                groups_to_delete = self.graph.selected_groups.copy()

                # Process each group separately to ensure all are deleted
                for group in groups_to_delete:
                    self.graph.delete_group(group)

                # Clear selection after all deletions are complete
                self.graph.selected_group = None
                self.graph.selected_groups = []
                self.graph.selected_nodes = []

                # Get the main window instance and update the group list
                main_window = self.window()
                if isinstance(main_window, QMainWindow):
                    main_window._update_group_list()
                self.update()

    def mousePressEvent(self, event):
        """
        Handle mouse press events for node selection and edge creation.

        Args:
            event: Mouse event
        """
        widget_point = event.pos()
        graph_point = (QPointF(widget_point) - self.pan_offset) / self.zoom

        # When the mouse center button (wheel button) is pressed, pan operation begins regardless of mode.
        if event.button() == Qt.MiddleButton:
            self.panning = True
            self.pan_start = event.pos()
            self.pan_offset_start = self.pan_offset
            self.setCursor(Qt.ClosedHandCursor)
            return

        # Process based on operation mode
        if self.current_mode == self.NORMAL_MODE:
            # Normal mode - Node selection and movement
            if event.button() == Qt.LeftButton:
                clicked_point = graph_point
                node = self.graph.find_node_at_position(clicked_point)
                shift_pressed = event.modifiers() & Qt.ShiftModifier

                if node:
                    group = self.graph.get_group_for_node(node)
                    if (
                        group
                        and group in self.graph.selected_groups
                        and not shift_pressed
                    ):
                        # Flag only when deselection is enabled by clicking again
                        if self.enabled_deselect_methods.get(
                            self.DESELECT_BY_RECLICK, True
                        ):
                            # Instead of immediate toggle, set pending deselect flag and record press position.
                            self._pending_deselect = True
                            self._press_pos = clicked_point
                    else:
                        self.dragging = True
                        self.drag_start = clicked_point
                        if group:
                            # Multi-selection with Shift key
                            if shift_pressed:
                                # If already selected, do nothing; if not, add to selection
                                if group not in self.graph.selected_groups:
                                    self.graph.selected_groups.append(group)
                            else:
                                # Single selection (reset current selection)
                                self.graph.selected_groups = [group]

                            # Update selected nodes
                            self.graph.selected_nodes = []
                            for g in self.graph.selected_groups:
                                self.graph.selected_nodes.extend(
                                    g.get_nodes(self.graph.nodes)
                                )
                        else:
                            if not shift_pressed:
                                # Clear selections if shift is not pressed
                                self.graph.selected_groups = []
                            self.graph.selected_nodes = [node]
                        self.update()
                else:
                    # If no node is found, check if click is within a NodeGroup boundary.
                    group = self.find_group_at_position(clicked_point)
                    if group:
                        # Multi-selection with Shift key
                        if shift_pressed:
                            # If already selected, do nothing; if not, add to selection
                            if group not in self.graph.selected_groups:
                                self.graph.selected_groups.append(group)
                        else:
                            # Single selection (reset current selection)
                            self.graph.selected_groups = [group]

                        # Update selected nodes
                        self.graph.selected_nodes = []
                        for g in self.graph.selected_groups:
                            self.graph.selected_nodes.extend(
                                g.get_nodes(self.graph.nodes)
                            )
                        self.update()
                    else:
                        # If no node or group is found, it is considered a background click.
                        # Only when background click deselection is enabled
                        if (
                            self.enabled_deselect_methods.get(
                                self.DESELECT_BY_BACKGROUND, True
                            )
                            and self.graph.selected_groups
                            and not shift_pressed
                        ):
                            # Deselect
                            self.graph.selected_groups = []
                            self.graph.selected_nodes = []
                            self.update()

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
                        # Check if node belongs to any of the target groups
                        node_belongs_to_target = False
                        node_group = self.graph.get_group_for_node(node)

                        # First check edit_target_groups for multi-selection
                        if self.edit_target_groups and node_group:
                            for group in self.edit_target_groups:
                                if node in group.get_nodes(self.graph.nodes):
                                    node_belongs_to_target = True
                                    break
                        # No need to fall back to single edit_target_group anymore

                        if node_belongs_to_target:
                            # Use for edge creation in edit mode
                            self.current_edge_start = node
                            self.temp_edge_end = graph_point
                            # Change cursor during edit mode
                            self.setCursor(Qt.CrossCursor)

                elif self.edit_submode == self.EDIT_SUBMODE_KNIFE:
                    # Knife mode - start cutting operation
                    self.is_cutting = True
                    self.knife_path = [(graph_point.x(), graph_point.y())]
                    self.highlighted_edges = []
                    self.update()

            elif event.button() == Qt.RightButton:
                # Right-click in edit mode - show context menu
                if self.edit_target_groups:
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

        # Pan operation is applied regardless of mode (when pressing the center button)
        if self.panning:
            dx = widget_point.x() - self.pan_start.x()
            dy = widget_point.y() - self.pan_start.y()
            self.pan_offset = self.pan_offset_start + QPointF(dx, dy)
            self.update()
            return  # Skip other processes while panning

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
        elif self.current_mode == self.EDIT_MODE:
            if self.edit_submode == self.EDIT_SUBMODE_KNIFE and self.is_cutting:
                # Add point to knife path
                self.knife_path.append((graph_point.x(), graph_point.y()))

                # Find intersecting edges
                self.highlighted_edges = find_intersecting_edges(
                    self.graph, self.knife_path
                )
                self.update()
            else:
                # Other edit modes - ignore drag operations
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

        # Pan operation end when center button (wheel button) is released
        if event.button() == Qt.MiddleButton:
            if self.panning:
                self.panning = False
                # Return to the appropriate cursor depending on the mode
                if self.current_mode == self.EDIT_MODE:
                    if self.edit_submode == self.EDIT_SUBMODE_ERASER:
                        self.setCursor(Qt.ForbiddenCursor)
                    else:
                        self.setCursor(Qt.CrossCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
            return

        if self.current_mode == self.NORMAL_MODE:
            # Normal mode - Only handle dragging
            if event.button() == Qt.LeftButton:
                if self._pending_deselect:
                    # Deselect NodeGroup on a short click.
                    self.graph.selected_groups = []
                    self.graph.selected_nodes = []
                    self._pending_deselect = False
                    self.update()
                    return
                self.dragging = False
                self.drag_start = None

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

            elif (
                event.button() == Qt.LeftButton
                and self.edit_submode == self.EDIT_SUBMODE_KNIFE
            ):
                # Complete cutting operation
                if self.is_cutting and self.highlighted_edges:
                    # Remove all highlighted edges
                    for edge in self.highlighted_edges:
                        if edge in self.graph.edges:
                            self.graph.edges.remove(edge)

                # Reset knife mode state
                self.is_cutting = False
                self.knife_path = []
                self.highlighted_edges = []
                self.update()

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
        The zoom is centered on the mouse cursor position.
        """
        # マウスカーソルの位置を取得（ウィジェット座標系）
        mouse_pos = event.pos()

        # マウスカーソルの位置をグラフ座標系に変換（現在のズームとパンを考慮）
        mouse_graph_pos = (mouse_pos - self.pan_offset) / self.zoom

        # ズーム倍率を計算
        delta = event.angleDelta().y()
        zoom_factor = 1.0 + delta / 1200.0  # Adjust sensitivity as needed
        new_zoom = self.zoom * zoom_factor

        # ズーム制限を適用
        if new_zoom > self.max_zoom:
            new_zoom = self.max_zoom
        if new_zoom < self.min_zoom:
            new_zoom = self.min_zoom

        # 新しいズーム倍率を設定
        old_zoom = self.zoom
        self.zoom = new_zoom

        # マウスカーソル位置を維持するためにパンオフセットを調整
        # 新しいパンオフセット = マウス位置 - (グラフ座標 * 新しいズーム)
        new_pan = mouse_pos - (mouse_graph_pos * new_zoom)
        self.pan_offset = new_pan

        self.update()

    def _complete_edge_creation(self, point):
        """
        Complete the edge creation process by connecting to a target node.

        Args:
            point (QPointF): The point where the mouse was released
        """
        target_node = self.graph.find_node_at_position(point)
        if target_node and target_node != self.current_edge_start:
            # Get groups for both nodes
            source_group = self.graph.get_group_for_node(self.current_edge_start)
            target_group = self.graph.get_group_for_node(target_node)

            # Edit mode specific processing
            if self.current_mode == self.EDIT_MODE:
                # Check if both nodes belong to any of the target groups
                source_belongs = False
                target_belongs = False

                # Check if both nodes belong to any of the edit target groups
                for group in self.edit_target_groups:
                    if self.current_edge_start in group.get_nodes(self.graph.nodes):
                        source_belongs = True
                    if target_node in group.get_nodes(self.graph.nodes):
                        target_belongs = True
                    if source_belongs and target_belongs:
                        break

                # Add edge if both nodes belong to the edit target groups
                if source_belongs and target_belongs:
                    self.graph.add_edge(self.current_edge_start, target_node)
            elif self.current_mode == self.NORMAL_MODE:
                # Normal mode - allow connections between any nodes
                self.graph.add_edge(self.current_edge_start, target_node)
                # Update selection with both groups if they exist
                if source_group and target_group:
                    self.graph.selected_groups = [source_group, target_group]
                    self.graph.selected_nodes = []
                    for group in self.graph.selected_groups:
                        self.graph.selected_nodes.extend(
                            group.get_nodes(self.graph.nodes)
                        )
                else:
                    # If nodes don't belong to groups, just select the nodes
                    self.graph.selected_groups = []
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
            self.logger.error(f"Failed to import graph: {e}")
