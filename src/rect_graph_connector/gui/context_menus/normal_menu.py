"""
This module contains the context menu for normal mode in the canvas.
"""

from PyQt5.QtWidgets import QAction, QInputDialog, QMenu

from ...config import config


class NormalContextMenu(QMenu):
    """
    Context menu for the normal mode operations.

    This menu provides options like setting node ID starting index
    and other normal mode specific operations.
    """

    def __init__(self, parent=None, controller=None):  # Add controller parameter
        """
        Initialize the normal mode context menu.

        Args:
            parent: The parent widget (usually the Canvas)
            controller: The NormalModeController instance
        """
        super().__init__(parent)
        self.canvas = parent  # Keep canvas ref for mapping coordinates if needed
        self.controller = controller  # Store controller reference
        self._create_actions()
        self._build_menu()
        self.copied_groups_data = (
            None  # Store copied groups data (maybe move to controller?)
        )

    def _create_actions(self):
        """Create the actions for the context menu."""
        # Set node ID start index action
        title = config.get_string(
            "normal_menu.set_node_id.title", "Set Node ID Starting Index"
        )
        self.set_node_id_start_action = QAction(title, self)
        self.set_node_id_start_action.setToolTip(
            config.get_string(
                "normal_menu.set_node_id.tooltip",
                "Change the starting index for node IDs in the graph.",
            )
        )
        self.set_node_id_start_action.triggered.connect(self._set_node_id_start_index)

        # Copy group action
        title = config.get_string("normal_menu.copy.title", "Copy Group")
        self.copy_action = QAction(title, self)
        self.copy_action.setToolTip(
            config.get_string(
                "normal_menu.copy.tooltip",
                "Copy the selected node group to be pasted later.",
            )
        )
        self.copy_action.triggered.connect(self._copy_selected_groups)
        self.copy_action.setEnabled(False)  # Initially disabled

        # Paste group action
        title = config.get_string("normal_menu.paste.title", "Paste Group")
        self.paste_action = QAction(title, self)
        self.paste_action.setToolTip(
            config.get_string(
                "normal_menu.paste.tooltip", "Paste the previously copied node group."
            )
        )
        self.paste_action.triggered.connect(self._paste_groups)
        self.paste_action.setEnabled(False)  # Initially disabled

        # Delete group action
        title = config.get_string("normal_menu.delete.title", "Delete Group")
        self.delete_action = QAction(title, self)
        self.delete_action.setToolTip(
            config.get_string(
                "normal_menu.delete.tooltip", "Delete the selected node group or nodes."
            )
        )
        self.delete_action.triggered.connect(self._delete_selected_groups)
        self.delete_action.setEnabled(False)  # Initially disabled

        # Rotate group action
        title = config.get_string(
            "normal_menu.rotate_individual.title", "Rotate Individual Elements"
        )
        self.rotate_action = QAction(title, self)
        self.rotate_action.setToolTip(
            config.get_string(
                "normal_menu.rotate_individual.tooltip",
                "Rotate each selected group or node around its own center point by 90 degrees.",
            )
        )
        self.rotate_action.triggered.connect(self._rotate_selected_groups)
        self.rotate_action.setEnabled(False)  # Initially disabled

        # Rotate groups together action
        title = config.get_string(
            "normal_menu.rotate_common_center.title", "Rotate Around Common Center"
        )
        self.rotate_group_action = QAction(title, self)
        self.rotate_group_action.setToolTip(
            config.get_string(
                "normal_menu.rotate_common_center.tooltip",
                "Rotate multiple selected groups as a single unit around their common center point by 90 degrees.",
            )
        )
        self.rotate_group_action.triggered.connect(self._rotate_groups_together)
        self.rotate_group_action.setEnabled(False)  # Initially disabled

        # Switch to Edit-Mode action
        title = config.get_string(
            "normal_menu.switch_to_edit.title", "Switch to Edit-Mode"
        )
        self.switch_to_edit_action = QAction(title, self)
        self.switch_to_edit_action.setToolTip(
            config.get_string(
                "normal_menu.switch_to_edit.tooltip",
                "Switch to edit mode to create and modify connections between nodes.",
            )
        )
        self.switch_to_edit_action.triggered.connect(self._switch_to_edit_mode)

        # Toggle Grid action
        title = config.get_string("common_menu.toggle_grid.title", "Show Grid")
        self.toggle_grid_action = QAction(title, self)
        self.toggle_grid_action.setToolTip(
            config.get_string(
                "common_menu.toggle_grid.tooltip",
                "Toggle the visibility of the background grid.",
            )
        )
        self.toggle_grid_action.setCheckable(True)
        self.toggle_grid_action.triggered.connect(self._toggle_grid)

    def _build_menu(self):
        """Build the menu structure by adding actions."""
        self.addAction(self.set_node_id_start_action)
        self.addSeparator()
        self.addAction(self.copy_action)
        self.addAction(self.paste_action)
        self.addSeparator()
        self.addAction(self.delete_action)
        self.addAction(self.rotate_action)
        self.addAction(self.rotate_group_action)
        self.addSeparator()
        self.addAction(self.toggle_grid_action)
        self.addSeparator()
        self.addAction(self.switch_to_edit_action)

    def showEvent(self, event):
        """
        Update action states based on the current selection when the menu is shown.
        """
        super().showEvent(event)
        if not self.controller:
            return

        # Use selection model from controller
        has_groups_selection = len(self.controller.selection_model.selected_groups) > 0
        has_nodes_selection = len(self.controller.selection_model.selected_nodes) > 0
        has_selection = has_groups_selection or has_nodes_selection

        # Enable/disable copy action based on group selection
        self.copy_action.setEnabled(has_groups_selection)
        # Enable/disable paste action based on whether groups have been copied
        self.paste_action.setEnabled(self.copied_groups_data is not None)
        # Enable/disable delete and rotate actions based on selection
        self.delete_action.setEnabled(has_selection)
        self.rotate_action.setEnabled(has_selection)
        # Enable rotate_group_action only if multiple groups are selected
        self.rotate_group_action.setEnabled(
            len(self.controller.selection_model.selected_groups) > 1
        )
        # Enable switch_to_edit_action only if there are selected groups
        # (since edit mode requires target groups)
        self.switch_to_edit_action.setEnabled(has_groups_selection)

        # Update grid action checked state
        self.toggle_grid_action.setChecked(self.controller.view_state.grid_visible)

    def _set_node_id_start_index(self):
        """
        Display a dialog to set the node ID starting index.
        The change will apply to all nodes in the graph.
        """
        # Get the current node ID starting index
        current_start = config.node_id_start

        # Show an input dialog to get the new starting index
        title = config.get_string(
            "normal_menu.set_node_id.title", "Set Node ID Starting Index"
        )
        prompt = config.get_string(
            "normal_menu.set_node_id.prompt",
            "Enter the starting index for node IDs (0 or higher):",
        )
        new_start, ok = QInputDialog.getInt(
            self,
            title,
            prompt,
            value=current_start,
            min=0,
            max=1000000,  # Arbitrary high limit
        )

        if ok:
            # Update the node ID start in the graph
            self.canvas.graph.set_node_id_start(new_start)
            self.canvas.update()  # Redraw the canvas to show new IDs

    def _copy_selected_groups(self):
        """
        Copy the currently selected node groups.
        """
        if self.controller and self.controller.selection_model.selected_groups:
            # Call controller method to handle copying
            self.copied_groups_data = self.controller.copy_selection()
            # Update paste action state immediately
            self.paste_action.setEnabled(self.copied_groups_data is not None)

    def _paste_groups(self):
        """
        Paste the previously copied node groups.
        The new groups will be positioned at the bottom right of the original groups.
        """
        if self.controller and self.copied_groups_data:
            # Call controller method to handle pasting
            self.controller.paste(self.copied_groups_data)
            # Optionally clear copied data after paste? Or allow multiple pastes?
            # self.copied_groups_data = None
            # self.paste_action.setEnabled(False)

            # Controller should handle selection updates and canvas update

    def _delete_selected_groups(self):
        """
        Delete the currently selected node groups or nodes.
        This delegates the action to the NormalModeController.
        """
        if self.controller:
            self.controller.delete_selection()
            # Controller should handle graph updates and canvas redraw

    def _rotate_selected_groups(self):
        """
        Rotate each selected group or node around its own center point individually.
        This delegates the action to the NormalModeController.
        """
        if self.controller:
            self.controller.rotate_selection()
            # Controller should handle graph updates and canvas redraw

    def _rotate_groups_together(self):
        """
        Rotate multiple selected groups as a single unit around their common center point.
        This delegates the action to the NormalModeController.
        """
        if self.controller:
            self.controller.rotate_selection_together()
            # Controller should handle graph updates and canvas redraw

    def _switch_to_edit_mode(self):
        """
        Switch from normal mode to edit mode.
        This uses the input handler's mode switching mechanism.
        """
        if self.controller and self.controller.input_handler:
            # Request mode switch via InputHandler
            # Assumes EDIT_MODE constant is accessible, e.g., via input_handler
            self.controller.input_handler.request_mode_switch(
                self.controller.input_handler.EDIT_MODE
            )

    def _toggle_grid(self, checked):
        """Toggle grid visibility."""
        if self.controller:
            self.controller.view_state.grid_visible = checked
            # Emit signal if UI needs update (e.g., toolbar button)
            if hasattr(self.canvas, "grid_state_changed"):
                self.canvas.grid_state_changed.emit(
                    self.controller.view_state.grid_visible,
                    self.controller.view_state.snap_to_grid,
                )
            self.canvas.update()  # Trigger redraw
