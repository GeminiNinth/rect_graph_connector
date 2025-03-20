"""
Tests for the geometry utility functions.
"""

import pytest
from PyQt5.QtCore import QPointF, QRectF

from rect_graph_connector.utils.geometry import GeometryCalculator, Point


def test_calculate_distance():
    """Test calculating distance between two points."""
    # Convert QPointF to Point for GeometryCalculator
    point1 = Point(x=0, y=0)
    point2 = Point(x=3, y=4)

    # Distance should be 5 (Pythagorean theorem: sqrt(3^2 + 4^2) = 5)
    assert GeometryCalculator.calculate_distance(point1, point2) == 5.0

    # Distance should be commutative
    assert GeometryCalculator.calculate_distance(point2, point1) == 5.0

    # Distance to self should be 0
    assert GeometryCalculator.calculate_distance(point1, point1) == 0.0
