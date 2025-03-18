"""
This module provides utilities for file operations, particularly CSV handling.
"""

import csv
from typing import List, Tuple
import os
from datetime import datetime


class FileHandler:
    """
    A utility class for handling file operations.

    This class provides static methods for various file operations,
    particularly focusing on CSV file handling for graph data.
    """

    @staticmethod
    def export_graph_to_csv(edges: List[Tuple[int, int]], filepath: str = None) -> None:
        """
        Export graph edges to a CSV file.

        Args:
            edges (List[Tuple[int, int]]): List of edges represented as (source_id, target_id)
            filepath (str): Path to the output CSV file
        """
        if not filepath:
            date_str = datetime.now().strftime("%Y%m%d")
            output_dir = "./output"
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f"graph_output_{date_str}.csv")

        try:
            with open(filepath, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["source", "target"])  # Write header
                writer.writerows(edges)  # Write edge data
        except IOError as e:
            raise IOError(f"Failed to write to CSV file: {e}")

    @staticmethod
    def import_graph_from_csv(filepath: str) -> List[Tuple[int, int]]:
        """
        Import graph edges from a CSV file.

        Args:
            filepath (str): Path to the input CSV file

        Returns:
            List[Tuple[int, int]]: List of edges represented as (source_id, target_id)

        Raises:
            IOError: If the file cannot be read or has invalid format
        """
        try:
            edges = []
            with open(filepath, "r", newline="") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                for row in reader:
                    if len(row) != 2:
                        raise ValueError(
                            "Invalid CSV format: each row must have exactly 2 values"
                        )
                    try:
                        source = int(row[0])
                        target = int(row[1])
                        edges.append((source, target))
                    except ValueError:
                        raise ValueError(
                            "Invalid CSV format: edge IDs must be integers"
                        )
            return edges
        except IOError as e:
            raise IOError(f"Failed to read CSV file: {e}")
