"""
Edit mode controller for handling input in edit mode.

This module provides the EditModeController class which handles
user interactions in the edit mode of the canvas.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtWidgets import QApplication, QWidget

from ...config import config
from ...gui.context_menus.edit_menu import EditContextMenu  # Moved and removed '+'
from ...models.connectivity import find_intersecting_edges
from ..mode_controller import ModeController
from .edit_mode_helpers import (
    AllForOneModeHelper,
    BridgeModeHelper,
    ConnectModeHelper,
    DragHelper,
    EdgeHelper,
    KnifeModeHelper,
    ParallelModeHelper,
)


class EditModeController(ModeController):
    """
    Controller for handling input in edit mode.

    Edit mode allows users to create and modify connections between nodes,
    as well as perform operations like cutting edges with the knife tool.

    Attributes:
        Inherits all attributes from ModeController
        edit_target_groups (list): Groups being edited
        edit_submode (str): Current edit submode
        current_edge_start: Starting node for edge creation
        temp_edge_end: Temporary end point for edge preview
        knife_path (list): Points in the knife path
        highlighted_edges (list): Edges intersecting with knife path
        is_cutting (bool): Whether cutting operation is active
        all_for_one_selected_nodes (list): Nodes selected in All-For-One mode
        parallel_selected_nodes (list): Nodes selected in Parallel mode
        parallel_edge_endpoints (list): Endpoints for parallel edges
        bridge_selected_groups (list): Groups selected for bridge connection
        canvas (QWidget): The canvas widget this controller interacts with.
    """

    def __init__(
        self,
        view_state,
        selection_model,
        hover_state,
        graph,
        canvas: QWidget,
        input_handler,  # Add input_handler parameter
    ):
        """
        Initialize the edit mode controller.

        Args:
            view_state: The view state model
            selection_model: The selection model
            hover_state: The hover state model
            graph: The graph model
        """
        super().__init__(view_state, selection_model, hover_state, graph)

        # Edit mode specific state
        self.edit_target_groups = []

        # Edit submodes
        self.EDIT_SUBMODE_CONNECT = config.get_constant(
            "edit_submodes.connect", "connect"
        )
        self.EDIT_SUBMODE_KNIFE = config.get_constant("edit_submodes.knife", "knife")
        self.EDIT_SUBMODE_ALL_FOR_ONE = config.get_constant(
            "edit_submodes.all_for_one", "all_for_one"
        )
        self.EDIT_SUBMODE_PARALLEL = config.get_constant(
            "edit_submodes.parallel", "parallel"
        )
        self.EDIT_SUBMODE_BRIDGE = config.get_constant("edit_submodes.bridge", "bridge")

        self.edit_submode = self.EDIT_SUBMODE_CONNECT

        # Edge creation state
        self.current_edge_start = None
        self.temp_edge_end = None
        self.potential_target_node = None

        # Knife mode state
        self.knife_path = []
        self.highlighted_edges = []
        self.is_cutting = False

        # All-For-One connection mode state
        self.all_for_one_selected_nodes = []

        # Parallel connection mode state
        self.parallel_selected_nodes = []
        self.parallel_edge_endpoints = []
        self._pending_parallel_drag = False

        # Bridge connection mode state
        self.bridge_selected_groups = []
        self.bridge_floating_menus = {}
        self.bridge_preview_lines = []
        self.bridge_edge_nodes = {}
        self.bridge_connection_params = None

        self.canvas = canvas  # Store canvas reference
        # Initialize the context menu specific to this mode, passing the controller
        self.context_menu = EditContextMenu(self.canvas, self)
        self.input_handler = input_handler  # Store input_handler reference

    def set_edit_submode(self, submode):
        """
        Set the edit submode.

        Args:
            submode (str): The submode to set
        """
        old_submode = self.edit_submode
        self.edit_submode = submode

        # Reset state when changing submodes
        if old_submode == self.EDIT_SUBMODE_KNIFE:
            self.knife_path = []
            self.highlighted_edges = []
            self.is_cutting = False

        if (
            old_submode == self.EDIT_SUBMODE_ALL_FOR_ONE
            and submode != self.EDIT_SUBMODE_ALL_FOR_ONE
        ):
            self.all_for_one_selected_nodes = []

        if (
            old_submode == self.EDIT_SUBMODE_PARALLEL
            and submode != self.EDIT_SUBMODE_PARALLEL
        ):
            self.parallel_selected_nodes = []
            self.parallel_edge_endpoints = []

        if (
            old_submode == self.EDIT_SUBMODE_BRIDGE
            and submode != self.EDIT_SUBMODE_BRIDGE
        ):
            self.bridge_selected_groups = []
            self.bridge_floating_menus = {}
            self.bridge_preview_lines = []
            self.bridge_edge_nodes = {}

        # Update cursor based on submode
        if submode == self.EDIT_SUBMODE_KNIFE:
            # TODO: Create a custom knife cursor image if desired
            self.canvas.setCursor(Qt.CrossCursor)  # Use Cross for now
        elif submode in [
            self.EDIT_SUBMODE_ALL_FOR_ONE,
            self.EDIT_SUBMODE_PARALLEL,
            self.EDIT_SUBMODE_BRIDGE,
        ]:
            self.canvas.setCursor(Qt.ArrowCursor)
        else:  # Default connect mode
            self.canvas.setCursor(Qt.CrossCursor)

        # Emit mode changed signal via input handler to update UI
        mode_string = f"{self.input_handler.EDIT_MODE}/{submode}"
        self.input_handler.mode_changed.emit(mode_string)

    def set_edit_target_groups(self, groups):
        """
        Set the target groups for editing.

        Args:
            groups (list): The groups to edit
        """
        self.edit_target_groups = groups

    def handle_mouse_press(self, event, graph_point, widget_point):
        """
        Handle mouse press events in edit mode.

        In edit mode, left-click behavior depends on the current submode:
        - Connect: Select nodes to create edges
        - Knife: Start cutting operation
        - All-For-One: Select multiple source nodes
        - Parallel: Select multiple source nodes for parallel edges
        - Bridge: Select groups for bridge connections

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        if event.button() == Qt.LeftButton:
            if self.edit_submode == self.EDIT_SUBMODE_CONNECT:
                return self._handle_connect_mode_press(event, graph_point)
            elif self.edit_submode == self.EDIT_SUBMODE_KNIFE:
                return self._handle_knife_mode_press(event, graph_point)
            elif self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                return self._handle_all_for_one_mode_press(event, graph_point)
            elif self.edit_submode == self.EDIT_SUBMODE_PARALLEL:
                return self._handle_parallel_mode_press(event, graph_point)
            elif self.edit_submode == self.EDIT_SUBMODE_BRIDGE:
                return self._handle_bridge_mode_press(event, graph_point)

        elif event.button() == Qt.RightButton:
            # Right-click shows context menu (handled by canvas)
            return False

        return False

    def handle_mouse_move(self, event, graph_point, widget_point):
        """
        Handle mouse move events in edit mode.

        In edit mode, mouse movement behavior depends on the current submode.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Update hover state
        new_hovered_node = self.graph.find_node_at_position(graph_point)

        # When creating an edge, we're interested in potential target nodes
        if self.current_edge_start:
            # Store the previous potential target to check if it changed
            previous_target = self.potential_target_node

            # Save potential target node but don't change the main hover state
            self.potential_target_node = (
                new_hovered_node
                if new_hovered_node != self.current_edge_start
                else None
            )

            # If potential target changed, update hover state
            if previous_target != self.potential_target_node:
                self.hover_state.set_potential_target(self.potential_target_node)

            # Update edge preview
            self.temp_edge_end = graph_point

            # For parallel connection mode, update all edge endpoints
            if (
                self.edit_submode == self.EDIT_SUBMODE_PARALLEL
                and self.current_edge_start in self.parallel_selected_nodes
            ):
                self._update_parallel_edge_endpoints(graph_point)

            return True
        elif new_hovered_node != self.hover_state.hovered_node:
            # Update hover state with connected nodes and edges
            connected_nodes = []
            edges = []

            if new_hovered_node:
                # Find direct connected nodes and edges
                for edge in self.graph.edges:
                    if edge[0] == new_hovered_node.id:
                        target_node = next(
                            (n for n in self.graph.nodes if n.id == edge[1]), None
                        )
                        if target_node:
                            connected_nodes.append(target_node)
                            edges.append((new_hovered_node, target_node))
                    elif edge[1] == new_hovered_node.id:
                        source_node = next(
                            (n for n in self.graph.nodes if n.id == edge[0]), None
                        )
                        if source_node:
                            connected_nodes.append(source_node)
                            edges.append((source_node, new_hovered_node))

                # Add selected nodes in special modes
                if (
                    self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE
                    and new_hovered_node in self.all_for_one_selected_nodes
                ):
                    for node in self.all_for_one_selected_nodes:
                        if node != new_hovered_node and node not in connected_nodes:
                            connected_nodes.append(node)

                if (
                    self.edit_submode == self.EDIT_SUBMODE_PARALLEL
                    and new_hovered_node in self.parallel_selected_nodes
                ):
                    for node in self.parallel_selected_nodes:
                        if node != new_hovered_node and node not in connected_nodes:
                            connected_nodes.append(node)

            self.hover_state.update_hover_state(
                new_hovered_node, connected_nodes, edges
            )

        # Handle dragging
        if self.dragging and self.drag_start:
            self._handle_dragging(graph_point)
            return True

        # Update selection rectangle
        if self.is_selecting:
            self.selection_rect_end = QPointF(graph_point)
            return True

        # Handle knife mode
        if self.edit_submode == self.EDIT_SUBMODE_KNIFE and self.is_cutting:
            self.knife_path.append((graph_point.x(), graph_point.y()))

            # Find intersecting edges that belong to the target groups
            self.highlighted_edges = find_intersecting_edges(
                self.graph, self.knife_path, self.edit_target_groups
            )
            return True

        return False

    def handle_mouse_release(self, event, graph_point, widget_point):
        """
        Handle mouse release events in edit mode.

        In edit mode, mouse release behavior depends on the current submode.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        if event.button() == Qt.LeftButton:
            # First check if we're finishing a node drag operation
            if self.dragging:
                self.dragging = False
                self.drag_start = None
                self.drag_start_node = None
                return True

            # Check if we have a pending drag operation that was never started
            elif self._pending_parallel_drag:
                # If we reached here, the user clicked on a node but didn't drag far enough
                # to start edge creation, so we should deselect the node now
                if self.drag_start_node:
                    if (
                        self.edit_submode == self.EDIT_SUBMODE_PARALLEL
                        and self.drag_start_node in self.parallel_selected_nodes
                    ):
                        # Remove node from parallel selection
                        self.parallel_selected_nodes.remove(self.drag_start_node)
                    elif (
                        self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE
                        and self.drag_start_node in self.all_for_one_selected_nodes
                    ):
                        # Remove node from all-for-one selection
                        self.all_for_one_selected_nodes.remove(self.drag_start_node)

                # Reset state
                self._pending_parallel_drag = False
                self.drag_start_node = None
                self.press_pos = None
                return True

            # Then handle edge creation if active
            elif self.current_edge_start:
                if self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                    self._complete_all_for_one_edge_creation(graph_point)
                elif self.edit_submode == self.EDIT_SUBMODE_PARALLEL:
                    self._complete_parallel_connection(graph_point)
                else:
                    self._complete_edge_creation(graph_point)
                return True

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
                return True

            # Handle rectangle selection completion
            elif (
                self.is_selecting
                and self.selection_rect_start
                and self.selection_rect_end
            ):
                self._complete_rectangle_selection()
                return True

        return False

    def handle_key_press(self, event):
        """
        Handle key press events in edit mode.

        Args:
            event: The key event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        if event.key() == Qt.Key_Escape:
            # Handle special edit submodes
            if self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                # Cancel All-For-One connection mode and go back to connect mode
                self.all_for_one_selected_nodes = []
                self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
                return True
            elif self.edit_submode == self.EDIT_SUBMODE_PARALLEL:
                # Cancel Parallel connection mode and go back to connect mode
                self.parallel_selected_nodes = []
                self.parallel_edge_endpoints = []
                self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
                return True
            elif self.edit_submode == self.EDIT_SUBMODE_BRIDGE:
                # In Bridge mode, ESC clears selected groups or exits the mode
                if self.bridge_selected_groups:
                    # Clear selected groups
                    self.bridge_selected_groups = []
                    self.bridge_floating_menus = {}
                    self.bridge_edge_nodes = {}
                    self.bridge_preview_lines = {}
                    return True
                else:
                    # Exit bridge mode if no groups are selected
                    self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
                    return True

            # Only when deselection using the ESC key is enabled
            if self.selection_model.is_deselect_method_enabled("escape"):
                self.selection_model.clear_selection()
                return True

        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # In All-For-One connection mode, confirm the connections and return to connect mode
            if self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE:
                # Confirm connections by exiting All-For-One connection mode but keeping any changes
                self.set_edit_submode(self.EDIT_SUBMODE_CONNECT)
                return True
            elif (
                self.edit_submode == self.EDIT_SUBMODE_BRIDGE
                and len(self.bridge_selected_groups) == 2
            ):
                # Open bridge connection window when Enter is pressed with 2 groups selected
                # This will be handled by the canvas
                return False

        elif event.key() == Qt.Key_Delete:
            # Delete key in edit mode: Delete selected edges
            if self.selection_model.selected_edges:
                for source_node, target_node in self.selection_model.selected_edges:
                    edge_to_remove = None
                    for edge in self.graph.edges:
                        if edge[0] == source_node.id and edge[1] == target_node.id:
                            edge_to_remove = edge
                            break
                    if edge_to_remove:
                        self.graph.edges.remove(edge_to_remove)
                self.selection_model.selected_edges = []
                return True

        elif event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            if self.edit_submode in [
                self.EDIT_SUBMODE_ALL_FOR_ONE,
                self.EDIT_SUBMODE_PARALLEL,
            ]:
                # Handle Ctrl+A for both All-For-One and Parallel modes
                eligible_nodes = []
                for group in self.edit_target_groups:
                    eligible_nodes.extend(group.get_nodes(self.graph.nodes))

                # Check if all eligible nodes are already selected
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
                return True
            else:
                # Default behavior in other edit submodes: Select all edges
                all_edges = []
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
                            all_edges.append((source_node, target_node))
                    except StopIteration:
                        continue

                self.selection_model.select_edges(all_edges)
                return True

        return False

    # Helper methods that delegate to the helper classes

    def _handle_connect_mode_press(self, event, graph_point):
        """Delegate to ConnectModeHelper"""
        return ConnectModeHelper.handle_press(self, event, graph_point)

    def _handle_knife_mode_press(self, event, graph_point):
        """Delegate to KnifeModeHelper"""
        return KnifeModeHelper.handle_press(self, event, graph_point)

    def _handle_all_for_one_mode_press(self, event, graph_point):
        """Delegate to AllForOneModeHelper"""
        return AllForOneModeHelper.handle_press(self, event, graph_point)

    def _handle_parallel_mode_press(self, event, graph_point):
        """Delegate to ParallelModeHelper"""
        return ParallelModeHelper.handle_press(self, event, graph_point)

    def _handle_bridge_mode_press(self, event, graph_point):
        """Delegate to BridgeModeHelper"""
        return BridgeModeHelper.handle_press(self, event, graph_point)

    def _handle_dragging(self, graph_point):
        """Delegate to DragHelper"""
        DragHelper.handle_dragging(self, graph_point)

    def _complete_edge_creation(self, graph_point):
        """Delegate to ConnectModeHelper"""
        ConnectModeHelper.complete_edge_creation(self, graph_point)

    def _complete_all_for_one_edge_creation(self, graph_point):
        """Delegate to AllForOneModeHelper"""
        AllForOneModeHelper.complete_edge_creation(self, graph_point)

    def _complete_parallel_connection(self, graph_point):
        """Delegate to ParallelModeHelper"""
        ParallelModeHelper.complete_connection(self, graph_point)

    def _update_parallel_edge_endpoints(self, graph_point):
        """Delegate to ParallelModeHelper"""
        ParallelModeHelper.update_edge_endpoints(self, graph_point)

    def _find_edge_at_position(self, point, tolerance=5):
        """Delegate to EdgeHelper"""
        return EdgeHelper.find_edge_at_position(self, point, tolerance)

    def handle_context_menu(self, event, widget_point):
        """
        Handle context menu requests in edit mode.

        Args:
            event: The mouse event that triggered the context menu
            widget_point: The point in widget coordinates where the menu should appear

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Prepare the menu (update action states)
        self.context_menu.prepare_for_display()
        # Map the widget point to global coordinates for the menu
        global_point = self.canvas.mapToGlobal(widget_point)
        # Show the edit mode context menu at the global position
        self.context_menu.exec_(global_point)
        return True
