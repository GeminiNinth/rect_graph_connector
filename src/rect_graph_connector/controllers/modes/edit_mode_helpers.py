"""
Helper classes for the EditModeController.

This module provides helper classes for the EditModeController to handle
different edit submodes and operations.
"""

from PyQt5.QtCore import QPointF, Qt


class ConnectModeHelper:
    """
    Helper class for handling connect mode operations.
    """

    @staticmethod
    def handle_press(controller, event, graph_point):
        """
        Handle mouse press in connect mode.

        Args:
            controller: The EditModeController instance
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # First check for edge selection
        edge = controller._find_edge_at_position(graph_point)
        shift_pressed = event.modifiers() & Qt.ShiftModifier

        if edge:
            # Check if at least one endpoint of the edge belongs to target groups
            source_group = controller.graph.get_group_for_node(edge[0])
            target_group = controller.graph.get_group_for_node(edge[1])
            if (
                source_group in controller.edit_target_groups
                or target_group in controller.edit_target_groups
            ):
                # Handle edge selection with proper toggling
                if (
                    edge in controller.selection_model.selected_edges
                    and not shift_pressed
                ):
                    # Deselect if already selected and shift is not pressed
                    controller.selection_model.deselect_edge(edge)
                else:
                    if not shift_pressed:
                        # Clear previous selection if shift is not pressed
                        controller.selection_model.selected_edges = []
                    if edge not in controller.selection_model.selected_edges:
                        controller.selection_model.select_edge(
                            edge, add_to_selection=True
                        )

                return True

        # If no edge was clicked, proceed with node selection for edge creation
        node = controller.graph.find_node_at_position(graph_point)
        if node:
            # Check if node belongs to any of the target groups
            node_belongs_to_target = False
            node_group = controller.graph.get_group_for_node(node)

            if controller.edit_target_groups and node_group:
                for group in controller.edit_target_groups:
                    if node in group.get_nodes(controller.graph.nodes):
                        node_belongs_to_target = True
                        break

            if node_belongs_to_target:
                # Check for shift key to determine if we're dragging or creating an edge
                if event.modifiers() & Qt.ShiftModifier:
                    # With shift, drag the node
                    controller.dragging = True
                    controller.drag_start = QPointF(graph_point)
                    # Select the node
                    controller.selection_model.select_node(node)
                else:
                    # By default, create an edge (original behavior)
                    # Clear edge selection when starting new edge creation
                    controller.selection_model.selected_edges = []
                    controller.current_edge_start = node
                    controller.temp_edge_end = QPointF(graph_point)

                return True

        # If no valid node was clicked, start rectangle selection
        controller.is_selecting = True
        controller.selection_rect_start = QPointF(graph_point)
        controller.selection_rect_end = QPointF(graph_point)
        return True

    @staticmethod
    def complete_edge_creation(controller, graph_point):
        """
        Complete the edge creation process by connecting to a target node.

        Args:
            controller: The EditModeController instance
            graph_point: The point where the mouse was released
        """
        target_node = controller.graph.find_node_at_position(graph_point)
        if target_node and target_node != controller.current_edge_start:
            # Check if the source node belongs to any of the target groups
            source_belongs = False
            for group in controller.edit_target_groups:
                if controller.current_edge_start in group.get_nodes(
                    controller.graph.nodes
                ):
                    source_belongs = True
                    break

            # Add edge if the source node belongs to the edit target groups
            if source_belongs:
                controller.graph.add_edge(controller.current_edge_start, target_node)

        # Reset
        controller.current_edge_start = None
        controller.temp_edge_end = None
        controller.potential_target_node = None


class KnifeModeHelper:
    """
    Helper class for handling knife mode operations.
    """

    @staticmethod
    def handle_press(controller, event, graph_point):
        """
        Handle mouse press in knife mode.

        Args:
            controller: The EditModeController instance
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Start cutting operation
        controller.is_cutting = True
        controller.knife_path = [(graph_point.x(), graph_point.y())]
        controller.highlighted_edges = []
        return True


