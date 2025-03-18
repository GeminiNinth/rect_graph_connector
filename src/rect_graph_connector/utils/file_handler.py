"""
This module provides utilities for file operations, particularly CSV handling.
"""

import csv
from typing import List, Tuple, Dict
import os
from datetime import datetime
import yaml
from yaml import Loader


class FileHandler:
    """
    A utility class for handling file operations.

    This class provides static methods for various file operations,
    including YAML exports/imports for full graph data (nodes, edges, and groups).
    """

    @staticmethod
    def export_graph_to_yaml(
        nodes: List[Dict],
        edges: List[Tuple[int, int]],
        groups: List[Dict] = None,
        filepath: str = None,
    ) -> None:
        """
        Export graph data to a YAML file in a format compatible with PyTorch Geometric.

        Args:
            nodes (List[Dict]): List of nodes with their attributes
            edges (List[Tuple[int, int]]): List of edges (source_id, target_id)
            groups (List[Dict]): Optional list of group data, each group might have:
                {
                    "id": some_identifier,
                    "name": group_name,
                    "node_ids": [...],
                    "rows": ...,
                    "cols": ...
                }
            filepath (str): Path to the output YAML file
        """

        if groups is None:
            groups = []

        # Prepare the output file path
        if not filepath:
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "./output"
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f"graph_output_{date_str}.yaml")

        # Combine all graph data
        graph_data = {"nodes": nodes, "edges": edges, "groups": groups}

        # Write to YAML
        try:
            with open(filepath, "w") as file:
                yaml.dump(graph_data, file)
            print(f"Graph data exported to: {filepath}")
        except IOError as e:
            raise IOError(f"Failed to write to YAML file: {e}")

    @staticmethod
    def import_graph_from_yaml(filepath: str) -> Dict:
        """
        Import graph data from a YAML file, including nodes, edges, and groups.

        Args:
            filepath (str): Path to the input YAML file

        Returns:
            Dict: Graph data with keys "nodes", "edges", and possibly "groups"

        Raises:
            IOError: If the file cannot be read or has invalid format
        """

        try:
            with open(filepath, "r") as file:
                # Use yaml.load with Loader to handle !!python/tuple tags
                data = yaml.load(file, Loader=Loader)
                if not data:
                    raise IOError("YAML file contains no data.")
                # Optionally validate the data's structure if needed
                if "nodes" not in data or "edges" not in data:
                    raise IOError("YAML file missing required keys (nodes, edges).")

                # Return the entire data, including groups if present
                return data
        except (IOError, yaml.YAMLError) as e:
            raise IOError(f"Failed to read YAML file: {e}")
