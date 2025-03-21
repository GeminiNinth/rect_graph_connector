"""
This module contains concrete implementations of different node shapes.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Type, Union

from ..config import config
from ..utils.logging_utils import get_logger
from .base_node import BaseNode, NodeShape

logger = get_logger(__name__)


@dataclass
class RectangleNode(BaseNode):
    """
    A class representing a rectangular node in the graph.

    Attributes:
        id (int): Unique identifier for the node
        x (float): X-coordinate of the node's center
        y (float): Y-coordinate of the node's center
        row (int): Row position in the grid
        col (int): Column position in the grid
        size (float): Size of the rectangular node (width = height = size)
        shape (str): Shape of the node (always "rectangle")
    """

    def __post_init__(self):
        """Initialize with rectangle shape."""
        super().__post_init__()
        self.shape = NodeShape.RECTANGLE.value

    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if a point is contained within the rectangular node's boundaries.

        Args:
            x (float): X-coordinate of the point
            y (float): Y-coordinate of the point

        Returns:
            bool: True if the point is within the node's boundaries, False otherwise
        """
        return abs(self.x - x) <= self.size / 2 and abs(self.y - y) <= self.size / 2

    def calculate_edge_connection_point(
        self, target_x: float, target_y: float
    ) -> Tuple[float, float]:
        """
        Calculate the point on the rectangle's edge where a connection to the target point should be drawn.

        Args:
            target_x (float): X-coordinate of the target point
            target_y (float): Y-coordinate of the target point

        Returns:
            Tuple[float, float]: The x, y coordinates of the connection point on the rectangle's edge
        """
        dx = target_x - self.x
        dy = target_y - self.y

        # Handle the case where the target is at the same position as the node
        if dx == 0 and dy == 0:
            return self.x, self.y

        # Calculate the absolute values for comparison
        abs_dx = abs(dx)
        abs_dy = abs(dy)

        half_size = self.size / 2

        # Determine which edge to use based on the slope of the line to the target
        if abs_dx * half_size <= abs_dy * half_size:
            # Intersection with top or bottom edge
            py = self.y + (half_size if dy > 0 else -half_size)
            # Avoid division by zero
            px = self.x + (dx * (py - self.y) / dy if dy != 0 else 0)
        else:
            # Intersection with left or right edge
            px = self.x + (half_size if dx > 0 else -half_size)
            # Avoid division by zero
            py = self.y + (dy * (px - self.x) / dx if dx != 0 else 0)

        return px, py

    def copy(self):
        """
        Create a copy of this node.

        Returns:
            RectangleNode: A new RectangleNode with the same attributes
        """
        return RectangleNode(
            id=self.id,
            x=self.x,
            y=self.y,
            row=self.row,
            col=self.col,
            size=self.size,
            shape=self.shape,
        )


@dataclass
class CircleNode(BaseNode):
    """
    A class representing a circular node in the graph.

    Attributes:
        id (int): Unique identifier for the node
        x (float): X-coordinate of the node's center
        y (float): Y-coordinate of the node's center
        row (int): Row position in the grid
        col (int): Column position in the grid
        size (float): Size of the circular node (diameter)
        shape (str): Shape of the node (always "circle")
    """

    def __post_init__(self):
        """Initialize with circle shape."""
        super().__post_init__()
        self.shape = NodeShape.CIRCLE.value

    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if a point is contained within the circular node's boundaries.

        Args:
            x (float): X-coordinate of the point
            y (float): Y-coordinate of the point

        Returns:
            bool: True if the point is within the node's boundaries, False otherwise
        """
        dx = self.x - x
        dy = self.y - y
        distance_squared = dx * dx + dy * dy
        radius_squared = (self.size / 2) ** 2
        return distance_squared <= radius_squared

    def calculate_edge_connection_point(
        self, target_x: float, target_y: float
    ) -> Tuple[float, float]:
        """
        Calculate the point on the circle's edge where a connection to the target point should be drawn.

        Args:
            target_x (float): X-coordinate of the target point
            target_y (float): Y-coordinate of the target point

        Returns:
            Tuple[float, float]: The x, y coordinates of the connection point on the circle's edge
        """
        dx = target_x - self.x
        dy = target_y - self.y

        # Handle the case where the target is at the same position as the node
        if dx == 0 and dy == 0:
            return self.x, self.y

        # Calculate the distance to the target
        distance = (dx * dx + dy * dy) ** 0.5

        # Normalize the direction vector
        if distance > 0:
            dx /= distance
            dy /= distance

        # Calculate the point on the circle's edge
        radius = self.size / 2
        px = self.x + dx * radius
        py = self.y + dy * radius

        return px, py

    def copy(self):
        """
        Create a copy of this node.

        Returns:
            CircleNode: A new CircleNode with the same attributes
        """
        return CircleNode(
            id=self.id,
            x=self.x,
            y=self.y,
            row=self.row,
            col=self.col,
            size=self.size,
            shape=self.shape,
        )


# Node factory functions


def create_node(x: float, y: float, shape: str = None, **kwargs) -> BaseNode:
    """
    Factory function to create a node of the specified shape.

    Args:
        x (float): X-coordinate of the node's center
        y (float): Y-coordinate of the node's center
        shape (str, optional): Shape of the node. If None, uses the default from config.
        **kwargs: Additional arguments to pass to the node constructor

    Returns:
        BaseNode: A new node of the appropriate subclass
    """
    if shape is None:
        shape = config.get_constant("node_shapes.default", "rectangle")

    shape = shape.lower()
    if shape == "circle":
        return CircleNode(x=x, y=y, **kwargs)
    else:  # Default to rectangle
        return RectangleNode(x=x, y=y, **kwargs)


def node_from_dict(data: Dict) -> BaseNode:
    """
    Create a node from a dictionary.

    Args:
        data (Dict): Dictionary containing node attributes

    Returns:
        BaseNode: A new node of the appropriate subclass
    """
    logger.debug(f"DEBUG: node_from_dict called with data={data}")

    # Handle missing keys with default values
    node_id = data.get("id", str(id(data)))  # Use object id if no id provided
    x = data.get("x", 0)
    y = data.get("y", 0)
    row = data.get("row", 0)
    col = data.get("col", 0)
    size = data.get("size", None)
    shape = data.get("shape", None)

    # Create the appropriate node type based on shape
    return create_node(x=x, y=y, id=node_id, row=row, col=col, size=size, shape=shape)