class AllForOneModeHelper:
    """
    Helper class for handling All-For-One mode operations.
    """

    @staticmethod
    def handle_press(controller, event, graph_point):
        """
        Handle mouse press in All-For-One mode.

        Args:
            controller: The EditModeController instance
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # In All-For-One connection mode, left click toggles node selection
        node = controller.graph.find_node_at_position(graph_point)
        shift_pressed = event.modifiers() & Qt.ShiftModifier

        if node:
            # Check if node belongs to any of the target groups
            node_belongs_to_target = False
            node_group = controller.graph.get_group_for_node(node)

            if controller.edit_target_groups and node_group:
                for group in controller.edit_target_groups:
                    if node in group.get_nodes(controller.graph.nodes):
                        node_belongs_to_target = True
                        break

            if node_belongs_to_target:
                # Toggle selection: select if not selected, deselect if already selected
                if node in controller.all_for_one_selected_nodes:
                    # If node is already selected, prepare for possible drag operation
                    # We'll track if this is a drag or just a click when the mouse moves
                    controller._pending_parallel_drag = True
                    controller.press_pos = QPointF(graph_point)
                    controller.drag_start_node = node
                else:
                    # If node is not selected
                    if not shift_pressed:
                        # Clear selection if shift isn't pressed
                        controller.all_for_one_selected_nodes = []
                    # Add node to selection
                    controller.all_for_one_selected_nodes.append(node)

                return True

        # If no node was clicked, start rectangle selection
        controller.is_selecting = True
        controller.selection_rect_start = QPointF(graph_point)
        controller.selection_rect_end = QPointF(graph_point)
        if not shift_pressed:
            controller.all_for_one_selected_nodes = []
        return True

    @staticmethod
    def complete_edge_creation(controller, graph_point):
        """
        Complete the All-For-One connection creation process.

        Args:
            controller: The EditModeController instance
            graph_point: The point where the mouse was released
        """
        target_node = controller.graph.find_node_at_position(graph_point)
        if not target_node or target_node == controller.current_edge_start:
            # No target node or trying to connect to self
            controller.current_edge_start = None
            controller.temp_edge_end = None
            return

        # Create edges from all selected nodes to the target node
        for source_node in controller.all_for_one_selected_nodes:
            if source_node != target_node:  # Avoid self-loops
                controller.graph.add_edge(source_node, target_node)

        # Reset
        controller.current_edge_start = None
        controller.temp_edge_end = None
        controller.potential_target_node = None


class ParallelModeHelper:
    """
    Helper class for handling Parallel mode operations.
    """

    @staticmethod
    def handle_press(controller, event, graph_point):
        """
        Handle mouse press in Parallel mode.

        Args:
            controller: The EditModeController instance
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # In Parallel connection mode, left click either starts edge creation or rectangle selection
        node = controller.graph.find_node_at_position(graph_point)
        shift_pressed = event.modifiers() & Qt.ShiftModifier

        if node:
            # Check if node belongs to any of the target groups
            node_belongs_to_target = False
            node_group = controller.graph.get_group_for_node(node)

            if controller.edit_target_groups and node_group:
                for group in controller.edit_target_groups:
                    if node in group.get_nodes(controller.graph.nodes):
                        node_belongs_to_target = True
                        break

            if node_belongs_to_target:
                # Toggle selection: select if not selected, deselect if already selected
                if node in controller.parallel_selected_nodes:
                    # If node is already selected, prepare for possible drag operation
                    # We'll track if this is a drag or just a click when the mouse moves
                    controller._pending_parallel_drag = True
                    controller.press_pos = QPointF(graph_point)
                    controller.drag_start_node = node
                else:
                    # If node is not selected
                    if not shift_pressed:
                        # Clear selection if shift isn't pressed
                        controller.parallel_selected_nodes = []
                    # Add node to selection
                    controller.parallel_selected_nodes.append(node)

                return True

        # If no node was clicked, start rectangle selection
        controller.is_selecting = True
        controller.selection_rect_start = QPointF(graph_point)
        controller.selection_rect_end = QPointF(graph_point)
        # Clear selection if shift is not pressed
        if not shift_pressed:
            controller.parallel_selected_nodes = []
        return True

    @staticmethod
    def complete_connection(controller, graph_point):
        """
        Complete the Parallel connection process.

        Args:
            controller: The EditModeController instance
            graph_point: The point where the mouse was released
        """
        if not controller.current_edge_start or not controller.parallel_selected_nodes:
            return

        # Calculate the displacement vector from the drag start node
        start_pos = QPointF(
            controller.current_edge_start.x, controller.current_edge_start.y
        )
        delta_vector = graph_point - start_pos

        # Create edges for each selected node if a target node exists at the endpoint
        for source_node in controller.parallel_selected_nodes:
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

            for node in controller.graph.nodes:
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
                for group in controller.edit_target_groups:
                    if source_node in group.get_nodes(controller.graph.nodes):
                        source_belongs = True
                        break

                # Add edge if source node belongs to the edit target groups
                if source_belongs:
                    controller.graph.add_edge(source_node, target_node)

        # Reset
        controller.current_edge_start = None
        controller.temp_edge_end = None
        controller.parallel_edge_endpoints = []
        controller.potential_target_node = None

    @staticmethod
    def update_edge_endpoints(controller, graph_point):
        """
        Update the endpoints for parallel edges during dragging.

        Args:
            controller: The EditModeController instance
            graph_point: The current mouse position
        """
        # Calculate direction and distance for the drag
        start_pos = QPointF(
            controller.current_edge_start.x, controller.current_edge_start.y
        )
        delta_vector = graph_point - start_pos

        # Update endpoints for all selected nodes
        controller.parallel_edge_endpoints = []
        for node in controller.parallel_selected_nodes:
            if node:
                node_pos = QPointF(node.x, node.y)
                # Calculate the end point by adding the same delta vector
                end_point = (
                    node_pos.x() + delta_vector.x(),
                    node_pos.y() + delta_vector.y(),
                )
                controller.parallel_edge_endpoints.append(end_point)


