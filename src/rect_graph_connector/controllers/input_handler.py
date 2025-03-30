"""
Input handler for managing user interactions with the canvas.

This module provides the InputHandler class which centralizes all input processing
and delegates to appropriate mode controllers based on the current mode.
"""

from PyQt5.QtCore import QObject, QPointF, Qt, pyqtSignal  # Import QObject
from PyQt5.QtWidgets import QWidget

from ..config import config
from ..models.graph import Graph
from ..models.hover_state_model import HoverStateModel
from ..models.selection_model import SelectionModel
from ..models.view_state_model import ViewStateModel


class InputHandler(QObject):  # Inherit from QObject
    """
    Centralized input handler for the canvas.
    This class manages all user input events (mouse and keyboard) and delegates
    to the appropriate mode controller based on the current mode. It provides
    a clean separation between input handling and rendering logic.

    Attributes:
        view_state (ViewStateModel): The view state model
        selection_model (SelectionModel): The selection model
        hover_state (HoverStateModel): The hover state model
        graph (Graph): The graph model
        current_mode (str): The current interaction mode
        current_mode_controller: The controller for the current mode
    """

    mode_changed = pyqtSignal(str)  # Add signal definition

    def __init__(
        self,
        view_state: ViewStateModel,
        selection_model: SelectionModel,
        hover_state: HoverStateModel,
        graph: Graph,
        canvas: QWidget,  # Add canvas parameter
    ):
        """
        Initialize the input handler.

        Args:
            view_state (ViewStateModel): The view state model
            selection_model (SelectionModel): The selection model
            hover_state (HoverStateModel): The hover state model
            graph (Graph): The graph model
            canvas (QWidget): The canvas widget
        """
        super().__init__()  # Call QObject initializer
        self.view_state = view_state
        self.selection_model = selection_model
        self.hover_state = hover_state
        self.graph = graph
        self.canvas = canvas  # Store canvas reference

        # Mode constants
        self.NORMAL_MODE = config.get_constant("canvas_modes.normal", "normal")
        self.EDIT_MODE = config.get_constant("canvas_modes.edit", "edit")

        # Current mode and controller
        self.current_mode = self.NORMAL_MODE
        self.current_mode_controller = None

        # Interaction state
        self.dragging = False
        self.drag_start = None
        self.drag_start_node = None
        self.current_edge_start = None
        self.temp_edge_end = None
        self.pending_deselect = False
        self.press_pos = None

        # Rectangle selection state
        self.is_selecting = False
        self.selection_rect_start = None
        self.selection_rect_end = None

        # Panning state
        self.panning = False

        # Initialize mode controllers
        self._init_mode_controllers()

    def _init_mode_controllers(self):
        """Initialize the mode controllers."""
        # Import here to avoid circular imports
        from .modes.edit_mode_controller import EditModeController
        from .modes.normal_mode_controller import NormalModeController

        self.mode_controllers = {
            self.NORMAL_MODE: NormalModeController(
                self.view_state,
                self.selection_model,
                self.hover_state,
                self.graph,
                self.canvas,
                self,  # Pass input_handler (self)
            ),
            self.EDIT_MODE: EditModeController(
                self.view_state,
                self.selection_model,
                self.hover_state,
                self.graph,
                self.canvas,
                self,  # Pass input_handler (self)
            ),
        }

        self.current_mode_controller = self.mode_controllers[self.current_mode]

    def set_mode(self, mode):
        """
        Set the current interaction mode.

        Args:
            mode (str): The mode to set (NORMAL_MODE or EDIT_MODE)
        """
        if mode not in [self.NORMAL_MODE, self.EDIT_MODE]:
            return

        self.current_mode = mode
        self.current_mode_controller = self.mode_controllers[mode]

        # Reset interaction state
        self.hover_state.clear()

        # Update cursor based on mode
        if mode == self.EDIT_MODE:
            self.canvas.setCursor(Qt.CrossCursor)
        else:
            self.canvas.setCursor(Qt.ArrowCursor)

        # Emit signal
        self.mode_changed.emit(self.current_mode)

    def request_mode_switch(self, requested_mode):
        """
        Request to switch the interaction mode.

        Args:
            requested_mode (str): The mode to switch to.
        """
        # Basic validation, could be expanded
        if requested_mode in self.mode_controllers:
            # TODO: Add logic here if specific conditions must be met before switching
            # e.g., ensure no ongoing operation like dragging

            # Set the new mode
            self.set_mode(requested_mode)

            # Optionally, update the edit target groups if switching to edit mode
            if requested_mode == self.EDIT_MODE:
                edit_controller = self.mode_controllers[self.EDIT_MODE]
                # Use currently selected groups as target for edit mode
                edit_controller.set_edit_target_groups(
                    self.selection_model.selected_groups.copy()
                )
                # Clear node selection when entering edit mode, keep group selection
                self.selection_model.select_nodes([], add_to_selection=False)
            elif requested_mode == self.NORMAL_MODE:
                # Clear edit targets when switching back to normal
                edit_controller = self.mode_controllers[self.EDIT_MODE]
                edit_controller.set_edit_target_groups([])

            # TODO: Emit a signal if UI needs to update based on mode switch
            # self.canvas.mode_changed.emit(requested_mode) # Example if canvas had signal

    def handle_mouse_press(self, event, widget_point):
        """
        Handle mouse press events.

        Args:
            event: The mouse event
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Convert to graph coordinates
        graph_point = self._widget_to_graph_point(widget_point)

        # Handle middle button panning regardless of mode
        if event.button() == Qt.MiddleButton:
            self._start_panning(widget_point)
            return True

        # Handle right button for context menu
        if event.button() == Qt.RightButton:
            return self.current_mode_controller.handle_context_menu(event, widget_point)

        # Delegate other mouse presses to current mode controller
        return self.current_mode_controller.handle_mouse_press(
            event, graph_point, widget_point
        )

    def handle_mouse_move(self, event, widget_point):
        """
        Handle mouse move events.

        Args:
            event: The mouse event
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Convert to graph coordinates
        graph_point = self._widget_to_graph_point(widget_point)

        # Handle panning if active
        if self.panning:
            self._update_panning(widget_point)
            return True

        # Delegate to current mode controller
        return self.current_mode_controller.handle_mouse_move(
            event, graph_point, widget_point
        )

    def handle_mouse_release(self, event, widget_point):
        """
        Handle mouse release events.

        Args:
            event: The mouse event
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Convert to graph coordinates
        graph_point = self._widget_to_graph_point(widget_point)

        # Handle panning end
        if event.button() == Qt.MiddleButton and self.panning:
            self._end_panning()
            return True

        # Delegate to current mode controller
        return self.current_mode_controller.handle_mouse_release(
            event, graph_point, widget_point
        )

    def handle_key_press(self, event):
        """
        Handle key press events.

        Args:
            event: The key event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Grid toggle ('G') is now mode-specific (Normal mode only)

        # Delegate key presses to current mode controller
        return self.current_mode_controller.handle_key_press(event)

    def handle_wheel(self, event, widget_point):
        """
        Handle mouse wheel events for zooming.

        Args:
            event: The wheel event
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Convert mouse cursor position to graph coordinate system
        mouse_graph_pos = self._widget_to_graph_point(widget_point)

        # Calculate zoom magnification
        delta = event.angleDelta().y()
        zoom_sensitivity = config.get_constant("zoom.factor", 1200.0)
        zoom_factor = 1.0 + delta / zoom_sensitivity
        new_zoom = self.view_state.zoom * zoom_factor

        # Store old zoom for calculation
        old_zoom = self.view_state.zoom

        # Set new zoom (will be clamped in the model)
        self.view_state.zoom = new_zoom

        # Adjust pan offset to maintain mouse cursor position relative to the new origin
        canvas_center = self.canvas.rect().center()
        new_pan = (
            widget_point - canvas_center - (mouse_graph_pos * self.view_state.zoom)
        )
        self.view_state.pan_offset = new_pan

        return True

    def _widget_to_graph_point(self, widget_point):
        """
        Convert a point from widget coordinates to graph coordinates.

        Args:
            widget_point: The point in widget coordinates

        Returns:
            QPointF: The point in graph coordinates
        """
        canvas_center = self.canvas.rect().center()
        # Reverse the transformation: subtract center offset, subtract pan, divide by zoom
        return (
            widget_point - canvas_center - self.view_state.pan_offset
        ) / self.view_state.zoom

    def _start_panning(self, widget_point):
        """
        Start a panning operation.

        Args:
            widget_point: The starting point in widget coordinates
        """
        self.panning = True
        self.view_state.start_panning(widget_point)

    def _update_panning(self, widget_point):
        """
        Update the panning operation.

        Args:
            widget_point: The current point in widget coordinates
        """
        self.view_state.update_panning(widget_point)

    def _end_panning(self):
        """End the panning operation."""
        self.panning = False
        self.view_state.end_panning()
