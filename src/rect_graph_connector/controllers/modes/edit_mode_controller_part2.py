"""
Second part of the edit mode controller implementation.

This module contains additional methods for the EditModeController class
to handle various edit mode operations.
"""

from PyQt5.QtCore import QPointF, Qt


class EditModeControllerPart2:
    """
    Mixin class containing additional methods for EditModeController.

    This class is not meant to be instantiated directly, but rather
    to provide methods that will be mixed into the EditModeController class.
    """

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

    def _handle_connect_mode_press(self, event, graph_point):
        """
        Handle mouse press in connect mode.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # First check for edge selection
        edge = self._find_edge_at_position(graph_point)
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
                if edge in self.selection_model.selected_edges and not shift_pressed:
                    # Deselect if already selected and shift is not pressed
                    self.selection_model.deselect_edge(edge)
                else:
                    if not shift_pressed:
                        # Clear previous selection if shift is not pressed
                        self.selection_model.selected_edges = []
                    if edge not in self.selection_model.selected_edges:
                        self.selection_model.select_edge(edge, add_to_selection=True)

                return True

        # If no edge was clicked, proceed with node selection for edge creation
        node = self.graph.find_node_at_position(graph_point)
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
                # Check for shift key to determine if we're dragging or creating an edge
                if event.modifiers() & Qt.ShiftModifier:
                    # With shift, drag the node
                    self.dragging = True
                    self.drag_start = QPointF(graph_point)
                    # Select the node
                    self.selection_model.select_node(node)
                else:
                    # By default, create an edge (original behavior)
                    # Clear edge selection when starting new edge creation
                    self.selection_model.selected_edges = []
                    self.current_edge_start = node
                    self.temp_edge_end = QPointF(graph_point)

                return True

        # If no valid node was clicked, start rectangle selection
        self.is_selecting = True
        self.selection_rect_start = QPointF(graph_point)
        self.selection_rect_end = QPointF(graph_point)
        return True

    def _handle_knife_mode_press(self, event, graph_point):
        """
        Handle mouse press in knife mode.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Start cutting operation
        self.is_cutting = True
        self.knife_path = [(graph_point.x(), graph_point.y())]
        self.highlighted_edges = []
        return True

    def _handle_all_for_one_mode_press(self, event, graph_point):
        """
        Handle mouse press in All-For-One mode.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
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
                    self.press_pos = QPointF(graph_point)
                    self.drag_start_node = node
                else:
                    # If node is not selected
                    if not shift_pressed:
                        # Clear selection if shift isn't pressed
                        self.all_for_one_selected_nodes = []
                    # Add node to selection
                    self.all_for_one_selected_nodes.append(node)

                return True

        # If no node was clicked, start rectangle selection
        self.is_selecting = True
        self.selection_rect_start = QPointF(graph_point)
        self.selection_rect_end = QPointF(graph_point)
        if not shift_pressed:
            self.all_for_one_selected_nodes = []
        return True

    def _handle_parallel_mode_press(self, event, graph_point):
        """
        Handle mouse press in Parallel mode.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
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
                    self.press_pos = QPointF(graph_point)
                    self.drag_start_node = node
                else:
                    # If node is not selected
                    if not shift_pressed:
                        # Clear selection if shift isn't pressed
                        self.parallel_selected_nodes = []
                    # Add node to selection
                    self.parallel_selected_nodes.append(node)

                return True

        # If no node was clicked, start rectangle selection
        self.is_selecting = True
        self.selection_rect_start = QPointF(graph_point)
        self.selection_rect_end = QPointF(graph_point)
        # Clear selection if shift is not pressed
        if not shift_pressed:
            self.parallel_selected_nodes = []
        return True

    def _handle_bridge_mode_press(self, event, graph_point):
        """
        Handle mouse press in Bridge mode.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # In Bridge connection mode, left click selects NodeGroups
        # First check if the click is inside a floating menu
        clicked_menu = False
        for group_id, menu in self.bridge_floating_menus.items():
            if hasattr(menu, "contains") and menu.contains(graph_point):
                # Handle floating menu click (e.g., change edge highlighting position)
                if hasattr(menu, "handle_click"):
                    new_position = menu.handle_click(graph_point)
                    if new_position:
                        # Update edge nodes for the group based on new highlight position
                        for i, group in enumerate(self.bridge_selected_groups):
                            if group.id == group_id:
                                if i == 0 and hasattr(
                                    self.bridge_connection_params,
                                    "source_highlight_pos",
                                ):
                                    self.bridge_connection_params.source_highlight_pos = (
                                        new_position
                                    )
                                elif hasattr(
                                    self.bridge_connection_params,
                                    "target_highlight_pos",
                                ):
                                    self.bridge_connection_params.target_highlight_pos = (
                                        new_position
                                    )
                                break

                clicked_menu = True
                break

        if clicked_menu:
            # If we clicked a menu, don't process further
            return True

        # If click wasn't on a menu, check for NodeGroup selection
        group = None
        for g in self.graph.node_groups:
            # Simple check if point is within group bounds
            group_nodes = g.get_nodes(self.graph.nodes)
            if not group_nodes:
                continue

            # Calculate group boundary
            min_x = min(node.x - node.size / 2 for node in group_nodes)
            min_y = min(node.y - node.size / 2 for node in group_nodes)
            max_x = max(node.x + node.size / 2 for node in group_nodes)
            max_y = max(node.y + node.size / 2 for node in group_nodes)

            # Check if point is within group boundary
            if min_x <= graph_point.x() <= max_x and min_y <= graph_point.y() <= max_y:
                group = g
                break

        if group and group in self.edit_target_groups:
            # Handle NodeGroup selection for bridge mode
            if group in self.bridge_selected_groups:
                # If already selected, deselect it
                self.bridge_selected_groups.remove(group)
            else:
                # If not already selected, add to selected groups (max 2)
                if len(self.bridge_selected_groups) >= 2:
                    # If already have 2 groups, remove the first one (FIFO)
                    self.bridge_selected_groups.pop(0)

                # Add new group to selected groups
                self.bridge_selected_groups.append(group)

            return True

        return False

    def _handle_dragging(self, graph_point):
        """
        Handle dragging of selected nodes.

        Args:
            graph_point: The current point in graph coordinates
        """
        if not self.selection_model.selected_nodes:
            return

        dx = graph_point.x() - self.drag_start.x()
        dy = graph_point.y() - self.drag_start.y()

        if self.view_state.grid_visible and self.view_state.snap_to_grid:
            # Get reference node for snapping
            reference_node = None
            if (
                self.drag_start_node
                and self.drag_start_node in self.selection_model.selected_nodes
            ):
                reference_node = self.drag_start_node
            elif self.selection_model.selected_nodes:
                reference_node = self.selection_model.selected_nodes[0]
            else:
                return

            # Calculate target position for reference node
            target_x = reference_node.x + dx
            target_y = reference_node.y + dy

            # Snap to grid
            snapped_x, snapped_y = self._snap_to_grid_point(target_x, target_y)

            # Calculate adjusted displacement
            adjusted_dx = snapped_x - reference_node.x
            adjusted_dy = snapped_y - reference_node.y

            # Move all selected nodes
            for node in self.selection_model.selected_nodes:
                node.x += adjusted_dx
                node.y += adjusted_dy

            # Update drag start for next movement
            self.drag_start = QPointF(
                self.drag_start.x() + adjusted_dx, self.drag_start.y() + adjusted_dy
            )
        else:
            # Normal movement without snapping
            for node in self.selection_model.selected_nodes:
                node.move(dx, dy)

            # Update drag start for next movement
            self.drag_start = graph_point

    def _complete_edge_creation(self, graph_point):
        """
        Complete the edge creation process by connecting to a target node.

        Args:
            graph_point: The point where the mouse was released
        """
        target_node = self.graph.find_node_at_position(graph_point)
        if target_node and target_node != self.current_edge_start:
            # Check if the source node belongs to any of the target groups
            source_belongs = False
            for group in self.edit_target_groups:
                if self.current_edge_start in group.get_nodes(self.graph.nodes):
                    source_belongs = True
                    break

            # Add edge if the source node belongs to the edit target groups
            if source_belongs:
                self.graph.add_edge(self.current_edge_start, target_node)

        # Reset
        self.current_edge_start = None
        self.temp_edge_end = None
        self.potential_target_node = None

    def _complete_all_for_one_edge_creation(self, graph_point):
        """
        Complete the All-For-One connection creation process.

        Args:
            graph_point: The point where the mouse was released
        """
        target_node = self.graph.find_node_at_position(graph_point)
        if not target_node or target_node == self.current_edge_start:
            # No target node or trying to connect to self
            self.current_edge_start = None
            self.temp_edge_end = None
            return

        # Create edges from all selected nodes to the target node
        for source_node in self.all_for_one_selected_nodes:
            if source_node != target_node:  # Avoid self-loops
                self.graph.add_edge(source_node, target_node)

        # Reset
        self.current_edge_start = None
        self.temp_edge_end = None
        self.potential_target_node = None

    def _complete_parallel_connection(self, graph_point):
        """
        Complete the Parallel connection process.

        Args:
            graph_point: The point where the mouse was released
        """
        if not self.current_edge_start or not self.parallel_selected_nodes:
            return

        # Calculate the displacement vector from the drag start node
        start_pos = QPointF(self.current_edge_start.x, self.current_edge_start.y)
        delta_vector = graph_point - start_pos

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
        self.potential_target_node = None

    def _update_parallel_edge_endpoints(self, graph_point):
        """
        Update the endpoints for parallel edges during dragging.

        Args:
            graph_point: The current mouse position
        """
        # Calculate direction and distance for the drag
        start_pos = QPointF(self.current_edge_start.x, self.current_edge_start.y)
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

    def _find_edge_at_position(self, point, tolerance=5):
        """
        Find an edge near the given point in graph coordinates.

        Args:
            point: The point in graph coordinates
            tolerance: Maximum distance from point to edge to be considered a hit

        Returns:
            tuple: (source_node, target_node) if an edge is found, None otherwise
        """
        # Convert tolerance to graph coordinates
        scaled_tolerance = tolerance / self.view_state.zoom

        for edge in self.graph.edges:
            try:
                # Get the actual node objects
                source_node = next(n for n in self.graph.nodes if n.id == edge[0])
                target_node = next(n for n in self.graph.nodes if n.id == edge[1])

                # Calculate actual edge endpoints considering node sizes
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

                # Check if the point is within tolerance
                if distance <= scaled_tolerance:
                    return (source_node, target_node)

            except StopIteration:
                continue

        return None
