"""
Unit tests for the node shapes implementation.
"""

import pytest
from rect_graph_connector.models.node import RectangleNode, CircleNode, create_node
from rect_graph_connector.models.base_node import NodeShape


class TestNodeShapes:
    """Test cases for node shapes implementation."""

    def test_rectangle_node_creation(self):
        """Test creating a rectangular node."""
        node = RectangleNode(x=100, y=100)
        assert node.x == 100
        assert node.y == 100
        assert node.shape == NodeShape.RECTANGLE.value

    def test_circle_node_creation(self):
        """Test creating a circular node."""
        node = CircleNode(x=100, y=100)
        assert node.x == 100
        assert node.y == 100
        assert node.shape == NodeShape.CIRCLE.value

    def test_factory_function(self):
        """Test the node factory function."""
        rect_node = create_node(x=100, y=100, shape="rectangle")
        circle_node = create_node(x=200, y=200, shape="circle")
        default_node = create_node(x=300, y=300)  # Should default to rectangle

        assert isinstance(rect_node, RectangleNode)
        assert isinstance(circle_node, CircleNode)
        assert isinstance(default_node, RectangleNode)

    def test_rectangle_contains_point(self):
        """Test point containment for rectangular nodes."""
        node = RectangleNode(x=100, y=100, size=40)

        # Points inside the rectangle
        assert node.contains_point(100, 100)  # Center
        assert node.contains_point(80, 80)  # Top-left corner
        assert node.contains_point(120, 120)  # Bottom-right corner

        # Points outside the rectangle
        assert not node.contains_point(70, 100)  # Left of rectangle
        assert not node.contains_point(130, 100)  # Right of rectangle
        assert not node.contains_point(100, 70)  # Above rectangle
        assert not node.contains_point(100, 130)  # Below rectangle

    def test_circle_contains_point(self):
        """Test point containment for circular nodes."""
        node = CircleNode(x=100, y=100, size=40)

        # Points inside the circle
        assert node.contains_point(100, 100)  # Center
        assert node.contains_point(110, 110)  # Within radius

        # Points outside the circle
        assert not node.contains_point(80, 80)  # Outside radius (corner)
        assert not node.contains_point(120, 100)  # Right edge of circle
        assert not node.contains_point(100, 130)  # Below circle

    def test_rectangle_edge_connection(self):
        """Test edge connection point calculation for rectangular nodes."""
        node = RectangleNode(x=100, y=100, size=40)

        # Test connection points in different directions
        # Right
        x, y = node.calculate_edge_connection_point(200, 100)
        assert x == 120
        assert y == 100

        # Left
        x, y = node.calculate_edge_connection_point(0, 100)
        assert x == 80
        assert y == 100

        # Top
        x, y = node.calculate_edge_connection_point(100, 0)
        assert x == 100
        assert y == 80

        # Bottom
        x, y = node.calculate_edge_connection_point(100, 200)
        assert x == 100
        assert y == 120

    def test_circle_edge_connection(self):
        """Test edge connection point calculation for circular nodes."""
        node = CircleNode(x=100, y=100, size=40)

        # Test connection points in different directions
        # Right
        x, y = node.calculate_edge_connection_point(200, 100)
        assert abs(x - 120) < 0.001
        assert abs(y - 100) < 0.001

        # Left
        x, y = node.calculate_edge_connection_point(0, 100)
        assert abs(x - 80) < 0.001
        assert abs(y - 100) < 0.001

        # Top
        x, y = node.calculate_edge_connection_point(100, 0)
        assert abs(x - 100) < 0.001
        assert abs(y - 80) < 0.001

        # Bottom
        x, y = node.calculate_edge_connection_point(100, 200)
        assert abs(x - 100) < 0.001
        assert abs(y - 120) < 0.001

        # Diagonal
        x, y = node.calculate_edge_connection_point(200, 200)
        # For diagonal, we need to check that the point is on the circle
        # and in the right direction
        distance = ((x - 100) ** 2 + (y - 100) ** 2) ** 0.5
        assert abs(distance - 20) < 0.001  # Should be on the circle (radius = 20)
        assert x > 100 and y > 100  # Should be in the bottom-right direction
