"""
Tests for the ModeController class.
"""

import pytest
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtTest import QTest

from rect_graph_connector.gui.canvas import Canvas

# Since we don't have direct access to the ModeController class yet,
# we'll test the mode functionality through the Canvas class
# which should have a mode_controller attribute or similar functionality


class TestModeController:
    """Test suite for mode controller functionality."""

    def test_mode_switching(self, canvas):
        """Test switching between different modes."""
        # Initial mode should be NORMAL_MODE
        assert canvas.current_mode == canvas.NORMAL_MODE

        # Switch to EDIT_MODE
        canvas.set_mode(canvas.EDIT_MODE)
        assert canvas.current_mode == canvas.EDIT_MODE

        # Switch back to NORMAL_MODE
        canvas.set_mode(canvas.NORMAL_MODE)
        assert canvas.current_mode == canvas.NORMAL_MODE

    def test_edit_submode_switching(self, canvas):
        """Test switching between different edit submodes."""
        # First switch to EDIT_MODE
        canvas.set_mode(canvas.EDIT_MODE)

        # Default edit submode should be EDIT_SUBMODE_CONNECT
        assert canvas.edit_submode == canvas.EDIT_SUBMODE_CONNECT

        # Switch to knife submode
        canvas.set_edit_submode(canvas.EDIT_SUBMODE_KNIFE)
        assert canvas.edit_submode == canvas.EDIT_SUBMODE_KNIFE

        # Switch to all-for-one submode
        canvas.set_edit_submode(canvas.EDIT_SUBMODE_ALL_FOR_ONE)
        assert canvas.edit_submode == canvas.EDIT_SUBMODE_ALL_FOR_ONE

        # Switch to parallel submode
        canvas.set_edit_submode(canvas.EDIT_SUBMODE_PARALLEL)
        assert canvas.edit_submode == canvas.EDIT_SUBMODE_PARALLEL

        # Switch back to connect submode
        canvas.set_edit_submode(canvas.EDIT_SUBMODE_CONNECT)
        assert canvas.edit_submode == canvas.EDIT_SUBMODE_CONNECT

    def test_mode_signal_emission(self, canvas, qtbot):
        """Test that mode change signals are emitted correctly."""
        # Connect to the mode_changed signal
        with qtbot.waitSignal(canvas.mode_changed, timeout=1000) as blocker:
            # Change the mode
            canvas.set_mode(canvas.EDIT_MODE)

        # Check that the signal was emitted with the correct mode
        assert blocker.args == [canvas.EDIT_MODE]

        # Connect to the mode_changed signal again
        with qtbot.waitSignal(canvas.mode_changed, timeout=1000) as blocker:
            # Change the mode back
            canvas.set_mode(canvas.NORMAL_MODE)

        # Check that the signal was emitted with the correct mode
        assert blocker.args == [canvas.NORMAL_MODE]

    def test_keyboard_mode_switching(self, canvas):
        """Test switching modes using keyboard shortcuts."""
        # Select a node to enable edit mode toggle
        node = canvas.graph.nodes[0] if canvas.graph.nodes else None

        if node:
            # Create a group for the node if it doesn't have one
            if not canvas.graph.get_group_for_node(node):
                group_id = canvas.graph.create_node_group([node])

            # Select the node's group
            group = canvas.graph.get_group_for_node(node)
            canvas.graph.selected_groups = [group]

            # Press E key to toggle edit mode
            QTest.keyClick(canvas, Qt.Key_E)
            assert canvas.current_mode == canvas.EDIT_MODE

            # Press E key again to toggle back to normal mode
            QTest.keyClick(canvas, Qt.Key_E)
            assert canvas.current_mode == canvas.NORMAL_MODE

    def test_cursor_changes_with_mode(self, canvas):
        """Test that the cursor changes appropriately with mode changes."""
        # Initial cursor in normal mode should be ArrowCursor
        assert canvas.cursor().shape() == Qt.ArrowCursor

        # Switch to edit mode
        canvas.set_mode(canvas.EDIT_MODE)
        # Cursor in edit mode should be CrossCursor
        assert canvas.cursor().shape() == Qt.CrossCursor

        # Switch to knife submode
        canvas.set_edit_submode(canvas.EDIT_SUBMODE_KNIFE)
        # Cursor in knife mode should be CrossCursor (or a custom cursor)
        assert canvas.cursor().shape() == Qt.CrossCursor

        # Switch back to normal mode
        canvas.set_mode(canvas.NORMAL_MODE)
        # Cursor should be back to ArrowCursor
        assert canvas.cursor().shape() == Qt.ArrowCursor
