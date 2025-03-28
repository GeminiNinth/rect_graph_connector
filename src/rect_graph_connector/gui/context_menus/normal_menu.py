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

    def __init__(self, parent=None):
        """
        Initialize the normal mode context menu.

        Args:
            parent: The parent widget (usually the Canvas)
        """
        super().__init__(parent)
        self.canvas = parent
        self._create_actions()
        self._build_menu()
        self.copied_groups_data = None  # Store copied groups data

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
        title = config.get_string("normal_menu.rotate.title", "Rotate Group")
        self.rotate_action = QAction(title, self)
        self.rotate_action.setToolTip(
            config.get_string(
                "normal_menu.rotate.tooltip",
                "Rotate the selected node group or nodes by 90 degrees.",
            )
        )
        self.rotate_action.triggered.connect(self._rotate_selected_groups)
        self.rotate_action.setEnabled(False)  # Initially disabled

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

    def _build_menu(self):
        """Build the menu structure by adding actions."""
        self.addAction(self.set_node_id_start_action)
        self.addSeparator()
        self.addAction(self.copy_action)
        self.addAction(self.paste_action)
        self.addSeparator()
        self.addAction(self.delete_action)
        self.addAction(self.rotate_action)
        self.addSeparator()
        self.addAction(self.switch_to_edit_action)

    def showEvent(self, event):
        """
        Update action states based on the current selection when the menu is shown.
        """
        super().showEvent(event)
        # Check if there are selected groups or nodes
        has_selection = (
            len(self.canvas.graph.selected_groups) > 0
            or len(self.canvas.graph.selected_nodes) > 0
        )

        # Enable/disable copy action based on selection
        self.copy_action.setEnabled(len(self.canvas.graph.selected_groups) > 0)
        # Enable/disable paste action based on whether groups have been copied
        self.paste_action.setEnabled(self.copied_groups_data is not None)
        # Enable/disable delete and rotate actions based on selection
        self.delete_action.setEnabled(has_selection)
        self.rotate_action.setEnabled(has_selection)
        # Enable switch_to_edit_action only if there are selected groups
        # (since edit mode requires target groups)
        self.switch_to_edit_action.setEnabled(
            len(self.canvas.graph.selected_groups) > 0
        )

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
        if not self.canvas.graph.selected_groups:
            return

        # Use the graph's copy_groups method to create a deep copy of the selected groups
        self.copied_groups_data = self.canvas.graph.copy_groups(
            self.canvas.graph.selected_groups
        )

    def _paste_groups(self):
        """
        Paste the previously copied node groups.
        The new groups will be positioned at the bottom right of the original groups.
        """
        if not self.copied_groups_data:
            return

        # Use the graph's paste_groups method to create new groups
        # This method handles creating new UUIDs and node IDs
        new_groups = self.canvas.graph.paste_groups(self.copied_groups_data)

        if new_groups:
            # Clear current selection and select the newly created groups
            self.canvas.graph.selected_groups = new_groups

            # Update selected nodes
            self.canvas.graph.selected_nodes = []
            for group in new_groups:
                self.canvas.graph.selected_nodes.extend(
                    group.get_nodes(self.canvas.graph.nodes)
                )

            # Update the parent window's group list
            main_window = self.canvas.window()
            if hasattr(main_window, "_update_group_list"):
                main_window._update_group_list()

            # Redraw the canvas
            self.canvas.update()

    def _delete_selected_groups(self):
        """
        Delete the currently selected node groups or nodes.
        This calls the main window's _handle_delete method.
        """
        main_window = self.canvas.window()
        if hasattr(main_window, "_handle_delete"):
            main_window._handle_delete()

    def _rotate_selected_groups(self):
        """
        Rotate the currently selected node groups or nodes.
        This calls the main window's _handle_rotate method.
        """
        main_window = self.canvas.window()
        if hasattr(main_window, "_handle_rotate"):
            main_window._handle_rotate()

    def _switch_to_edit_mode(self):
        """
        Switch from normal mode to edit mode.
        This uses the canvas's toggle_edit_mode method.
        """
        if self.canvas:
            # If there are selected groups, they will be used as edit targets
            self.canvas.toggle_edit_mode()
