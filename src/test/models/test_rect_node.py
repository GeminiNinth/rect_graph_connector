"""
Tests for the SingleNode model class.
"""

import uuid

import pytest

from rect_graph_connector.models.rect_node import SingleNode


def test_rect_node_initialization():
    """Test that a SingleNode initializes with the correct values."""
    # Test with explicit ID
    node = SingleNode(x=100, y=200, size=40, id="test_node")
    assert node.x == 100
    assert node.y == 200
    assert node.size == 40
    assert node.id == "test_node"

    # Test with auto-generated ID
    node = SingleNode(x=100, y=200, size=40)
    assert node.x == 100
    assert node.y == 200
    assert node.size == 40
    assert isinstance(node.id, str)
    assert len(node.id) > 0  # ID should not be empty


def test_rect_node_move():
    """Test moving a SingleNode."""
    node = SingleNode(x=100, y=100, size=40, id="test_node")

    # Move the node
    node.move(50, 25)

    # Check that the position was updated
    assert node.x == 150
    assert node.y == 125

    # Move the node with negative values
    node.move(-30, -15)

    # Check that the position was updated
    assert node.x == 120
    assert node.y == 110


def test_rect_node_contains_point():
    """Test checking if a SingleNode contains a point."""
    node = SingleNode(x=100, y=100, size=40, id="test_node")

    # Points inside the node
    assert node.contains_point(100, 100) is True  # Center
    assert node.contains_point(80, 80) is True  # Top-left corner
    assert node.contains_point(120, 120) is True  # Bottom-right corner

    # Points outside the node
    assert node.contains_point(50, 50) is False  # Far from the node
    assert node.contains_point(150, 100) is False  # Just outside the right edge
    assert node.contains_point(100, 150) is False  # Just outside the bottom edge


def test_rect_node_equality():
    """Test SingleNode equality comparison."""
    node1 = SingleNode(x=100, y=100, size=40, id="node1")
    node2 = SingleNode(x=100, y=100, size=40, id="node1")  # Same ID as node1
    node3 = SingleNode(x=100, y=100, size=40, id="node3")  # Different ID

    # Nodes with the same ID should be considered equal
    assert node1 == node2

    # Nodes with different IDs should be considered different
    assert node1 != node3

    # A node should equal itself
    assert node1 == node1


def test_rect_node_hash():
    """Test SingleNode hash function."""
    node1 = SingleNode(x=100, y=100, size=40, id="node1")
    node2 = SingleNode(
        x=200, y=200, size=30, id="node1"
    )  # Same ID, different attributes

    # Nodes with the same ID should have the same hash
    assert hash(node1) == hash(node2)

    # Create a set of nodes to test hash functionality
    node_set = {node1, node2}

    # Since node1 and node2 have the same ID, they should be considered the same in a set
    assert len(node_set) == 1


def test_rect_node_str_representation():
    """Test the string representation of a SingleNode."""
    node = SingleNode(x=100, y=100, size=40, id="test_node")

    # Check that the string representation contains the node's attributes
    str_repr = str(node)
    assert "test_node" in str_repr
    assert "100" in str_repr
    assert "40" in str_repr


def test_rect_node_to_dict():
    """Test converting a SingleNode to a dictionary."""
    node = SingleNode(x=100, y=100, size=40, id="test_node")

    # Convert to dictionary
    node_dict = node.to_dict()

    # Check that the dictionary contains the correct values
    assert node_dict["id"] == "test_node"
    assert node_dict["x"] == 100
    assert node_dict["y"] == 100
    assert node_dict["size"] == 40


def test_rect_node_from_dict():
    """Test creating a SingleNode from a dictionary."""
    # Create a dictionary with node data
    node_dict = {"id": "test_node", "x": 100, "y": 100, "size": 40}

    # Create a node from the dictionary
    node = SingleNode.from_dict(node_dict)

    # Check that the node has the correct values
    assert node.id == "test_node"
    assert node.x == 100
    assert node.y == 100
    assert node.size == 40

    # Test with missing ID (should generate one)
    node_dict = {"x": 100, "y": 100, "size": 40}

    node = SingleNode.from_dict(node_dict)
    assert node.x == 100
    assert node.y == 100
    assert node.size == 40
    assert isinstance(node.id, str)
    assert len(node.id) > 0  # ID should not be empty


def test_rect_node_copy():
    """Test creating a copy of a SingleNode."""
    node = SingleNode(x=100, y=100, size=40, id="test_node")

    # Create a copy
    copy = node.copy()

    # Check that the copy has the same values
    assert copy.id == node.id
    assert copy.x == node.x
    assert copy.y == node.y
    assert copy.size == node.size

    # Check that modifying the copy doesn't affect the original
    copy.x = 200
    assert node.x == 100
    assert copy.x == 200
