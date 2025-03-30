"""
Canvas view for graph visualization.
"""

from PyQt5.QtCore import QPointF  # Ensure QPointF is imported
from PyQt5.QtCore import QMimeData, QRect, QRectF, Qt, pyqtSignal
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
from ..models.hover_state_model import HoverStateModel
from ..models.selection_model import SelectionModel
from ..models.view_state_model import ViewStateModel
from ..utils.logging_utils import get_logger
from .gui.composite_renderer import CompositeRenderer
from .gui.edge_renderer import EdgeRenderer
from .gui.group_renderer import GroupRenderer
from .gui.node_renderer import NodeRenderer
from .gui.styles.edge_style import EdgeStyle
from .gui.styles.group_style import GroupStyle
from .gui.styles.node_style import NodeStyle

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

    # NodeGroup selection deselection methods flags
    DESELECT_BY_ESCAPE = config.get_constant("deselect_methods.escape", "escape")
    DESELECT_BY_RECLICK = config.get_constant("deselect_methods.reclick", "reclick")
    DESELECT_BY_BACKGROUND = config.get_constant(
        "deselect_methods.background", "background"
    )

    # Signal to notify grid visibility and snap state changes
    grid_state_changed = pyqtSignal(bool, bool)  # grid_visible, snap_enabled

    def __init__(self, parent=None, input_handler=None):
        """
        Initialize the canvas widget.

        Args:
            parent: Parent widget
            input_handler: Optional InputHandler instance for dependency injection
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
        # Instantiate BorderRenderer here as it needs to draw before transformations
        from .gui.border_renderer import BorderRenderer
        from .gui.styles.border_style import BorderStyle

        self.border_renderer = BorderRenderer(self.view_state, BorderStyle())

        # Initialize composite renderer (without border renderer)
        self.renderer = CompositeRenderer(
            self.view_state,
            self.graph,
            group_renderer=self.group_renderer,
            edge_renderer=self.edge_renderer,
            node_renderer=self.node_renderer,
        )

        # Initialize input handler (dependency injection)
        if input_handler:
            self.input_handler = input_handler
        else:
            # Import here to avoid circular imports
            from ..controllers.input_handler import InputHandler

            self.input_handler = InputHandler(
                self.view_state,
                self.selection_model,
                self.hover_state,
                self.graph,
                self,  # Pass self (CanvasView instance) as canvas
            )
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

        # Border will be drawn last

        # Save painter state
        painter.save()

        # Apply view transformations (pan and zoom)
        painter.translate(self.view_state.pan_offset)
        painter.scale(self.view_state.zoom, self.view_state.zoom)

        # Prepare temporary edge data if applicable
        temp_edge_data_tuple = None
        if self.input_handler.current_mode == self.input_handler.EDIT_MODE:
            controller = self.input_handler.current_mode_controller
            if controller.current_edge_start and controller.temp_edge_end:
                temp_edge_data_tuple = (
                    controller.current_edge_start,
                    controller.temp_edge_end,
                )

        # Prepare edit target groups if in edit mode
        edit_target_groups_list = []
        if self.input_handler.current_mode == self.input_handler.EDIT_MODE:
            edit_target_groups_list = (
                self.input_handler.current_mode_controller.edit_target_groups
            )

        # Prepare knife data if in knife submode
        knife_data_dict = None
        if (
            self.input_handler.current_mode == self.input_handler.EDIT_MODE
            and self.input_handler.current_mode_controller.edit_submode
            == self.input_handler.current_mode_controller.EDIT_SUBMODE_KNIFE
        ):
            controller = self.input_handler.current_mode_controller
            knife_data_dict = {
                "path": [
                    QPointF(p[0], p[1]) for p in controller.knife_path
                ],  # Convert tuples to QPointF
                "highlighted_edges": controller.highlighted_edges,
            }

        # Prepare potential target node if creating edge
        potential_target_node_obj = None
        if (
            self.input_handler.current_mode == self.input_handler.EDIT_MODE
            and self.input_handler.current_mode_controller.current_edge_start
        ):
            potential_target_node_obj = (
                self.input_handler.current_mode_controller.potential_target_node
            )

        # Draw the graph using the composite renderer (now with transformed painter)
        self.renderer.draw(
            painter,
            selected_nodes=self.selection_model.selected_nodes,
            selected_edges=self.selection_model.selected_edges,
            selected_groups=self.selection_model.selected_groups,
            hover_node=self.hover_state.hovered_node,
            hover_edge=self.hover_state.hovered_edges,
            hover_connected_nodes=self.hover_state.hovered_connected_nodes,
            hover_group=None,  # TODO: Implement group hover if needed
            temp_edge_data=temp_edge_data_tuple,  # Pass the prepared tuple
            edit_target_groups=edit_target_groups_list,  # Pass edit target groups
            knife_data=knife_data_dict,  # Pass knife data
            potential_target_node=potential_target_node_obj,  # Pass potential target
        )

        # Restore painter state (removes graph transformations)
        painter.restore()

        # Draw border last (on top of everything, in widget coordinates)
        self.border_renderer.draw(painter)

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

    def mousePressEvent(self, event):
        """
        Handle mouse press events by delegating to the input handler.

        Args:
            event: Mouse event
        """
        try:
            # Delegate to input handler
            self.input_handler.handle_mouse_press(event, event.pos())
            # Update the view
            self.update()
        except Exception as e:
            self.logger.error(f"Error in mousePressEvent: {e}")

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events by delegating to the input handler.

        Args:
            event: Mouse event
        """
        try:
            # Delegate to input handler
            self.input_handler.handle_mouse_move(event, event.pos())
            # Update the view
            self.update()
        except Exception as e:
            self.logger.error(f"Error in mouseMoveEvent: {e}")

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events by delegating to the input handler.

        Args:
            event: Mouse event
        """
        try:
            # Delegate to input handler
            self.input_handler.handle_mouse_release(event, event.pos())
            # Update the view
            self.update()
        except Exception as e:
            self.logger.error(f"Error in mouseReleaseEvent: {e}")

    def keyPressEvent(self, event):
        """
        Handle key press events by delegating to the input handler.

        Args:
            event: Key event
        """
        try:
            # Delegate to input handler
            self.input_handler.handle_key_press(event)
            # Update the view
            self.update()
        except Exception as e:
            self.logger.error(f"Error in keyPressEvent: {e}")

    def wheelEvent(self, event):
        """
        Handle mouse wheel events by delegating to the input handler.

        Args:
            event: Wheel event
        """
        try:
            # Delegate to input handler
            self.input_handler.handle_wheel(event, event.pos())
            # Update the view
            self.update()
        except Exception as e:
            self.logger.error(f"Error in wheelEvent: {e}")
