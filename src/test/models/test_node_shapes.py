"""
Unit tests for the node shapes implementation.
"""

import pytest
import uuid
from math import isclose
from rect_graph_connector.models.node import (
    RectangleNode,
    CircleNode,
    create_node,
    node_from_dict,
)
from rect_graph_connector.models.base_node import BaseNode, NodeShape
from rect_graph_connector.config import config


class TestNodeShapes:
    """Test cases for node shapes implementation."""

    def test_rectangle_node_creation(self):
        """Test creating a rectangular node with various parameters."""
        # Basic creation with minimum required parameters
        node = RectangleNode(x=100, y=100)
        assert node.x == 100
        assert node.y == 100
        assert node.shape == NodeShape.RECTANGLE.value
        assert node.size == config.get_dimension("node.default_size", 30.0)
        assert isinstance(node.id, str)  # ID should be a string (UUID)

        # Creation with all parameters
        node = RectangleNode(x=100, y=100, id="test-id", row=5, col=10, size=40)
        assert node.x == 100
        assert node.y == 100
        assert node.id == "test-id"
        assert node.row == 5
        assert node.col == 10
        assert node.size == 40
        assert node.shape == NodeShape.RECTANGLE.value

        # Zero and negative position values should be accepted
        node = RectangleNode(x=0, y=-100)
        assert node.x == 0
        assert node.y == -100

    def test_circle_node_creation(self):
        """Test creating a circular node with various parameters."""
        # Basic creation with minimum required parameters
        node = CircleNode(x=100, y=100)
        assert node.x == 100
        assert node.y == 100
        assert node.shape == NodeShape.CIRCLE.value
        assert node.size == config.get_dimension("node.default_size", 30.0)
        assert isinstance(node.id, str)

        # Creation with all parameters
        node = CircleNode(x=100, y=100, id="test-id", row=5, col=10, size=40)
        assert node.x == 100
        assert node.y == 100
        assert node.id == "test-id"
        assert node.row == 5
        assert node.col == 10
        assert node.size == 40
        assert node.shape == NodeShape.CIRCLE.value

        # Zero and negative position values should be accepted
        node = CircleNode(x=0, y=-100)
        assert node.x == 0
        assert node.y == -100

    def test_node_shape_enum(self):
        """Test the NodeShape enum and its methods."""
        # Test enum values
        assert NodeShape.RECTANGLE.value == "rectangle"
        assert NodeShape.CIRCLE.value == "circle"

        # Test from_string method
        assert NodeShape.from_string("rectangle") == NodeShape.RECTANGLE
        assert NodeShape.from_string("RECTANGLE") == NodeShape.RECTANGLE
        assert NodeShape.from_string("circle") == NodeShape.CIRCLE
        assert NodeShape.from_string("CIRCLE") == NodeShape.CIRCLE

        # Test handling of unknown shape strings
        assert NodeShape.from_string("unknown") == NodeShape.RECTANGLE
        assert NodeShape.from_string("") == NodeShape.RECTANGLE

    def test_factory_function_basic(self):
        """Test the basic functionality of node factory function."""
        rect_node = create_node(x=100, y=100, shape="rectangle")
        circle_node = create_node(x=200, y=200, shape="circle")
        default_node = create_node(
            x=300, y=300
        )  # Should default to circle based on constants.yaml

        assert isinstance(rect_node, RectangleNode)
        assert isinstance(circle_node, CircleNode)
        assert isinstance(default_node, CircleNode)  # Default is now circle

        # Test with uppercase shape names
        rect_node = create_node(x=100, y=100, shape="RECTANGLE")
        circle_node = create_node(x=200, y=200, shape="CIRCLE")

        assert isinstance(rect_node, RectangleNode)
        assert isinstance(circle_node, CircleNode)

    def test_factory_function_with_additional_params(self):
        """Test factory function with additional parameters."""
        node = create_node(
            x=100, y=100, shape="rectangle", id="custom-id", row=5, col=10, size=40
        )

        assert isinstance(node, RectangleNode)
        assert node.x == 100
        assert node.y == 100
        assert node.id == "custom-id"
        assert node.row == 5
        assert node.col == 10
        assert node.size == 40

    def test_node_from_dict(self):
        """Test creating nodes from dictionary representations."""
        # Complete dictionary
        node_dict = {
            "id": "test-id",
            "x": 100,
            "y": 200,
            "row": 5,
            "col": 10,
            "size": 40,
            "shape": "circle",
        }

        node = node_from_dict(node_dict)
        assert isinstance(node, CircleNode)
        assert node.id == "test-id"
        assert node.x == 100
        assert node.y == 200
        assert node.row == 5
        assert node.col == 10
        assert node.size == 40
        assert node.shape == "circle"

        # Minimal dictionary with default values
        minimal_dict = {"x": 100, "y": 200}
        node = node_from_dict(minimal_dict)

        assert node.x == 100
        assert node.y == 200
        assert isinstance(node.id, str)  # Should generate a random ID
        assert node.row == 0  # Default value
        assert node.col == 0  # Default value
        assert node.size == config.get_dimension("node.default_size", 30.0)
        assert node.shape == config.get_constant("node_shapes.default", "circle")

        # Dictionary with unknown shape (should default to rectangle)
        unknown_shape_dict = {"x": 100, "y": 200, "shape": "unknown_shape"}

        node = node_from_dict(unknown_shape_dict)
        assert (
            node.shape == NodeShape.RECTANGLE.value
        )  # Defaults to rectangle for unknown shapes

    def test_to_dict_method(self):
        """Test conversion of nodes to dictionary representation."""
        # Rectangle node
        rect_node = RectangleNode(x=100, y=200, id="rect-id", row=5, col=10, size=40)

        rect_dict = rect_node.to_dict()
        assert rect_dict["id"] == "rect-id"
        assert rect_dict["x"] == 100
        assert rect_dict["y"] == 200
        assert rect_dict["row"] == 5
        assert rect_dict["col"] == 10
        assert rect_dict["size"] == 40
        assert rect_dict["shape"] == NodeShape.RECTANGLE.value

        # Circle node
        circle_node = CircleNode(x=300, y=400, id="circle-id", row=15, col=20, size=50)

        circle_dict = circle_node.to_dict()
        assert circle_dict["id"] == "circle-id"
        assert circle_dict["x"] == 300
        assert circle_dict["y"] == 400
        assert circle_dict["row"] == 15
        assert circle_dict["col"] == 20
        assert circle_dict["size"] == 50
        assert circle_dict["shape"] == NodeShape.CIRCLE.value

    def test_node_equality_and_hashing(self):
        """Test node equality comparison and hashing."""
        # Same ID should be equal regardless of other attributes
        node1 = RectangleNode(x=100, y=100, id="same-id")
        node2 = RectangleNode(x=200, y=200, id="same-id")  # Different coordinates
        node3 = CircleNode(x=100, y=100, id="same-id")  # Different class

        assert node1 == node2
        assert node1 == node3
        assert hash(node1) == hash(node2)
        assert hash(node1) == hash(node3)

        # Different IDs should not be equal
        node4 = RectangleNode(x=100, y=100, id="different-id")
        assert node1 != node4
        assert hash(node1) != hash(node4)

        # Non-BaseNode objects should not be equal
        assert node1 != "not a node"
        assert node1 != 123
        assert node1 != {"id": "same-id"}

    def test_node_movement(self):
        """Test the node movement functionality."""
        node = RectangleNode(x=100, y=100)

        # Basic movement
        node.move(10, 20)
        assert node.x == 110
        assert node.y == 120

        # Negative movement
        node.move(-30, -40)
        assert node.x == 80
        assert node.y == 80

        # Zero movement
        node.move(0, 0)
        assert node.x == 80
        assert node.y == 80

        # Decimal movement
        node.move(0.5, 1.5)
        assert node.x == 80.5
        assert node.y == 81.5

    def test_node_copy(self):
        """Test the node copy functionality."""
        # Rectangle node
        original_rect = RectangleNode(
            x=100, y=200, id="original-id", row=5, col=10, size=40
        )

        copied_rect = original_rect.copy()

        assert copied_rect is not original_rect  # Different objects
        assert copied_rect.id == original_rect.id
        assert copied_rect.x == original_rect.x
        assert copied_rect.y == original_rect.y
        assert copied_rect.row == original_rect.row
        assert copied_rect.col == original_rect.col
        assert copied_rect.size == original_rect.size
        assert copied_rect.shape == original_rect.shape

        # Circle node
        original_circle = CircleNode(
            x=300, y=400, id="circle-id", row=15, col=20, size=50
        )

        copied_circle = original_circle.copy()

        assert copied_circle is not original_circle  # Different objects
        assert copied_circle.id == original_circle.id
        assert copied_circle.x == original_circle.x
        assert copied_circle.y == original_circle.y
        assert copied_circle.row == original_circle.row
        assert copied_circle.col == original_circle.col
        assert copied_circle.size == original_circle.size
        assert copied_circle.shape == original_circle.shape

    def test_rectangle_contains_point_basic(self):
        """Test basic point containment for rectangular nodes."""
        node = RectangleNode(x=100, y=100, size=40)

        # Points inside the rectangle
        assert node.contains_point(100, 100)  # Center
        assert node.contains_point(80, 80)  # Top-left corner
        assert node.contains_point(120, 120)  # Bottom-right corner
        assert node.contains_point(80, 120)  # Bottom-left corner
        assert node.contains_point(120, 80)  # Top-right corner

        # Points on the edges
        assert node.contains_point(80, 100)  # Left edge
        assert node.contains_point(120, 100)  # Right edge
        assert node.contains_point(100, 80)  # Top edge
        assert node.contains_point(100, 120)  # Bottom edge

        # Points outside the rectangle
        assert not node.contains_point(79, 100)  # Just left of rectangle
        assert not node.contains_point(121, 100)  # Just right of rectangle
        assert not node.contains_point(100, 79)  # Just above rectangle
        assert not node.contains_point(100, 121)  # Just below rectangle
        assert not node.contains_point(79, 79)  # Outside top-left corner
        assert not node.contains_point(121, 121)  # Outside bottom-right corner

    def test_rectangle_contains_point_edge_cases(self):
        """Test edge cases for rectangle point containment."""
        # Zero-size node (should still contain its center point due to <= comparison)
        zero_node = RectangleNode(x=100, y=100, size=0)
        assert zero_node.contains_point(100, 100)  # Center point
        assert not zero_node.contains_point(101, 100)  # Adjacent point

        # Very large node
        large_node = RectangleNode(x=0, y=0, size=10000)
        assert large_node.contains_point(0, 0)  # Center
        assert large_node.contains_point(4999, 4999)  # Far bottom-right corner within
        assert large_node.contains_point(
            -5000, -5000
        )  # Far top-left corner exactly on edge

    def test_circle_contains_point_basic(self):
        """Test basic point containment for circular nodes."""
        node = CircleNode(x=100, y=100, size=40)
        radius = 20  # size/2

        # Points inside the circle
        assert node.contains_point(100, 100)  # Center
        assert node.contains_point(110, 110)  # Within radius (diagonal)
        assert node.contains_point(120, 100)  # Right edge (exactly on radius)
        assert node.contains_point(100, 120)  # Bottom edge (exactly on radius)
        assert node.contains_point(80, 100)  # Left edge (exactly on radius)
        assert node.contains_point(100, 80)  # Top edge (exactly on radius)

        # Points outside the circle
        assert not node.contains_point(100 + radius + 1, 100)  # Just beyond right edge
        assert not node.contains_point(100, 100 + radius + 1)  # Just beyond bottom edge
        assert not node.contains_point(100 - radius - 1, 100)  # Just beyond left edge
        assert not node.contains_point(100, 100 - radius - 1)  # Just beyond top edge
        assert not node.contains_point(130, 130)  # Far outside (diagonal)

    def test_circle_contains_point_edge_cases(self):
        """Test edge cases for circle point containment."""
        # Zero-size node (should still contain its center point)
        zero_node = CircleNode(x=100, y=100, size=0)
        assert zero_node.contains_point(100, 100)  # Center point
        assert not zero_node.contains_point(101, 100)  # Adjacent point

        # Very large node
        large_node = CircleNode(x=0, y=0, size=10000)
        assert large_node.contains_point(0, 0)  # Center
        assert large_node.contains_point(5000, 0)  # Right edge (exactly on radius)
        assert not large_node.contains_point(5001, 0)  # Just beyond radius

        # Points very close to the edge
        close_node = CircleNode(x=100, y=100, size=40)
        distance = 19.999  # Just inside radius of 20
        # Point just inside circle
        assert close_node.contains_point(100 + distance, 100)

    def test_rectangle_edge_connection_basic(self):
        """Test basic edge connection point calculation for rectangular nodes."""
        node = RectangleNode(x=100, y=100, size=40)

        # Test connection points in cardinal directions
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

    def test_rectangle_edge_connection_advanced(self):
        """Test advanced edge connection point calculations for rectangular nodes."""
        node = RectangleNode(x=100, y=100, size=40)

        # Test diagonal connections
        # Top-right
        x, y = node.calculate_edge_connection_point(200, 50)
        assert abs(x - 120) < 0.001  # Should be on right edge
        assert y > 80 and y < 100  # Should be between top edge and center

        # Bottom-right
        x, y = node.calculate_edge_connection_point(200, 150)
        assert abs(x - 120) < 0.001  # Should be on right edge
        assert y > 100 and y < 120  # Should be between center and bottom edge

        # Bottom-left
        x, y = node.calculate_edge_connection_point(0, 150)
        assert abs(x - 80) < 0.001  # Should be on left edge
        assert y > 100 and y < 120  # Should be between center and bottom edge

        # Top-left
        x, y = node.calculate_edge_connection_point(0, 50)
        assert abs(x - 80) < 0.001  # Should be on left edge
        assert y > 80 and y < 100  # Should be between top edge and center

    def test_rectangle_edge_connection_edge_cases(self):
        """Test edge cases for rectangular edge connection calculation."""
        node = RectangleNode(x=100, y=100, size=40)

        # Target at same position as node
        x, y = node.calculate_edge_connection_point(100, 100)
        assert x == 100
        assert y == 100

        # Target exactly at corner points
        # Top-right corner
        x, y = node.calculate_edge_connection_point(120, 80)
        assert (
            abs(x - 120) < 0.001 or abs(y - 80) < 0.001
        )  # Should be on either right or top edge

        # Zero-size node
        zero_node = RectangleNode(x=100, y=100, size=0)
        x, y = zero_node.calculate_edge_connection_point(200, 100)
        assert x == 100
        assert y == 100  # Should return the node's position

    def test_circle_edge_connection_basic(self):
        """Test basic edge connection point calculation for circular nodes."""
        node = CircleNode(x=100, y=100, size=40)

        # Test connection points in cardinal directions
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

    def test_circle_edge_connection_diagonal(self):
        """Test diagonal edge connection point calculation for circular nodes."""
        node = CircleNode(x=100, y=100, size=40)
        radius = 20  # size/2

        # Diagonal directions
        # Top-right (45 degrees)
        x, y = node.calculate_edge_connection_point(200, 0)
        distance = ((x - 100) ** 2 + (y - 100) ** 2) ** 0.5
        assert abs(distance - radius) < 0.001  # Should be on the circle
        assert x > 100 and y < 100  # Should be in top-right quadrant

        # Bottom-right (135 degrees)
        x, y = node.calculate_edge_connection_point(200, 200)
        distance = ((x - 100) ** 2 + (y - 100) ** 2) ** 0.5
        assert abs(distance - radius) < 0.001
        assert x > 100 and y > 100  # Should be in bottom-right quadrant

        # Bottom-left (225 degrees)
        x, y = node.calculate_edge_connection_point(0, 200)
        distance = ((x - 100) ** 2 + (y - 100) ** 2) ** 0.5
        assert abs(distance - radius) < 0.001
        assert x < 100 and y > 100  # Should be in bottom-left quadrant

        # Top-left (315 degrees)
        x, y = node.calculate_edge_connection_point(0, 0)
        distance = ((x - 100) ** 2 + (y - 100) ** 2) ** 0.5
        assert abs(distance - radius) < 0.001
        assert x < 100 and y < 100  # Should be in top-left quadrant

    def test_circle_edge_connection_edge_cases(self):
        """Test edge cases for circular edge connection calculation."""
        node = CircleNode(x=100, y=100, size=40)

        # Target at same position as node
        x, y = node.calculate_edge_connection_point(100, 100)
        assert x == 100
        assert y == 100

        # Zero-size node
        zero_node = CircleNode(x=100, y=100, size=0)
        x, y = zero_node.calculate_edge_connection_point(200, 100)
        assert x == 100
        assert y == 100  # Should return the node's position

        # Very large distance (should still normalize correctly)
        x, y = node.calculate_edge_connection_point(10000, 10000)
        distance = ((x - 100) ** 2 + (y - 100) ** 2) ** 0.5
        assert abs(distance - 20) < 0.001  # Should still be on circle edge
        assert x > 100 and y > 100  # Should be in bottom-right direction

    def test_contains_qpointf_wrapper(self):
        """Test the contains wrapper method that accepts QPointF."""
        from PyQt5.QtCore import QPointF

        # Rectangle node
        rect_node = RectangleNode(x=100, y=100, size=40)
        assert rect_node.contains(QPointF(100, 100))  # Inside
        assert not rect_node.contains(QPointF(200, 200))  # Outside

        # Circle node
        circle_node = CircleNode(x=100, y=100, size=40)
        assert circle_node.contains(QPointF(100, 100))  # Inside
        assert not circle_node.contains(QPointF(200, 200))  # Outside
