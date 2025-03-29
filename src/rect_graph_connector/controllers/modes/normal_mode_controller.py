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
        canvas: QWidget,  # Add canvas parameter
    ):
        """Initialize the normal mode controller."""
        super().__init__(view_state, selection_model, hover_state, graph)
        self.canvas = canvas  # Store canvas reference
        # Initialize the context menu specific to this mode
        self.context_menu = NormalContextMenu(self.canvas)

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
                    # Start dragging
                    self.dragging = True
                    self.drag_start = QPointF(graph_point)
                    self.drag_start_node = node

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

                        # Update selected nodes
                        self._update_selected_nodes_from_groups()
                    else:
                        # Node without group
                        if not shift_pressed:
                            self.selection_model.clear_selection()
                        self.selection_model.select_node(node)

                return True
            else:
                # Check for group click (without hitting a specific node)
                group = self._find_group_at_position(graph_point)
                if group:
                    # Start dragging
                    self.dragging = True
                    self.drag_start = QPointF(graph_point)

                    # Handle selection
                    if shift_pressed:
                        # Multi-selection with Shift
                        self.selection_model.select_group(group, add_to_selection=True)
                        self.graph.bring_group_to_front(group)
                    else:
                        # Single selection
                        self.selection_model.select_group(group, add_to_selection=False)
                        self.graph.bring_group_to_front(group)

                    # Update selected nodes
                    self._update_selected_nodes_from_groups()

                    # Store a reference node from the clicked group for movement
                    group_nodes = group.get_nodes(self.graph.nodes)
                    if group_nodes:
                        self.drag_start_node = group_nodes[0]

                    return True
                else:
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
                self.drag_start = self.press_pos

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
                self.drag_start = None
                self.drag_start_node = None
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
                return True

        # Handle Ctrl+A for selecting all groups
        elif event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            if self.graph.node_groups:
                self.selection_model.select_groups(list(self.graph.node_groups))
                self._update_selected_nodes_from_groups()
                return True

        return False

    def _handle_dragging(self, graph_point):
        """
        Handle dragging of selected nodes/groups.

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
        # Show the normal mode context menu at the clicked position
        self.context_menu.show_menu(widget_point)
        return True
