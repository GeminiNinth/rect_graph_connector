"""
Tests for the connectivity module.
"""

import pytest
from PyQt5.QtCore import QPointF

from rect_graph_connector.models.connectivity import (
    delete_edge_at_position,
    find_intersecting_edges,
)
from rect_graph_connector.models.graph import Graph
from rect_graph_connector.models.rect_node import SingleNode


@pytest.fixture
def graph_with_edges():
    """
    Fixture that provides a Graph with nodes and edges for testing.

    Returns:
        Graph: A Graph instance with test data
    """
    graph = Graph()

    # Create nodes in a grid pattern
    node1 = SingleNode(x=100, y=100, size=40, id="node1")
    node2 = SingleNode(x=300, y=100, size=40, id="node2")
    node3 = SingleNode(x=100, y=300, size=40, id="node3")
    node4 = SingleNode(x=300, y=300, size=40, id="node4")

    # Add nodes to graph
    graph.nodes.extend([node1, node2, node3, node4])

    # Add edges
    graph.add_edge(node1, node2)  # Horizontal edge at top
    graph.add_edge(node3, node4)  # Horizontal edge at bottom
    graph.add_edge(node1, node3)  # Vertical edge at left
    graph.add_edge(node2, node4)  # Vertical edge at right
    graph.add_edge(node1, node4)  # Diagonal edge from top-left to bottom-right

    return graph


def test_find_intersecting_edges(graph_with_edges):
    """Test finding edges that intersect with a path."""
    # Create a horizontal line that intersects with the vertical edges
    path = [(50, 200), (350, 200)]

    # Find intersecting edges
    intersecting_edges = find_intersecting_edges(graph_with_edges, path)

    # Should find the two vertical edges and the diagonal edge
    assert len(intersecting_edges) == 3

    # Check that the correct edges were found
    edge_pairs = [(edge[0], edge[1]) for edge in intersecting_edges]
    assert ("node1", "node3") in edge_pairs
    assert ("node2", "node4") in edge_pairs

    # Create a vertical line that intersects with the horizontal edges
    path = [(200, 50), (200, 350)]

    # Find intersecting edges
    intersecting_edges = find_intersecting_edges(graph_with_edges, path)

    # Should find the two horizontal edges and the diagonal edge
    assert len(intersecting_edges) == 3

    # Check that the correct edges were found
    edge_pairs = [(edge[0], edge[1]) for edge in intersecting_edges]
    assert ("node1", "node2") in edge_pairs
    assert ("node3", "node4") in edge_pairs

    # Create a diagonal line that intersects with the diagonal edge
    path = [(300, 50), (50, 350)]

    # Find intersecting edges
    intersecting_edges = find_intersecting_edges(graph_with_edges, path)

    # Should find the diagonal edge and one horizontal edge
    assert len(intersecting_edges) == 2

    # Check that the correct edge was found
    edge_pairs = [(edge[0], edge[1]) for edge in intersecting_edges]
    assert ("node1", "node4") in edge_pairs


def test_delete_edge_at_position(graph_with_edges):
    """Test deleting an edge at a specific position."""
    # Get the initial number of edges
    initial_edge_count = len(graph_with_edges.edges)

    # Try to delete an edge at a position where there is no edge
    deleted = delete_edge_at_position(graph_with_edges, QPointF(50, 50))

    # No edge should be deleted
    assert not deleted
    assert len(graph_with_edges.edges) == initial_edge_count

    # Delete the horizontal edge at the top
    deleted = delete_edge_at_position(graph_with_edges, QPointF(200, 100))

    # One edge should be deleted
    assert deleted
    assert len(graph_with_edges.edges) == initial_edge_count - 1

    # Check that the correct edge was deleted
    for edge in graph_with_edges.edges:
        assert not (edge[0] == "node1" and edge[1] == "node2")
        assert not (edge[0] == "node2" and edge[1] == "node1")

    # Delete the vertical edge at the left
    deleted = delete_edge_at_position(graph_with_edges, QPointF(100, 200))

    # One more edge should be deleted
    assert deleted
    assert len(graph_with_edges.edges) == initial_edge_count - 2

    # Check that the correct edge was deleted
    for edge in graph_with_edges.edges:
        assert not (edge[0] == "node1" and edge[1] == "node3")
        assert not (edge[0] == "node3" and edge[1] == "node1")


def test_find_intersecting_edges_with_complex_path(graph_with_edges):
    """Test finding edges that intersect with a complex path with multiple segments."""
    # Create a zigzag path that intersects with multiple edges
    path = [(50, 50), (150, 200), (250, 150), (350, 250)]

    # Find intersecting edges
    intersecting_edges = find_intersecting_edges(graph_with_edges, path)

    # Should find multiple edges
    assert len(intersecting_edges) > 0

    # Create a closed path (polygon) that surrounds node1
    path = [(50, 50), (150, 50), (150, 150), (50, 150), (50, 50)]

    # Find intersecting edges
    intersecting_edges = find_intersecting_edges(graph_with_edges, path)

    # Should find edges connected to node1
    assert len(intersecting_edges) > 0

    # Check that all found edges involve node1
    for edge in intersecting_edges:
        assert edge[0] == "node1" or edge[1] == "node1"


def test_find_intersecting_edges_with_empty_path(graph_with_edges):
    """Test finding edges with an empty path."""
    # Empty path
    path = []

    # Find intersecting edges
    intersecting_edges = find_intersecting_edges(graph_with_edges, path)

    # Should find no edges
    assert len(intersecting_edges) == 0

    # Path with only one point (not a line)
    path = [(100, 100)]

    # Find intersecting edges
    intersecting_edges = find_intersecting_edges(graph_with_edges, path)

    # Should find no edges
    assert len(intersecting_edges) == 0


def test_delete_edge_at_position_with_tolerance(graph_with_edges):
    """Test deleting an edge at a position with different tolerance values."""
    # Get the initial number of edges
    initial_edge_count = len(graph_with_edges.edges)

    # Try to delete an edge at a position near but not exactly on an edge
    # with default tolerance
    deleted = delete_edge_at_position(graph_with_edges, QPointF(205, 100))

    # Edge should be deleted with default tolerance
    assert deleted
    assert len(graph_with_edges.edges) == initial_edge_count - 1

    # Try to delete an edge at a position further from an edge
    # with a smaller tolerance
    deleted = delete_edge_at_position(graph_with_edges, QPointF(110, 200), tolerance=2)

    # Edge should not be deleted with smaller tolerance
    assert not deleted
    assert len(graph_with_edges.edges) == initial_edge_count - 1

    # Try with a larger tolerance
    deleted = delete_edge_at_position(graph_with_edges, QPointF(110, 200), tolerance=15)

    # Edge should be deleted with larger tolerance
    assert deleted
    assert len(graph_with_edges.edges) == initial_edge_count - 2