class BridgeModeHelper:
    """
    Helper class for handling Bridge mode operations.
    """

    @staticmethod
    def handle_press(controller, event, graph_point):
        """
        Handle mouse press in Bridge mode.

        Args:
            controller: The EditModeController instance
            event: The mouse event
            graph_point: The point in graph coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # In Bridge connection mode, left click selects NodeGroups
        # First check if the click is inside a floating menu
        clicked_menu = False
        for group_id, menu in controller.bridge_floating_menus.items():
            if hasattr(menu, "contains") and menu.contains(graph_point):
                # Handle floating menu click (e.g., change edge highlighting position)
                if hasattr(menu, "handle_click"):
                    new_position = menu.handle_click(graph_point)
                    if new_position:
                        # Update edge nodes for the group based on new highlight position
                        for i, group in enumerate(controller.bridge_selected_groups):
                            if group.id == group_id:
                                if i == 0 and hasattr(
                                    controller.bridge_connection_params,
                                    "source_highlight_pos",
                                ):
                                    controller.bridge_connection_params.source_highlight_pos = (
                                        new_position
                                    )
                                elif hasattr(
                                    controller.bridge_connection_params,
                                    "target_highlight_pos",
                                ):
                                    controller.bridge_connection_params.target_highlight_pos = (
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
        for g in controller.graph.node_groups:
            # Simple check if point is within group bounds
            group_nodes = g.get_nodes(controller.graph.nodes)
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

        if group and group in controller.edit_target_groups:
            # Handle NodeGroup selection for bridge mode
            if group in controller.bridge_selected_groups:
                # If already selected, deselect it
                controller.bridge_selected_groups.remove(group)
            else:
                # If not already selected, add to selected groups (max 2)
                if len(controller.bridge_selected_groups) >= 2:
                    # If already have 2 groups, remove the first one (FIFO)
                    controller.bridge_selected_groups.pop(0)

                # Add new group to selected groups
                controller.bridge_selected_groups.append(group)

            return True

        return False


class DragHelper:
    """
    Helper class for handling node dragging operations.
    """

    @staticmethod
    def handle_dragging(controller, graph_point):
        """
        Handle dragging of selected nodes.

        Args:
            controller: The EditModeController instance
            graph_point: The current point in graph coordinates
        """
        if not controller.selection_model.selected_nodes:
            return

        dx = graph_point.x() - controller.drag_start.x()
        dy = graph_point.y() - controller.drag_start.y()

        if controller.view_state.grid_visible and controller.view_state.snap_to_grid:
            # Get reference node for snapping
            reference_node = None
            if (
                controller.drag_start_node
                and controller.drag_start_node
                in controller.selection_model.selected_nodes
            ):
                reference_node = controller.drag_start_node
            elif controller.selection_model.selected_nodes:
                reference_node = controller.selection_model.selected_nodes[0]
            else:
                return

            # Calculate target position for reference node
            target_x = reference_node.x + dx
            target_y = reference_node.y + dy

            # Snap to grid
            snapped_x, snapped_y = controller._snap_to_grid_point(target_x, target_y)

            # Calculate adjusted displacement
            adjusted_dx = snapped_x - reference_node.x
            adjusted_dy = snapped_y - reference_node.y

            # Move all selected nodes
            for node in controller.selection_model.selected_nodes:
                node.x += adjusted_dx
                node.y += adjusted_dy

            # Update drag start for next movement
            controller.drag_start = QPointF(
                controller.drag_start.x() + adjusted_dx,
                controller.drag_start.y() + adjusted_dy,
            )
        else:
            # Normal movement without snapping
            for node in controller.selection_model.selected_nodes:
                node.move(dx, dy)

            # Update drag start for next movement
            controller.drag_start = graph_point


class EdgeHelper:
    """
    Helper class for edge-related operations.
    """

    @staticmethod
    def find_edge_at_position(controller, point, tolerance=5):
        """
        Find an edge near the given point in graph coordinates.

        Args:
            controller: The EditModeController instance
            point: The point in graph coordinates
            tolerance: Maximum distance from point to edge to be considered a hit

        Returns:
            tuple: (source_node, target_node) if an edge is found, None otherwise
        """
        # Convert tolerance to graph coordinates
        scaled_tolerance = tolerance / controller.view_state.zoom

        for edge in controller.graph.edges:
            try:
                # Get the actual node objects
                source_node = next(n for n in controller.graph.nodes if n.id == edge[0])
                target_node = next(n for n in controller.graph.nodes if n.id == edge[1])

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
