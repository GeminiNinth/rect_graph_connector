"""
This module contains the context menu for edit mode in the canvas.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QMenu

from ...config import config


class EditContextMenu(QMenu):
    """
    Context menu for the edit mode operations.

    This menu provides options for connectivity operations and
    toggling between different edit submodes.
    """

    def __init__(self, parent=None):
        """
        Initialize the edit mode context menu.

        Args:
            parent: The parent widget (usually the Canvas)
        """
        super().__init__(parent)
        self.canvas = parent
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

        # Add connection actions to the submenu
        self.connection_menu.addAction(self.connect_4_directions_action)
        self.connection_menu.addAction(self.connect_8_directions_action)
        self.connection_menu.addAction(self.all_for_one_action)
        self.connection_menu.addAction(self.parallel_action)

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

    def _build_menu(self):
        """Build the menu structure by adding actions."""
        self.addMenu(self.connection_menu)
        self.addSeparator()
        self.addAction(self.toggle_knife_action)

    def _toggle_knife_mode(self, checked):
        """
        Toggle between knife mode and normal edit mode.

        Args:
            checked (bool): Whether the knife mode is enabled
        """
        if self.canvas:
            if checked:
                self.canvas.set_edit_submode(self.canvas.EDIT_SUBMODE_KNIFE)
            else:
                self.canvas.set_edit_submode(self.canvas.EDIT_SUBMODE_CONNECT)

    def _toggle_all_for_one_connection_mode(self):
        """
        Toggle All-For-One connection mode.

        This mode allows selecting multiple nodes and drawing edges from all selected nodes at once.
        """
        if self.canvas:
            # Check if already in All-For-One connection mode, if so go back to connect mode
            if self.canvas.edit_submode == self.canvas.EDIT_SUBMODE_ALL_FOR_ONE:
                self.canvas.set_edit_submode(self.canvas.EDIT_SUBMODE_CONNECT)
            else:
                self.canvas.set_edit_submode(self.canvas.EDIT_SUBMODE_ALL_FOR_ONE)

    def _connect_nodes_in_8_directions(self):
        """
        Connect all nodes in the current edit target groups in 8 directions by
        delegating to the graph service.
        """
        if not self.canvas.edit_target_groups:
            return

        # Delegate the connection logic to the graph service
        from ...models.connectivity import connect_nodes_in_8_directions

        # Process each target group
        for group in self.canvas.edit_target_groups:
            # Get the nodes in the target group
            group_nodes = group.get_nodes(self.canvas.graph.nodes)
            if group_nodes:
                connect_nodes_in_8_directions(self.canvas.graph, group_nodes)

        # Update display
        self.canvas.update()

    def _connect_nodes_in_4_directions(self):
        """
        Connect all nodes in the current edit target groups in 4 directions by
        delegating to the graph service.
        """
        if not self.canvas.edit_target_groups:
            return

        # Delegate the connection logic to the graph service
        from ...models.connectivity import connect_nodes_in_4_directions

        # Process each target group
        for group in self.canvas.edit_target_groups:
            # Get the nodes in the target group
            group_nodes = group.get_nodes(self.canvas.graph.nodes)
            if group_nodes:
                connect_nodes_in_4_directions(self.canvas.graph, group_nodes)

        # Update display
        self.canvas.update()

    def _toggle_parallel_connection_mode(self):
        """
        Toggle Parallel connection mode.

        This mode allows selecting multiple nodes and drawing edges from all selected nodes
        in the same direction and distance simultaneously.
        """
        if self.canvas:
            # Check if already in Parallel connection mode, if so go back to connect mode
            if self.canvas.edit_submode == self.canvas.EDIT_SUBMODE_PARALLEL:
                self.canvas.set_edit_submode(self.canvas.EDIT_SUBMODE_CONNECT)
            else:
                self.canvas.set_edit_submode(self.canvas.EDIT_SUBMODE_PARALLEL)

    def prepare_for_display(self):
        """
        Prepare the menu before displaying it, updating state as needed.
        """
        if self.canvas:
            # Update toggle knife action state
            self.toggle_knife_action.setChecked(
                self.canvas.edit_submode == self.canvas.EDIT_SUBMODE_KNIFE
            )

            # Update All-For-One connection action state (add checkable property first)
            if not hasattr(self.all_for_one_action, "setCheckable"):
                self.all_for_one_action.setCheckable(True)
            self.all_for_one_action.setChecked(
                self.canvas.edit_submode == self.canvas.EDIT_SUBMODE_ALL_FOR_ONE
            )

            # Update Parallel connection action state
            if not hasattr(self.parallel_action, "setCheckable"):
                self.parallel_action.setCheckable(True)
            self.parallel_action.setChecked(
                self.canvas.edit_submode == self.canvas.EDIT_SUBMODE_PARALLEL
            )
