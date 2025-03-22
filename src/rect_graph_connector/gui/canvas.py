"""
This module contains the Canvas widget for graph visualization.
"""

from PyQt5.QtCore import QMimeData, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QPainter, QPen
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QInputDialog,
    QMainWindow,
    QMenu,
    QWidget,
)

from ..config import config
from ..models.connectivity import delete_edge_at_position, find_intersecting_edges
from ..models.graph import Graph
from ..models.rect_node import SingleNode
from ..utils.file_handler import FileHandler
from ..utils.logging_utils import get_logger
from .context_menus.edit_menu import EditContextMenu
from .context_menus.normal_menu import NormalContextMenu
from .floating_menu import FloatingMenu
from .import_dialog import ImportModeDialog
from .rendering import CompositeRenderer
from ..models.bridge_connector import BridgeConnector, BridgeConnectionParams


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
    EDIT_SUBMODE_ALL_FOR_ONE = config.get_constant(
        "edit_submodes.all_for_one", "all_for_one"
    )  # All-For-One connection mode for multiple node selection
    EDIT_SUBMODE_PARALLEL = config.get_constant(
        "edit_submodes.parallel", "parallel"
    )  # Parallel connection mode for drawing edges in same direction
    EDIT_SUBMODE_BRIDGE = config.get_constant(
        "edit_submodes.bridge", "bridge"
    )  # Bridge connection mode for bipartite connections between node groups

    # Signal to notify mode changes
    mode_changed = pyqtSignal(str)

    # Signal to notify when a NodeGroup is selected in the canvas
    group_selected = pyqtSignal(object)  # Emits the selected NodeGroup

    # NodeGroup selection deselection methods flags
    # These flags control which deselection methods are enabled
    DESELECT_BY_ESCAPE = config.get_constant("deselect_methods.escape", "escape")
    DESELECT_BY_RECLICK = config.get_constant("deselect_methods.reclick", "reclick")
    DESELECT_BY_BACKGROUND = config.get_constant(
        "deselect_methods.background", "background"
    )

    # Signal to notify grid visibility and snap state changes
    grid_state_changed = pyqtSignal(bool, bool)  # grid_visible, snap_enabled

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
        self.renderer = CompositeRenderer(self, self.graph)

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
        self._pending_parallel_drag = False
        self._drag_start_node = None
        self.drag_start = None
        self.current_edge_start = None
        self.temp_edge_end = None
        self._pending_deselect = False
        self._pending_parallel_drag = False
        self._press_pos = None
        self._drag_start_node = None

        # Grid display and snap state
        self.grid_visible = False
        self.snap_to_grid = False

        # Get parent main window
        self.main_window = None
        parent_widget = self.parent()
        while parent_widget:
            if hasattr(parent_widget, "_update_grid_snap_state"):
                self.main_window = parent_widget
                break
            parent_widget = parent_widget.parent()

        # Edge selection state
        self.selected_edges = []  # List of selected edges
        self._pending_edge_deselect = False  # Flag for edge deselection
        self._edge_press_pos = None  # Position where edge was clicked

        # Knife mode state
        self.knife_path = []  # List of points forming the knife path
        self.highlighted_edges = []  # List of edges intersecting with knife path
        self.is_cutting = False  # Flag to indicate active cutting operation

        # All-For-One connection mode state
        self.all_for_one_selected_nodes = (
            []
        )  # Nodes selected in All-For-One connection mode

        # Parallel connection mode state
        self.parallel_selected_nodes = []  # Nodes selected in Parallel connection mode
        self.parallel_edge_endpoints = (
            []
        )  # Temporary virtual edges during parallel connection drag

        # Bridge connection mode state
        self.bridge_selected_groups = (
            []
        )  # NodeGroups selected for bridge connection (max 2)
        self.bridge_floating_menus = {}  # Floating menus for each selected group
        self.bridge_connector = BridgeConnector(self.graph)  # Bridge connector instance
        self.bridge_connection_params = (
            BridgeConnectionParams()
        )  # Connection parameters
        self.bridge_preview_lines = []  # Preview lines for bridge connections
        self.bridge_edge_nodes = {}  # Dict of edge nodes for each group

        # Rectangle selection state
        self.selection_rect_start = (
            None  # Start point of selection rectangle (in graph coordinates)
        )
        self.selection_rect_end = (
            None  # End point of selection rectangle (in graph coordinates)
        )
        self.is_selecting = False  # Whether rectangle selection is active

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
            self.all_for_one_selected_nodes = []  # Clear All-For-One selection
            self.parallel_selected_nodes = []  # Clear Parallel selection
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
            submode (str): The submode to set (EDIT_SUBMODE_CONNECT, EDIT_SUBMODE_KNIFE,
                          EDIT_SUBMODE_ALL_FOR_ONE, EDIT_SUBMODE_PARALLEL, or EDIT_SUBMODE_BRIDGE)
        """
        old_submode = self.edit_submode
        self.edit_submode = submode

        # Reset knife mode state
        if old_submode == self.EDIT_SUBMODE_KNIFE:
            self.knife_path = []
            self.highlighted_edges = []
            self.is_cutting = False

        # Reset All-For-One connection mode state when exiting All-For-One connection mode
        if (
            old_submode == self.EDIT_SUBMODE_ALL_FOR_ONE
            and submode != self.EDIT_SUBMODE_ALL_FOR_ONE
        ):
            self.all_for_one_selected_nodes = []

        # Reset Parallel connection mode state when exiting Parallel connection mode
        if (
            old_submode == self.EDIT_SUBMODE_PARALLEL
            and submode != self.EDIT_SUBMODE_PARALLEL
        ):
            self.parallel_selected_nodes = []
            self.parallel_edge_endpoints = []

        # Reset Bridge connection mode state when exiting Bridge connection mode
        if (
            old_submode == self.EDIT_SUBMODE_BRIDGE
            and submode != self.EDIT_SUBMODE_BRIDGE
        ):
            self.bridge_selected_groups = []
            self.bridge_floating_menus = {}
            self.bridge_preview_lines = []
            self.bridge_edge_nodes = {}
            self.bridge_connection_params = BridgeConnectionParams()

        # Update cursor based on submode
        if submode == self.EDIT_SUBMODE_KNIFE:
            # Knife cursor (using CrossCursor as a temporary solution)
            # TODO: Create a custom knife cursor image
            self.setCursor(Qt.CrossCursor)
        elif submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
            # All-For-One connection mode cursor
            self.setCursor(Qt.ArrowCursor)
        elif submode == self.EDIT_SUBMODE_PARALLEL:
            # Parallel connection mode cursor
            self.setCursor(Qt.ArrowCursor)
        elif submode == self.EDIT_SUBMODE_BRIDGE:
            # Bridge connection mode cursor
            self.setCursor(Qt.ArrowCursor)
        else:
            # Default edit mode cursor
            self.setCursor(Qt.CrossCursor)

        # Emit mode changed signal to update the UI
        mode_text = self.current_mode
        if submode == self.EDIT_SUBMODE_BRIDGE:
            mode_text = config.get_string(
                "main_window.mode.edit_bridge", "Mode: Edit - Bridge"
            )

        self.mode_changed.emit(mode_text)

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

        # Pass All-For-One connection selected nodes to renderer
        all_for_one_data = None
        if (
            self.current_mode == self.EDIT_MODE
            and self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE
            and self.all_for_one_selected_nodes
        ):
            all_for_one_data = self.all_for_one_selected_nodes

        # Pass Parallel connection data to renderer
        parallel_data = None
        if (
            self.current_mode == self.EDIT_MODE
            and self.edit_submode == self.EDIT_SUBMODE_PARALLEL
        ):
            parallel_data = {
                "selected_nodes": self.parallel_selected_nodes,
                "edge_endpoints": self.parallel_edge_endpoints,
            }

        # Pass Bridge connection data to renderer
        bridge_data = None
        if (
            self.current_mode == self.EDIT_MODE
            and self.edit_submode == self.EDIT_SUBMODE_BRIDGE
        ):
            bridge_data = {
                "floating_menus": self.bridge_floating_menus,
                "preview_lines": self.bridge_preview_lines,
                "selected_groups": self.bridge_selected_groups,
                "edge_nodes": self.bridge_edge_nodes,
            }

        # Prepare selection rectangle data
        selection_rect_data = None
        if self.is_selecting and self.selection_rect_start and self.selection_rect_end:
            selection_rect_data = {
                "start": self.selection_rect_start,
                "end": self.selection_rect_end,
            }

        # Use the renderer to draw the graph
        self.renderer.draw(
            painter,
            mode=self.current_mode,
            temp_edge_data=temp_edge_data,
            edit_target_groups=self.edit_target_groups,
            knife_data=knife_data,
            selected_edges=self.selected_edges,
            all_for_one_selected_nodes=all_for_one_data,
            selection_rect_data=selection_rect_data,
            parallel_data=parallel_data,
            bridge_data=bridge_data,
        )

    def find_edge_at_position(self, point, tolerance=5):
        """
        Find an edge near the given point in graph coordinates.
        Only considers the visible part of the edge between node boundaries.

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

                # Calculate actual edge endpoints considering node sizes
                start_pos, end_pos = (
                    self.renderer.edge_renderer.calculate_edge_endpoints(
                        source_node, target_node
                    )
                )

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

                # Check if the point is within tolerance and the projection is on the visible part of the edge
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

    def _update_bridge_edge_nodes(self):
        """
        Update the edge nodes for the bridge connection based on current highlight positions.
        """
        self.bridge_edge_nodes = {}

        # Get edge nodes for each selected group
        for i, group in enumerate(self.bridge_selected_groups):
            highlight_pos = None
            if i == 0 and len(self.bridge_selected_groups) > 0:
                highlight_pos = self.bridge_connection_params.source_highlight_pos
            elif i == 1:
                highlight_pos = self.bridge_connection_params.target_highlight_pos

            edge_nodes = self.bridge_connector._get_edge_nodes(group, highlight_pos)
            if edge_nodes:
                self.bridge_edge_nodes[group.id] = edge_nodes

    def _update_bridge_preview_lines(self):
        """
        Update the preview lines for bridge connections between selected groups.
        """
        self.bridge_preview_lines = []

        # Make sure we have exactly 2 groups selected
        if len(self.bridge_selected_groups) != 2:
            return

        source_group = self.bridge_selected_groups[0]
        target_group = self.bridge_selected_groups[1]

        # Get preview lines from bridge connector
        self.bridge_preview_lines = self.bridge_connector.get_connection_preview(
            source_group, target_group, self.bridge_connection_params
        )

    def _open_bridge_connection_window(self):
        """
        Open the bridge connection settings window.
        """
        from .bridge_window import BridgeConnectionWindow

        # Make sure we have exactly 2 groups selected
        if len(self.bridge_selected_groups) != 2:
            return

        source_group = self.bridge_selected_groups[0]
        target_group = self.bridge_selected_groups[1]

        # Show the bridge connection window
        if BridgeConnectionWindow.show_dialog(
            self.graph, source_group, target_group, self
        ):
            # If connections were created, exit bridge mode
            self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
            self.update()

    def keyPressEvent(self, event):
        """
        Handle keyboard events for mode switching and edge operations.

        Args:
            event: Keyboard event
        """
        if event.key() == Qt.Key_G:
            # Toggle grid visibility with G key
            self.grid_visible = not self.grid_visible

            # Store old snap state to restore if needed
            old_snap_state = self.snap_to_grid

            # If we're turning grid off, disable snapping but remember state
            if not self.grid_visible:
                self.snap_to_grid = False
            else:
                # When turning grid back on, restore previous snap state if it was on
                self.snap_to_grid = old_snap_state

            # If we're turning grid on and snap is enabled,
            # snap all nodes to grid now
            if self.grid_visible and self.snap_to_grid:
                self._snap_all_nodes_to_grid()

            # Update the main window's snap checkbox state if available
            if self.main_window:
                self.main_window._update_grid_snap_state(self.grid_visible)

            # Emit the grid state changed signal with current states
            self.grid_state_changed.emit(self.grid_visible, old_snap_state)
            self.update()
            return

        if event.key() == Qt.Key_Escape:
            # Handle special edit submodes
            if self.current_mode == self.EDIT_MODE:
                if self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                    # Cancel All-For-One connection mode and go back to connect mode
                    self.all_for_one_selected_nodes = []
                    self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
                    self.update()
                    return
                elif self.edit_submode == self.EDIT_SUBMODE_PARALLEL:
                    # Cancel Parallel connection mode and go back to connect mode
                    self.parallel_selected_nodes = []
                    self.parallel_edge_endpoints = []
                    self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
                    self.update()
                    return
                elif self.edit_submode == self.EDIT_SUBMODE_BRIDGE:
                    # In Bridge mode, ESC clears selected groups or exits the mode
                    if self.bridge_selected_groups:
                        # Clear selected groups
                        self.bridge_selected_groups = []
                        self.bridge_floating_menus = {}
                        self.bridge_edge_nodes = {}
                        self.bridge_preview_lines = {}
                        self.update()
                    else:
                        # Exit bridge mode if no groups are selected
                        self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
                    return

            # Only when deselection using the ESC key is enabled
            if self.enabled_deselect_methods.get(self.DESELECT_BY_ESCAPE, True):
                # Clear all selections
                self.graph.selected_groups = []
                self.graph.selected_nodes = []
                self.selected_edges = []
                if self.current_mode == self.EDIT_MODE:
                    self.toggle_edit_mode()
                self.update()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # In All-For-One connection mode, confirm the connections and return to connect mode
            if (
                self.current_mode == self.EDIT_MODE
                and self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE
            ):
                # Confirm connections by exiting All-For-One connection mode but keeping any changes
                self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
                self.update()
            elif (
                self.current_mode == self.EDIT_MODE
                and self.edit_submode == self.EDIT_SUBMODE_BRIDGE
                and len(self.bridge_selected_groups) == 2
            ):
                # Open bridge connection window when Enter is pressed with 2 groups selected
                self._open_bridge_connection_window()
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
                        # Emit signal for each selected group
                        self.group_selected.emit(group)
                    self.update()
            elif self.current_mode == self.EDIT_MODE:
                if self.edit_submode in [
                    self.EDIT_SUBMODE_ALL_FOR_ONE,
                    self.EDIT_SUBMODE_PARALLEL,
                ]:
                    # Handle Ctrl+A for both All-For-One and Parallel modes
                    eligible_nodes = []
                    for group in self.edit_target_groups:
                        eligible_nodes.extend(group.get_nodes(self.graph.nodes))

                    # Check if all eligible nodes are already selected
                    # We need to compare node IDs instead of node objects since SingleNode isn't hashable
                    eligible_node_ids = {node.id for node in eligible_nodes}

                    if self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                        selected_node_ids = {
                            node.id for node in self.all_for_one_selected_nodes
                        }
                        if eligible_node_ids == selected_node_ids:
                            self.all_for_one_selected_nodes = []  # Deselect all
                        else:
                            self.all_for_one_selected_nodes = (
                                eligible_nodes.copy()
                            )  # Select all
                    else:  # EDIT_SUBMODE_PARALLEL
                        selected_node_ids = {
                            node.id for node in self.parallel_selected_nodes
                        }
                        if eligible_node_ids == selected_node_ids:
                            self.parallel_selected_nodes = []  # Deselect all
                        else:
                            self.parallel_selected_nodes = (
                                eligible_nodes.copy()
                            )  # Select all
                    self.update()
                else:
                    # Default behavior in other edit submodes: Select all edges
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
                                or target_group in self.edit_target_groups
                            ):
                                self.selected_edges.append((source_node, target_node))
                        except StopIteration:
                            continue
                    self.update()
        elif event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            # Ctrl+C to copy selected groups in normal mode
            if self.current_mode == self.NORMAL_MODE and self.graph.selected_groups:
                # Use the normal context menu's copy method
                self.normal_context_menu._copy_selected_groups()

        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            # Ctrl+V to paste copied groups in normal mode
            if self.current_mode == self.NORMAL_MODE and hasattr(
                self.normal_context_menu, "copied_groups_data"
            ):
                if self.normal_context_menu.copied_groups_data:
                    # Use the normal context menu's paste method
                    self.normal_context_menu._paste_groups()

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
                        # Store the initially clicked node for reference during movement
                        self._drag_start_node = node

                        # If start dragging by clicking on a node, it is possible that the z-index update at the time of selection is not called, so renew just in case
                        if self._pending_deselect and self.graph.selected_groups:
                            # Only update in case of pending_deselect (already updated during normal selection)
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
                                    # Emit signal that a group was selected
                                    self.group_selected.emit(group)
                            else:
                                # Single selection (reset current selection)
                                self.graph.selected_groups = [group]
                                # Move selected groups to the front instantly (update z-index)
                                self.graph.bring_group_to_front(group)
                                # Emit signal that a group was selected
                                self.group_selected.emit(group)

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
                        # Set dragging flag to true when clicking on a group
                        self.dragging = True
                        self.drag_start = clicked_point
                        # Multi-selection with Shift key
                        if shift_pressed:
                            # If already selected, do nothing; if not, add to selection
                            if group not in self.graph.selected_groups:
                                self.graph.selected_groups.append(group)
                                # Move to the front the moment you select a group (update z-index)
                                self.graph.bring_group_to_front(group)
                                # Emit signal that a group was selected
                                self.group_selected.emit(group)
                        else:
                            # Single selection (reset current selection)
                            self.graph.selected_groups = [group]
                            # Move to the front the moment you select a group (update z-index)
                            self.graph.bring_group_to_front(group)
                            # Emit signal that a group was selected
                            self.group_selected.emit(group)

                        # Update selected nodes
                        self.graph.selected_nodes = []
                        for g in self.graph.selected_groups:
                            self.graph.selected_nodes.extend(
                                g.get_nodes(self.graph.nodes)
                            )

                        # Store a reference node from the clicked group for movement
                        if group.get_nodes(self.graph.nodes):
                            self._drag_start_node = group.get_nodes(self.graph.nodes)[0]

                        self.update()
                    else:
                        # If no node or group is found, it is considered a background click.
                        # Start rectangle selection if not start dragging an edge
                        if not self.dragging and not self.current_edge_start:
                            self.is_selecting = True
                            self.selection_rect_start = graph_point
                            self.selection_rect_end = graph_point
                            # Only deselect if background click deselection is enabled and not shift-clicking
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
                        # Check if at least one endpoint of the edge belongs to target groups
                        source_group = self.graph.get_group_for_node(edge[0])
                        target_group = self.graph.get_group_for_node(edge[1])
                        if (
                            source_group in self.edit_target_groups
                            or target_group in self.edit_target_groups
                        ):
                            # Handle edge selection with proper toggling
                            if edge in self.selected_edges and not shift_pressed:
                                # Deselect if already selected and shift is not pressed
                                self.selected_edges.remove(edge)
                            else:
                                if not shift_pressed:
                                    # Clear previous selection if shift is not pressed
                                    self.selected_edges = []
                                if edge not in self.selected_edges:
                                    self.selected_edges.append(edge)

                            # Force update to ensure edge highlighting is visible
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
                            # Check for shift key to determine if we're dragging or creating an edge
                            if event.modifiers() & Qt.ShiftModifier:
                                # With shift, drag the node
                                self.dragging = True
                                self.drag_start = graph_point
                                # Select the node
                                self.graph.selected_nodes = [node]
                                # Change cursor to indicate dragging mode
                                self.setCursor(Qt.ClosedHandCursor)
                            else:
                                # By default, create an edge (original behavior)
                                # Clear edge selection when starting new edge creation
                                self.selected_edges = []
                                self.current_edge_start = node
                                self.temp_edge_end = graph_point
                                # Change cursor during edge creation
                                self.setCursor(Qt.CrossCursor)
                        else:
                            # If no valid node was clicked, start rectangle selection
                            self.is_selecting = True
                            self.selection_rect_start = graph_point
                            self.selection_rect_end = graph_point
                            self.update()
                    else:
                        # If no node was clicked at all, start rectangle selection
                        self.is_selecting = True
                        self.selection_rect_start = graph_point
                        self.selection_rect_end = graph_point
                        self.update()

                elif self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                    # In All-For-One connection mode, left click toggles node selection
                    node = self.graph.find_node_at_position(graph_point)
                    shift_pressed = event.modifiers() & Qt.ShiftModifier

                    if node:
                        # Check if node belongs to any of the target groups
                        node_belongs_to_target = False
                        node_group = self.graph.get_group_for_node(node)

                        if self.edit_target_groups and node_group:
                            for group in self.edit_target_groups:
                                if node in group.get_nodes(self.graph.nodes):
                                    node_belongs_to_target = True
                                    break

                        if node_belongs_to_target:
                            # Toggle selection: select if not selected, deselect if already selected
                            if node in self.all_for_one_selected_nodes:
                                # If node is already selected, prepare for possible drag operation
                                # We'll track if this is a drag or just a click when the mouse moves
                                self._pending_parallel_drag = True
                                self._press_pos = graph_point
                                self._drag_start_node = node
                            else:
                                # If node is not selected
                                if not shift_pressed:
                                    # Clear selection if shift isn't pressed
                                    self.all_for_one_selected_nodes = []
                                # Add node to selection
                                self.all_for_one_selected_nodes.append(node)
                            self.update()

                elif self.edit_submode == self.EDIT_SUBMODE_PARALLEL:
                    # In Parallel connection mode, left click either starts edge creation or rectangle selection
                    node = self.graph.find_node_at_position(graph_point)
                    shift_pressed = event.modifiers() & Qt.ShiftModifier

                    if node:
                        # Check if node belongs to any of the target groups
                        node_belongs_to_target = False
                        node_group = self.graph.get_group_for_node(node)

                        if self.edit_target_groups and node_group:
                            for group in self.edit_target_groups:
                                if node in group.get_nodes(self.graph.nodes):
                                    node_belongs_to_target = True
                                    break

                        if node_belongs_to_target:
                            # Toggle selection: select if not selected, deselect if already selected
                            if node in self.parallel_selected_nodes:
                                # If node is already selected, prepare for possible drag operation
                                # We'll track if this is a drag or just a click when the mouse moves
                                self._pending_parallel_drag = True
                                self._press_pos = graph_point
                                self._drag_start_node = node
                            else:
                                # If node is not selected
                                if not shift_pressed:
                                    # Clear selection if shift isn't pressed
                                    self.parallel_selected_nodes = []
                                # Add node to selection
                                self.parallel_selected_nodes.append(node)
                            self.update()
                    else:
                        # If no node was clicked, start rectangle selection
                        self.is_selecting = True
                        self.selection_rect_start = graph_point
                        self.selection_rect_end = graph_point
                        # Clear selection if shift is not pressed
                        if not shift_pressed:
                            self.parallel_selected_nodes = []
                        self.update()

                elif self.edit_submode == self.EDIT_SUBMODE_BRIDGE:
                    # In Bridge connection mode, left click selects NodeGroups and interacts with floating menus
                    shift_pressed = event.modifiers() & Qt.ShiftModifier

                    # First check if the click is inside a floating menu
                    clicked_menu = False
                    for group_id, menu in self.bridge_floating_menus.items():
                        if menu.contains(graph_point):
                            # Handle floating menu click (e.g., change edge highlighting position)
                            new_position = menu.handle_click(graph_point)
                            if new_position:
                                # Update edge nodes for the group based on new highlight position
                                for i, group in enumerate(self.bridge_selected_groups):
                                    if group.id == group_id:
                                        if i == 0:
                                            self.bridge_connection_params.source_highlight_pos = (
                                                new_position
                                            )
                                        else:
                                            self.bridge_connection_params.target_highlight_pos = (
                                                new_position
                                            )
                                        break

                                # Update edge nodes
                                self._update_bridge_edge_nodes()
                                # Update preview lines
                                self._update_bridge_preview_lines()
                                self.update()
                            clicked_menu = True
                            break

                    if clicked_menu:
                        # If we clicked a menu, don't process further
                        return

                    # If click wasn't on a menu, check for NodeGroup selection
                    group = self.find_group_at_position(graph_point)
                    if group:
                        # Handle NodeGroup selection for bridge mode
                        if group in self.bridge_selected_groups:
                            # If already selected, do nothing (will keep the group selected)
                            # We don't want to deselect a group by clicking on it again in bridge mode
                            pass
                        else:
                            # If not already selected, add to selected groups (max 2)
                            if len(self.bridge_selected_groups) >= 2:
                                # If already have 2 groups, remove the first one (FIFO)
                                removed_group = self.bridge_selected_groups.pop(0)
                                # Remove its floating menu
                                if removed_group.id in self.bridge_floating_menus:
                                    del self.bridge_floating_menus[removed_group.id]

                            # Add new group to selected groups
                            self.bridge_selected_groups.append(group)

                            # Create floating menu for this group
                            # Determine if this is a source or target group based on selection order
                            group_type = (
                                "source"
                                if len(self.bridge_selected_groups) == 1
                                else "target"
                            )
                            self.bridge_floating_menus[group.id] = FloatingMenu(
                                group, group_type=group_type
                            )

                            # Update edge nodes
                            self._update_bridge_edge_nodes()

                            # Update preview lines if we have 2 groups
                            if len(self.bridge_selected_groups) == 2:
                                self._update_bridge_preview_lines()

                            # Update UI with selected groups
                            title_text = config.get_string(
                                "main_window.mode.edit_bridge", "Mode: Edit - Bridge"
                            )
                            self.mode_changed.emit(title_text)
                            self.update()

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

        # Update selection rectangle if we're in selection mode (for any mouse button)
        if self.is_selecting:
            self.selection_rect_end = graph_point
            self.update()
            return

        # Handle pending drag check in Edit mode for All-For-One and Parallel connection submodes
        if self.current_mode == self.EDIT_MODE:
            if (
                self._pending_parallel_drag
                and self._press_pos
                and self._drag_start_node
            ):
                # If movement exceeds threshold, start edge creation instead of deselection
                drag_threshold = config.get_constant("interaction.drag_threshold", 5)
                if (graph_point - self._press_pos).manhattanLength() > drag_threshold:
                    self._pending_parallel_drag = False
                    self.current_edge_start = self._drag_start_node
                    self.temp_edge_end = graph_point

                    # Initialize endpoints depending on the mode
                    if self.edit_submode == self.EDIT_SUBMODE_PARALLEL:
                        # Initialize endpoints for all selected nodes in Parallel mode
                        self.parallel_edge_endpoints = [None] * len(
                            self.parallel_selected_nodes
                        )

                    self.update()
                    return

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

                # Calculate the relative position of the current mouse point to drag start
                if self.grid_visible and self.snap_to_grid:
                    # Get the offset between original drag start and current mouse position
                    total_dx = graph_point.x() - self.drag_start.x()
                    total_dy = graph_point.y() - self.drag_start.y()

                    # Use the initially clicked node as the reference point if available
                    # Otherwise, fall back to using the first selected node
                    if (
                        self._drag_start_node
                        and self._drag_start_node in self.graph.selected_nodes
                    ):
                        reference_x = self._drag_start_node.x
                        reference_y = self._drag_start_node.y
                    elif self.graph.selected_nodes:
                        # Fall back to the first selected node if drag_start_node is not set
                        reference_node = self.graph.selected_nodes[0]
                        reference_x = reference_node.x
                        reference_y = reference_node.y
                    else:
                        # This should not happen, but just in case
                        return

                    # Calculate target position for the reference node
                    target_x = reference_x + total_dx
                    target_y = reference_y + total_dy

                    # Find nearest grid point for the reference node
                    snapped_x, snapped_y = self._snap_to_grid_point(target_x, target_y)

                    # Calculate adjusted displacement to maintain relative positions
                    adjusted_dx = snapped_x - reference_x
                    adjusted_dy = snapped_y - reference_y

                    # Move all selected nodes by the adjusted displacement
                    for node in self.graph.selected_nodes:
                        node.x += adjusted_dx
                        node.y += adjusted_dy

                    # Update drag start for next movement calculation
                    self.drag_start = QPointF(
                        self.drag_start.x() + adjusted_dx,
                        self.drag_start.y() + adjusted_dy,
                    )
                else:
                    # Normal movement without snapping
                    for node in self.graph.selected_nodes:
                        node.move(dx, dy)

                    # Update drag start for next movement
                    self.drag_start = graph_point

                self.update()
        elif self.current_mode == self.EDIT_MODE:
            # Check if we're dragging a node in edit mode
            if self.dragging and self.drag_start:
                dx = graph_point.x() - self.drag_start.x()
                dy = graph_point.y() - self.drag_start.y()

                # Move nodes with proper grid snapping if enabled
                if self.grid_visible and self.snap_to_grid:
                    # Get the offset between original drag start and current mouse position
                    total_dx = graph_point.x() - self.drag_start.x()
                    total_dy = graph_point.y() - self.drag_start.y()

                    # Use the initially clicked node as the reference point if available
                    # Otherwise, fall back to using the first selected node
                    if (
                        self._drag_start_node
                        and self._drag_start_node in self.graph.selected_nodes
                    ):
                        reference_x = self._drag_start_node.x
                        reference_y = self._drag_start_node.y
                    elif self.graph.selected_nodes:
                        # Fall back to the first selected node if drag_start_node is not set
                        reference_node = self.graph.selected_nodes[0]
                        reference_x = reference_node.x
                        reference_y = reference_node.y
                    else:
                        # This should not happen, but just in case
                        return

                    # Calculate target position for the reference node
                    target_x = reference_x + total_dx
                    target_y = reference_y + total_dy

                    # Find nearest grid point for the reference node
                    snapped_x, snapped_y = self._snap_to_grid_point(target_x, target_y)

                    # Calculate adjusted displacement to maintain relative positions
                    adjusted_dx = snapped_x - reference_x
                    adjusted_dy = snapped_y - reference_y

                    # Move all selected nodes by the adjusted displacement
                    for node in self.graph.selected_nodes:
                        node.x += adjusted_dx
                        node.y += adjusted_dy

                    # Update drag start for next movement calculation
                    self.drag_start = QPointF(
                        self.drag_start.x() + adjusted_dx,
                        self.drag_start.y() + adjusted_dy,
                    )
                else:
                    # Normal movement without snapping
                    for node in self.graph.selected_nodes:
                        node.move(dx, dy)

                    # Update drag start for next movement
                    self.drag_start = graph_point

                # Force a redraw to update edge positions
                self.update()
            elif self.edit_submode == self.EDIT_SUBMODE_KNIFE and self.is_cutting:
                # Add point to knife path
                self.knife_path.append((graph_point.x(), graph_point.y()))

                # Find intersecting edges that belong to the target groups
                self.highlighted_edges = find_intersecting_edges(
                    self.graph, self.knife_path, self.edit_target_groups
                )
                self.update()

        # Update edge previews in both modes
        if self.current_edge_start:
            self.temp_edge_end = graph_point

            # For parallel connection mode, update all edge endpoints
            if (
                self.edit_submode == self.EDIT_SUBMODE_PARALLEL
                and self.current_edge_start in self.parallel_selected_nodes
            ):
                # Calculate direction and distance for the drag
                start_pos = QPointF(
                    self.current_edge_start.x, self.current_edge_start.y
                )
                delta_vector = graph_point - start_pos

                # Update endpoints for all selected nodes
                self.parallel_edge_endpoints = []
                for node in self.parallel_selected_nodes:
                    if node:
                        node_pos = QPointF(node.x, node.y)
                        # Calculate the end point by adding the same delta vector
                        end_point = (
                            node_pos.x() + delta_vector.x(),
                            node_pos.y() + delta_vector.y(),
                        )
                        self.parallel_edge_endpoints.append(end_point)

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
                self._drag_start_node = None

                # Handle rectangle selection completion
                if (
                    self.is_selecting
                    and self.selection_rect_start
                    and self.selection_rect_end
                ):
                    self._complete_rectangle_selection()
                    self.is_selecting = False
                    self.selection_rect_start = None
                    self.selection_rect_end = None
                    self.update()

            # Edge creation in normal mode is disabled
            elif event.button() == Qt.RightButton:
                # Clear any accidentally started edge (shouldn't happen with updated code)
                self.current_edge_start = None
                self.temp_edge_end = None
                self.update()

        elif self.current_mode == self.EDIT_MODE:
            # Edit mode - Handle multiple interactions
            if event.button() == Qt.LeftButton:
                # First check if we're finishing a node drag operation
                if self.dragging:
                    # End the dragging operation
                    self.dragging = False
                    self.drag_start = None
                    self._drag_start_node = None
                    # Reset cursor back to the edit mode cursor
                    self.setCursor(Qt.CrossCursor)
                    # Force an update to ensure edges are redrawn correctly
                    self.update()
                    return
                # Check if we have a pending drag operation that was never started (for either connection mode)
                elif self._pending_parallel_drag:
                    # If we reached here, the user clicked on a node but didn't drag far enough
                    # to start edge creation, so we should deselect the node now
                    if self._drag_start_node:
                        if (
                            self.edit_submode == self.EDIT_SUBMODE_PARALLEL
                            and self._drag_start_node in self.parallel_selected_nodes
                        ):
                            # Remove node from parallel selection
                            self.parallel_selected_nodes.remove(self._drag_start_node)
                        elif (
                            self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE
                            and self._drag_start_node in self.all_for_one_selected_nodes
                        ):
                            # Remove node from all-for-one selection
                            self.all_for_one_selected_nodes.remove(
                                self._drag_start_node
                            )

                    # Reset state
                    self._pending_parallel_drag = False
                    self._drag_start_node = None
                    self._press_pos = None
                    self.update()
                # Then handle edge creation if active
                elif self.current_edge_start:
                    if self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                        # In All-For-One connection mode, create edges from all selected nodes
                        self._complete_all_for_one_edge_creation(graph_point)
                    elif self.edit_submode == self.EDIT_SUBMODE_PARALLEL:
                        # In Parallel connection mode, create parallel edges from all selected nodes
                        self._complete_parallel_connection(graph_point)
                    else:
                        # In normal edit mode, create single edge
                        self._complete_edge_creation(graph_point)
                # Handle knife tool completion
                elif self.edit_submode == self.EDIT_SUBMODE_KNIFE and self.is_cutting:
                    # Complete cutting operation
                    if self.highlighted_edges:
                        # Remove all highlighted edges
                        for edge in self.highlighted_edges:
                            if edge in self.graph.edges:
                                self.graph.edges.remove(edge)

                    # Reset knife mode state
                    self.is_cutting = False
                    self.knife_path = []
                    self.highlighted_edges = []
                    self.update()
                # Handle rectangle selection completion
                elif (
                    self.is_selecting
                    and self.selection_rect_start
                    and self.selection_rect_end
                ):
                    self._complete_rectangle_selection()
                    self.is_selecting = False
                    self.selection_rect_start = None
                    self.selection_rect_end = None
                    self.update()
                    # Right-click handling for rectangle selection in All-For-One and Parallel modes
                    # has been removed as these modes now use only left-click for consistency
                    return

            elif event.button() == Qt.RightButton:
                # Right-click will be used for context menu in the future when not in rectangle selection
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
                # Check if the source node belongs to any of the target groups
                source_belongs = False

                # Check if the source node belongs to any of the edit target groups
                for group in self.edit_target_groups:
                    if self.current_edge_start in group.get_nodes(self.graph.nodes):
                        source_belongs = True
                        break

                # Add edge if the source node belongs to the edit target groups
                if source_belongs:
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

    def _complete_all_for_one_edge_creation(self, point):
        """
        Complete the All-For-One connection creation process by connecting from all selected nodes to target node.
        When dragging from a selected node to another node (selected or not), all selected nodes will create edges
        to the target node.

        Args:
            point (QPointF): The point where the mouse was released
        """
        target_node = self.graph.find_node_at_position(point)
        if not target_node or target_node == self.current_edge_start:
            # No target node or trying to connect to self
            self.current_edge_start = None
            self.temp_edge_end = None
            self.update()
            return

        # Create edges from all selected nodes to the target node
        # regardless of whether the target belongs to a selected group or not
        for source_node in self.all_for_one_selected_nodes:
            if source_node != target_node:  # Avoid self-loops
                self.graph.add_edge(source_node, target_node)

        # Reset
        self.current_edge_start = None
        self.temp_edge_end = None
        self.update()

    def _complete_parallel_connection(self, point):
        """
        Complete the Parallel connection process by creating edges from all selected nodes
        in the same direction and distance as the dragged edge. For each selected node,
        check if there's a target node at the end position of the virtual edge. If a node
        exists there, create an edge; if not, don't create an edge.

        Args:
            point (QPointF): The point where the mouse was released
        """
        if not self.current_edge_start or not self.parallel_selected_nodes:
            # No start node or no selected nodes
            return

        # Calculate the displacement vector from the drag start node
        start_pos = QPointF(self.current_edge_start.x, self.current_edge_start.y)
        delta_vector = point - start_pos

        # Create edges for each selected node if a target node exists at the endpoint
        for source_node in self.parallel_selected_nodes:
            if not source_node:
                continue

            # Calculate the expected endpoint position for this source node
            source_pos = QPointF(source_node.x, source_node.y)
            expected_endpoint = QPointF(
                source_pos.x() + delta_vector.x(), source_pos.y() + delta_vector.y()
            )

            # Find if there's a node at the expected endpoint
            # Using a small tolerance to make it easier to connect
            node_size = source_node.size  # Use node size as a reference for tolerance
            target_node = None

            for node in self.graph.nodes:
                node_pos = QPointF(node.x, node.y)
                distance = (
                    (node_pos.x() - expected_endpoint.x()) ** 2
                    + (node_pos.y() - expected_endpoint.y()) ** 2
                ) ** 0.5

                # If there's a node within half a node size, consider it the target
                if distance <= node_size / 2:
                    target_node = node
                    break

            # If a target node was found and it's not the same as the source node
            if target_node and target_node != source_node:
                # Check if source node belongs to target groups
                source_belongs = False

                for group in self.edit_target_groups:
                    if source_node in group.get_nodes(self.graph.nodes):
                        source_belongs = True
                        break

                # Add edge if source node belongs to the edit target groups
                if source_belongs:
                    self.graph.add_edge(source_node, target_node)

        # Reset
        self.current_edge_start = None
        self.temp_edge_end = None
        self.parallel_edge_endpoints = []
        self.update()

    def _complete_rectangle_selection(self):
        """
        Complete the rectangle selection and select nodes/groups/edges based on the current mode.

        Different selection behavior is implemented based on the direction of selection:
        - Left to right (increasing X): Only objects completely inside the rectangle are selected
        - Right to left (decreasing X): Objects that intersect with the rectangle are selected
        """
        if not self.selection_rect_start or not self.selection_rect_end:
            return

        # Calculate the rectangle bounds
        x1, y1 = self.selection_rect_start.x(), self.selection_rect_start.y()
        x2, y2 = self.selection_rect_end.x(), self.selection_rect_end.y()

        # Create normalized rectangle (min_x, min_y, width, height)
        min_x = min(x1, x2)
        min_y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        rect = QRectF(min_x, min_y, width, height)

        # Determine selection direction
        left_to_right = x1 < x2
        shift_pressed = QApplication.keyboardModifiers() & Qt.ShiftModifier

        # Different handling based on mode
        if self.current_mode == self.NORMAL_MODE:
            # In normal mode, select NodeGroups
            selected_groups = []

            for group in self.graph.node_groups:
                group_nodes = group.get_nodes(self.graph.nodes)
                if not group_nodes:
                    continue

                # Calculate group bounds
                group_min_x = min(node.x - node.size / 2 for node in group_nodes)
                group_min_y = min(node.y - node.size / 2 for node in group_nodes)
                group_max_x = max(node.x + node.size / 2 for node in group_nodes)
                group_max_y = max(node.y + node.size / 2 for node in group_nodes)
                group_rect = QRectF(
                    group_min_x,
                    group_min_y,
                    group_max_x - group_min_x,
                    group_max_y - group_min_y,
                )

                if left_to_right:
                    # Strict containment for left-to-right selection
                    if rect.contains(group_rect):
                        selected_groups.append(group)
                else:
                    # Intersection for right-to-left selection
                    if rect.intersects(group_rect):
                        selected_groups.append(group)

            # Apply the selection
            if not shift_pressed:
                self.graph.selected_groups = selected_groups
            else:
                # Additive selection with shift key
                for group in selected_groups:
                    if group not in self.graph.selected_groups:
                        self.graph.selected_groups.append(group)

            # Emit signal for each selected group
            for group in selected_groups:
                self.group_selected.emit(group)

            # Update selected nodes based on selected groups
            self.graph.selected_nodes = []
            for group in self.graph.selected_groups:
                self.graph.selected_nodes.extend(group.get_nodes(self.graph.nodes))

        elif self.current_mode == self.EDIT_MODE:
            if self.edit_submode in [
                self.EDIT_SUBMODE_ALL_FOR_ONE,
                self.EDIT_SUBMODE_PARALLEL,
            ]:
                # Handle node selection for both All-For-One and Parallel modes
                selected_nodes = []

                for group in self.edit_target_groups:
                    for node in group.get_nodes(self.graph.nodes):
                        node_rect = QRectF(
                            node.x - node.size / 2,
                            node.y - node.size / 2,
                            node.size,
                            node.size,
                        )

                        if left_to_right:
                            # Strict containment for left-to-right
                            if rect.contains(node_rect):
                                selected_nodes.append(node)
                        else:
                            # Intersection for right-to-left
                            if rect.intersects(node_rect):
                                selected_nodes.append(node)

                # Apply the selection based on mode
                if self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                    if not shift_pressed:
                        self.all_for_one_selected_nodes = selected_nodes
                    else:
                        # Additive selection with shift key
                        for node in selected_nodes:
                            if node not in self.all_for_one_selected_nodes:
                                self.all_for_one_selected_nodes.append(node)
                else:  # EDIT_SUBMODE_PARALLEL
                    if not shift_pressed:
                        self.parallel_selected_nodes = selected_nodes
                    else:
                        # Additive selection with shift key
                        for node in selected_nodes:
                            if node not in self.parallel_selected_nodes:
                                self.parallel_selected_nodes.append(node)

            else:  # Default edit mode - select edges
                selected_edges = []

                for edge in self.graph.edges:
                    try:
                        source_node = next(
                            n for n in self.graph.nodes if n.id == edge[0]
                        )
                        target_node = next(
                            n for n in self.graph.nodes if n.id == edge[1]
                        )

                        # Only consider edges within edit target groups
                        source_group = self.graph.get_group_for_node(source_node)
                        target_group = self.graph.get_group_for_node(target_node)

                        if (
                            source_group in self.edit_target_groups
                            or target_group in self.edit_target_groups
                        ):

                            # Get edge endpoints
                            start_point, end_point = (
                                self.renderer.edge_renderer.calculate_edge_endpoints(
                                    source_node, target_node
                                )
                            )

                            # Check if line intersects with selection rectangle
                            line_rect = QRectF(
                                start_point.x(),
                                start_point.y(),
                                end_point.x() - start_point.x(),
                                end_point.y() - start_point.y(),
                            )
                            line_rect = line_rect.normalized()

                            # Check if edge intersects with or contained in rectangle
                            # Use different selection logic based on direction
                            if left_to_right:
                                # Strict containment for left-to-right (match Normal mode)
                                if rect.contains(start_point) and rect.contains(
                                    end_point
                                ):
                                    selected_edges.append((source_node, target_node))
                            else:
                                # Intersection for right-to-left (keep existing behavior)
                                if rect.intersects(line_rect) or (
                                    rect.contains(start_point)
                                    or rect.contains(end_point)
                                ):
                                    selected_edges.append((source_node, target_node))

                    except StopIteration:
                        continue

                # Apply the selection
                if not shift_pressed:
                    self.selected_edges = selected_edges
                else:
                    # Additive selection with shift key
                    for edge in selected_edges:
                        if edge not in self.selected_edges:
                            self.selected_edges.append(edge)

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

    def _snap_to_grid_point(self, x, y):
        """
        Snap a point to the nearest grid point.

        Args:
            x (float): X coordinate
            y (float): Y coordinate

        Returns:
            tuple: (snapped_x, snapped_y) coordinates
        """
        standard_spacing = config.get_dimension("grid.spacing", 40.0)
        grid_spacing = (
            standard_spacing / 2
        )  # Half the standard spacing to match the finer grid

        snapped_x = round(x / grid_spacing) * grid_spacing
        snapped_y = round(y / grid_spacing) * grid_spacing
        return snapped_x, snapped_y

    def _snap_all_nodes_to_grid(self):
        """
        Snap all nodes to the nearest grid points.
        Called when grid is toggled on with snap enabled or when snap is toggled on.
        """
        if not self.grid_visible or not self.snap_to_grid:
            return

        # First, snap all selected nodes
        for node in self.graph.selected_nodes:
            node.x, node.y = self._snap_to_grid_point(node.x, node.y)

        # Then snap all other nodes
        for node in self.graph.nodes:
            if node not in self.graph.selected_nodes:
                node.x, node.y = self._snap_to_grid_point(node.x, node.y)

        self.update()

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

                # Select all groups if it's a force import (replacing existing data)
                # or select the most recently added groups otherwise
                if mode == "force":
                    # For force mode, all groups are new, so select all of them
                    self.graph.selected_groups = self.graph.node_groups.copy()
                else:
                    # For other modes, select the most recently added groups
                    # We'll assume these are the ones at the end of the node_groups list
                    # This depends on the implementation of import functions that add new groups at the end
                    num_imported_groups = len(imported_data.get("groups", []))
                    if (
                        num_imported_groups > 0
                        and len(self.graph.node_groups) >= num_imported_groups
                    ):
                        self.graph.selected_groups = self.graph.node_groups[
                            -num_imported_groups:
                        ]
                    else:
                        # Fallback - select all groups if we can't determine which ones are new
                        self.graph.selected_groups = self.graph.node_groups.copy()

                # Update selected nodes based on selected groups
                self.graph.selected_nodes = []
                for group in self.graph.selected_groups:
                    self.graph.selected_nodes.extend(group.get_nodes(self.graph.nodes))

                # Update the parent window's group list
                if hasattr(self.parent(), "_update_group_list"):
                    self.parent()._update_group_list()
                elif hasattr(self.parent().parent(), "_update_group_list"):
                    self.parent().parent()._update_group_list()
                self.update()

        except IOError as e:
            self.logger.error(f"Failed to import graph: {e}")
