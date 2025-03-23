"""
Canvas view for graph visualization.
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
from ..models.graph import Graph
from ..models.view_state_model import ViewStateModel
from ..models.selection_model import SelectionModel
from ..models.hover_state_model import HoverStateModel
from ..models.connectivity import delete_edge_at_position, find_intersecting_edges
from ..utils.logging_utils import get_logger
from .gui.composite_renderer import CompositeRenderer
from .gui.node_renderer import NodeRenderer
from .gui.group_renderer import GroupRenderer
from .gui.edge_renderer import EdgeRenderer
from .gui.styles.node_style import NodeStyle
from .gui.styles.group_style import GroupStyle
from .gui.styles.edge_style import EdgeStyle

logger = get_logger(__name__)


class CanvasView(QWidget):
    """
    A custom widget for visualizing and interacting with the graph.

    This widget handles the rendering of nodes and edges, as well as
    user interactions such as dragging nodes and creating edges.
    It supports multiple interaction modes for different editing operations.

    Attributes:
        graph (Graph): The graph model
        view_state (ViewStateModel): The view state model
        selection_model (SelectionModel): The selection model
        hover_state (HoverStateModel): The hover state model
        renderer (CompositeRenderer): The composite renderer
    """

    # Define mode constants
    NORMAL_MODE = config.get_constant("canvas_modes.normal", "normal")
    EDIT_MODE = config.get_constant("canvas_modes.edit", "edit")

    # Define edit sub-modes
    EDIT_SUBMODE_CONNECT = config.get_constant("edit_submodes.connect", "connect")
    EDIT_SUBMODE_KNIFE = config.get_constant("edit_submodes.knife", "knife")
    EDIT_SUBMODE_ALL_FOR_ONE = config.get_constant(
        "edit_submodes.all_for_one", "all_for_one"
    )
    EDIT_SUBMODE_PARALLEL = config.get_constant("edit_submodes.parallel", "parallel")
    EDIT_SUBMODE_BRIDGE = config.get_constant("edit_submodes.bridge", "bridge")

    # Signal to notify mode changes
    mode_changed = pyqtSignal(str)

    # Signal to notify when a NodeGroup is selected in the canvas
    group_selected = pyqtSignal(object)  # Emits the selected NodeGroup

    # NodeGroup selection deselection methods flags
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

        # Initialize models
        self.graph = Graph()
        self.view_state = ViewStateModel()
        self.selection_model = SelectionModel()
        self.hover_state = HoverStateModel()

        # Initialize logger
        self.logger = get_logger(__name__)

        # Initialize styles
        node_style = NodeStyle()
        group_style = GroupStyle()
        edge_style = EdgeStyle()

        # Initialize renderers
        self.node_renderer = NodeRenderer(self.view_state, self.graph, node_style)
        self.group_renderer = GroupRenderer(self.view_state, self.graph, group_style)
        self.edge_renderer = EdgeRenderer(self.view_state, self.graph, edge_style)

        # Initialize composite renderer with core renderers
        self.renderer = CompositeRenderer(
            self.view_state,
            self.graph,
            group_renderer=self.group_renderer,
            edge_renderer=self.edge_renderer,
            node_renderer=self.node_renderer,
        )

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

        # Edge selection state
        self._pending_edge_deselect = False
        self._edge_press_pos = None

        # Knife mode state
        self.knife_path = []
        self.highlighted_edges = []
        self.is_cutting = False

        # All-For-One connection mode state
        self.all_for_one_selected_nodes = []

        # Parallel connection mode state
        self.parallel_selected_nodes = []
        self.parallel_edge_endpoints = []

        # Bridge connection mode state
        self.bridge_selected_groups = []
        self.bridge_floating_menus = {}
        self.bridge_connection_params = None
        self.bridge_preview_lines = []
        self.bridge_edge_nodes = {}

        # Rectangle selection state
        self.selection_rect_start = None
        self.selection_rect_end = None
        self.is_selecting = False

        # Mode management
        self.current_mode = self.NORMAL_MODE
        self.edit_target_groups = []
        self.edit_submode = self.EDIT_SUBMODE_CONNECT

        # Context menus
        from ..gui.context_menus.edit_menu import EditContextMenu
        from ..gui.context_menus.normal_menu import NormalContextMenu

        self.edit_context_menu = EditContextMenu(self)
        self.normal_context_menu = NormalContextMenu(self)

        # Get parent main window
        self.main_window = None
        parent_widget = self.parent()
        while parent_widget:
            if hasattr(parent_widget, "_update_grid_snap_state"):
                self.main_window = parent_widget
                break
            parent_widget = parent_widget.parent()

        # Initialize flags for deselection methods
        self.selection_model.enabled_deselect_methods = {
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

        # Connect view state changes to update
        self.view_state.state_changed.subscribe(self.update)
        self.selection_model.selection_changed.subscribe(self.update)
        self.hover_state.hover_changed.subscribe(self.update)

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Set minimum size for better usability
        self.setMinimumHeight(config.get_dimension("canvas.min_height", 500))

        # Enable keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        """
        Handle the paint event to render the graph.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the graph using the composite renderer
        self.renderer.draw(
            painter,
            selected_nodes=self.selection_model.selected_nodes,
            selected_edges=self.selection_model.selected_edges,
            selected_groups=self.selection_model.selected_groups,
            hover_node=self.hover_state.hover_node,
            hover_edge=self.hover_state.hover_edge,
            hover_group=self.hover_state.hover_group,
        )

    # Property getters and setters
    @property
    def zoom(self):
        """Get the current zoom level."""
        return self.view_state.zoom

    @zoom.setter
    def zoom(self, value):
        """Set the zoom level."""
        self.view_state.zoom = value

    @property
    def pan_offset(self):
        """Get the current pan offset."""
        return self.view_state.pan_offset

    @pan_offset.setter
    def pan_offset(self, value):
        """Set the pan offset."""
        self.view_state.pan_offset = value

    @property
    def grid_visible(self):
        """Get whether the grid is visible."""
        return self.view_state.grid_visible

    @grid_visible.setter
    def grid_visible(self, value):
        """Set whether the grid is visible."""
        self.view_state.grid_visible = value

    @property
    def snap_to_grid(self):
        """Get whether snapping to grid is enabled."""
        return self.view_state.snap_to_grid

    @snap_to_grid.setter
    def snap_to_grid(self, value):
        """Set whether snapping to grid is enabled."""
        self.view_state.snap_to_grid = value

    @property
    def selected_edges(self):
        """Get the selected edges."""
        return self.selection_model.selected_edges

    @selected_edges.setter
    def selected_edges(self, value):
        """Set the selected edges."""
        self.selection_model.selected_edges = value
