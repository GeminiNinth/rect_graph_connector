"""
This module contains the Graph class which manages the graph structure and node groups.
"""

from typing import List, Tuple, Optional, Set, Dict
from PyQt5.QtCore import QPointF
from .rect_node import RectNode


class NodeGroup:
    """
    A class representing a group of nodes.

    Attributes:
        name (str): Name of the node group
        nodes (List[RectNode]): List of nodes in the group
        label_position (str): Position of the group name label ('top-left', 'top-center', etc.)
    """

    # Label position constants
    POSITION_TOP_LEFT = "top-left"
    POSITION_TOP_CENTER = "top-center"
    POSITION_TOP_RIGHT = "top-right"
    POSITION_BOTTOM_LEFT = "bottom-left"
    POSITION_BOTTOM_CENTER = "bottom-center"
    POSITION_BOTTOM_RIGHT = "bottom-right"

    def __init__(
        self, name: str, nodes: List[RectNode], label_position: str = POSITION_TOP_LEFT
    ):
        """
        Initialize a node group.

        Args:
            name (str): Name of the node group
            nodes (List[RectNode]): List of nodes in the group
            label_position (str): Position of the group name label
        """
        self.name = name
        self.nodes = nodes
        self.label_position = label_position


class Graph:
    """
    A class managing the graph structure and node groups.

    This class handles the graph's nodes, edges, and node groups, providing methods
    for manipulating the graph structure and managing node selections.

    Attributes:
        nodes (List[RectNode]): List of all nodes in the graph
        edges (List[Tuple[int, int]]): List of edges represented as (source_id, target_id)
        node_groups (List[NodeGroup]): List of node groups
        selected_nodes (List[RectNode]): Currently selected nodes
        selected_group (Optional[NodeGroup]): Currently selected group
    """

    def __init__(self):
        """Initialize an empty graph structure."""
        self.nodes: List[RectNode] = []
        self.edges: List[Tuple[int, int]] = []
        self.node_groups: List[NodeGroup] = []
        self.selected_nodes: List[RectNode] = []
        self.selected_group: Optional[NodeGroup] = None
        self.next_group_number: int = 1

    def add_node_group(
        self,
        rows: int,
        cols: int,
        base_x: float = 100.0,
        base_y: float = 100.0,
        spacing: float = 40.0,
        name: Optional[str] = None,
    ) -> NodeGroup:
        """
        Add a new group of nodes arranged in a grid pattern.

        Args:
            rows (int): Number of rows in the grid
            cols (int): Number of columns in the grid
            base_x (float): Starting x-coordinate for the grid
            base_y (float): Starting y-coordinate for the grid
            spacing (float): Space between nodes
            name (Optional[str]): Name of the node group, defaults to "Node {n}"

        Returns:
            NodeGroup: The newly created group of nodes
        """
        new_nodes = []
        for i in range(rows):
            for j in range(cols):
                x = base_x + j * spacing
                y = base_y + i * spacing
                node = RectNode(id=len(self.nodes), x=x, y=y, row=i, col=j)
                self.nodes.append(node)
                new_nodes.append(node)

        # Create a default name if none provided
        if name is None:
            name = f"Node {self.next_group_number}"
            self.next_group_number += 1

        new_group = NodeGroup(name, new_nodes)
        self.node_groups.append(new_group)
        return new_group

    def add_edge(self, source_node: RectNode, target_node: RectNode) -> None:
        """
        Add an edge between two nodes.

        Args:
            source_node (RectNode): Source node of the edge
            target_node (RectNode): Target node of the edge
        """
        if source_node != target_node:
            self.edges.append((source_node.id, target_node.id))

    def delete_group(self, group: NodeGroup) -> None:
        """
        Delete a group of nodes and their associated edges.

        Args:
            group (NodeGroup): The group of nodes to delete
        """
        # Remove edges connected to any node in the group
        node_ids = {node.id for node in group.nodes}
        self.edges = [
            edge
            for edge in self.edges
            if edge[0] not in node_ids and edge[1] not in node_ids
        ]

        # Remove nodes
        self.nodes = [node for node in self.nodes if node not in group.nodes]

        # Remove group
        if group in self.node_groups:
            self.node_groups.remove(group)

        # Clear selection if it was part of the deleted group
        if any(node in group.nodes for node in self.selected_nodes):
            self.selected_nodes.clear()

        # Clear selected group if it was the deleted group
        if self.selected_group == group:
            self.selected_group = None

    def rotate_group(self, nodes: List[RectNode]) -> None:
        """
        Rotate a group of nodes 90 degrees clockwise around their center.

        Args:
            nodes (List[RectNode]): The nodes to rotate
        """
        if not nodes:
            return

        # Calculate group center
        center_x = sum(node.x for node in nodes) / len(nodes)
        center_y = sum(node.y for node in nodes) / len(nodes)

        # Rotate each node
        for node in nodes:
            # Convert to relative coordinates
            rel_x = node.x - center_x
            rel_y = node.y - center_y

            # Apply 90-degree rotation
            node.x = center_x - rel_y
            node.y = center_y + rel_x

    def reset(self) -> None:
        """Reset the graph to its initial empty state."""
        self.nodes.clear()
        self.edges.clear()
        self.node_groups.clear()
        self.selected_nodes.clear()
        self.selected_group = None
        self.next_group_number = 1

    def move_group_up(self, group: NodeGroup) -> bool:
        """
        Move a node group up in the order.

        Args:
            group (NodeGroup): The group to move up

        Returns:
            bool: True if the group was moved, False otherwise
        """
        index = self.node_groups.index(group)
        if index > 0:
            self.node_groups[index], self.node_groups[index - 1] = (
                self.node_groups[index - 1],
                self.node_groups[index],
            )
            self._reassign_node_ids()
            return True
        return False

    def move_group_down(self, group: NodeGroup) -> bool:
        """
        Move a node group down in the order.

        Args:
            group (NodeGroup): The group to move down

        Returns:
            bool: True if the group was moved, False otherwise
        """
        index = self.node_groups.index(group)
        if index < len(self.node_groups) - 1:
            self.node_groups[index], self.node_groups[index + 1] = (
                self.node_groups[index + 1],
                self.node_groups[index],
            )
            self._reassign_node_ids()
            return True
        return False

    def _reassign_node_ids(self) -> None:
        """
        Reassign node IDs based on the current order of node groups.
        This preserves the edge connections by updating the edge references.
        """
        # Create a mapping from old IDs to nodes
        old_id_to_node = {node.id: node for node in self.nodes}

        # Create a mapping from old IDs to new IDs
        old_to_new_id = {}
        new_id = 0

        # Assign new IDs to nodes based on group order
        for group in self.node_groups:
            for node in group.nodes:
                old_to_new_id[node.id] = new_id
                node.id = new_id
                new_id += 1

        # Update edges with new IDs
        new_edges = []
        for source_id, target_id in self.edges:
            new_source_id = old_to_new_id.get(source_id)
            new_target_id = old_to_new_id.get(target_id)
            if new_source_id is not None and new_target_id is not None:
                new_edges.append((new_source_id, new_target_id))

        self.edges = new_edges

    def rename_group(self, group: NodeGroup, new_name: str) -> None:
        """
        Rename a node group.

        Args:
            group (NodeGroup): The group to rename
            new_name (str): The new name for the group
        """
        if group in self.node_groups:
            # Check for existing group names and append incrementing number if necessary
            existing_names = {g.name for g in self.node_groups}
            original_name = new_name
            counter = 1
            while new_name in existing_names:
                new_name = f"{original_name} ({counter})"
                counter += 1
            group.name = new_name

    def find_node_at_position(self, point: QPointF) -> Optional[RectNode]:
        """
        Find a node at the given position.

        Args:
            point (QPointF): The position to check

        Returns:
            Optional[RectNode]: The node at the position, or None if no node is found
        """
        for node in self.nodes:
            if node.contains(point):
                return node
        return None

    def get_group_for_node(self, node: RectNode) -> Optional[NodeGroup]:
        """
        Find the group containing the given node.

        Args:
            node (RectNode): The node to find the group for

        Returns:
            Optional[NodeGroup]: The group containing the node, or None if not found
        """
        for group in self.node_groups:
            if node in group.nodes:
                return group
        return None
