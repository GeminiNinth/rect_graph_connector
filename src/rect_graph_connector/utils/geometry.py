"""
This module provides geometric calculation utilities for the graph visualization.
"""

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Point:
    """
    A simple point class representing 2D coordinates.

    Attributes:
        x (float): X-coordinate
        y (float): Y-coordinate
    """

    x: float
    y: float


class GeometryCalculator:
    """
    A utility class for geometric calculations.

    This class provides static methods for various geometric operations
    such as rotation, distance calculation, and coordinate transformations.
    """

    @staticmethod
    def rotate_point(point: Point, center: Point, angle_degrees: float) -> Point:
        """
        Rotate a point around a center point by a specified angle.

        Args:
            point (Point): The point to rotate
            center (Point): The center point of rotation
            angle_degrees (float): The rotation angle in degrees

        Returns:
            Point: The rotated point
        """
        # Convert angle to radians
        angle_rad = math.radians(angle_degrees)

        # Translate point to origin
        translated_x = point.x - center.x
        translated_y = point.y - center.y

        # Rotate
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        rotated_x = translated_x * cos_angle - translated_y * sin_angle
        rotated_y = translated_x * sin_angle + translated_y * cos_angle

        # Translate back
        return Point(x=rotated_x + center.x, y=rotated_y + center.y)

    @staticmethod
    def calculate_distance(point1: Point, point2: Point) -> float:
        """
        Calculate the Euclidean distance between two points.

        Args:
            point1 (Point): First point
            point2 (Point): Second point

        Returns:
            float: The distance between the points
        """
        print(f"Calculating distance between {point1} and {point2}")
        dx = point2.x - point1.x
        dy = point2.y - point1.y
        result = math.sqrt(dx * dx + dy * dy)
        print(f"Distance result: {result}")
        return result

    @staticmethod
    def calculate_center(points: list[Point]) -> Point:
        """
        Calculate the center point (centroid) of a set of points.

        Args:
            points (list[Point]): List of points

        Returns:
            Point: The center point

        Raises:
            ValueError: If the points list is empty
        """
        if not points:
            raise ValueError("Cannot calculate center of empty point set")

        total_x = sum(p.x for p in points)
        total_y = sum(p.y for p in points)
        count = len(points)

        return Point(x=total_x / count, y=total_y / count)

    @staticmethod
    def calculate_bounding_box(points: list[Point]) -> Tuple[Point, Point]:
        """
        Calculate the bounding box of a set of points.

        Args:
            points (list[Point]): List of points

        Returns:
            Tuple[Point, Point]: The top-left and bottom-right points of the bounding box

        Raises:
            ValueError: If the points list is empty
        """
        if not points:
            raise ValueError("Cannot calculate bounding box of empty point set")

        min_x = min(p.x for p in points)
        min_y = min(p.y for p in points)
        max_x = max(p.x for p in points)
        max_y = max(p.y for p in points)

        return Point(x=min_x, y=min_y), Point(x=max_x, y=max_y)
