"""
Base renderer class for all rendering components.
"""

from abc import ABC, abstractmethod
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QPointF

from ...models.view_state_model import ViewStateModel
from .styles.base_style import BaseStyle


class BaseRenderer(ABC):
    """
    Abstract base class for all renderers.

    This class provides common functionality and interface for rendering operations.
    It uses the ViewStateModel for view state information and a style object for
    appearance settings.

    Attributes:
        view_state (ViewStateModel): The view state model
        style (BaseStyle): The style object for this renderer
    """

    def __init__(self, view_state: ViewStateModel, style: BaseStyle):
        """
        Initialize the renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (BaseStyle): The style object for this renderer
        """
        self.view_state = view_state
        self.style = style

    @abstractmethod
    def draw(self, painter: QPainter, **kwargs):
        """
        Draw the component on the canvas.
        Must be implemented by concrete renderer classes.

        Args:
            painter (QPainter): The painter to use for drawing
            **kwargs: Additional drawing parameters
        """
        pass

    def apply_transform(self, painter: QPainter):
        """
        Apply pan and zoom transformations to the painter.

        Args:
            painter (QPainter): The painter to transform
        """
        painter.translate(self.view_state.pan_offset)
        painter.scale(self.view_state.zoom, self.view_state.zoom)

    def calculate_edge_endpoints(self, source_node, target_node):
        """
        Calculate the actual visual endpoints of an edge considering node sizes.

        Args:
            source_node: The source node
            target_node: The target node

        Returns:
            tuple: (start_point, end_point) as QPointF objects
        """
        # Get node centers
        start_center = QPointF(source_node.x, source_node.y)
        end_center = QPointF(target_node.x, target_node.y)

        # Calculate direction vector
        direction = end_center - start_center
        if direction.manhattanLength() == 0:
            return start_center, end_center

        # Normalize direction vector
        length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
        normalized_dir = QPointF(direction.x() / length, direction.y() / length)

        # Calculate actual endpoints considering node sizes
        start_point = QPointF(
            start_center.x() + normalized_dir.x() * source_node.size / 2,
            start_center.y() + normalized_dir.y() * source_node.size / 2,
        )
        end_point = QPointF(
            end_center.x() - normalized_dir.x() * target_node.size / 2,
            end_center.y() - normalized_dir.y() * target_node.size / 2,
        )

        return start_point, end_point
