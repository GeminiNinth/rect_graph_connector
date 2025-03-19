"""
This module contains the RectNode class which represents a rectangular node in the graph.
"""

from dataclasses import dataclass
from PyQt5.QtCore import QPointF
from ..config import config


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

    id: int
    x: float
    y: float
    row: int
    col: int
    size: float = None

    def __post_init__(self):
        """Initialize default values from configuration if not provided."""
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
