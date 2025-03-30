"""
This module contains the context menu for edit mode in the canvas.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QMenu

from ...config import config
from ...models.connectivity import (  # Import necessary functions
    connect_nodes_in_4_directions,
    connect_nodes_in_8_directions,
)


class EditContextMenu(QMenu):
    """
    Context menu for the edit mode operations.

    This menu provides options for connectivity operations and
    toggling between different edit submodes.
    """

    def __init__(
        self, parent=None, edit_mode_controller=None
    ):  # Add controller to signature
        """
        Initialize the edit mode context menu.

        Args:
            parent: The parent widget (usually the Canvas)
            edit_mode_controller: The controller managing edit mode state
        """
        super().__init__(parent)
        self.canvas = parent  # Keep canvas reference for actions needing it
        self.controller = edit_mode_controller  # Store controller reference
        self._create_actions()
        self._build_menu()

    def _create_actions(self):
        """Create the actions for the context menu."""
        # Create Connection submenu
        connection_title = config.get_string("edit_menu.connection.title", "Connection")
        self.connection_menu = QMenu(connection_title, self)

        # Enable tooltips for the submenu
        self.connection_menu.setToolTipsVisible(True)

        # Connect all nodes in 4 directions action
        four_dir_text = config.get_string(
            "edit_menu.connection.four_directions", "4-neighborhood"
        )
        self.connect_4_directions_action = QAction(four_dir_text, self)
        self.connect_4_directions_action.setToolTip(
            config.get_string(
                "edit_menu.connection.four_directions_tooltip",
                "Connect all nodes in the selected group with edges in 4 directions (up, down, left, right).",
            )
        )
        self.connect_4_directions_action.triggered.connect(
            self._connect_nodes_in_4_directions
        )

        # Connect all nodes in 8 directions action
        eight_dir_text = config.get_string(
            "edit_menu.connection.eight_directions", "8-neighborhood"
        )
        self.connect_8_directions_action = QAction(eight_dir_text, self)
        self.connect_8_directions_action.setToolTip(
            config.get_string(
                "edit_menu.connection.eight_directions_tooltip",
                "Connect all nodes in the selected group with edges in 8 directions (including diagonals).",
            )
        )
        self.connect_8_directions_action.triggered.connect(
            self._connect_nodes_in_8_directions
        )

        # All-For-One connection action
        all_for_one_text = config.get_string(
            "edit_menu.connection.all_for_one", "All-For-One connection"
        )
        self.all_for_one_action = QAction(all_for_one_text, self)
        self.all_for_one_action.setToolTip(
            config.get_string(
                "edit_menu.connection.all_for_one_tooltip",
                "Enables multiple node selection. When drawing from a selected node, identical edges extend from all selected nodes automatically.",
            )
        )
        self.all_for_one_action.triggered.connect(
            self._toggle_all_for_one_connection_mode
        )

        # Parallel connection action
        parallel_text = config.get_string(
            "edit_menu.connection.parallel", "Parallel connection"
        )
        self.parallel_action = QAction(parallel_text, self)
        self.parallel_action.setToolTip(
            config.get_string(
                "edit_menu.connection.parallel_tooltip",
                "Enables selecting multiple nodes and drawing edges in parallel in the same direction and distance.",
            )
        )
        self.parallel_action.triggered.connect(self._toggle_parallel_connection_mode)

        # Bridge connection action
        bridge_text = config.get_string(
            "edit_menu.connection.bridge", "Bridge connection"
        )
        self.bridge_action = QAction(bridge_text, self)
        self.bridge_action.setToolTip(
            config.get_string(
                "edit_menu.connection.bridge_tooltip",
                "Creates bipartite graph connections between two selected node groups with customizable connection patterns.",
            )
        )
        self.bridge_action.triggered.connect(self._toggle_bridge_connection_mode)

        # Add connection actions to the submenu
        self.connection_menu.addAction(self.connect_4_directions_action)
        self.connection_menu.addAction(self.connect_8_directions_action)
        self.connection_menu.addAction(self.all_for_one_action)
        self.connection_menu.addAction(self.parallel_action)
        self.connection_menu.addAction(self.bridge_action)

        # Toggle knife mode action
        knife_text = config.get_string(
            "edit_menu.knife.title", "Knife Mode (Cut Edges)"
        )
        self.toggle_knife_action = QAction(knife_text, self)
        self.toggle_knife_action.setToolTip(
            config.get_string(
                "edit_menu.knife.tooltip",
                "Enables knife mode to cut edges between nodes by drawing a line across them.",
            )
        )
        self.toggle_knife_action.setCheckable(True)
        self.toggle_knife_action.triggered.connect(self._toggle_knife_mode)

        # Switch to Normal-Mode action
        title = config.get_string(
            "edit_menu.switch_to_normal.title", "Switch to Normal-Mode"
        )
        self.switch_to_normal_action = QAction(title, self)
        self.switch_to_normal_action.setToolTip(
            config.get_string(
                "edit_menu.switch_to_normal.tooltip",
                "Switch back to normal mode for node group management.",
            )
        )
        self.switch_to_normal_action.triggered.connect(self._switch_to_normal_mode)

        # REMOVED: Toggle Grid action

    def _build_menu(self):
        """Build the menu structure by adding actions."""
        # Add delete selected edges action
        delete_edges_text = config.get_string(
            "edit_menu.delete_edges.title", "Delete Selected Edges"
        )
        self.delete_edges_action = QAction(delete_edges_text, self)
        self.delete_edges_action.setToolTip(
            config.get_string(
                "edit_menu.delete_edges.tooltip",
                "Delete the currently selected edges.",
            )
        )
        self.delete_edges_action.triggered.connect(self._delete_selected_edges)

        self.addMenu(self.connection_menu)
        self.addSeparator()
        self.addAction(self.delete_edges_action)
        self.addSeparator()
        self.addAction(self.toggle_knife_action)
        # REMOVED: Grid toggle action separator
        self.addSeparator()
        self.addAction(self.switch_to_normal_action)

    def _toggle_knife_mode(self, checked):
        """
        Toggle between knife mode and normal edit mode.

        Args:
            checked (bool): Whether the knife mode is enabled
        """
        # Use self.controller instead of self.canvas
        if self.controller:
            if checked:
                self.controller.set_edit_submode(self.controller.EDIT_SUBMODE_KNIFE)
            else:
                # Revert to default connect mode when unchecked
                self.controller.set_edit_submode(self.controller.EDIT_SUBMODE_CONNECT)

    def _toggle_all_for_one_connection_mode(self):
        """
        Toggle All-For-One connection mode.

        This mode allows selecting multiple nodes and drawing edges from all selected nodes at once.
        """
        # Use self.controller instead of self.canvas
        if self.controller:
            # Check if already in All-For-One connection mode, if so go back to connect mode
            if self.controller.edit_submode == self.controller.EDIT_SUBMODE_ALL_FOR_ONE:
                self.controller.set_edit_submode(self.controller.EDIT_SUBMODE_CONNECT)
            else:
                self.controller.set_edit_submode(
                    self.controller.EDIT_SUBMODE_ALL_FOR_ONE
                )

    def _toggle_bridge_connection_mode(self):
        """
        Toggle Bridge connection mode.

        This mode allows selecting two node groups and creating bipartite graph connections
        between their edge nodes with customizable parameters.
        """
        # Use self.controller instead of self.canvas
        if self.controller:
            # Check if already in Bridge connection mode, if so go back to connect mode
            if self.controller.edit_submode == self.controller.EDIT_SUBMODE_BRIDGE:
                self.controller.set_edit_submode(self.controller.EDIT_SUBMODE_CONNECT)
            else:
                self.controller.set_edit_submode(self.controller.EDIT_SUBMODE_BRIDGE)

    def _connect_nodes_in_8_directions(self):
        """
        Connect all nodes in the current edit target groups in 8 directions by
        delegating to the graph service.
        """
        if (
            not self.controller or not self.controller.edit_target_groups
        ):  # Use self.controller
            return

        # Process each target group
        for group in self.controller.edit_target_groups:  # Use self.controller
            # Get the nodes in the target group
            group_nodes = group.get_nodes(
                self.controller.graph.nodes
            )  # Use self.controller.graph
            if group_nodes:
                # Use the imported function directly
                connect_nodes_in_8_directions(self.controller.graph, group_nodes)

        # Update display
        self.canvas.update()

    def _connect_nodes_in_4_directions(self):
        """
        Connect all nodes in the current edit target groups in 4 directions by
        delegating to the graph service.
        """
        if (
            not self.controller or not self.controller.edit_target_groups
        ):  # Use self.controller
            return

        # Process each target group
        for group in self.controller.edit_target_groups:  # Use self.controller
            # Get the nodes in the target group
            group_nodes = group.get_nodes(
                self.controller.graph.nodes
            )  # Use self.controller.graph
            if group_nodes:
                # Use the imported function directly
                connect_nodes_in_4_directions(self.controller.graph, group_nodes)

        # Update display
        self.canvas.update()

    def _toggle_parallel_connection_mode(self):
        """
        Toggle Parallel connection mode.

        This mode allows selecting multiple nodes and drawing edges from all selected nodes
        in the same direction and distance simultaneously.
        """
        # Use self.controller instead of self.canvas
        if self.controller:
            # Check if already in Parallel connection mode, if so go back to connect mode
            if self.controller.edit_submode == self.controller.EDIT_SUBMODE_PARALLEL:
                self.controller.set_edit_submode(self.controller.EDIT_SUBMODE_CONNECT)
            else:
                self.controller.set_edit_submode(self.controller.EDIT_SUBMODE_PARALLEL)

    def _delete_selected_edges(self):
        """
        Delete all currently selected edges.
        Delegates to the controller.
        """
        # TODO: Implement delete_selected_edges in EditModeController
        if self.controller:
            # Assuming EditModeController will have a method like this
            # self.controller.delete_selected_edges()
            print("Placeholder: Delete selected edges action triggered")
            # Temporary direct access for now, needs refactoring
            if self.controller.selection_model.selected_edges:
                edges_to_delete = self.controller.selection_model.selected_edges.copy()
                for source_node, target_node in edges_to_delete:
                    edge_tuple = (source_node.id, target_node.id)
                    if edge_tuple in self.controller.graph.edges:
                        self.controller.graph.edges.remove(edge_tuple)
                    elif (
                        target_node.id,
                        source_node.id,
                    ) in self.controller.graph.edges:
                        self.controller.graph.edges.remove(
                            (target_node.id, source_node.id)
                        )

                self.controller.selection_model.clear_selection()  # Clear edge selection
                self.canvas.update()

    def _switch_to_normal_mode(self):
        """
        Switch from edit mode to normal mode.
        This uses the canvas's toggle_edit_mode method.
        """
        # Use input_handler on controller
        if self.controller and self.controller.input_handler:
            self.controller.input_handler.request_mode_switch(
                self.controller.input_handler.NORMAL_MODE
            )

    # REMOVED: _toggle_grid method

    def prepare_for_display(self):
        """
        Prepare the menu before displaying it, updating state as needed.
        """
        if self.controller:  # Check if controller exists
            # Update delete edges action state (enabled only if edges are selected in the model)
            self.delete_edges_action.setEnabled(
                bool(self.controller.selection_model.selected_edges)
            )

            # Update toggle knife action state
            self.toggle_knife_action.setChecked(
                self.controller.edit_submode == self.controller.EDIT_SUBMODE_KNIFE
            )

            # Update All-For-One connection action state (add checkable property first)
            if not hasattr(self.all_for_one_action, "setCheckable"):
                self.all_for_one_action.setCheckable(True)
            self.all_for_one_action.setChecked(
                self.controller.edit_submode == self.controller.EDIT_SUBMODE_ALL_FOR_ONE
            )

            # Update Parallel connection action state
            if not hasattr(self.parallel_action, "setCheckable"):
                self.parallel_action.setCheckable(True)
            self.parallel_action.setChecked(
                self.controller.edit_submode == self.controller.EDIT_SUBMODE_PARALLEL
            )

            # Update Bridge connection action state
            if not hasattr(self.bridge_action, "setCheckable"):
                self.bridge_action.setCheckable(True)
            self.bridge_action.setChecked(
                self.controller.edit_submode == self.controller.EDIT_SUBMODE_BRIDGE
            )

            # REMOVED: Update grid action checked state
