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
from ..config import config


class Canvas(QWidget):
    """
    A custom widget for visualizing and interacting with the graph.

    This widget handles the rendering of nodes and edges, as well as
    user interactions such as dragging nodes and creating edges.
    It supports multiple interaction modes for different editing operations.
    """

    # Define mode constants
    NORMAL_MODE = config.get_constant("canvas_modes.normal", "normal")
    EDIT_MODE = config.get_constant("canvas_modes.edit", "edit")

    # Define edit sub-modes
    EDIT_SUBMODE_CONNECT = config.get_constant(
        "edit_submodes.connect", "connect"
    )  # Default edit submode for edge connection
    EDIT_SUBMODE_KNIFE = config.get_constant(
        "edit_submodes.knife", "knife"
    )  # Knife submode for edge deletion with path

    # Signal to notify mode changes
    mode_changed = pyqtSignal(str)

    # NodeGroup selection deselection methods flags
    # These flags control which deselection methods are enabled
    DESELECT_BY_ESCAPE = config.get_constant("deselect_methods.escape", "escape")
    DESELECT_BY_RECLICK = config.get_constant("deselect_methods.reclick", "reclick")
    DESELECT_BY_BACKGROUND = config.get_constant(
        "deselect_methods.background", "background"
    )

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
        self.zoom = config.get_constant("zoom.default", 1.0)
        self.min_zoom = config.get_dimension("canvas.min_zoom", 0.1)
        self.max_zoom = config.get_dimension("canvas.max_zoom", 10.0)

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

        # Edge selection state
        self.selected_edges = []  # List of selected edges
        self._pending_edge_deselect = False  # Flag for edge deselection
        self._edge_press_pos = None  # Position where edge was clicked

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
        self.setMinimumHeight(config.get_dimension("canvas.min_height", 500))

        # Enable keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)

        # Initialize flags for deselection methods
        # Get default values from config or use default (all enabled)
        self.enabled_deselect_methods = {
            self.DESELECT_BY_ESCAPE: config.get_constant(
                "deselect_methods.defaults.escape", True
            ),
            self.DESELECT_BY_RECLICK: config.get_constant(
                "deselect_methods.defaults.reclick", True
            ),
            self.DESELECT_BY_BACKGROUND: config.get_constant(
                "deselect_methods.defaults.background", True
            ),
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
            # Clear all edit mode state when switching back to normal mode
            self.edit_target_groups = []
            self.selected_edges = []  # Clear edge selection
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
            self.selected_edges,  # Pass selected edges for highlighting
        )

    def find_edge_at_position(self, point, tolerance=5):
        """
        Find an edge near the given point in graph coordinates.

        Args:
            point (QPointF): The point in graph coordinates
            tolerance (float): Maximum distance from point to edge to be considered a hit

        Returns:
            tuple: (start_node, end_node) if an edge is found, None otherwise
        """
        # Convert tolerance to graph coordinates
        scaled_tolerance = tolerance / self.zoom

        for edge in self.graph.edges:
            try:
                # Get the actual node objects
                source_node = next(n for n in self.graph.nodes if n.id == edge[0])
                target_node = next(n for n in self.graph.nodes if n.id == edge[1])

                start_pos = QPointF(source_node.x, source_node.y)
                end_pos = QPointF(target_node.x, target_node.y)

                # Calculate distance from point to line segment
                line_vec = end_pos - start_pos
                point_vec = QPointF(point) - start_pos
                line_length = (line_vec.x() ** 2 + line_vec.y() ** 2) ** 0.5

                if line_length == 0:
                    continue

                # Calculate projection
                t = max(
                    0,
                    min(
                        1,
                        (point_vec.x() * line_vec.x() + point_vec.y() * line_vec.y())
                        / (line_length**2),
                    ),
                )
                projection = start_pos + t * line_vec

                # Calculate distance from point to projection
                distance = (
                    (point.x() - projection.x()) ** 2
                    + (point.y() - projection.y()) ** 2
                ) ** 0.5

                if distance <= scaled_tolerance:
                    return (source_node, target_node)

            except StopIteration:
                continue
        return None

    def find_group_at_position(self, point):
        """
        Find a node group that contains the given point in graph coordinates.
        Returns the frontmost group (highest z-index) if multiple groups overlap at the point.

        Args:
            point (QPointF): The point in graph coordinates.

        Returns:
            The node group if found, otherwise None.
        """
        # Get groups sorted by z-index (highest to lowest)
        # This ensures we select the visually frontmost group when groups overlap
        sorted_groups = sorted(
            self.graph.node_groups, key=lambda g: g.z_index, reverse=True
        )

        # First detect all overlapping groups
        overlapping_groups = []

        for group in sorted_groups:
            group_nodes = group.get_nodes(self.graph.nodes)
            if not group_nodes:
                continue

            # Calculate group boundary with margin
            border_margin = config.get_dimension("group.border_margin", 5)
            effective_margin = border_margin / self.zoom
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

            # Record the group containing points
            if min_x <= point.x() <= max_x and min_y <= point.y() <= max_y:
                overlapping_groups.append(group)

        # If the group overlaps with points
        if overlapping_groups:
            # Since it has already been sorted by z-index in descending order, the first group is at the forefront
            return overlapping_groups[0]

        return None

    def keyPressEvent(self, event):
        """
        Handle keyboard events for mode switching and edge operations.

        Args:
            event: Keyboard event
        """
        if event.key() == Qt.Key_Escape:
            # Only when deselection using the ESC key is enabled
            if self.enabled_deselect_methods.get(self.DESELECT_BY_ESCAPE, True):
                # Clear all selections
                self.graph.selected_groups = []
                self.graph.selected_nodes = []
                self.selected_edges = []
                if self.current_mode == self.EDIT_MODE:
                    self.toggle_edit_mode()
                self.update()
        elif event.key() == Qt.Key_E and self.graph.selected_groups:
            # When entering edit mode, use all selected groups
            self.toggle_edit_mode()
        elif event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            if self.current_mode == self.NORMAL_MODE:
                # Ctrl+A in normal mode: Select all NodeGroups
                if self.graph.node_groups:
                    self.graph.selected_groups = list(self.graph.node_groups)
                    self.graph.selected_nodes = []
                    for group in self.graph.selected_groups:
                        self.graph.selected_nodes.extend(
                            group.get_nodes(self.graph.nodes)
                        )
                    self.update()
            elif self.current_mode == self.EDIT_MODE:
                # Ctrl+A in edit mode: Select all edges in target groups
                self.selected_edges = []
                for edge in self.graph.edges:
                    try:
                        # Get actual node objects
                        source_node = next(
                            n for n in self.graph.nodes if n.id == edge[0]
                        )
                        target_node = next(
                            n for n in self.graph.nodes if n.id == edge[1]
                        )

                        source_group = self.graph.get_group_for_node(source_node)
                        target_group = self.graph.get_group_for_node(target_node)

                        if (
                            source_group in self.edit_target_groups
                            and target_group in self.edit_target_groups
                        ):
                            self.selected_edges.append((source_node, target_node))
                    except StopIteration:
                        continue
                self.update()
        elif (
            event.key()
            == getattr(
                Qt, f"Key_{config.get_constant('keyboard_shortcuts.rotate', 'R')}"
            )
            and self.current_mode == self.NORMAL_MODE
        ):
            # Rotate selected groups using keyboard shortcut
            if self.graph.selected_groups:
                self.graph.rotate_node_groups(self.graph.selected_groups)
                self.update()
        elif event.key() == Qt.Key_Delete:
            if self.current_mode == self.NORMAL_MODE:
                # Delete key in normal mode: Delete selected groups
                if self.graph.selected_groups and len(self.graph.selected_groups) > 0:
                    groups_to_delete = self.graph.selected_groups.copy()
                    for group in groups_to_delete:
                        self.graph.delete_group(group)
                    self.graph.selected_group = None
                    self.graph.selected_groups = []
                    self.graph.selected_nodes = []
                    main_window = self.window()
                    if isinstance(main_window, QMainWindow):
                        main_window._update_group_list()
                    self.update()
            elif self.current_mode == self.EDIT_MODE:
                # Delete key in edit mode: Delete selected edges
                if self.selected_edges:
                    for source_node, target_node in self.selected_edges:
                        edge_to_remove = None
                        for edge in self.graph.edges:
                            if edge[0] == source_node.id and edge[1] == target_node.id:
                                edge_to_remove = edge
                                break
                        if edge_to_remove:
                            self.graph.edges.remove(edge_to_remove)
                    self.selected_edges = []
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

                        # If start dragging by clicking on a node, it is possible that the z-index update at the time of selection is not called, so renew just in case
                        if self._pending_deselect and self.graph.selected_groups:
                            # pending_deselectの場合のみ更新（通常の選択時は既に更新済み）
                            for group in self.graph.selected_groups:
                                self.graph.bring_group_to_front(group)
                        if group:
                            # Multi-selection with Shift key
                            if shift_pressed:
                                # If already selected, do nothing; if not, add to selection
                                if group not in self.graph.selected_groups:
                                    self.graph.selected_groups.append(group)
                                    # Move the added group to the front immediately (update z-index)
                                    self.graph.bring_group_to_front(group)
                            else:
                                # Single selection (reset current selection)
                                self.graph.selected_groups = [group]
                                # Move selected groups to the front instantly (update z-index)
                                self.graph.bring_group_to_front(group)

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
                                # Move to the front the moment you select a group (update z-index)
                                self.graph.bring_group_to_front(group)
                        else:
                            # Single selection (reset current selection)
                            self.graph.selected_groups = [group]
                            # Move to the front the moment you select a group (update z-index)
                            self.graph.bring_group_to_front(group)

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
                    # First check for edge selection
                    edge = self.find_edge_at_position(graph_point)
                    shift_pressed = event.modifiers() & Qt.ShiftModifier

                    if edge:
                        # Check if edge belongs to target groups
                        source_group = self.graph.get_group_for_node(edge[0])
                        target_group = self.graph.get_group_for_node(edge[1])
                        if (
                            source_group in self.edit_target_groups
                            and target_group in self.edit_target_groups
                        ):
                            if edge in self.selected_edges and not shift_pressed:
                                # Deselect if already selected and shift is not pressed
                                self.selected_edges.remove(edge)
                            else:
                                if not shift_pressed:
                                    # Clear previous selection if shift is not pressed
                                    self.selected_edges = []
                                if edge not in self.selected_edges:
                                    self.selected_edges.append(edge)
                            self.update()
                            return

                    # If no edge was clicked, proceed with node selection for edge creation
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

                        if node_belongs_to_target:
                            # Clear edge selection when starting new edge creation
                            self.selected_edges = []
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
                drag_threshold = config.get_constant("interaction.drag_threshold", 5)
                if (graph_point - self._press_pos).manhattanLength() > drag_threshold:
                    self._pending_deselect = False
                    self.dragging = True
                    self.drag_start = self._press_pos

                    # Move the selected group to the front when you start dragging
                    if self.graph.selected_groups:
                        for group in self.graph.selected_groups:
                            self.graph.bring_group_to_front(group)

            # Normal mode - You can drag nodes or pan the view
            if self.dragging and self.drag_start:
                dx = graph_point.x() - self.drag_start.x()
                dy = graph_point.y() - self.drag_start.y()

                # Remove continuous updates of z-index during dragging
                # z-index is updated only when dragging starts (mousePress) and ends (mouseRelease)

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
                    if self.edit_submode == self.EDIT_SUBMODE_KNIFE:
                        self.setCursor(Qt.CrossCursor)  # Knife mode cursor
                    else:
                        self.setCursor(Qt.CrossCursor)  # Default edit mode cursor
                else:
                    self.setCursor(Qt.ArrowCursor)  # Normal mode cursor
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

                # Drag operation complete -No z-index update when drag is finished
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
        # Get the position of the mouse cursor (widget coordinate system)
        mouse_pos = event.pos()

        # Convert mouse cursor position to graph coordinate system (considering current zoom and pan)
        mouse_graph_pos = (mouse_pos - self.pan_offset) / self.zoom

        # Calculate zoom magnification
        delta = event.angleDelta().y()
        zoom_sensitivity = config.get_constant("zoom.factor", 1200.0)
        zoom_factor = 1.0 + delta / zoom_sensitivity
        new_zoom = self.zoom * zoom_factor

        # Apply zoom limits
        if new_zoom > self.max_zoom:
            new_zoom = self.max_zoom
        if new_zoom < self.min_zoom:
            new_zoom = self.min_zoom

        # Set a new zoom magnification
        old_zoom = self.zoom
        self.zoom = new_zoom

        # Adjust pan offset to maintain mouse cursor position
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
