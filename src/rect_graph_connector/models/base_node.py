"""
This module contains the BaseNode class which serves as the abstract base class for different node shapes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple

from PyQt5.QtCore import QPointF

from ..config import config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


class NodeShape(Enum):
    """Enumeration of supported node shapes."""

    RECTANGLE = "rectangle"
    CIRCLE = "circle"

    @classmethod
    def from_string(cls, shape_str: str) -> "NodeShape":
        """Convert a string to a NodeShape enum value."""
        shape_str = shape_str.lower()
        if shape_str == "rectangle":
            return cls.RECTANGLE
        elif shape_str == "circle":
            return cls.CIRCLE
        else:
            logger.warning(f"Unknown shape: {shape_str}, defaulting to RECTANGLE")
            return cls.RECTANGLE


@dataclass
class BaseNode(ABC):
    """
    Abstract base class for nodes in the graph.

    Attributes:
        id (int): Unique identifier for the node
        x (float): X-coordinate of the node's center
        y (float): Y-coordinate of the node's center
        row (int): Row position in the grid
        col (int): Column position in the grid
        size (float): Size of the node (width = height = size)
        shape (NodeShape): Shape of the node (rectangle, circle, etc.)
    """

    x: float
    y: float
    id: int = None  # Default value for backward compatibility with tests
    row: int = 0  # Default value for backward compatibility
    col: int = 0  # Default value for backward compatibility
    size: float = None
    shape: str = None

    def __post_init__(self):
        """Initialize default values from configuration if not provided."""
        # Generate a unique ID if none is provided
        if self.id is None:
            import uuid

            self.id = str(uuid.uuid4())

        logger.debug(
            f"DEBUG: BaseNode.__post_init__ called with id={self.id}, x={self.x}, y={self.y}, row={self.row}, col={self.col}, size={self.size}, shape={self.shape}"
        )
        if self.size is None:
            self.size = config.get_dimension("node.default_size", 30.0)

        # Set default shape if not provided
        if self.shape is None:
            self.shape = config.get_constant("node_shapes.default", "rectangle")

    def contains(self, point: QPointF) -> bool:
        """
        Check if a point is contained within the node's boundaries.

        Args:
            point (QPointF): The point to check

        Returns:
            bool: True if the point is within the node's boundaries, False otherwise
        """
        return self.contains_point(point.x(), point.y())

    @abstractmethod
    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if a point is contained within the node's boundaries.

        Args:
            x (float): X-coordinate of the point
            y (float): Y-coordinate of the point

        Returns:
            bool: True if the point is within the node's boundaries, False otherwise
        """
        pass

    @abstractmethod
    def calculate_edge_connection_point(
        self, target_x: float, target_y: float
    ) -> Tuple[float, float]:
        """
        Calculate the point on the node's edge where a connection to the target point should be drawn.

        Args:
            target_x (float): X-coordinate of the target point
            target_y (float): Y-coordinate of the target point

        Returns:
            Tuple[float, float]: The x, y coordinates of the connection point on the node's edge
        """
        pass

    def move(self, dx: float, dy: float) -> None:
        """
        Move the node by the specified delta values.

        Args:
            dx (float): Change in x-coordinate
            dy (float): Change in y-coordinate
        """
        self.x += dx
        self.y += dy

    def to_dict(self) -> dict:
        """
        Convert the node to a dictionary representation.

        Returns:
            dict: Dictionary containing the node's attributes
        """
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "row": self.row,
            "col": self.col,
            "size": self.size,
            "shape": self.shape,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create a node from a dictionary. This method should be implemented by subclasses
        to return the appropriate node type based on the shape in the data.

        Args:
            data (dict): Dictionary containing node attributes

        Returns:
            BaseNode: A new node instance of the appropriate subclass
        """
        # This will be implemented in the factory method in the node module
        pass

    def __eq__(self, other):
        """
        Check if two nodes are equal based on their ID.

        Args:
            other: The other node to compare with

        Returns:
            bool: True if the nodes have the same ID, False otherwise
        """
        if not isinstance(other, BaseNode):
            return False
        return self.id == other.id

    def __hash__(self):
        """
        Hash function for BaseNode based on its ID.

        Returns:
            int: Hash value
        """
        return hash(self.id)
