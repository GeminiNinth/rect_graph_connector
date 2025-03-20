"""
Tests for the Graph model class.
"""

import pytest
from PyQt5.QtCore import QPointF

from rect_graph_connector.models.graph import Graph
from rect_graph_connector.models.rect_node import RectNode


def test_graph_initialization():
    """Test that a new Graph initializes with empty collections."""
    graph = Graph()
    assert graph.nodes == []
    assert graph.edges == []
    assert graph.node_groups == []
    assert graph.selected_nodes == []
    assert graph.selected_groups == []


def test_add_node():
    """Test adding a node to the graph."""
    graph = Graph()
    node = RectNode(x=100, y=100, size=40, id="test_node")

    # Add the node
    graph.nodes.append(node)

    # Check that the node was added
    assert len(graph.nodes) == 1
    assert graph.nodes[0] is node


def test_add_edge():
    """Test adding an edge between two nodes."""
    graph = Graph()
    node1 = RectNode(x=100, y=100, size=40, id="node1")
    node2 = RectNode(x=200, y=100, size=40, id="node2")

    # Add the nodes
    graph.nodes.extend([node1, node2])

    # Add an edge
    graph.add_edge(node1, node2)

    # Check that the edge was added
    assert len(graph.edges) == 1
    assert graph.edges[0] == (node1.id, node2.id)

    # Test that duplicate edges are not added
    graph.add_edge(node1, node2)
    assert len(graph.edges) == 1  # Still just one edge


def test_create_node_group():
    """Test creating a node group."""
    graph = Graph()
    node1 = RectNode(x=100, y=100, size=40, id="node1")
    node2 = RectNode(x=200, y=100, size=40, id="node2")

    # Add the nodes
    graph.nodes.extend([node1, node2])

    # Create a group
    group_id = graph.create_node_group([node1, node2])

    # Check that the group was created
    assert len(graph.node_groups) == 1
    group = graph.node_groups[0]
    assert group.id == group_id
    assert set(group.node_ids) == {node1.id, node2.id}


def test_delete_group():
    """Test deleting a node group."""
    graph = Graph()
    node1 = RectNode(x=100, y=100, size=40, id="node1")
    node2 = RectNode(x=200, y=100, size=40, id="node2")

    # Add the nodes
    graph.nodes.extend([node1, node2])

    # Create a group
    group_id = graph.create_node_group([node1, node2])
    group = next(g for g in graph.node_groups if g.id == group_id)

    # Delete the group
    graph.delete_group(group)

    # Check that the group was deleted
    assert len(graph.node_groups) == 0

    # Check that the nodes still exist
    assert len(graph.nodes) == 2


def test_find_node_at_position():
    """Test finding a node at a specific position."""
    graph = Graph()
    node1 = RectNode(x=100, y=100, size=40, id="node1")
    node2 = RectNode(x=200, y=100, size=40, id="node2")

    # Add the nodes
    graph.nodes.extend([node1, node2])

    # Test finding node1
    found_node = graph.find_node_at_position(QPointF(100, 100))
    assert found_node is node1

    # Test finding node2
    found_node = graph.find_node_at_position(QPointF(200, 100))
    assert found_node is node2

    # Test finding a node near its center (within its size)
    found_node = graph.find_node_at_position(QPointF(110, 110))
    assert found_node is node1

    # Test not finding a node at a position far from any node
    found_node = graph.find_node_at_position(QPointF(300, 300))
    assert found_node is None


def test_get_group_for_node():
    """Test getting the group that a node belongs to."""
    graph = Graph()
    node1 = RectNode(x=100, y=100, size=40, id="node1")
    node2 = RectNode(x=200, y=100, size=40, id="node2")
    node3 = RectNode(x=300, y=100, size=40, id="node3")

    # Add the nodes
    graph.nodes.extend([node1, node2, node3])

    # Create a group for node1 and node2
    group_id = graph.create_node_group([node1, node2])
    group = next(g for g in graph.node_groups if g.id == group_id)

    # Test getting the group for node1
    found_group = graph.get_group_for_node(node1)
    assert found_group is group

    # Test getting the group for node2
    found_group = graph.get_group_for_node(node2)
    assert found_group is group

    # Test getting the group for node3 (which doesn't belong to any group)
    found_group = graph.get_group_for_node(node3)
    assert found_group is None


def test_bring_group_to_front():
    """Test bringing a group to the front (updating z-index)."""
    graph = Graph()
    node1 = RectNode(x=100, y=100, size=40, id="node1")
    node2 = RectNode(x=200, y=100, size=40, id="node2")
    node3 = RectNode(x=300, y=100, size=40, id="node3")
    node4 = RectNode(x=400, y=100, size=40, id="node4")

    # Add the nodes
    graph.nodes.extend([node1, node2, node3, node4])

    # Create two groups
    group1_id = graph.create_node_group([node1, node2])
    group1 = next(g for g in graph.node_groups if g.id == group1_id)

    group2_id = graph.create_node_group([node3, node4])
    group2 = next(g for g in graph.node_groups if g.id == group2_id)

    # Initially, group2 should have a higher z-index than group1
    assert group2.z_index > group1.z_index

    # Bring group1 to the front
    graph.bring_group_to_front(group1)

    # Now group1 should have a higher z-index than group2
    assert group1.z_index > group2.z_index


def test_rotate_node_groups():
    """Test rotating node groups."""
    graph = Graph()
    node1 = RectNode(x=100, y=100, size=40, id="node1")
    node2 = RectNode(x=200, y=100, size=40, id="node2")

    # Add the nodes
    graph.nodes.extend([node1, node2])

    # Create a group
    group_id = graph.create_node_group([node1, node2])
    group = next(g for g in graph.node_groups if g.id == group_id)

    # Record original positions
    original_pos1 = (node1.x, node1.y)
    original_pos2 = (node2.x, node2.y)

    # Rotate the group
    graph.rotate_node_groups([group])

    # Check that the positions have changed
    assert (node1.x, node1.y) != original_pos1
    assert (node2.x, node2.y) != original_pos2

    # The center of the group should remain approximately the same
    original_center_x = (original_pos1[0] + original_pos2[0]) / 2
    original_center_y = (original_pos1[1] + original_pos2[1]) / 2

    new_center_x = (node1.x + node2.x) / 2
    new_center_y = (node1.y + node2.y) / 2

    # Allow for small floating-point differences
    assert abs(new_center_x - original_center_x) < 0.001
    assert abs(new_center_y - original_center_y) < 0.001


def test_import_graph():
    """Test importing graph data."""
    graph = Graph()

    # Create import data
    import_data = {
        "nodes": [
            {"id": "node1", "x": 100, "y": 100, "size": 40},
            {"id": "node2", "x": 200, "y": 100, "size": 40},
        ],
        "edges": [("node1", "node2")],
        "groups": [
            {"id": "group1", "node_ids": ["node1", "node2"], "name": "Test Group"}
        ],
    }

    # Import the data in "force" mode (replace existing data)
    graph.import_graph(import_data, "force")

    # Check that the data was imported correctly
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert len(graph.node_groups) == 1

    # Check node data
    node1 = next(n for n in graph.nodes if n.id == "node1")
    assert node1.x == 100
    assert node1.y == 100
    assert node1.size == 40

    # Check edge data
    assert graph.edges[0] == ("node1", "node2")

    # Check group data
    group = graph.node_groups[0]
    assert group.id == "group1"
    assert set(group.node_ids) == {"node1", "node2"}
    assert group.name == "Test Group"
