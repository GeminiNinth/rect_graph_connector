"""
Tests for the Canvas widget.
"""

import pytest
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtTest import QTest

from rect_graph_connector.gui.canvas import Canvas
from rect_graph_connector.models.rect_node import RectNode


def test_canvas_initialization(canvas):
    """Test that the canvas initializes with the correct default values."""
    assert canvas is not None
    assert canvas.current_mode == canvas.NORMAL_MODE
    assert canvas.graph is not None
    assert len(canvas.graph.nodes) == 0
    assert len(canvas.graph.edges) == 0
    assert canvas.zoom == 1.0
    assert canvas.grid_visible is False
    assert canvas.snap_to_grid is False


def test_set_mode(canvas):
    """Test that the canvas mode can be changed."""
    # Initial mode should be NORMAL_MODE
    assert canvas.current_mode == canvas.NORMAL_MODE

    # Change to EDIT_MODE
    canvas.set_mode(canvas.EDIT_MODE)
    assert canvas.current_mode == canvas.EDIT_MODE

    # Change back to NORMAL_MODE
    canvas.set_mode(canvas.NORMAL_MODE)
    assert canvas.current_mode == canvas.NORMAL_MODE

    # Invalid mode should not change the current mode
    canvas.set_mode("invalid_mode")
    assert canvas.current_mode == canvas.NORMAL_MODE


def test_toggle_edit_mode(canvas):
    """Test toggling between normal and edit modes."""
    # Initial mode should be NORMAL_MODE
    assert canvas.current_mode == canvas.NORMAL_MODE

    # Toggle to EDIT_MODE
    canvas.toggle_edit_mode()
    assert canvas.current_mode == canvas.EDIT_MODE

    # Toggle back to NORMAL_MODE
    canvas.toggle_edit_mode()
    assert canvas.current_mode == canvas.NORMAL_MODE


def test_grid_visibility_toggle(canvas):
    """Test toggling grid visibility with the G key."""
    # Initial grid visibility should be False
    assert canvas.grid_visible is False

    # Simulate pressing the G key
    QTest.keyClick(canvas, Qt.Key_G)
    assert canvas.grid_visible is True

    # Simulate pressing the G key again
    QTest.keyClick(canvas, Qt.Key_G)
    assert canvas.grid_visible is False


def test_find_node_at_position(canvas):
    """Test finding a node at a specific position."""
    # Add a test node to the canvas
    node = RectNode(x=100, y=100, size=40, id="test_node")
    canvas.graph.nodes.append(node)

    # Test finding the node at its position
    found_node = canvas.graph.find_node_at_position(QPointF(100, 100))
    assert found_node is node

    # Test not finding a node at a different position
    found_node = canvas.graph.find_node_at_position(QPointF(200, 200))
    assert found_node is None


def test_snap_to_grid(canvas):
    """Test snapping coordinates to the grid."""
    # Test snapping a point to the grid
    snapped_x, snapped_y = canvas._snap_to_grid_point(42, 37)

    # The exact values depend on the grid spacing configuration
    # but we can check that they're different from the input
    assert snapped_x != 42 or snapped_y != 37

    # Test snapping all nodes
    # First add a node
    node = RectNode(x=42, y=37, size=40, id="test_node")
    canvas.graph.nodes.append(node)
    canvas.graph.selected_nodes = [node]

    # Enable grid and snapping
    canvas.grid_visible = True
    canvas.snap_to_grid = True

    # Snap all nodes
    canvas._snap_all_nodes_to_grid()

    # Check that the node position has changed
    assert node.x != 42 or node.y != 37


def test_key_press_escape(canvas):
    """Test that pressing Escape clears selections."""
    # Add a test node and select it
    node = RectNode(x=100, y=100, size=40, id="test_node")
    canvas.graph.nodes.append(node)
    canvas.graph.selected_nodes = [node]

    # Create a group and select it
    group_id = canvas.graph.create_node_group([node])
    group = next(g for g in canvas.graph.node_groups if g.id == group_id)
    canvas.graph.selected_groups = [group]

    # Simulate pressing Escape
    QTest.keyClick(canvas, Qt.Key_Escape)

    # Check that selections are cleared
    assert len(canvas.graph.selected_nodes) == 0
    assert len(canvas.graph.selected_groups) == 0


def test_mouse_press_on_node(canvas, qtbot):
    """Test selecting a node with mouse press."""
    print("DEBUG: test_mouse_press_on_node started")

    # Add a test node
    node = RectNode(x=100, y=100, size=40, id="test_node")
    canvas.graph.nodes.append(node)
    print(f"DEBUG: Added node: {node}, x={node.x}, y={node.y}, size={node.size}")

    # Create a group for the node
    group_id = canvas.graph.create_node_group([node])
    group = next(g for g in canvas.graph.node_groups if g.id == group_id)
    print(f"DEBUG: Created group with id: {group_id}")

    # Calculate widget coordinates for the node
    widget_x = int(node.x * canvas.zoom + canvas.pan_offset.x())
    widget_y = int(node.y * canvas.zoom + canvas.pan_offset.y())
    print(f"DEBUG: Calculated widget coordinates: ({widget_x}, {widget_y})")
    print(f"DEBUG: Canvas zoom: {canvas.zoom}, pan_offset: {canvas.pan_offset}")

    # Create a QPoint for the click position
    from PyQt5.QtCore import QPoint

    click_pos = QPoint(widget_x, widget_y)
    print(f"DEBUG: Created QPoint for click: {click_pos}")

    # Click on the node
    print(f"DEBUG: Attempting to click at position: {click_pos}")
    try:
        qtbot.mouseClick(canvas, Qt.LeftButton, pos=click_pos)
        print("DEBUG: mouseClick succeeded")
    except Exception as e:
        print(f"DEBUG: mouseClick failed with error: {e}")
        # Try alternative approach
        print("DEBUG: Trying direct event simulation")
        from PyQt5.QtGui import QMouseEvent

        mouse_event = QMouseEvent(
            QMouseEvent.MouseButtonPress,
            click_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        canvas.mousePressEvent(mouse_event)

    # Check that the node's group is selected
    print(f"DEBUG: Selected groups: {[g.id for g in canvas.graph.selected_groups]}")
    print(f"DEBUG: Selected nodes: {[n.id for n in canvas.graph.selected_nodes]}")
    assert group in canvas.graph.selected_groups
    assert node in canvas.graph.selected_nodes
    print("DEBUG: test_mouse_press_on_node completed")
