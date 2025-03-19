"""
This module contains the context menu for edit mode in the canvas.
"""

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt


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
        self.connection_menu = QMenu("Connection", self)

        # Connect all nodes in 4 directions action
        self.connect_4_directions_action = QAction("4-neighborhood", self)
        self.connect_4_directions_action.triggered.connect(
            self._connect_nodes_in_4_directions
        )

        # Connect all nodes in 8 directions action
        self.connect_8_directions_action = QAction("8-neighborhood", self)
        self.connect_8_directions_action.triggered.connect(
            self._connect_nodes_in_8_directions
        )

        # Add connection actions to the submenu
        self.connection_menu.addAction(self.connect_4_directions_action)
        self.connection_menu.addAction(self.connect_8_directions_action)

        # Toggle eraser mode action
        self.toggle_eraser_action = QAction("Eraser Mode (Delete Edges)", self)
        self.toggle_eraser_action.setCheckable(True)
        self.toggle_eraser_action.triggered.connect(self._toggle_eraser_mode)

    def _build_menu(self):
        """Build the menu structure by adding actions."""
        self.addMenu(self.connection_menu)
        self.addSeparator()
        self.addAction(self.toggle_eraser_action)

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

    def _toggle_eraser_mode(self, checked):
        """
        Toggle between eraser mode and normal edit mode.

        Args:
            checked (bool): Whether the eraser mode is enabled
        """
        if self.canvas:
            if checked:
                self.canvas.set_edit_submode(self.canvas.EDIT_SUBMODE_ERASER)
            else:
                self.canvas.set_edit_submode(self.canvas.EDIT_SUBMODE_CONNECT)

    def prepare_for_display(self):
        """
        Prepare the menu before displaying it, updating state as needed.
        """
        if self.canvas:
            # Update toggle eraser action state
            self.toggle_eraser_action.setChecked(
                self.canvas.edit_submode == self.canvas.EDIT_SUBMODE_ERASER
            )
