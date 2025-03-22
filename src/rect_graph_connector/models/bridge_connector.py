"""
This module contains the logic for creating bridge connections between node groups.

A bridge connection is a bipartite graph connection between two node groups, where
edge nodes from each group are connected according to specified parameters.
"""

from typing import Dict, List, Optional, Tuple, Set

from PyQt5.QtCore import QPointF

from ..config import config
from .graph import Graph, NodeGroup
from .node import BaseNode
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


class BridgeConnectionParams:
    """
    Class to store parameters for bridge connections between two node groups.

    Attributes:
        source_to_target_count (int): Number of connections from source to target group
        target_to_source_count (int): Number of connections from target to source group
        source_highlight_pos (str): Position of highlighted nodes in source group
        target_highlight_pos (str): Position of highlighted nodes in target group
    """

    def __init__(
        self,
        source_to_target_count: int = 1,
        target_to_source_count: int = 1,
        source_highlight_pos: str = None,
        target_highlight_pos: str = None,
    ):
        """
        Initialize bridge connection parameters.

        Args:
            source_to_target_count: Number of connections from source to target (default: 1)
            target_to_source_count: Number of connections from target to source (default: 1)
            source_highlight_pos: Position of highlighted nodes in source group
            target_highlight_pos: Position of highlighted nodes in target group
        """
        # Get the default position from config if not specified
        default_pos = config.get_constant(
            "bridge_connection.highlight_positions.default", "row_first"
        )

        self.source_to_target_count = max(1, source_to_target_count)
        self.target_to_source_count = max(1, target_to_source_count)
        self.source_highlight_pos = source_highlight_pos or default_pos
        self.target_highlight_pos = target_highlight_pos or default_pos

        # Validate counts
        min_conn = config.get_constant("bridge_connection.min_connections", 1)
        max_conn = config.get_constant("bridge_connection.max_connections", 10)
        self.source_to_target_count = max(
            min_conn, min(max_conn, self.source_to_target_count)
        )
        self.target_to_source_count = max(
            min_conn, min(max_conn, self.target_to_source_count)
        )


