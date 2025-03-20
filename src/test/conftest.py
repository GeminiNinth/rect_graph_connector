"""
This module contains pytest fixtures for testing the rect_graph_connector application.
"""

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from rect_graph_connector.gui.canvas import Canvas
from rect_graph_connector.models.graph import Graph
from rect_graph_connector.models.rect_node import RectNode


@pytest.fixture
def app(qapp):
    """
    Fixture that provides a QApplication instance.
    Uses the built-in qapp fixture from pytest-qt.

    Returns:
        QApplication: The application instance
    """
    return qapp


@pytest.fixture
def graph():
    """
    Fixture that provides a clean Graph instance for testing.

    Returns:
        Graph: A new Graph instance
    """
    return Graph()


@pytest.fixture
def canvas(app):
    """
    Fixture that provides a Canvas widget for testing.

    Args:
        app: The QApplication fixture

    Returns:
        Canvas: A new Canvas instance
    """
    return Canvas()


@pytest.fixture
def rect_node():
    """
    Fixture that provides a RectNode instance for testing.

    Returns:
        RectNode: A new RectNode instance with default values
    """
    return RectNode(x=100, y=100, size=40, id="test_node")


@pytest.fixture
def populated_graph():
    """
    Fixture that provides a Graph instance with some pre-populated nodes and edges.

    Returns:
        Graph: A Graph instance with test data
    """
    graph = Graph()

    # Create nodes
    node1 = RectNode(x=100, y=100, size=40, id="node1")
    node2 = RectNode(x=200, y=100, size=40, id="node2")
    node3 = RectNode(x=100, y=200, size=40, id="node3")
    node4 = RectNode(x=200, y=200, size=40, id="node4")

    # Add nodes to graph
    graph.nodes.extend([node1, node2, node3, node4])

    # Create a node group
    group_id = graph.create_node_group([node1, node2])
    group = next(g for g in graph.node_groups if g.id == group_id)

    # Add some edges
    graph.add_edge(node1, node2)
    graph.add_edge(node3, node4)

    return graph
