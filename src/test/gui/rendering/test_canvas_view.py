"""
Tests for the CanvasView class.
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QPointF, QEvent
from PyQt5.QtGui import QMouseEvent, QWheelEvent, QPainter
from PyQt5.QtWidgets import QApplication

from rect_graph_connector.rendering.canvas_view import CanvasView
from rect_graph_connector.controllers.input_handler import InputHandler
from rect_graph_connector.models.view_state_model import ViewStateModel
from rect_graph_connector.models.selection_model import SelectionModel
from rect_graph_connector.models.hover_state_model import HoverStateModel
from rect_graph_connector.models.graph import Graph


@pytest.fixture
def mock_input_handler():
    """Create a mock InputHandler."""
    mock = MagicMock(spec=InputHandler)
    return mock


@pytest.fixture
def canvas_view(mock_input_handler):
    """Create a CanvasView with a mock InputHandler."""
    # Create the canvas view with the mock input handler
    view = CanvasView(input_handler=mock_input_handler)
    return view


def create_mouse_event(event_type, button, position, modifiers=Qt.NoModifier):
    """Helper function to create a QMouseEvent."""
    return QMouseEvent(event_type, position, button, button, modifiers)


def test_init(canvas_view, mock_input_handler):
    """Test that CanvasView is initialized correctly with an InputHandler."""
    # Verify the input handler was set
    assert canvas_view.input_handler == mock_input_handler


def test_mouse_press_event(canvas_view, mock_input_handler):
    """Test that mousePressEvent delegates to the InputHandler."""
    # Create a mouse event
    pos = QPointF(100, 100)
    event = create_mouse_event(QEvent.MouseButtonPress, Qt.LeftButton, pos)

    # Call the method
    canvas_view.mousePressEvent(event)

    # Verify the input handler's handle_mouse_press was called
    mock_input_handler.handle_mouse_press.assert_called_once()

    # Verify the event and position were passed correctly
    args, _ = mock_input_handler.handle_mouse_press.call_args
    assert args[0] == event
    assert args[1] == pos


def test_mouse_move_event(canvas_view, mock_input_handler):
    """Test that mouseMoveEvent delegates to the InputHandler."""
    # Create a mouse event
    pos = QPointF(100, 100)
    event = create_mouse_event(QEvent.MouseMove, Qt.NoButton, pos)

    # Call the method
    canvas_view.mouseMoveEvent(event)

    # Verify the input handler's handle_mouse_move was called
    mock_input_handler.handle_mouse_move.assert_called_once()

    # Verify the event and position were passed correctly
    args, _ = mock_input_handler.handle_mouse_move.call_args
    assert args[0] == event
    assert args[1] == pos


def test_mouse_release_event(canvas_view, mock_input_handler):
    """Test that mouseReleaseEvent delegates to the InputHandler."""
    # Create a mouse event
    pos = QPointF(100, 100)
    event = create_mouse_event(QEvent.MouseButtonRelease, Qt.LeftButton, pos)

    # Call the method
    canvas_view.mouseReleaseEvent(event)

    # Verify the input handler's handle_mouse_release was called
    mock_input_handler.handle_mouse_release.assert_called_once()

    # Verify the event and position were passed correctly
    args, _ = mock_input_handler.handle_mouse_release.call_args
    assert args[0] == event
    assert args[1] == pos


def test_key_press_event(canvas_view, mock_input_handler):
    """Test that keyPressEvent delegates to the InputHandler."""
    # Create a key event
    event = MagicMock(spec=QEvent)
    event.key.return_value = Qt.Key_A

    # Call the method
    canvas_view.keyPressEvent(event)

    # Verify the input handler's handle_key_press was called
    mock_input_handler.handle_key_press.assert_called_once_with(event)


def test_wheel_event(canvas_view, mock_input_handler):
    """Test that wheelEvent delegates to the InputHandler."""
    # Create a wheel event
    pos = QPointF(100, 100)
    event = MagicMock(spec=QWheelEvent)
    event.pos.return_value = pos

    # Call the method
    canvas_view.wheelEvent(event)

    # Verify the input handler's handle_wheel was called
    mock_input_handler.handle_wheel.assert_called_once()

    # Verify the event and position were passed correctly
    args, _ = mock_input_handler.handle_wheel.call_args
    assert args[0] == event
    assert args[1] == pos


def test_error_handling(canvas_view, mock_input_handler):
    """Test that errors in event handlers are properly caught and logged."""
    # Make the input handler's handle_mouse_press raise an exception
    mock_input_handler.handle_mouse_press.side_effect = Exception("Test error")

    # Mock the logger
    canvas_view.logger.error = MagicMock()

    # Create a mouse event
    pos = QPointF(100, 100)
    event = create_mouse_event(QEvent.MouseButtonPress, Qt.LeftButton, pos)

    # Call the method - should not raise an exception
    canvas_view.mousePressEvent(event)

    # Verify the error was logged
    canvas_view.logger.error.assert_called_once()
    assert "Error in mousePressEvent" in canvas_view.logger.error.call_args[0][0]


def test_update_after_event(canvas_view, mock_input_handler):
    """Test that the view is updated after handling an event."""
    # Mock the update method
    canvas_view.update = MagicMock()

    # Create a mouse event
    pos = QPointF(100, 100)
    event = create_mouse_event(QEvent.MouseButtonPress, Qt.LeftButton, pos)

    # Call the method
    canvas_view.mousePressEvent(event)

    # Verify update was called
    canvas_view.update.assert_called_once()


def test_paint_event(canvas_view):
    """Test that paintEvent correctly uses the renderer."""
    # Mock the renderer
    canvas_view.renderer.draw = MagicMock()

    # Create a paint event
    event = MagicMock()

    # Mock QPainter
    with patch("PyQt5.QtGui.QPainter", autospec=True) as mock_painter_class:
        mock_painter = mock_painter_class.return_value

        # Call the method
        canvas_view.paintEvent(event)

        # Verify the painter was created
        mock_painter_class.assert_called_once_with(canvas_view)

        # Verify setRenderHint was called
        mock_painter.setRenderHint.assert_called_once_with(QPainter.Antialiasing)

        # Verify the renderer's draw method was called
        canvas_view.renderer.draw.assert_called_once()

        # Verify the correct arguments were passed
        args, kwargs = canvas_view.renderer.draw.call_args
        assert args[0] == mock_painter
        assert kwargs["selected_nodes"] == canvas_view.selection_model.selected_nodes
        assert kwargs["selected_edges"] == canvas_view.selection_model.selected_edges
        assert kwargs["selected_groups"] == canvas_view.selection_model.selected_groups
        assert kwargs["hover_node"] == canvas_view.hover_state.hovered_node
        assert kwargs["hover_edge"] == canvas_view.hover_state.hovered_edges