class BridgeConnector:
    """
    A class for creating and managing bridge connections between two node groups.

    Bridge connections are bipartite graph connections between edge nodes of two groups.
    The number of connections and which nodes are used can be configured.
    """

    # Constants for highlight positions
    POS_ROW_FIRST = config.get_constant(
        "bridge_connection.highlight_positions.row_first", "row_first"
    )
    POS_ROW_LAST = config.get_constant(
        "bridge_connection.highlight_positions.row_last", "row_last"
    )
    POS_COL_FIRST = config.get_constant(
        "bridge_connection.highlight_positions.col_first", "col_first"
    )
    POS_COL_LAST = config.get_constant(
        "bridge_connection.highlight_positions.col_last", "col_last"
    )

    def __init__(self, graph: Graph):
        """
        Initialize bridge connector with graph reference.

        Args:
            graph: The graph to operate on
        """
        self.graph = graph

    def create_bridge_connection(
        self,
        source_group: NodeGroup,
        target_group: NodeGroup,
        params: BridgeConnectionParams,
    ) -> bool:
        """
        Create bridge connections between two node groups.

        Args:
            source_group: The source node group
            target_group: The target node group
            params: Bridge connection parameters

        Returns:
            bool: True if connections were created successfully, False otherwise
        """
        if not source_group or not target_group or source_group == target_group:
            logger.warning("Invalid groups for bridge connection")
            return False

        # Get edge nodes for each group
        source_nodes = self._get_edge_nodes(source_group, params.source_highlight_pos)
        target_nodes = self._get_edge_nodes(target_group, params.target_highlight_pos)

        if not source_nodes or not target_nodes:
            logger.warning(
                f"No valid edge nodes found in groups: {source_group.name}, {target_group.name}"
            )
            return False

        # Create source to target connections
        if params.source_to_target_count > 0:
            self._generate_bipartite_connections(
                source_nodes, target_nodes, params.source_to_target_count
            )

        # Create target to source connections
        if params.target_to_source_count > 0:
            self._generate_bipartite_connections(
                target_nodes, source_nodes, params.target_to_source_count
            )

        logger.info(
            f"Created bridge connection between {source_group.name} and {target_group.name}"
        )
        return True

    def get_connection_preview(
        self,
        source_group: NodeGroup,
        target_group: NodeGroup,
        params: BridgeConnectionParams,
    ) -> List[Tuple[QPointF, QPointF]]:
        """
        Get preview lines for bridge connections without actually creating them.

        Args:
            source_group: The source node group
            target_group: The target node group
            params: Bridge connection parameters

        Returns:
            List of tuples of (start_point, end_point) for preview lines
        """
        preview_lines = []

        if not source_group or not target_group or source_group == target_group:
            return preview_lines

        # Get edge nodes for each group
        source_nodes = self._get_edge_nodes(source_group, params.source_highlight_pos)
        target_nodes = self._get_edge_nodes(target_group, params.target_highlight_pos)

        if not source_nodes or not target_nodes:
            return preview_lines

        # Add source to target preview lines
        if params.source_to_target_count > 0:
            connections = self._generate_bipartite_mapping(
                source_nodes, target_nodes, params.source_to_target_count
            )
            for source_idx, target_indices in connections.items():
                source_node = source_nodes[source_idx]
                for target_idx in target_indices:
                    target_node = target_nodes[target_idx]
                    preview_lines.append(
                        (
                            QPointF(source_node.x, source_node.y),
                            QPointF(target_node.x, target_node.y),
                        )
                    )

        # Add target to source preview lines
        if params.target_to_source_count > 0:
            connections = self._generate_bipartite_mapping(
                target_nodes, source_nodes, params.target_to_source_count
            )
            for target_idx, source_indices in connections.items():
                target_node = target_nodes[target_idx]
                for source_idx in source_indices:
                    source_node = source_nodes[source_idx]
                    preview_lines.append(
                        (
                            QPointF(target_node.x, target_node.y),
                            QPointF(source_node.x, source_node.y),
                        )
                    )

        return preview_lines

    def _get_edge_nodes(self, group: NodeGroup, highlight_pos: str) -> List[BaseNode]:
        """
        Get the edge nodes from a group based on highlight position.

        Args:
            group: The node group
            highlight_pos: Position specification (row_first, row_last, col_first, col_last)

        Returns:
            List of edge nodes based on the specified position
        """
        nodes = group.get_nodes(self.graph.nodes)
        if not nodes:
            return []

        # Group nodes by row and column
        rows = {}
        cols = {}

        for node in nodes:
            if node.row not in rows:
                rows[node.row] = []
            if node.col not in cols:
                cols[node.col] = []

            rows[node.row].append(node)
            cols[node.col].append(node)

        # Sort nodes by their position
        for r in rows:
            rows[r].sort(key=lambda n: n.col)

        for c in cols:
            cols[c].sort(key=lambda n: n.row)

        # Get the edge nodes based on highlight position
        edge_nodes = []

        if highlight_pos == self.POS_ROW_FIRST:
            # Get first node from each row
            sorted_rows = sorted(rows.keys())
            for r in sorted_rows:
                if rows[r]:
                    edge_nodes.append(rows[r][0])  # First node in row

        elif highlight_pos == self.POS_ROW_LAST:
            # Get last node from each row
            sorted_rows = sorted(rows.keys())
            for r in sorted_rows:
                if rows[r]:
                    edge_nodes.append(rows[r][-1])  # Last node in row

        elif highlight_pos == self.POS_COL_FIRST:
            # Get first node from each column
            sorted_cols = sorted(cols.keys())
            for c in sorted_cols:
                if cols[c]:
                    edge_nodes.append(cols[c][0])  # First node in column

        elif highlight_pos == self.POS_COL_LAST:
            # Get last node from each column
            sorted_cols = sorted(cols.keys())
            for c in sorted_cols:
                if cols[c]:
                    edge_nodes.append(cols[c][-1])  # Last node in column

        else:
            # Default: get all nodes
            edge_nodes = nodes

        return edge_nodes

    def _generate_bipartite_mapping(
        self,
        source_nodes: List[BaseNode],
        target_nodes: List[BaseNode],
        connection_count: int,
    ) -> Dict[int, Set[int]]:
        """
        Generate a mapping of source to target node indices for bipartite connections.

        Args:
            source_nodes: List of source nodes
            target_nodes: List of target nodes
            connection_count: Number of connections per source node

        Returns:
            Dict mapping source node index to set of target node indices
        """
        if not source_nodes or not target_nodes or connection_count <= 0:
            return {}

        connections = {}
        source_count = len(source_nodes)
        target_count = len(target_nodes)

        # Calculate max possible connections per source node
        max_connections = min(connection_count, target_count)

        # Create connections for each source node
        for source_idx in range(source_count):
            connections[source_idx] = set()

            # For evenly distributed connections
            if max_connections >= target_count:
                # Connect to all targets (full bipartite connectivity)
                for target_idx in range(target_count):
                    connections[source_idx].add(target_idx)
            else:
                # Connect to a subset of targets
                # Uses a distribution pattern based on source index to evenly spread connections
                for c in range(max_connections):
                    # Calculate target index with even distribution
                    target_idx = (
                        source_idx + c * (target_count // max_connections)
                    ) % target_count
                    connections[source_idx].add(target_idx)

        return connections

    def _generate_bipartite_connections(
        self,
        source_nodes: List[BaseNode],
        target_nodes: List[BaseNode],
        connection_count: int,
    ) -> None:
        """
        Generate bipartite connections between source and target nodes.

        Args:
            source_nodes: List of source nodes
            target_nodes: List of target nodes
            connection_count: Number of connections per source node
        """
        connections = self._generate_bipartite_mapping(
            source_nodes, target_nodes, connection_count
        )

        # Create actual edges in the graph
        for source_idx, target_indices in connections.items():
            source_node = source_nodes[source_idx]
            for target_idx in target_indices:
                target_node = target_nodes[target_idx]
                self.graph.add_edge(source_node, target_node)
