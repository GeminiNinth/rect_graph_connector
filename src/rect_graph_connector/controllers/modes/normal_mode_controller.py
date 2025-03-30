"""
Normal mode controller for handling input in normal mode.

This module provides the NormalModeController class which handles
user interactions in the normal mode of the canvas.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtWidgets import QApplication, QWidget

from ...config import config
from ...gui.context_menus.normal_menu import NormalContextMenu
from ..mode_controller import ModeController


class NormalModeController(ModeController):
    """
    Controller for handling input in normal mode.

    Normal mode is the default interaction mode where users can select,
    move, and manipulate node groups as a whole.

    Attributes:
        Inherits all attributes from ModeController
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
        """Initialize the normal mode controller."""
        super().__init__(view_state, selection_model, hover_state, graph)
        self.canvas = canvas
        self.input_handler = input_handler  # Store input_handler reference
        # Initialize the context menu specific to this mode, passing the controller
        self.context_menu = NormalContextMenu(
            self.canvas, self
        )  # Pass self (controller)
        self.drag_initial_positions = {}  # Store initial node positions on drag start

    def handle_mouse_press(self, event, graph_point, widget_point):
        """
        Handle mouse press events in normal mode.

        In normal mode, left-click selects and begins dragging nodes/groups,
        while right-click shows the context menu.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        if event.button() == Qt.LeftButton:
            # Find node or group under cursor
            node = self.graph.find_node_at_position(graph_point)
            shift_pressed = event.modifiers() & Qt.ShiftModifier

            if node:
                # Store the clicked node immediately for potential drag reference
                self.drag_start_node = node
                # Handle node click
                group = self.graph.get_group_for_node(node)
                if (
                    group
                    and group in self.selection_model.selected_groups
                    and not shift_pressed
                ):
                    # Set pending deselect flag if clicking on already selected group
                    if self.selection_model.is_deselect_method_enabled("reclick"):
                        self.pending_deselect = True
                        self.press_pos = QPointF(graph_point)
                else:
                    # Start dragging immediately
                    self.dragging = True
                    self.drag_start = QPointF(
                        graph_point
                    )  # Store the absolute start point of the drag
                    # self.drag_start_node is already set above
                    # Store initial positions of all selected nodes
                    self.drag_initial_positions = {
                        node.id: QPointF(node.x, node.y)
                        for node in self.selection_model.selected_nodes
                    }
                    # Also add the start node if it wasn't part of the selection yet (e.g., single node drag)
                    if (
                        self.drag_start_node
                        and self.drag_start_node.id not in self.drag_initial_positions
                    ):
                        self.drag_initial_positions[self.drag_start_node.id] = QPointF(
                            self.drag_start_node.x, self.drag_start_node.y
                        )

                    # Handle selection
                    if group:
                        if shift_pressed:
                            # Multi-selection with Shift
                            self.selection_model.select_group(
                                group, add_to_selection=True
                            )
                            self.graph.bring_group_to_front(group)
                        else:
                            # Single selection
                            self.selection_model.select_group(
                                group, add_to_selection=False
                            )
                            self.graph.bring_group_to_front(group)

                        # Update selected nodes (important to do this *before* storing initial positions)
                        self._update_selected_nodes_from_groups()
                        # Re-store initial positions now that selection is updated
                        self.drag_initial_positions = {
                            node.id: QPointF(node.x, node.y)
                            for node in self.selection_model.selected_nodes
                        }

                    else:
                        # Node without group
                        if not shift_pressed:
                            self.selection_model.clear_selection()
                        self.selection_model.select_node(node)
                        # Store initial position for the single selected node
                        self.drag_initial_positions = {node.id: QPointF(node.x, node.y)}

                return True
            else:
                # If no node is clicked, it's a background click
                # Background click - start rectangle selection
                self.is_selecting = True
                self.selection_rect_start = QPointF(graph_point)
                self.selection_rect_end = QPointF(graph_point)

                # Deselect if background click deselection is enabled and not shift-clicking
                if (
                    self.selection_model.is_deselect_method_enabled("background")
                    and self.selection_model.selected_groups
                    and not shift_pressed
                ):
                    self.selection_model.clear_selection()

                return True

        elif event.button() == Qt.RightButton:
            # Right-click shows context menu (handled by canvas)
            return False

        return False

    def handle_mouse_move(self, event, graph_point, widget_point):
        """
        Handle mouse move events in normal mode.

        In normal mode, mouse movement handles dragging nodes/groups
        and updating the selection rectangle.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Check for pending deselect and convert to drag if moved enough
        if self.pending_deselect and self.press_pos:
            drag_threshold = config.get_constant("interaction.drag_threshold", 5)
            if (graph_point - self.press_pos).manhattanLength() > drag_threshold:
                self.pending_deselect = False
                self.dragging = True
                self.drag_start = (
                    self.press_pos
                )  # Start drag from original press position
                # Store initial positions when drag confirmed after pending deselect
                self.drag_initial_positions = {
                    node.id: QPointF(node.x, node.y)
                    for node in self.selection_model.selected_nodes
                }
                if (
                    self.drag_start_node
                    and self.drag_start_node.id not in self.drag_initial_positions
                ):
                    self.drag_initial_positions[self.drag_start_node.id] = QPointF(
                        self.drag_start_node.x, self.drag_start_node.y
                    )

                # Move selected groups to front when starting drag
                for group in self.selection_model.selected_groups:
                    self.graph.bring_group_to_front(group)

        # Handle dragging
        if self.dragging and self.drag_start:
            self._handle_dragging(graph_point)
            return True

        # Update selection rectangle
        if self.is_selecting:
            self.selection_rect_end = QPointF(graph_point)
            return True

        return False

    def handle_mouse_release(self, event, graph_point, widget_point):
        """
        Handle mouse release events in normal mode.

        In normal mode, mouse release completes dragging operations
        and finalizes selection rectangles.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        if event.button() == Qt.LeftButton:
            # Handle pending deselect (short click on selected group)
            if self.pending_deselect:
                self.selection_model.clear_selection()
                self.pending_deselect = False
                return True

            # End dragging
            if self.dragging:
                self.dragging = False
                # Final snap after drag release if snap is enabled
                if self.view_state.snap_to_grid:
                    # Snap based on the node that was initially dragged
                    if (
                        self.drag_start_node
                        and self.drag_start_node.id in self.drag_initial_positions
                    ):
                        initial_ref_pos = self.drag_initial_positions[
                            self.drag_start_node.id
                        ]
                        current_ref_pos = QPointF(
                            self.drag_start_node.x, self.drag_start_node.y
                        )
                        snapped_target = self._snap_point_to_grid(
                            current_ref_pos
                        )  # Snap current pos

                        final_dx = snapped_target.x() - self.drag_start_node.x
                        final_dy = snapped_target.y() - self.drag_start_node.y

                        if abs(final_dx) > 0.1 or abs(final_dy) > 0.1:
                            for node in self.selection_model.selected_nodes:
                                node.x += final_dx
                                node.y += final_dy
                            self.canvas.update()
                    # else: Consider snapping groups if drag started on background? For now, do nothing extra.

                self.drag_start = None
                self.drag_start_node = None
                self.drag_initial_positions = {}  # Clear initial positions
                return True

            # Complete rectangle selection
            if (
                self.is_selecting
                and self.selection_rect_start
                and self.selection_rect_end
            ):
                left_to_right, min_x, min_y, width, height = (
                    self._complete_rectangle_selection()
                )
                rect = QRectF(min_x, min_y, width, height)

                # Find groups in the selection rectangle
                selected_groups = []
                for group in self.graph.node_groups:
                    group_nodes = group.get_nodes(self.graph.nodes)
                    if not group_nodes:
                        continue

                    # Check if group is in selection rectangle
                    group_in_rect = False
                    if left_to_right:
                        # Strict containment (all nodes must be inside)
                        group_in_rect = all(
                            rect.contains(node.x, node.y) for node in group_nodes
                        )
                    else:
                        # Intersection (any node inside is enough)
                        group_in_rect = any(
                            rect.contains(node.x, node.y) for node in group_nodes
                        )

                    if group_in_rect:
                        selected_groups.append(group)

                # Update selection
                shift_pressed = QApplication.keyboardModifiers() & Qt.ShiftModifier
                if selected_groups:
                    if shift_pressed:
                        # Add to current selection
                        for group in selected_groups:
                            self.selection_model.select_group(
                                group, add_to_selection=True
                            )
                    else:
                        # Replace current selection
                        self.selection_model.select_groups(selected_groups)

                    # Update selected nodes
                    self._update_selected_nodes_from_groups()

                return True

        return False

    def handle_key_press(self, event):
        """
        Handle key press events in normal mode.

        Args:
            event: The key event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Handle Escape key for deselection
        if event.key() == Qt.Key_Escape:
            if self.selection_model.is_deselect_method_enabled("escape"):
                self.selection_model.clear_selection()
                return True

        # Handle Delete key for deleting selected groups
        elif event.key() == Qt.Key_Delete:
            if self.selection_model.selected_groups:
                groups_to_delete = self.selection_model.selected_groups.copy()
                for group in groups_to_delete:
                    self.graph.delete_group(group)
                self.selection_model.clear_selection()
                # Update main window list if needed
                main_window = self.canvas.window()
                if hasattr(main_window, "_update_group_list"):
                    main_window._update_group_list()
                self.canvas.update()
                return True

        # Handle Ctrl+A for selecting all groups
        elif event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            if self.graph.node_groups:
                self.selection_model.select_groups(list(self.graph.node_groups))
                self._update_selected_nodes_from_groups()
                return True

        # Handle Ctrl+C for copying selected groups
        elif event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            if self.selection_model.selected_groups:
                # Store copied data in the context menu for now
                # Ideally, this would use a dedicated clipboard model/service
                self.context_menu.copied_groups_data = self.copy_selection()
                # Update paste action state in menu
                self.context_menu.paste_action.setEnabled(
                    self.context_menu.copied_groups_data is not None
                )
                return True

        # Handle Ctrl+V for pasting groups
        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            if self.context_menu.copied_groups_data:
                self.paste(self.context_menu.copied_groups_data)
                # Optionally clear clipboard after paste?
                # self.context_menu.copied_groups_data = None
                # self.context_menu.paste_action.setEnabled(False)
                return True

        # Handle E key for switching to Edit mode
        elif event.key() == Qt.Key_E and self.selection_model.selected_groups:
            # Request mode switch via InputHandler
            self.input_handler.request_mode_switch(self.input_handler.EDIT_MODE)
            return True

        # Handle R key for rotation
        elif event.key() == Qt.Key_R:
            if self.selection_model.selected_groups:
                shift_pressed = event.modifiers() & Qt.ShiftModifier
                if shift_pressed and len(self.selection_model.selected_groups) > 1:
                    # Rotate multiple groups around common center
                    self.graph.rotate_groups_around_center(
                        self.selection_model.selected_groups
                    )
                else:
                    # Rotate each group individually
                    self.graph.rotate_node_groups(self.selection_model.selected_groups)
                self.canvas.update()  # Trigger redraw after rotation
                return True

        # Handle G key for toggling grid
        elif event.key() == Qt.Key_G:
            self.view_state.grid_visible = not self.view_state.grid_visible
            # Emit signal if UI needs update (e.g., toolbar button)
            if hasattr(self.canvas, "grid_state_changed"):
                self.canvas.grid_state_changed.emit(
                    self.view_state.grid_visible, self.view_state.snap_to_grid
                )
            self.canvas.update()  # Trigger redraw
            return True  # Event handled

        return False

    def _handle_dragging(self, graph_point):
        """
        Handle dragging of selected nodes/groups. Snaps based on the initially
        clicked node (`drag_start_node`) if snap_to_grid is enabled.

        Args:
            graph_point: The current point in graph coordinates
        """
        if not self.selection_model.selected_nodes or not self.drag_start:
            return

        # Calculate total displacement from the absolute start of the drag
        total_dx = graph_point.x() - self.drag_start.x()
        total_dy = graph_point.y() - self.drag_start.y()

        # Determine the final displacement to apply
        final_dx = total_dx
        final_dy = total_dy
        movement_applied = False  # Flag to track if nodes actually moved

        if self.view_state.grid_visible and self.view_state.snap_to_grid:
            reference_node = self.drag_start_node
            if reference_node and reference_node.id in self.drag_initial_positions:
                # Get the initial position of the reference node
                initial_ref_pos = self.drag_initial_positions[reference_node.id]

                # Calculate the ideal target position based on total displacement
                ideal_target_x = initial_ref_pos.x() + total_dx
                ideal_target_y = initial_ref_pos.y() + total_dy

                # Snap the ideal target position to the grid
                snapped_target = self._snap_point_to_grid(
                    QPointF(ideal_target_x, ideal_target_y)
                )

                # Calculate the final displacement needed to move from initial to snapped target
                final_dx = snapped_target.x() - initial_ref_pos.x()
                final_dy = snapped_target.y() - initial_ref_pos.y()
            # else: No valid reference node, use raw displacement (final_dx/dy remain total_dx/dy)

        # Apply the final displacement relative to the *initial* positions
        if abs(final_dx) > 0.1 or abs(final_dy) > 0.1:
            for node in self.selection_model.selected_nodes:
                if node.id in self.drag_initial_positions:
                    initial_pos = self.drag_initial_positions[node.id]
                    new_x = initial_pos.x() + final_dx
                    new_y = initial_pos.y() + final_dy
                    # Check if position actually changed significantly before updating
                    if abs(new_x - node.x) > 0.01 or abs(new_y - node.y) > 0.01:
                        node.x = new_x
                        node.y = new_y
                        movement_applied = True

        # Trigger redraw if any node moved
        if movement_applied:
            self.canvas.update()
        # NOTE: drag_start is NOT updated here. It remains the initial press point.

    def _update_selected_nodes_from_groups(self):
        """Update selected nodes based on selected groups."""
        nodes = []
        for group in self.selection_model.selected_groups:
            nodes.extend(group.get_nodes(self.graph.nodes))
        self.selection_model.selected_nodes = nodes

    def _find_group_at_position(self, point):
        """
        Find a node group that contains the given point in graph coordinates.
        Returns the frontmost group (highest z-index) if multiple groups overlap.
        NOTE: This is likely unused now due to selection logic change.

        Args:
            point (QPointF): The point in graph coordinates

        Returns:
            The node group if found, otherwise None
        """
        # Get groups sorted by z-index (highest to lowest)
        sorted_groups = sorted(
            self.graph.node_groups, key=lambda g: g.z_index, reverse=True
        )

        # Detect all overlapping groups
        overlapping_groups = []

        for group in sorted_groups:
            group_nodes = group.get_nodes(self.graph.nodes)
            if not group_nodes:
                continue

            # Calculate group boundary with margin
            border_margin = config.get_dimension("group.border_margin", 5)
            effective_margin = border_margin / self.view_state.zoom
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

            # Check if point is within group boundary
            if min_x <= point.x() <= max_x and min_y <= point.y() <= max_y:
                overlapping_groups.append(group)

        # Return frontmost group if any
        return overlapping_groups[0] if overlapping_groups else None

    def handle_context_menu(self, event, widget_point):
        """
        Handle context menu requests in normal mode.

        Args:
            event: The mouse event that triggered the context menu
            widget_point: The point in widget coordinates where the menu should appear

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Map the widget point to global coordinates for the menu
        global_point = self.canvas.mapToGlobal(widget_point)
        # Show the normal mode context menu at the global position
        self.context_menu.exec_(global_point)
        return True

    def copy_selection(self):
        """
        Copies the selected groups' data.

        Returns:
            dict: Data representing the copied groups, nodes, and internal edges,
                  or None if no groups are selected.
        """
        if not self.selection_model.selected_groups:
            return None
        # Use the graph's copy_groups method
        copied_data = self.graph.copy_groups(self.selection_model.selected_groups)
        # Store this data temporarily within the controller or a dedicated clipboard model
        # For now, let the menu store it, but ideally, it belongs here.
        return copied_data

    def paste(self, copied_data):
        """
        Pastes the previously copied group data into the graph.

        Args:
            copied_data (dict): The data returned by copy_groups.
        """
        if not copied_data:
            return

        # Use the graph's paste_groups method
        # TODO: Determine appropriate offset, maybe based on cursor or last paste?
        offset_x = config.get_dimension("paste.offset_x", 40)
        offset_y = config.get_dimension("paste.offset_y", 40)
        new_groups = self.graph.paste_groups(copied_data, offset_x, offset_y)

        if new_groups:
            # Clear current selection and select the newly created groups
            self.selection_model.select_groups(new_groups)
            self._update_selected_nodes_from_groups()  # Update selected nodes as well

            # Trigger necessary updates (e.g., main window list, canvas redraw)
            # This might involve emitting signals or calling update methods
            # on the input_handler or canvas if necessary.
            # For now, assume SelectionModel signals trigger canvas update.

            # Update the parent window's group list (if possible)
            # This coupling is not ideal, consider signals/events later
            main_window = self.canvas.window()
            if hasattr(main_window, "_update_group_list"):
                main_window._update_group_list()

            # Explicitly trigger canvas update if SelectionModel signal isn't enough
            self.canvas.update()

    def delete_selection(self):
        """
        Deletes the currently selected groups and/or nodes.
        (Placeholder - Actual logic might involve graph model methods)
        """
        print("Placeholder: NormalModeController.delete_selection()")
        # TODO: Implement logic using self.graph.delete_group or similar
        # Ensure self.selection_model is updated and canvas redraw is triggered.
        if self.selection_model.selected_groups:
            groups_to_delete = self.selection_model.selected_groups.copy()
            for group in groups_to_delete:
                self.graph.delete_group(group)  # Assuming this handles nodes and edges
            self.selection_model.clear_selection()  # Clear selection after delete
            # Update main window list if needed
            main_window = self.canvas.window()
            if hasattr(main_window, "_update_group_list"):
                main_window._update_group_list()
            self.canvas.update()

    def rotate_selection(self):
        """
        Rotates the selected groups/nodes individually around their centers.
        (Placeholder - Actual logic might involve graph model methods)
        """
        print("Placeholder: NormalModeController.rotate_selection()")
        # TODO: Implement logic using self.graph.rotate_node_groups or similar
        if self.selection_model.selected_groups:
            self.graph.rotate_node_groups(self.selection_model.selected_groups)
            self.canvas.update()
        elif self.selection_model.selected_nodes:
            # Handle rotation for individually selected nodes if needed
            pass

    def rotate_selection_together(self):
        """
        Rotates the selected groups together around their common center.
        (Placeholder - Actual logic might involve graph model methods)
        """
        print("Placeholder: NormalModeController.rotate_selection_together()")
        # TODO: Implement logic using self.graph.rotate_groups_around_center
        if len(self.selection_model.selected_groups) > 1:
            self.graph.rotate_groups_around_center(self.selection_model.selected_groups)
            self.canvas.update()

    def _snap_point_to_grid(self, point: QPointF) -> QPointF:
        """Snaps a given point to the nearest grid intersection."""
        # Grid spacing is based on node distance / 2
        node_distance = config.get_dimension("node.node_to_node_distance", 50)
        grid_spacing = node_distance / 2.0
        if grid_spacing == 0:
            return point  # Avoid division by zero

        snapped_x = round(point.x() / grid_spacing) * grid_spacing
        snapped_y = round(point.y() / grid_spacing) * grid_spacing
        return QPointF(snapped_x, snapped_y)

    def snap_all_groups_to_grid(self):
        """Snaps ALL groups to the nearest grid intersection based on their center."""
        if not self.view_state.snap_to_grid:
            return

        groups_moved = False
        # Iterate through ALL groups in the graph
        for group in self.graph.node_groups:
            group_nodes = group.get_nodes(self.graph.nodes)
            if not group_nodes:
                continue

            # Calculate current center
            center_x = sum(node.x for node in group_nodes) / len(group_nodes)
            center_y = sum(node.y for node in group_nodes) / len(group_nodes)
            current_center = QPointF(center_x, center_y)

            # Calculate snapped center
            snapped_center = self._snap_point_to_grid(current_center)

            # Calculate displacement and move nodes
            dx = snapped_center.x() - current_center.x()
            dy = snapped_center.y() - current_center.y()

            if abs(dx) > 0.1 or abs(dy) > 0.1:  # Apply only if there's a change
                for node in group_nodes:
                    node.x += dx
                    node.y += dy
                groups_moved = True  # Mark that at least one group moved

        # Update canvas only once if any group moved
        if groups_moved:
            self.canvas.update()
