"""
Base renderer class and common utilities for rendering operations.
"""

from abc import ABC, abstractmethod
import re
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import QPointF

from ...models.graph import Graph
from ...config import config


def parse_rgba(rgba_str):
    """
    Parse rgba string and return QColor object.
    Supports both hex and rgba() format.

    Args:
        rgba_str (str): Color string in format 'rgba(r,g,b,a)' or hex format
        where a can be integer (0-255) or float (0-1)

    Returns:
        QColor: QColor object with the specified color
    """
    if rgba_str.startswith("rgba"):
        # Parse rgba(r,g,b,a) format
        match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+|\d*\.\d+)\)", rgba_str)
        if match:
            r, g, b, a = match.groups()
            r, g, b = map(int, [r, g, b])
            # Convert alpha to 0-255 range if it's a float
            a = int(float(a) * 255) if "." in a else int(a)
            color = QColor()
            color.setRgb(r, g, b, a)
            return color
    # Default to direct QColor creation for hex format
    return QColor(rgba_str)


class BaseRenderer(ABC):
    """
    Abstract base class for all renderers.
    Provides common functionality and interface for rendering operations.
    """

    def __init__(self, canvas: QWidget, graph: Graph):
        """
        Initialize the renderer.

        Args:
            canvas (QWidget): The canvas widget to draw on
            graph (Graph): The graph model to render
        """
        self.canvas = canvas
        self.graph = graph

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

    def apply_transform(self, painter: QPainter):
        """
        Apply pan and zoom transformations to the painter.

        Args:
            painter (QPainter): The painter to transform
        """
        if hasattr(self.canvas, "pan_offset"):
            painter.translate(self.canvas.pan_offset)
        if hasattr(self.canvas, "zoom"):
            painter.scale(self.canvas.zoom, self.canvas.zoom)
