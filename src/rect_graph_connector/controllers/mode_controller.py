"""
Base mode controller for handling input in different modes.

This module provides the ModeController abstract base class which defines
the interface for all mode controllers.
"""

from abc import ABC, abstractmethod

from PyQt5.QtCore import QPointF

from ..models.graph import Graph
from ..models.hover_state_model import HoverStateModel
from ..models.selection_model import SelectionModel
from ..models.view_state_model import ViewStateModel


class ModeController(ABC):
    """
    Abstract base class for mode controllers.

    Mode controllers handle input events specific to a particular interaction mode.
    They provide a clean separation between mode-specific logic and the general
    input handling system.

    Attributes:
        view_state (ViewStateModel): The view state model
        selection_model (SelectionModel): The selection model
        hover_state (HoverStateModel): The hover state model
        graph (Graph): The graph model
    """

    def __init__(
        self,
        view_state: ViewStateModel,
        selection_model: SelectionModel,
        hover_state: HoverStateModel,
        graph: Graph,
    ):
        """
        Initialize the mode controller.

        Args:
            view_state (ViewStateModel): The view state model
            selection_model (SelectionModel): The selection model
            hover_state (HoverStateModel): The hover state model
            graph (Graph): The graph model
        """
        self.view_state = view_state
        self.selection_model = selection_model
        self.hover_state = hover_state
        self.graph = graph

        # Interaction state
        self.dragging = False
        self.drag_start = None
        self.drag_start_node = None
        self.pending_deselect = False
        self.press_pos = None

        # Rectangle selection state
        self.is_selecting = False
        self.selection_rect_start = None
        self.selection_rect_end = None

    @abstractmethod
    def handle_mouse_press(self, event, graph_point, widget_point):
        """
        Handle mouse press events.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        pass

    @abstractmethod
    def handle_mouse_move(self, event, graph_point, widget_point):
        """
        Handle mouse move events.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        pass

    @abstractmethod
    def handle_mouse_release(self, event, graph_point, widget_point):
        """
        Handle mouse release events.

        Args:
            event: The mouse event
            graph_point: The point in graph coordinates
            widget_point: The point in widget coordinates

        Returns:
            bool: True if the event was handled, False otherwise
        """
        pass

    @abstractmethod
    def handle_key_press(self, event):
        """
        Handle key press events.

        Args:
            event: The key event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        pass

    @abstractmethod
    def handle_context_menu(self, event, widget_point):
        """
        Handle context menu requests (e.g., right-click).

        Args:
            event: The mouse event that triggered the context menu
            widget_point: The point in widget coordinates where the menu should appear

        Returns:
            bool: True if the event was handled, False otherwise
        """
        pass

    def _complete_rectangle_selection(self):
        """
        Complete the rectangle selection and select nodes/groups/edges.

        Different selection behavior is implemented based on the direction of selection:
        - Left to right (increasing X): Only objects completely inside the rectangle are selected
        - Right to left (decreasing X): Objects that intersect with the rectangle are selected
        """
        if not self.selection_rect_start or not self.selection_rect_end:
            return

        # Calculate the rectangle bounds
        x1, y1 = self.selection_rect_start.x(), self.selection_rect_start.y()
        x2, y2 = self.selection_rect_end.x(), self.selection_rect_end.y()

        # Determine selection direction
        left_to_right = x1 < x2

        # Create normalized rectangle (min_x, min_y, width, height)
        min_x = min(x1, x2)
        min_y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        # Reset selection state
        self.is_selecting = False
        self.selection_rect_start = None
        self.selection_rect_end = None

        # Implement mode-specific selection logic in subclasses
        return left_to_right, min_x, min_y, width, height

    def _snap_to_grid_point(self, x, y):
        """
        Snap a point to the nearest grid point if grid snapping is enabled.

        Args:
            x (float): X coordinate
            y (float): Y coordinate

        Returns:
            tuple: (snapped_x, snapped_y)
        """
        if not self.view_state.grid_visible or not self.view_state.snap_to_grid:
            return x, y

        from ..config import config

        grid_size = config.get_dimension("node.node_to_node_distance", 50)

        snapped_x = round(x / grid_size) * grid_size
        snapped_y = round(y / grid_size) * grid_size

        return snapped_x, snapped_y
