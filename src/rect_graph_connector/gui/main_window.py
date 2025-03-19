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
    QFrame,
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QKeyEvent


class NodeGroupInputEdit(QLineEdit):
    """
    Custom QLineEdit for node group input that emits a signal when Enter is pressed.
    """

    enterPressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events, specifically the Enter/Return key."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.enterPressed.emit()
        else:
            super().keyPressEvent(event)


from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor

from .canvas import Canvas
from ..utils.file_handler import FileHandler
from ..utils.logging_utils import get_logger
from .import_dialog import ImportModeDialog
from ..config import config

logger = get_logger(__name__)


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
        window_title = config.get_string(
            "main_window.title", "Rectangular Graph Creator"
        )
        self.setWindowTitle(window_title)

        initial_x = config.get_dimension("main_window.initial.x", 100)
        initial_y = config.get_dimension("main_window.initial.y", 100)
        initial_width = config.get_dimension("main_window.initial.width", 800)
        initial_height = config.get_dimension("main_window.initial.height", 600)
        self.setGeometry(initial_x, initial_y, initial_width, initial_height)

    def _create_widgets(self):
        # Main widget and canvas
        self.main_widget = QWidget()
        self.canvas = Canvas()

        # Get the width of the input field
        row_col_width = config.get_dimension("input.row_col_width", 50)
        move_button_width = config.get_dimension("input.move_button_width", 40)

        # Control panel widgets
        self.row_input = NodeGroupInputEdit()
        self.row_input.setFixedWidth(row_col_width)
        self.row_input.enterPressed.connect(self._handle_input_enter)

        self.col_input = NodeGroupInputEdit()
        self.col_input.setFixedWidth(row_col_width)
        self.col_input.enterPressed.connect(self._handle_input_enter)

        self.add_button = QPushButton(
            config.get_string("main_window.buttons.add", "Add")
        )
        self.import_button = QPushButton(
            config.get_string("main_window.buttons.import", "Import")
        )
        self.export_button = QPushButton(
            config.get_string("main_window.buttons.export", "Export YAML")
        )
        self.reset_button = QPushButton(
            config.get_string("main_window.buttons.reset", "Reset All")
        )
        self.delete_button = QPushButton(
            config.get_string("main_window.buttons.delete", "Delete Group")
        )
        self.rotate_button = QPushButton(
            config.get_string("main_window.buttons.rotate", "Rotate Group")
        )

        # Side menu widgets
        self.group_list = QListWidget()
        self.group_list.setSelectionMode(QAbstractItemView.SingleSelection)

        side_panel_min_width = config.get_dimension(
            "main_window.side_panel.min_width", 150
        )
        self.group_list.setMinimumWidth(side_panel_min_width)

        self.move_up_button = QPushButton(
            config.get_string("main_window.buttons.move_up", "↑")
        )
        self.move_up_button.setToolTip(
            config.get_string("main_window.tooltips.move_up", "Move group up")
        )
        self.move_up_button.setFixedWidth(move_button_width)

        self.move_down_button = QPushButton(
            config.get_string("main_window.buttons.move_down", "↓")
        )
        self.move_down_button.setToolTip(
            config.get_string("main_window.tooltips.move_down", "Move group down")
        )
        self.move_down_button.setFixedWidth(move_button_width)

        # Mode display window
        self.mode_indicator = QFrame()
        self.mode_indicator.setFrameShape(QFrame.NoFrame)  # Remove frame shape
        mode_indicator_min_height = config.get_dimension(
            "mode_indicator.min_height", 30
        )
        mode_indicator_max_height = config.get_dimension(
            "mode_indicator.max_height", 30
        )
        self.mode_indicator.setMinimumHeight(mode_indicator_min_height)
        self.mode_indicator.setMaximumHeight(mode_indicator_max_height)

        normal_mode_text = config.get_string("main_window.mode.normal", "Mode: Normal")
        self.mode_label = QLabel(normal_mode_text)
        self.mode_label.setAlignment(Qt.AlignCenter)

    def _setup_layout(self):
        # Set main widget as central widget
        self.setCentralWidget(self.main_widget)

        # Create main layout
        layout = QVBoxLayout(self.main_widget)
        layout_margin = config.get_dimension("main_window.layout.margin", 5)
        layout_spacing = config.get_dimension("main_window.layout.spacing", 5)
        layout.setSpacing(layout_spacing)
        layout.setContentsMargins(
            layout_margin, layout_margin, layout_margin, layout_margin
        )

        # Create a splitter for the main area
        splitter = QSplitter(Qt.Horizontal)

        # Create and set up side menu
        side_menu = self._create_side_menu()
        splitter.addWidget(side_menu)

        # Add canvas to splitter
        splitter.addWidget(self.canvas)

        side_menu_width = config.get_dimension("main_window.splitter.side_menu", 150)
        canvas_width = config.get_dimension("main_window.splitter.canvas", 650)
        splitter.setSizes([side_menu_width, canvas_width])

        # Add splitter to layout
        layout.addWidget(splitter, stretch=85)

        # Mode Display Window Settings
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.mode_label)
        self.mode_indicator.setLayout(mode_layout)
        layout.addWidget(self.mode_indicator, stretch=5)

        # Create and set up control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel, stretch=10)

    def _create_side_menu(self) -> QWidget:
        """Create and return the side menu widget."""
        side_menu = QWidget()
        layout = QVBoxLayout(side_menu)

        layout_margin = config.get_dimension("main_window.layout.margin", 5)
        layout.setContentsMargins(
            layout_margin, layout_margin, layout_margin, layout_margin
        )

        node_groups_text = config.get_string(
            "main_window.labels.node_groups", "Node Groups"
        )
        title = QLabel(node_groups_text)
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
        max_height = config.get_dimension("main_window.control_panel.max_height", 50)
        control_panel.setMaximumHeight(max_height)

        layout = QHBoxLayout(control_panel)
        layout.setContentsMargins(0, 0, 0, 0)

        rows_label_text = config.get_string("main_window.labels.rows", "Rows:")
        cols_label_text = config.get_string("main_window.labels.cols", "Cols:")

        # Add row input
        layout.addWidget(QLabel(rows_label_text))
        layout.addWidget(self.row_input)

        # Add column input
        layout.addWidget(QLabel(cols_label_text))
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

        # Connecting mode change signal
        self.canvas.mode_changed.connect(self._update_mode_indicator)

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
            logger.warning("Please enter valid numbers for rows and columns")

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
            logger.error(f"Failed to export graph: {e}")

    def _handle_import(self):
        """Handle the Import button click event."""
        options = QFileDialog.Options()
        # Get dialog title and filter from configuration file
        import_dialog_title = config.get_string(
            "main_window.dialogs.import.title", "Import graph"
        )
        import_dialog_filter = config.get_string(
            "main_window.dialogs.import.filter", "YAML Files (*.yaml);;All Files (*)"
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            import_dialog_title,
            "",
            import_dialog_filter,
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
                logger.error(f"Failed to import graph: {e}")

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
        # Check if there are selected groups from multi-selection
        if (
            self.canvas.graph.selected_groups
            and len(self.canvas.graph.selected_groups) > 0
        ):
            # Create a copy of the list since we're modifying it during iteration
            groups_to_delete = self.canvas.graph.selected_groups.copy()
            # Log how many groups are being deleted
            logger.info(f"Deleting {len(groups_to_delete)} groups")

            # Process each group separately to ensure all are deleted
            for group in groups_to_delete:
                # Delete the group from the graph
                self.canvas.graph.delete_group(group)
                logger.info(f"Deleted group: {group.name} (ID: {group.id})")

            # Clear selection after all deletions are complete
            self.canvas.graph.selected_group = None
            self.canvas.graph.selected_groups = []
            self.canvas.graph.selected_nodes = []

            self._update_group_list()
            self.canvas.update()
        # Fallback to single selection if no groups in multi-selection
        elif self.canvas.graph.selected_group:
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
        # Check if we have multiple groups selected
        if (
            self.canvas.graph.selected_groups
            and len(self.canvas.graph.selected_groups) > 0
        ):
            # Log how many groups are being rotated
            logger.info(f"Rotating {len(self.canvas.graph.selected_groups)} groups")

            # Rotate each group around its own center point
            self.canvas.graph.rotate_node_groups(self.canvas.graph.selected_groups)

            for group in self.canvas.graph.selected_groups:
                logger.info(f"Rotated group: {group.name} (ID: {group.id})")

            self.canvas.update()
        # Fallback to the original implementation for single selection
        elif self.canvas.graph.selected_nodes:
            logger.info(
                f"Rotating {len(self.canvas.graph.selected_nodes)} nodes in a single group"
            )
            self.canvas.graph.rotate_group(self.canvas.graph.selected_nodes)
            self.canvas.update()

    def _handle_rename_group(self, item):
        """Handle the double-click event on a group item to rename it."""
        index = self.group_list.row(item)
        if 0 <= index < len(self.canvas.graph.node_groups):
            group = self.canvas.graph.node_groups[index]
            rename_dialog_title = config.get_string(
                "main_window.dialogs.rename.title", "Rename Group"
            )
            rename_dialog_prompt = config.get_string(
                "main_window.dialogs.rename.prompt", "Enter new group name:"
            )

            new_name, ok = QInputDialog.getText(
                self, rename_dialog_title, rename_dialog_prompt, text=group.name
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

    def _update_mode_indicator(self, mode):
        """
        Update the mode display window.

        Args:
            mode (str): Current mode ("normal" or "edit")
        """
        # Update mode display text
        if mode == self.canvas.EDIT_MODE:
            # Edit mode display
            if self.canvas.edit_submode == self.canvas.EDIT_SUBMODE_ALL_FOR_ONE:
                # All-For-One connection mode display
                mode_text = config.get_string(
                    "main_window.mode.edit_all_for_one", "Mode: Edit - All-For-One"
                )
                self.mode_label.setText(mode_text)
            elif self.canvas.edit_submode == self.canvas.EDIT_SUBMODE_PARALLEL:
                # Parallel connection mode display
                mode_text = config.get_string(
                    "main_window.mode.edit_parallel", "Mode: Edit - Parallel"
                )
                self.mode_label.setText(mode_text)
            else:
                # Normal edit mode display
                edit_target = ""
                if self.canvas.edit_target_groups:
                    group_names = [
                        group.name for group in self.canvas.edit_target_groups
                    ]
                    edit_target = f" - {', '.join(group_names)}"
                edit_mode_text = config.get_string(
                    "main_window.mode.edit", "Mode: Edit"
                )
                self.mode_label.setText(f"{edit_mode_text}{edit_target}")

            # Visual feedback - set reddish color (no border)
            edit_bg_color = config.get_color(
                "mode_indicator.edit", "rgba(255, 220, 220, 180)"
            )
            self.mode_indicator.setStyleSheet(f"background-color: {edit_bg_color};")
        else:
            normal_mode_text = config.get_string(
                "main_window.mode.normal", "Mode: Normal"
            )
            # Normal mode display
            self.mode_label.setText(normal_mode_text)
            # Visual feedback - return to normal color (no border)
            normal_bg_color = config.get_color(
                "mode_indicator.normal", "rgba(240, 240, 240, 180)"
            )
            self.mode_indicator.setStyleSheet(f"background-color: {normal_bg_color};")

    def keyPressEvent(self, event):
        """
        Handle keyboard events.

        Args:
            event (QKeyEvent): The key event to handle
        """
        # Delete key (Del) pressed
        if event.key() == Qt.Key_Delete:
            self._handle_delete()
        else:
            # Pass other key events to parent class
            super().keyPressEvent(event)

    def _handle_input_enter(self):
        """
        Handle Enter key press in row/col input fields.
        If both fields have valid values, add a new node group.
        """
        if self.row_input.text() and self.col_input.text():
            self._handle_add()

    def _update_group_list(self):
        """Update the group list to reflect the current state of node groups."""
        self.group_list.clear()
        for group in self.canvas.graph.node_groups:
            item = QListWidgetItem(group.name)
            self.group_list.addItem(item)
