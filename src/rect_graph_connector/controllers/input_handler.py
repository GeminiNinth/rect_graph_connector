"""
Input handler for managing user interactions with the canvas.

This module provides the InputHandler class which centralizes all input processing
and delegates to appropriate mode controllers based on the current mode.
"""

from PyQt5.QtCore import QObject, QPointF, QRectF, Qt, pyqtSignal  # Import QRectF
from PyQt5.QtWidgets import QApplication, QWidget  # Import QApplication

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

        # Rectangle selection state (managed here, updated by controllers)
        self.is_selecting = False
        self.selection_rect_start: QPointF | None = None
        self.selection_rect_end: QPointF | None = None

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

    def update_selection_rectangle(
        self, start_point: QPointF | None, end_point: QPointF | None
    ):
        """
        Update the selection rectangle coordinates. Called by mode controllers.

        Args:
            start_point (QPointF | None): The starting point in graph coordinates.
            end_point (QPointF | None): The current end point in graph coordinates.
        """
        self.selection_rect_start = start_point
        self.selection_rect_end = end_point

    def start_rectangle_selection(self, start_point: QPointF):
        """
        Start rectangle selection. Called by mode controllers.

        Args:
            start_point (QPointF): The starting point in graph coordinates.
        """
        self.is_selecting = True
        self.selection_rect_start = start_point
        self.selection_rect_end = start_point  # Initialize end point

    def end_rectangle_selection(self):
        """
        End rectangle selection. Called by mode controllers.
        """
        self.is_selecting = False
        # Keep start/end points for potential use by the controller that finishes selection
        # They will be cleared when a new selection starts or mode changes etc.

    def clear_selection_rectangle(self):
        """Clear the selection rectangle state."""
        self.is_selecting = False
        self.selection_rect_start = None
        self.selection_rect_end = None

    @property
    def selection_rectangle_data(self) -> dict | None:
        """
        Get the current selection rectangle data for rendering.

        Returns:
            dict | None: A dictionary with 'start' and 'end' QPointF points
                          if selection is active, otherwise None.
        """
        if self.is_selecting and self.selection_rect_start and self.selection_rect_end:
            return {"start": self.selection_rect_start, "end": self.selection_rect_end}
        return None

    def _perform_rectangle_selection(self):
        """
        Performs the selection logic based on the current rectangle selection
        and the active mode/submode. Updates the appropriate selection lists.
        """
        if not self.selection_rectangle_data:
            self.clear_selection_rectangle()
            return

        start_point = self.selection_rectangle_data["start"]
        end_point = self.selection_rectangle_data["end"]
        selection_rect = QRectF(start_point, end_point).normalized()
        leftward_selection = end_point.x() < start_point.x()
        shift_pressed = QApplication.keyboardModifiers() & Qt.ShiftModifier

        # Determine target type based on mode
        if self.current_mode == self.NORMAL_MODE:
            # --- Normal Mode: Select NodeGroups ---
            # A group is selected if the rectangle selects any of its nodes according
            # to the leftward (intersect) or rightward (contain) rule.
            newly_selected_groups = []
            for group in self.graph.node_groups:
                group_nodes = group.get_nodes(self.graph.nodes)
                if not group_nodes:
                    continue

                group_should_be_selected = False
                if leftward_selection:
                    # Leftward: Select if ANY node intersects
                    for node in group_nodes:
                        node_rect = QRectF(
                            node.x - node.size / 2,
                            node.y - node.size / 2,
                            node.size,
                            node.size,
                        )
                        if selection_rect.intersects(node_rect):
                            group_should_be_selected = True
                            break
                else:
                    # Rightward: Select only if ALL nodes are contained
                    all_nodes_contained = True
                    for node in group_nodes:
                        node_rect = QRectF(
                            node.x - node.size / 2,
                            node.y - node.size / 2,
                            node.size,
                            node.size,
                        )
                        if not selection_rect.contains(node_rect):
                            all_nodes_contained = False
                            break
                    if all_nodes_contained:
                        group_should_be_selected = True

                if group_should_be_selected:
                    newly_selected_groups.append(group)

            # Update SelectionModel based on shift key
            if shift_pressed:
                for group in newly_selected_groups:
                    self.selection_model.select_group(group, add_to_selection=True)
            else:
                self.selection_model.select_groups(
                    newly_selected_groups
                )  # Replaces existing

            # Update selected nodes based on the final selected groups in the model
            # This should be done by the controller after this method returns.

        elif self.current_mode == self.EDIT_MODE:
            controller = self.current_mode_controller
            edit_submode = controller.edit_submode
            edit_target_groups = controller.edit_target_groups

            if edit_submode in [
                controller.EDIT_SUBMODE_ALL_FOR_ONE,
                controller.EDIT_SUBMODE_PARALLEL,
            ]:
                # --- All-For-One / Parallel Mode: Select Nodes ---
                newly_selected_nodes = []
                for node in self.graph.nodes:
                    node_rect = QRectF(
                        node.x - node.size / 2,
                        node.y - node.size / 2,
                        node.size,
                        node.size,
                    )
                    node_group = self.graph.get_group_for_node(node)
                    # Select only nodes belonging to the target groups for editing
                    if node_group and node_group in edit_target_groups:
                        node_should_be_selected = False
                        if leftward_selection:
                            if selection_rect.intersects(node_rect):
                                node_should_be_selected = True
                        else:
                            if selection_rect.contains(node_rect):
                                node_should_be_selected = True

                        if node_should_be_selected:
                            newly_selected_nodes.append(node)

                # Update the specific node list in the EditModeController
                target_list = None
                if edit_submode == controller.EDIT_SUBMODE_ALL_FOR_ONE:
                    target_list = controller.all_for_one_selected_nodes
                else:  # Parallel
                    target_list = controller.parallel_selected_nodes

                if shift_pressed:
                    # Add newly selected nodes without duplicates
                    current_ids = {n.id for n in target_list}
                    for node in newly_selected_nodes:
                        if node.id not in current_ids:
                            target_list.append(node)
                else:
                    # Replace selection
                    if edit_submode == controller.EDIT_SUBMODE_ALL_FOR_ONE:
                        controller.all_for_one_selected_nodes = newly_selected_nodes
                    else:  # Parallel
                        controller.parallel_selected_nodes = newly_selected_nodes

            else:  # Default Edit Mode (Connect) or others: Select Edges
                # --- Connect Mode: Select Edges ---
                newly_selected_edges = []
                for edge in self.graph.edges:
                    try:
                        source_node = next(
                            n for n in self.graph.nodes if n.id == edge[0]
                        )
                        target_node = next(
                            n for n in self.graph.nodes if n.id == edge[1]
                        )

                        # Check if edge belongs to target groups being edited
                        source_group = self.graph.get_group_for_node(source_node)
                        target_group = self.graph.get_group_for_node(target_node)
                        if not (
                            source_group in edit_target_groups
                            or target_group in edit_target_groups
                        ):
                            continue

                        # Check if edge should be selected based on rect and direction
                        source_pos = QPointF(source_node.x, source_node.y)
                        target_pos = QPointF(target_node.x, target_node.y)
                        edge_should_be_selected = False
                        if leftward_selection:
                            # Leftward: Select if edge intersects (either endpoint inside is sufficient)
                            if selection_rect.contains(
                                source_pos
                            ) or selection_rect.contains(target_pos):
                                edge_should_be_selected = True
                        else:
                            # Rightward: Select if edge is fully contained (both endpoints inside)
                            if selection_rect.contains(
                                source_pos
                            ) and selection_rect.contains(target_pos):
                                edge_should_be_selected = True

                        if edge_should_be_selected:
                            newly_selected_edges.append((source_node, target_node))
                    except StopIteration:
                        continue

                # Update selection model for edges
                if shift_pressed:
                    for edge_tuple in newly_selected_edges:
                        self.selection_model.select_edge(
                            edge_tuple, add_to_selection=True
                        )
                else:
                    self.selection_model.select_edges(
                        newly_selected_edges
                    )  # Replaces existing

        # Clear the rectangle state after processing
        self.clear_selection_rectangle()
        # This method doesn't need to return anything
