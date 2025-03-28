"""
This module contains the main window implementation for the graph editor application.
"""

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QKeyEvent
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..config import config
from ..utils.file_handler import FileHandler
from ..utils.logging_utils import get_logger
from .canvas import Canvas
from .import_dialog import ImportModeDialog

logger = get_logger(__name__)


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

        # Get window dimensions from config
        initial_width = config.get_dimension("main_window.initial.width", 800)
        initial_height = config.get_dimension("main_window.initial.height", 600)

        # Set window size
        self.resize(initial_width, initial_height)

        # Center the window on the screen
        self.center_window()

    def center_window(self):
        """Center the window on the screen."""
        # Get the screen geometry
        screen_geometry = self.screen().geometry()

        # Calculate the center position
        center_x = (screen_geometry.width() - self.width()) // 2
        center_y = (screen_geometry.height() - self.height()) // 2

        # Move the window to the center
        self.move(center_x, center_y)

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

        # Side menu widgets
        self.group_list = QListWidget()
        self.group_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

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

        # Grid snap checkbox
        self.snap_checkbox = QCheckBox(
            config.get_string("main_window.grid.snap", "Snap to Grid")
        )
        self.snap_checkbox.setEnabled(
            False
        )  # Disabled by default since grid is initially hidden
        self.snap_checkbox.setStyleSheet(
            "opacity: 0.5"
        )  # Make it semi-transparent when disabled

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
        # Delete and Rotate buttons removed - functionality moved to context menu

        # Add snap checkbox at the bottom
        layout.addWidget(self.snap_checkbox)

        # Add stretch to push everything to the left
        layout.addStretch()

        return control_panel

    def _connect_signals(self):
        """Connect all signal handlers."""
        self.add_button.clicked.connect(self._handle_add)
        self.import_button.clicked.connect(self._handle_import)
        self.export_button.clicked.connect(self._handle_export)
        self.reset_button.clicked.connect(self._handle_reset)
        # Delete and Rotate button connections removed - functionality moved to context menu

        # Connect side menu signals
        self.group_list.itemDoubleClicked.connect(self._handle_rename_group)
        self.group_list.itemClicked.connect(self._handle_select_group)
        self.move_up_button.clicked.connect(self._handle_move_group_up)
        self.move_down_button.clicked.connect(self._handle_move_group_down)

        # Connecting mode change signal
        self.canvas.mode_changed.connect(self._update_mode_indicator)

        # Connect group selection signal from canvas
        self.canvas.group_selected.connect(self._handle_canvas_group_selected)

        # Connect grid signals
        self.canvas.grid_state_changed.connect(self._handle_grid_state_changed)
        self.snap_checkbox.stateChanged.connect(self._handle_snap_toggled)

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
                logger.info(f"  Deleted group: {group.name} (ID: {group.id})")

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
                logger.info(f"  Rotated group: {group.name} (ID: {group.id})")

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
        # Get all selected items in the list
        selected_items = self.group_list.selectedItems()

        # Check if we're in multi-selection mode (Shift key pressed)
        modifiers = QApplication.keyboardModifiers()
        shift_pressed = modifiers & Qt.ShiftModifier

        # Get the index of the clicked item
        current_index = self.group_list.row(item)

        # If not in multi-selection mode and not pressing shift, clear previous selection
        if not shift_pressed and len(selected_items) <= 1:
            self.canvas.graph.selected_groups = []
            self.canvas.graph.selected_nodes = []

            # Process the clicked item
            if 0 <= current_index < len(self.canvas.graph.node_groups):
                group = self.canvas.graph.node_groups[current_index]

                # Add this group to the selection
                self.canvas.graph.selected_groups.append(group)
                # Add the group's nodes to the selected nodes
                self.canvas.graph.selected_nodes.extend(
                    group.get_nodes(self.canvas.graph.nodes)
                )
        else:
            # Handle Shift key continuous selection
            if shift_pressed and len(selected_items) > 0:
                # Find the index of the last selected item before this click
                last_selected_index = -1
                for i in range(self.group_list.count()):
                    if i != current_index and self.group_list.item(i).isSelected():
                        last_selected_index = i

                # If we found a previously selected item, select all items between it and the current item
                if last_selected_index != -1:
                    # Determine the range of indices to select
                    start_idx = min(last_selected_index, current_index)
                    end_idx = max(last_selected_index, current_index)

                    # Select all groups in the range
                    for idx in range(start_idx, end_idx + 1):
                        if 0 <= idx < len(self.canvas.graph.node_groups):
                            group = self.canvas.graph.node_groups[idx]
                            if group not in self.canvas.graph.selected_groups:
                                self.canvas.graph.selected_groups.append(group)
                                # Add the group's nodes to the selected nodes
                                self.canvas.graph.selected_nodes.extend(
                                    group.get_nodes(self.canvas.graph.nodes)
                                )
                                # Select the item in the list
                                self.group_list.item(idx).setSelected(True)
                else:
                    # If no previous selection, just add the current group
                    if 0 <= current_index < len(self.canvas.graph.node_groups):
                        group = self.canvas.graph.node_groups[current_index]
                        if group not in self.canvas.graph.selected_groups:
                            self.canvas.graph.selected_groups.append(group)
                            # Add the group's nodes to the selected nodes
                            self.canvas.graph.selected_nodes.extend(
                                group.get_nodes(self.canvas.graph.nodes)
                            )
            else:
                # Regular multi-selection (Ctrl key)
                if 0 <= current_index < len(self.canvas.graph.node_groups):
                    group = self.canvas.graph.node_groups[current_index]
                    if group not in self.canvas.graph.selected_groups:
                        self.canvas.graph.selected_groups.append(group)
                        # Add the group's nodes to the selected nodes
                        self.canvas.graph.selected_nodes.extend(
                            group.get_nodes(self.canvas.graph.nodes)
                        )

        # Update the canvas
        self.canvas.update()

    def _handle_move_group_up(self):
        """Handle the move up button click event."""
        selected_items = self.group_list.selectedItems()
        if not selected_items:
            return

        # Get all selected indices and sort them in ascending order
        selected_indices = sorted(
            [self.group_list.row(item) for item in selected_items]
        )

        # Check if the topmost selected group is already at the top
        if selected_indices[0] <= 0:
            return

        # Move all selected groups up as a unit
        # We need to move them one by one, starting from the top
        for index in selected_indices:
            if 0 <= index < len(self.canvas.graph.node_groups):
                group = self.canvas.graph.node_groups[index]
                self.canvas.graph.move_group_up(group)

        # Update the list and maintain selection
        self._update_group_list()

        # Select all moved groups at their new positions
        self.group_list.clearSelection()
        for index in selected_indices:
            if index > 0:  # Only select if it was actually moved
                self.group_list.item(index - 1).setSelected(True)

        self.canvas.update()

    def _handle_move_group_down(self):
        """Handle the move down button click event."""
        selected_items = self.group_list.selectedItems()
        if not selected_items:
            return

        # Get all selected indices and sort them in descending order
        # We need to move from bottom to top when moving down to avoid index issues
        selected_indices = sorted(
            [self.group_list.row(item) for item in selected_items], reverse=True
        )

        # Check if the bottommost selected group is already at the bottom
        if selected_indices[0] >= len(self.canvas.graph.node_groups) - 1:
            return

        # Move all selected groups down as a unit
        # We need to move them one by one, starting from the bottom
        for index in selected_indices:
            if 0 <= index < len(self.canvas.graph.node_groups):
                group = self.canvas.graph.node_groups[index]
                self.canvas.graph.move_group_down(group)

        # Update the list and maintain selection
        self._update_group_list()

        # Select all moved groups at their new positions
        self.group_list.clearSelection()
        for index in selected_indices:
            if (
                index < len(self.canvas.graph.node_groups) - 1
            ):  # Only select if it was actually moved
                self.group_list.item(index + 1).setSelected(True)

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

    def _handle_snap_toggled(self, state):
        """
        Handle toggling of snap to grid checkbox.

        Args:
            state (int): Qt.Checked (2) if checked, Qt.Unchecked (0) if unchecked
        """
        from PyQt5.QtCore import Qt

        is_checked = state == Qt.Checked
        logger.info(f"Snap to grid toggled: {is_checked}")

        # Update canvas snap setting
        self.canvas.snap_to_grid = is_checked

        # Snap all nodes to grid if enabled
        if is_checked:
            self.canvas._snap_all_nodes_to_grid()

        # Emit the grid state changed signal to keep other components in sync
        self.canvas.grid_state_changed.emit(self.canvas.grid_visible, is_checked)

        # Refresh the canvas
        self.canvas.update()

    def _handle_grid_state_changed(self, grid_visible, snap_enabled):
        """
        Handle grid state changes from the canvas.

        Args:
            grid_visible (bool): Whether the grid is visible
            snap_enabled (bool): Whether snap to grid is enabled
        """
        # Update the checkbox state
        self.snap_checkbox.setEnabled(grid_visible)

        # Check the checkbox to match the snap state
        if grid_visible:
            self.snap_checkbox.setChecked(snap_enabled)
        else:
            # If grid is hidden, uncheck the checkbox
            self.snap_checkbox.setChecked(False)

        # Update the appearance of the checkbox
        opacity = 1.0 if grid_visible else 0.5
        self.snap_checkbox.setStyleSheet(f"opacity: {opacity}")

    def _update_grid_snap_state(self, visible):
        """
        Update the grid snap checkbox state based on grid visibility.

        Args:
            visible (bool): Whether the grid is visible
        """
        self.snap_checkbox.setEnabled(visible)

        if not visible:
            # If grid is hidden, also uncheck the checkbox
            # but don't set canvas.snap_to_grid to False to remember state
            self.snap_checkbox.setChecked(False)

        # Update the appearance of the checkbox
        opacity = 1.0 if visible else 0.5
        self.snap_checkbox.setStyleSheet(f"opacity: {opacity}")

    def _handle_canvas_group_selected(self, group):
        """
        Handle the group_selected signal from the canvas.
        Updates the side panel selection to match the canvas selection.

        Args:
            group (NodeGroup): The group that was selected in the canvas
        """
        # Update the side panel to reflect all selected groups in the canvas
        self._sync_side_panel_selection()

    def _sync_side_panel_selection(self):
        """
        Synchronize the side panel selection with the canvas selection.
        Selects all items in the side panel that correspond to selected groups in the canvas.
        """
        # Clear current selection in the side panel
        self.group_list.clearSelection()

        # Get all selected groups from the canvas
        selected_groups = self.canvas.graph.selected_groups

        # Select each corresponding item in the side panel
        for group in selected_groups:
            try:
                index = self.canvas.graph.node_groups.index(group)
                # Select the item without clearing other selections
                item = self.group_list.item(index)
                if item:
                    item.setSelected(True)
            except ValueError:
                # Group not found in the list
                logger.warning(
                    f"Selected group not found in node_groups list: {group.name}"
                )

    def _update_group_list(self):
        """Update the group list to reflect the current state of node groups."""
        self.group_list.clear()
        for group in self.canvas.graph.node_groups:
            item = QListWidgetItem(group.name)
            self.group_list.addItem(item)
