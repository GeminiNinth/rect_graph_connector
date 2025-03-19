"""
This module contains the context menu for normal mode in the canvas.
"""

from PyQt5.QtWidgets import QMenu, QAction, QInputDialog
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

    def _create_actions(self):
        """Create the actions for the context menu."""
        # Set node ID start index action
        self.set_node_id_start_action = QAction("Set Node ID Starting Index", self)
        self.set_node_id_start_action.triggered.connect(self._set_node_id_start_index)

    def _build_menu(self):
        """Build the menu structure by adding actions."""
        self.addAction(self.set_node_id_start_action)

    def _set_node_id_start_index(self):
        """
        Display a dialog to set the node ID starting index.
        The change will apply to all nodes in the graph.
        """
        # Get the current node ID starting index
        current_start = config.node_id_start

        # Show an input dialog to get the new starting index
        new_start, ok = QInputDialog.getInt(
            self,
            "Set Node ID Starting Index",
            "Enter the starting index for node IDs (0 or higher):",
            value=current_start,
            min=0,
            max=1000000,  # Arbitrary high limit
        )

        if ok:
            # Update the node ID start in the graph
            self.canvas.graph.set_node_id_start(new_start)
            self.canvas.update()  # Redraw the canvas to show new IDs
