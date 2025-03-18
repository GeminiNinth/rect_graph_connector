"""
This module contains the main window implementation for the graph editor application.
"""

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QInputDialog,
    QAbstractItemView,
)
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt, QSize

from .canvas import Canvas
from ..utils.file_handler import FileHandler
from .import_dialog import ImportModeDialog


class MainWindow(QMainWindow):
    """
    The main window of the graph editor application.

    This class manages the overall application layout and user interface elements,
    including the canvas and control panel.
    """

    def __init__(self):
        """Initialize the main window and set up the user interface."""
        super().__init__()
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

        # Initialize the group list
        self._update_group_list()

    def _setup_window(self):
        """Configure the main window properties."""
        self.setWindowTitle("Rectangular Graph Creator")
        self.setGeometry(100, 100, 800, 600)

    def _create_widgets(self):
        # Main widget and canvas
        self.main_widget = QWidget()
        self.canvas = Canvas()

        # Control panel widgets
        self.row_input = QLineEdit()
        self.row_input.setFixedWidth(50)

        self.col_input = QLineEdit()
        self.col_input.setFixedWidth(50)

        self.add_button = QPushButton("Add")
        self.import_button = QPushButton("Import")
        self.export_button = QPushButton("Export YAML")
        self.reset_button = QPushButton("Reset All")
        self.delete_button = QPushButton("Delete Group")
        self.rotate_button = QPushButton("Rotate Group")

        # Side menu widgets
        self.group_list = QListWidget()
        self.group_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.group_list.setMinimumWidth(150)

        self.move_up_button = QPushButton("↑")
        self.move_up_button.setToolTip("Move group up")
        self.move_up_button.setFixedWidth(40)

        self.move_down_button = QPushButton("↓")
        self.move_down_button.setToolTip("Move group down")
        self.move_down_button.setFixedWidth(40)

    def _setup_layout(self):
        # Set main widget as central widget
        self.setCentralWidget(self.main_widget)

        # Create main layout
        layout = QVBoxLayout(self.main_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create a splitter for the main area
        splitter = QSplitter(Qt.Horizontal)

        # Create and set up side menu
        side_menu = self._create_side_menu()
        splitter.addWidget(side_menu)

        # Add canvas to splitter
        splitter.addWidget(self.canvas)

        # Set the initial sizes of the splitter
        splitter.setSizes([150, 650])

        # Add splitter to layout
        layout.addWidget(splitter, stretch=90)

        # Create and set up control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel, stretch=10)

    def _create_side_menu(self) -> QWidget:
        """Create and return the side menu widget."""
        side_menu = QWidget()
        layout = QVBoxLayout(side_menu)
        layout.setContentsMargins(5, 5, 5, 5)

        # Add title
        title = QLabel("Node Groups")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Add group list
        layout.addWidget(self.group_list)

        # Add buttons for moving groups
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.move_up_button)
        button_layout.addWidget(self.move_down_button)
        layout.addLayout(button_layout)

        return side_menu

    def _create_control_panel(self) -> QWidget:
        control_panel = QWidget()
        control_panel.setMaximumHeight(50)

        layout = QHBoxLayout(control_panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add row input
        layout.addWidget(QLabel("Rows:"))
        layout.addWidget(self.row_input)

        # Add column input
        layout.addWidget(QLabel("Cols:"))
        layout.addWidget(self.col_input)

        # Add buttons
        layout.addWidget(self.add_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.rotate_button)

        # Add stretch to push everything to the left
        layout.addStretch()

        return control_panel

    def _connect_signals(self):
        """Connect all signal handlers."""
        self.add_button.clicked.connect(self._handle_add)
        self.import_button.clicked.connect(self._handle_import)
        self.export_button.clicked.connect(self._handle_export)
        self.reset_button.clicked.connect(self._handle_reset)
        self.delete_button.clicked.connect(self._handle_delete)
        self.rotate_button.clicked.connect(self._handle_rotate)

        # Connect side menu signals
        self.group_list.itemDoubleClicked.connect(self._handle_rename_group)
        self.group_list.itemClicked.connect(self._handle_select_group)
        self.move_up_button.clicked.connect(self._handle_move_group_up)
        self.move_down_button.clicked.connect(self._handle_move_group_down)

    def _handle_add(self):
        """Handle the Add button click event."""
        try:
            rows = int(self.row_input.text())
            cols = int(self.col_input.text())
            _ = self.canvas.graph.add_node_group(rows, cols)
            self._update_group_list()
            # Select the newly added group
            self.group_list.setCurrentRow(len(self.canvas.graph.node_groups) - 1)
            self.canvas.update()
        except ValueError:
            print("Please enter valid numbers for rows and columns")

    def _handle_export(self):
        """Handle the Export YAML button click event."""
        try:
            # Prepare node information (including row and col information)
            nodes = [
                {
                    "id": node.id,
                    "x": node.x,
                    "y": node.y,
                    "row": node.row,
                    "col": node.col,
                }
                for node in self.canvas.graph.nodes
            ]

            # Prepare group information
            groups = []
            for group in self.canvas.graph.node_groups:
                # Get nodes for each group
                group_nodes = group.get_nodes(self.canvas.graph.nodes)
                group_data = {
                    "id": group.id,  # Store unique group ID
                    "name": group.name,
                    "node_ids": [node.id for node in group_nodes],
                    "label_position": group.label_position,
                }
                groups.append(group_data)

            # Export graph data to a YAML file
            FileHandler.export_graph_to_yaml(nodes, self.canvas.graph.edges, groups)
        except IOError as e:
            print(f"Failed to export graph: {e}")

    def _handle_import(self):
        """Handle the Import button click event."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "グラフのインポート",
            "",
            "YAML Files (*.yaml);;All Files (*)",
            options=options,
        )
        if file_path:
            try:
                # Import graph data from the selected file
                imported_data = FileHandler.import_graph_from_yaml(file_path)

                # Replace existing IDs with UUIDs to ensure data uniqueness
                self._ensure_unique_identifiers(imported_data)

                # If the drawing window is empty (if there are no nodes), import directly without displaying the confirmation window
                if not self.canvas.graph.nodes:
                    # Use "force" mode for empty graphs (full replacement)
                    self.canvas.graph.import_graph(imported_data, "force")
                    self._update_group_list()
                    self.canvas.update()
                else:
                    # If there are existing nodes in the graph, display the Import Mode confirmation window
                    dialog = ImportModeDialog(self)
                    if dialog.exec_():
                        mode = dialog.get_selected_mode()
                        # Import graph data with the selected mode
                        self.canvas.graph.import_graph(imported_data, mode)
                        self._update_group_list()
                        self.canvas.update()
            except IOError as e:
                print(f"Failed to import graph: {e}")

    def _ensure_unique_identifiers(self, data):
        """
        Replace the group ID with the UUID to ensure the uniqueness of the imported data.

        Args:
            data (Dict): graph data to be imported
        """
        import uuid

        # Assign a UUID to a group
        if "groups" in data:
            for group in data["groups"]:
                # If no ID exists, create a new one
                if "id" not in group:
                    group["id"] = str(uuid.uuid4())

    def _handle_reset(self):
        """Handle the Reset All button click event."""
        self.canvas.graph.reset()
        self.group_list.clear()
        self.canvas.update()

    def _handle_delete(self):
        """Handle the Delete Group button click event."""
        # First check if there is a selected group
        if self.canvas.graph.selected_group:
            self.canvas.graph.delete_group(self.canvas.graph.selected_group)
            self._update_group_list()
            self.canvas.update()
        # If no group is selected, get groups from selected nodes
        elif self.canvas.graph.selected_nodes:
            group = self.canvas.graph.get_group_for_node(
                self.canvas.graph.selected_nodes[0]
            )
            if group:
                self.canvas.graph.delete_group(group)
                self._update_group_list()
                self.canvas.update()

    def _handle_rotate(self):
        """Handle the Rotate Group button click event."""
        if self.canvas.graph.selected_nodes:
            self.canvas.graph.rotate_group(self.canvas.graph.selected_nodes)
            # If necessary after rotating nodes, update the group's node_ids if necessary (not needed in the current implementation)
            self.canvas.update()

    def _handle_rename_group(self, item):
        """Handle the double-click event on a group item to rename it."""
        index = self.group_list.row(item)
        if 0 <= index < len(self.canvas.graph.node_groups):
            group = self.canvas.graph.node_groups[index]
            new_name, ok = QInputDialog.getText(
                self, "Rename Group", "Enter new group name:", text=group.name
            )
            if ok and new_name:
                self.canvas.graph.rename_group(group, new_name)
                item.setText(new_name)
                # Since IDs are managed, group references do not change even if the name changes.
                self._update_group_list()
                self.canvas.update()

    def _handle_select_group(self, item):
        """Handle the click event on a group item to select it."""
        index = self.group_list.row(item)
        if 0 <= index < len(self.canvas.graph.node_groups):
            group = self.canvas.graph.node_groups[index]
            self.canvas.graph.selected_nodes = group.get_nodes(self.canvas.graph.nodes)
            self.canvas.graph.selected_group = group
            self.canvas.update()

    def _handle_move_group_up(self):
        """Handle the move up button click event."""
        selected_items = self.group_list.selectedItems()
        if selected_items:
            index = self.group_list.row(selected_items[0])
            if 0 <= index < len(self.canvas.graph.node_groups):
                group = self.canvas.graph.node_groups[index]
                if self.canvas.graph.move_group_up(group):
                    self._update_group_list()
                    # Select the moved group
                    self.group_list.setCurrentRow(index - 1)
                    self.canvas.update()

    def _handle_move_group_down(self):
        """Handle the move down button click event."""
        selected_items = self.group_list.selectedItems()
        if selected_items:
            index = self.group_list.row(selected_items[0])
            if 0 <= index < len(self.canvas.graph.node_groups):
                group = self.canvas.graph.node_groups[index]
                if self.canvas.graph.move_group_down(group):
                    self._update_group_list()
                    # Select the moved group
                    self.group_list.setCurrentRow(index + 1)
                    self.canvas.update()

    def _update_group_list(self):
        """Update the group list to reflect the current state of node groups."""
        self.group_list.clear()
        for group in self.canvas.graph.node_groups:
            item = QListWidgetItem(group.name)
            self.group_list.addItem(item)
