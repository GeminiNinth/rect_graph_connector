"""
Tests for the InputHandler class.
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QPointF, QEvent
from PyQt5.QtGui import QMouseEvent, QWheelEvent

from rect_graph_connector.controllers.input_handler import InputHandler
from rect_graph_connector.models.view_state_model import ViewStateModel
from rect_graph_connector.models.selection_model import SelectionModel
from rect_graph_connector.models.hover_state_model import HoverStateModel
from rect_graph_connector.models.graph import Graph


@pytest.fixture
def input_handler():
    """Create a test InputHandler with mock dependencies."""
    view_state = MagicMock(spec=ViewStateModel)
    selection_model = MagicMock(spec=SelectionModel)
    hover_state = MagicMock(spec=HoverStateModel)
    graph = MagicMock(spec=Graph)

    # Configure mocks
    view_state.zoom = 1.0
    view_state.pan_offset = QPointF(0, 0)

    handler = InputHandler(view_state, selection_model, hover_state, graph)

    # Mock the mode controllers
    handler.mode_controllers = {
        handler.NORMAL_MODE: MagicMock(),
        handler.EDIT_MODE: MagicMock(),
    }
    handler.current_mode_controller = handler.mode_controllers[handler.current_mode]

    return handler


def test_handle_mouse_press(input_handler):
    """Test that mouse press events are properly delegated to the current mode controller."""
    # Create a mock mouse event
    event = MagicMock(spec=QMouseEvent)
    event.button.return_value = Qt.LeftButton
    widget_point = QPointF(100, 100)

    # Call the method
    input_handler.handle_mouse_press(event, widget_point)

    # Verify the current mode controller's handle_mouse_press was called
    input_handler.current_mode_controller.handle_mouse_press.assert_called_once()

    # Verify the event and points were passed correctly
    args, _ = input_handler.current_mode_controller.handle_mouse_press.call_args
    assert args[0] == event
    assert isinstance(args[1], QPointF)  # graph_point
    assert args[2] == widget_point


def test_handle_mouse_press_middle_button(input_handler):
    """Test that middle button press starts panning."""
    # Create a mock mouse event for middle button
    event = MagicMock(spec=QMouseEvent)
    event.button.return_value = Qt.MiddleButton
    widget_point = QPointF(100, 100)

    # Mock the _start_panning method
    input_handler._start_panning = MagicMock()

    # Call the method
    result = input_handler.handle_mouse_press(event, widget_point)

    # Verify _start_panning was called with the widget point
    input_handler._start_panning.assert_called_once_with(widget_point)

    # Verify the method returns True
    assert result is True

    # Verify the current mode controller's handle_mouse_press was NOT called
    input_handler.current_mode_controller.handle_mouse_press.assert_not_called()


def test_handle_mouse_move(input_handler):
    """Test that mouse move events are properly delegated to the current mode controller."""
    # Create a mock mouse event
    event = MagicMock(spec=QMouseEvent)
    widget_point = QPointF(100, 100)

    # Call the method
    input_handler.handle_mouse_move(event, widget_point)

    # Verify the current mode controller's handle_mouse_move was called
    input_handler.current_mode_controller.handle_mouse_move.assert_called_once()

    # Verify the event and points were passed correctly
    args, _ = input_handler.current_mode_controller.handle_mouse_move.call_args
    assert args[0] == event
    assert isinstance(args[1], QPointF)  # graph_point
    assert args[2] == widget_point


def test_handle_mouse_move_panning(input_handler):
    """Test that mouse move during panning updates the pan offset."""
    # Create a mock mouse event
    event = MagicMock(spec=QMouseEvent)
    widget_point = QPointF(100, 100)

    # Set panning state
    input_handler.panning = True

    # Mock the _update_panning method
    input_handler._update_panning = MagicMock()

    # Call the method
    result = input_handler.handle_mouse_move(event, widget_point)

    # Verify _update_panning was called with the widget point
    input_handler._update_panning.assert_called_once_with(widget_point)

    # Verify the method returns True
    assert result is True

    # Verify the current mode controller's handle_mouse_move was NOT called
    input_handler.current_mode_controller.handle_mouse_move.assert_not_called()


def test_handle_mouse_release(input_handler):
    """Test that mouse release events are properly delegated to the current mode controller."""
    # Create a mock mouse event
    event = MagicMock(spec=QMouseEvent)
    event.button.return_value = Qt.LeftButton
    widget_point = QPointF(100, 100)

    # Call the method
    input_handler.handle_mouse_release(event, widget_point)

    # Verify the current mode controller's handle_mouse_release was called
    input_handler.current_mode_controller.handle_mouse_release.assert_called_once()

    # Verify the event and points were passed correctly
    args, _ = input_handler.current_mode_controller.handle_mouse_release.call_args
    assert args[0] == event
    assert isinstance(args[1], QPointF)  # graph_point
    assert args[2] == widget_point


def test_handle_mouse_release_middle_button(input_handler):
    """Test that middle button release ends panning."""
    # Create a mock mouse event for middle button
    event = MagicMock(spec=QMouseEvent)
    event.button.return_value = Qt.MiddleButton
    widget_point = QPointF(100, 100)

    # Set panning state
    input_handler.panning = True

    # Mock the _end_panning method
    input_handler._end_panning = MagicMock()

    # Call the method
    result = input_handler.handle_mouse_release(event, widget_point)

    # Verify _end_panning was called
    input_handler._end_panning.assert_called_once()

    # Verify the method returns True
    assert result is True

    # Verify the current mode controller's handle_mouse_release was NOT called
    input_handler.current_mode_controller.handle_mouse_release.assert_not_called()


def test_handle_key_press(input_handler):
    """Test that key press events are properly delegated to the current mode controller."""
    # Create a mock key event
    event = MagicMock(spec=QEvent)

    # Call the method
    input_handler.handle_key_press(event)

    # Verify the current mode controller's handle_key_press was called
    input_handler.current_mode_controller.handle_key_press.assert_called_once_with(
        event
    )


def test_handle_wheel(input_handler):
    """Test that wheel events properly update the zoom level."""
    # Create a mock wheel event
    event = MagicMock(spec=QWheelEvent)
    event.angleDelta().y.return_value = 120  # Positive value for zoom in
    widget_point = QPointF(100, 100)

    # Call the method
    result = input_handler.handle_wheel(event, widget_point)

    # Verify the view_state's zoom was updated
    assert input_handler.view_state.zoom != 1.0

    # Verify the method returns True
    assert result is True


def test_set_mode(input_handler):
    """Test that setting the mode updates the current mode controller."""
    # Get the initial mode
    initial_mode = input_handler.current_mode
    new_mode = (
        input_handler.EDIT_MODE
        if initial_mode == input_handler.NORMAL_MODE
        else input_handler.NORMAL_MODE
    )

    # Call the method
    input_handler.set_mode(new_mode)

    # Verify the current mode was updated
    assert input_handler.current_mode == new_mode

    # Verify the current mode controller was updated
    assert (
        input_handler.current_mode_controller
        == input_handler.mode_controllers[new_mode]
    )

    # Verify the hover state was cleared
    input_handler.hover_state.clear.assert_called_once()


def test_widget_to_graph_point(input_handler):
    """Test that widget coordinates are correctly converted to graph coordinates."""
    # Set up test values
    widget_point = QPointF(100, 100)
    input_handler.view_state.zoom = 2.0
    input_handler.view_state.pan_offset = QPointF(10, 10)

    # Call the method
    graph_point = input_handler._widget_to_graph_point(widget_point)

    # Verify the conversion
    assert graph_point == QPointF(45, 45)  # (100-10)/2, (100-10)/2
