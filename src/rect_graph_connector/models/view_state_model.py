"""
View state model for managing canvas view state.
"""

from PyQt5.QtCore import QPointF

from .event import Event
from ..config import config


class ViewStateModel:
    """
    Model for managing the view state of the canvas.

    This class encapsulates the zoom level, pan offset, and grid visibility/snap settings.
    It provides properties for accessing and modifying these values, and emits events
    when the state changes to notify observers.

    Attributes:
        zoom (float): The current zoom level
        pan_offset (QPointF): The current pan offset
        grid_visible (bool): Whether the grid is visible
        snap_to_grid (bool): Whether snapping to grid is enabled
        state_changed (Event): Event emitted when any state changes
    """

    def __init__(self):
        """Initialize the view state with default values."""
        # Initialize zoom parameters
        self._zoom = config.get_constant("zoom.default", 1.0)
        self._min_zoom = config.get_dimension("canvas.min_zoom", 0.1)
        self._max_zoom = config.get_dimension("canvas.max_zoom", 10.0)

        # Initialize pan parameters
        self._pan_offset = QPointF(0, 0)
        self._panning = False
        self._pan_start = None
        self._pan_offset_start = QPointF(0, 0)

        # Initialize grid parameters
        self._grid_visible = False
        self._snap_to_grid = False

        # Event for notifying observers of state changes
        self.state_changed = Event()

    @property
    def zoom(self):
        """Get the current zoom level."""
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        """
        Set the zoom level, clamped to min/max values.

        Args:
            value (float): The new zoom level
        """
        # Clamp zoom to min/max values
        if value > self._max_zoom:
            value = self._max_zoom
        if value < self._min_zoom:
            value = self._min_zoom

        if self._zoom != value:
            self._zoom = value
            self.state_changed.emit()

    @property
    def min_zoom(self):
        """Get the minimum allowed zoom level."""
        return self._min_zoom

    @property
    def max_zoom(self):
        """Get the maximum allowed zoom level."""
        return self._max_zoom

    @property
    def pan_offset(self):
        """Get the current pan offset."""
        return self._pan_offset

    @pan_offset.setter
    def pan_offset(self, value):
        """
        Set the pan offset.

        Args:
            value (QPointF): The new pan offset
        """
        if self._pan_offset != value:
            self._pan_offset = value
            self.state_changed.emit()

    @property
    def panning(self):
        """Get whether panning is currently active."""
        return self._panning

    @panning.setter
    def panning(self, value):
        """
        Set whether panning is active.

        Args:
            value (bool): True if panning is active, False otherwise
        """
        self._panning = value

    @property
    def pan_start(self):
        """Get the starting point of the current pan operation."""
        return self._pan_start

    @pan_start.setter
    def pan_start(self, value):
        """
        Set the starting point of the current pan operation.

        Args:
            value (QPointF): The starting point
        """
        self._pan_start = value

    @property
    def pan_offset_start(self):
        """Get the pan offset at the start of the current pan operation."""
        return self._pan_offset_start

    @pan_offset_start.setter
    def pan_offset_start(self, value):
        """
        Set the pan offset at the start of the current pan operation.

        Args:
            value (QPointF): The starting pan offset
        """
        self._pan_offset_start = value

    @property
    def grid_visible(self):
        """Get whether the grid is visible."""
        return self._grid_visible

    @grid_visible.setter
    def grid_visible(self, value):
        """
        Set whether the grid is visible.

        Args:
            value (bool): True if the grid should be visible, False otherwise
        """
        if self._grid_visible != value:
            self._grid_visible = value

            # If turning grid off, disable snapping but remember state
            if not value:
                self._snap_to_grid = False

            self.state_changed.emit()

    @property
    def snap_to_grid(self):
        """Get whether snapping to grid is enabled."""
        return self._snap_to_grid

    @snap_to_grid.setter
    def snap_to_grid(self, value):
        """
        Set whether snapping to grid is enabled.

        Args:
            value (bool): True if snapping should be enabled, False otherwise
        """
        if self._snap_to_grid != value:
            self._snap_to_grid = value
            self.state_changed.emit()

    def start_panning(self, start_point):
        """
        Start a panning operation.

        Args:
            start_point (QPointF): The starting point of the pan
        """
        self._panning = True
        self._pan_start = start_point
        self._pan_offset_start = QPointF(self._pan_offset)

    def update_panning(self, current_point):
        """
        Update the pan offset during a panning operation.

        Args:
            current_point (QPointF): The current point of the pan
        """
        if not self._panning or self._pan_start is None:
            return

        dx = current_point.x() - self._pan_start.x()
        dy = current_point.y() - self._pan_start.y()
        self.pan_offset = self._pan_offset_start + QPointF(dx, dy)

    def end_panning(self):
        """End the current panning operation."""
        self._panning = False
        self._pan_start = None
