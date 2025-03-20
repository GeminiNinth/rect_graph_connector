"""
Tests for the FileHandler utility class.
"""

import os
import tempfile

import pytest
import yaml

from rect_graph_connector.models.graph import Graph
from rect_graph_connector.models.rect_node import RectNode
from rect_graph_connector.utils.file_handler import FileHandler


@pytest.fixture
def temp_yaml_file():
    """
    Fixture that creates a temporary YAML file for testing.

    Returns:
        str: Path to the temporary file
    """
    # Create a temporary file path
    temp_fd, temp_path = tempfile.mkstemp(suffix=".yaml")
    os.close(temp_fd)

    # Create a simple graph structure
    data = {
        "nodes": [
            {"id": "node1", "x": 100, "y": 100, "size": 40},
            {"id": "node2", "x": 200, "y": 100, "size": 40},
        ],
        "edges": [["node1", "node2"]],
        "groups": [
            {"id": "group1", "node_ids": ["node1", "node2"], "name": "Test Group"}
        ],
    }

    # Write to the file
    with open(temp_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

    yield temp_path

    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_csv_file():
    """
    Fixture that creates a temporary CSV file for testing.

    Returns:
        str: Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp:
        # Create a simple CSV structure
        temp.write(b"source,target\n")
        temp.write(b"node1,node2\n")
        temp.write(b"node2,node3\n")
        temp_path = temp.name

    yield temp_path

    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_import_graph_from_yaml(temp_yaml_file):
    """Test importing a graph from a YAML file."""
    # Import the graph
    imported_data = FileHandler.import_graph_from_yaml(temp_yaml_file)

    # Check that the data was imported correctly
    assert "nodes" in imported_data
    assert "edges" in imported_data
    assert "groups" in imported_data

    assert len(imported_data["nodes"]) == 2
    assert len(imported_data["edges"]) == 1
    assert len(imported_data["groups"]) == 1

    # Check node data
    node1 = next(n for n in imported_data["nodes"] if n["id"] == "node1")
    assert node1["x"] == 100
    assert node1["y"] == 100
    assert node1["size"] == 40

    # Check edge data
    assert imported_data["edges"][0] == ["node1", "node2"]

    # Check group data
    group1 = imported_data["groups"][0]
    assert group1["id"] == "group1"
    assert group1["node_ids"] == ["node1", "node2"]
    assert group1["name"] == "Test Group"


def test_export_graph_to_yaml(populated_graph):
    """Test exporting a graph to a YAML file."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp:
        temp_path = temp.name

    try:
        # Export the graph
        FileHandler.export_graph_to_yaml(populated_graph, temp_path)

        # Check that the file was created
        assert os.path.exists(temp_path)

        # Import the graph back to verify the data
        imported_data = FileHandler.import_graph_from_yaml(temp_path)

        # Check that the data was exported correctly
        assert "nodes" in imported_data
        assert "edges" in imported_data
        assert "groups" in imported_data

        assert len(imported_data["nodes"]) == len(populated_graph.nodes)
        assert len(imported_data["edges"]) == len(populated_graph.edges)
        assert len(imported_data["groups"]) == len(populated_graph.node_groups)

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_import_graph_from_csv(temp_csv_file):
    """Test importing a graph from a CSV file."""
    # Import the graph
    imported_data = FileHandler.import_graph_from_csv(temp_csv_file)

    # Check that the data was imported correctly
    assert "nodes" in imported_data
    assert "edges" in imported_data

    # CSV import should create nodes for each unique ID in the edges
    assert len(imported_data["nodes"]) == 3  # node1, node2, node3

    # Check edge data
    assert len(imported_data["edges"]) == 2
    assert ["node1", "node2"] in imported_data["edges"]
    assert ["node2", "node3"] in imported_data["edges"]


def test_export_graph_to_csv(populated_graph):
    """Test exporting a graph to a CSV file."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp:
        temp_path = temp.name

    try:
        # Export the graph
        FileHandler.export_graph_to_csv(populated_graph, temp_path)

        # Check that the file was created
        assert os.path.exists(temp_path)

        # Read the CSV file to verify the data
        with open(temp_path, "r") as f:
            lines = f.readlines()

        # Check header
        assert lines[0].strip() == "source,target"

        # Check that all edges are included
        for edge in populated_graph.edges:
            source_id, target_id = edge
            edge_line = f"{source_id},{target_id}\n"
            assert edge_line in lines or edge_line.strip() in [
                line.strip() for line in lines
            ]

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
