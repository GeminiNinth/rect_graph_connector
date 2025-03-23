"""
Edit mode controller for handling input in edit mode.

This module provides the EditModeController class which handles
user interactions in the edit mode of the canvas.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtWidgets import QApplication

from ..mode_controller import ModeController
from ...config import config
from ...models.connectivity import find_intersecting_edges


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
    """

    def __init__(self, view_state, selection_model, hover_state, graph):
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

        # Bridge connection mode state
        self.bridge_selected_groups = []
        self.bridge_floating_menus = {}
        self.bridge_preview_lines = []
        self.bridge_edge_nodes = {}
        self.bridge_connection_params = None

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

    # The rest of the implementation is in edit_mode_controller_part2.py
    from .edit_mode_controller_part2 import EditModeControllerPart2

    # Mix in the methods from part 2
    handle_mouse_release = EditModeControllerPart2.handle_mouse_release
    handle_key_press = EditModeControllerPart2.handle_key_press
    _handle_connect_mode_press = EditModeControllerPart2._handle_connect_mode_press
    _handle_knife_mode_press = EditModeControllerPart2._handle_knife_mode_press
    _handle_all_for_one_mode_press = (
        EditModeControllerPart2._handle_all_for_one_mode_press
    )
    _handle_parallel_mode_press = EditModeControllerPart2._handle_parallel_mode_press
    _handle_bridge_mode_press = EditModeControllerPart2._handle_bridge_mode_press
    _handle_dragging = EditModeControllerPart2._handle_dragging
    _complete_edge_creation = EditModeControllerPart2._complete_edge_creation
    _complete_all_for_one_edge_creation = (
        EditModeControllerPart2._complete_all_for_one_edge_creation
    )
    _complete_parallel_connection = (
        EditModeControllerPart2._complete_parallel_connection
    )
    _update_parallel_edge_endpoints = (
        EditModeControllerPart2._update_parallel_edge_endpoints
    )
    _find_edge_at_position = EditModeControllerPart2._find_edge_at_position
