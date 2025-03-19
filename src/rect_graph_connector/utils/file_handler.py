"""
This module provides utilities for file operations, particularly CSV handling.
"""

import csv
from typing import List, Tuple, Dict
import os
from datetime import datetime
import yaml
from yaml import Loader

from .logging_utils import get_logger
from ..config import config

logger = get_logger(__name__)


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
            # 設定ファイルから日付フォーマットとディレクトリを取得
            date_format = config.get_constant(
                "file_output.patterns.date_format", "%Y%m%d_%H%M%S"
            )
            date_str = datetime.now().strftime(date_format)

            # 出力ディレクトリを設定から取得
            output_dir = config.get_constant("file_output.directory", "./output")
            os.makedirs(output_dir, exist_ok=True)

            # ファイル名パターンを設定から取得
            filename_pattern = config.get_constant(
                "file_output.patterns.yaml_export", "graph_output_{date_str}.yaml"
            )
            filename = filename_pattern.format(date_str=date_str)
            filepath = os.path.join(output_dir, filename)

        # Combine all graph data
        graph_data = {"nodes": nodes, "edges": edges, "groups": groups}

        # Write to YAML
        try:
            with open(filepath, "w") as file:
                yaml.dump(graph_data, file)
            logger.info(f"Graph data exported to: {filepath}")
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
