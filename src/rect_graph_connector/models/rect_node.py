"""
This module contains the RectNode class which represents a rectangular node in the graph.
"""

from dataclasses import dataclass

from PyQt5.QtCore import QPointF

from ..config import config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class RectNode:
    """
    A class representing a rectangular node in the graph.

    Attributes:
        id (int): Unique identifier for the node
        x (float): X-coordinate of the node's center
        y (float): Y-coordinate of the node's center
        row (int): Row position in the grid
        col (int): Column position in the grid
        size (float): Size of the rectangular node (width = height = size)
    """

    x: float
    y: float
    id: int = None  # Default value for backward compatibility with tests
    row: int = 0  # Default value for backward compatibility
    col: int = 0  # Default value for backward compatibility
    size: float = None

    def __post_init__(self):
        """Initialize default values from configuration if not provided."""
        # Generate a unique ID if none is provided
        if self.id is None:
            import uuid

            self.id = str(uuid.uuid4())

        logger.debug(
            f"DEBUG: RectNode.__post_init__ called with id={self.id}, x={self.x}, y={self.y}, row={self.row}, col={self.col}, size={self.size}"
        )
        if self.size is None:
            self.size = config.get_dimension("node.default_size", 30.0)

    def contains(self, point: QPointF) -> bool:
        """
        Check if a point is contained within the node's boundaries.

        Args:
            point (QPointF): The point to check

        Returns:
            bool: True if the point is within the node's boundaries, False otherwise
        """
        return (
            abs(self.x - point.x()) <= self.size / 2
            and abs(self.y - point.y()) <= self.size / 2
        )

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
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create a RectNode from a dictionary.

        Args:
            data (dict): Dictionary containing node attributes

        Returns:
            RectNode: A new RectNode instance
        """
        logger.debug(f"DEBUG: RectNode.from_dict called with data={data}")

        # Handle missing keys with default values
        node_id = data.get("id", str(id(data)))  # Use object id if no id provided
        x = data.get("x", 0)
        y = data.get("y", 0)
        row = data.get("row", 0)
        col = data.get("col", 0)
        size = data.get("size", None)

        return cls(id=node_id, x=x, y=y, row=row, col=col, size=size)

    def copy(self):
        """
        Create a copy of this node.

        Returns:
            RectNode: A new RectNode with the same attributes
        """
        return RectNode(
            id=self.id, x=self.x, y=self.y, row=self.row, col=self.col, size=self.size
        )

    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if a point is contained within the node's boundaries.

        Args:
            x (float): X-coordinate of the point
            y (float): Y-coordinate of the point

        Returns:
            bool: True if the point is within the node's boundaries, False otherwise
        """
        return abs(self.x - x) <= self.size / 2 and abs(self.y - y) <= self.size / 2

    def __eq__(self, other):
        """
        Check if two nodes are equal based on their ID.

        Args:
            other: The other node to compare with

        Returns:
            bool: True if the nodes have the same ID, False otherwise
        """
        if not isinstance(other, RectNode):
            return False
        return self.id == other.id

    def __hash__(self):
        """
        Hash function for RectNode based on its ID.

        Returns:
            int: Hash value
        """
        return hash(self.id)
