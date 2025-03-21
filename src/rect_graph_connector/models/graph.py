"""
This module contains the Graph class which manages the graph structure and node groups.
"""

from typing import Dict, List, Optional, Set, Tuple

from PyQt5.QtCore import QPointF

from ..config import config
from ..utils.logging_utils import get_logger
from ..utils.naming_utils import (
    generate_unique_name,
    generate_unique_name_if_needed,
    rename_node,
)
from .node import BaseNode, create_node, node_from_dict

logger = get_logger(__name__)


class NodeGroup:
    """
    A class representing a group of nodes.

    Attributes:
        id (str): Unique identifier for the node group
        name (str): Name of the node group
        node_ids (List[int]): List of node IDs in the group
        nodes (List[BaseNode]): List of nodes in the group (computed property)
        label_position (str): Position of the group name label ('top-left', 'top-center', etc.)
        z_index (int): Z-index for rendering order (higher values are rendered on top)
    """

    # Label position constants
    POSITION_TOP = "top"
    POSITION_RIGHT = "right"
    POSITION_BOTTOM = "bottom"

    def __init__(
        self,
        name: str,
        nodes: Optional[List[BaseNode]] = None,
        node_ids: Optional[List[int]] = None,
        label_position: str = POSITION_TOP,
        group_id: Optional[str] = None,
        z_index: int = 0,
    ):
        """
        Initialize a node group.

        Args:
            name (str): Name of the node group
            nodes (List[SingleNode], optional): List of nodes in the group
            node_ids (List[int], optional): List of node IDs in the group
            label_position (str): Position of the group name label
            group_id (str, optional): Unique identifier for the group
            z_index (int): Z-index for rendering order (higher values are rendered on top)
        """
        import uuid

        self.id = group_id if group_id else str(uuid.uuid4())
        self.name = name
        self.label_position = label_position
        self.z_index = z_index  # For rendering order control

        # Initialize node_ids from either nodes or node_ids
        if nodes:
            self.node_ids = [node.id for node in nodes]
            self._nodes_cache = nodes  # Temporarily cache the nodes for initial setup
        elif node_ids:
            self.node_ids = node_ids
            self._nodes_cache = None
        else:
            self.node_ids = []
            self._nodes_cache = None

    @property
    def nodes(self) -> List[BaseNode]:
        """
        Property maintained for compatibility, but should be used with caution.
        This property returns a cached list, so to get the latest node list,
        you should use get_nodes(graph.nodes).

        Returns:
            List[BaseNode]: Cached node list if it exists, or an empty list
        """
        if hasattr(self, "_nodes_cache") and self._nodes_cache:
            return self._nodes_cache
        return []

    def get_nodes(self, all_nodes: List[BaseNode]) -> List[BaseNode]:
        """
        Get the nodes in this group from the full list of nodes.

        Args:
            all_nodes (List[BaseNode]): All nodes in the graph

        Returns:
            List[BaseNode]: Nodes that belong to this group
        """
        nodes = [node for node in all_nodes if node.id in self.node_ids]
        # Update cache
        self._nodes_cache = nodes
        return nodes


class Graph:
    """
    A class managing the graph structure and node groups.

    This class handles the graph's nodes, edges, and node groups, providing methods
    for manipulating the graph structure and managing node selections.

    Attributes:
        nodes (List[BaseNode]): List of all nodes in the graph
        edges (List[Tuple[int, int]]): List of edges represented as (source_id, target_id)
        node_groups (List[NodeGroup]): List of node groups
        selected_nodes (List[BaseNode]): Currently selected nodes
        selected_groups (List[NodeGroup]): Currently selected groups
        next_z_index (int): Next z-index value to assign for rendering order
    """

    def __init__(self):
        """Initialize an empty graph structure."""
        self.nodes: List[BaseNode] = []
        self.edges: List[Tuple[int, int]] = []
        self.node_groups: List[NodeGroup] = []
        self.group_map: Dict[str, NodeGroup] = {}  # Map with group ID as key
        self.selected_nodes: List[BaseNode] = []
        self.selected_groups: List[NodeGroup] = []
        self.next_group_number: int = 1
        self.next_z_index: int = 0  # Counter for assigning z-index values

    def add_node_group(
        self,
        rows: int,
        cols: int,
        base_x: float = None,
        base_y: float = None,
        spacing: float = None,
        name: Optional[str] = None,
    ) -> NodeGroup:
        """
        Add a new group of nodes arranged in a grid pattern.
        Assigns the highest z-index to the new group so it appears on top.

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
        from ..config import config

        # Get grid settings from configuration file
        if base_x is None:
            base_x = config.get_dimension("grid.base_x", 100.0)
        if base_y is None:
            base_y = config.get_dimension("grid.base_y", 100.0)
        if spacing is None:
            spacing = config.get_dimension("grid.spacing", 40.0)

        # Get starting node ID based on configuration and existing nodes
        next_id = config.node_id_start
        if self.nodes:
            # Find the maximum node ID and ensure new nodes start after it
            max_id = max(node.id for node in self.nodes)
            next_id = max(next_id, max_id + 1)

        new_nodes = []
        for i in range(rows):
            for j in range(cols):
                x = base_x + j * spacing
                y = base_y + i * spacing
                # Get the default shape from configuration
                shape = config.get_constant("node_shapes.default", "rectangle")
                node = create_node(id=next_id, x=x, y=y, row=i, col=j, shape=shape)
                self.nodes.append(node)
                new_nodes.append(node)
                next_id += 1

        # Create a default name if none provided
        if name is None:
            name = f"Node {self.next_group_number}"
            self.next_group_number += 1

        # Use naming utility to generate a unique name if duplicates are not allowed
        existing_names = [g.name for g in self.node_groups]
        name = generate_unique_name_if_needed(
            name, existing_names, allow_duplicates=config.allow_duplicate_names
        )

        # Assign the next z-index value to the new group
        # This ensures new groups are drawn on top
        new_group = NodeGroup(name=name, nodes=new_nodes, z_index=self.next_z_index)
        self.next_z_index += 1

        self.node_groups.append(new_group)
        # Add to group_map
        self.group_map[new_group.id] = new_group
        logger.info(f"Added new group: {new_group.name} (ID: {new_group.id})")
        return new_group

    def has_edge(self, source_node: BaseNode, target_node: BaseNode) -> bool:
        """
        Check if there is an edge between two nodes.

        Args:
            source_node (BaseNode): Source node of the edge
            target_node (BaseNode): Target node of the edge

        Returns:
            bool: True if an edge exists between the nodes, False otherwise
        """
        # Check for exact match
        if (source_node.id, target_node.id) in self.edges:
            return True

        # Check for reverse match
        if (target_node.id, source_node.id) in self.edges:
            return True

        # Check for duplicate edges with the same source and target
        for src, tgt in self.edges:
            if src == source_node.id and tgt == target_node.id:
                return True
            if src == target_node.id and tgt == source_node.id:
                return True

        return False

    def add_edge(self, source_node: BaseNode, target_node: BaseNode) -> None:
        """
        Add an edge between two nodes.

        Args:
            source_node (BaseNode): Source node of the edge
            target_node (BaseNode): Target node of the edge
        """
        if source_node != target_node and not self.has_edge(source_node, target_node):
            self.edges.append((source_node.id, target_node.id))

    def delete_group(self, group: NodeGroup) -> None:
        """
        Delete a group of nodes and their associated edges.
        After deletion, reassigns all node IDs to maintain consistency.

        Args:
            group (NodeGroup): The group of nodes to delete
        """
        if group is None:
            logger.warning("Attempted to delete a None group")
            return

        logger.info(f"Deleting group: {group.name} (ID: {group.id})")

        # Get nodes from the group
        group_nodes = group.get_nodes(self.nodes)
        logger.debug(f"Group contains {len(group_nodes)} nodes")

        # Identify node IDs belonging to other groups
        node_ids_in_other_groups = set()
        # Create a map of future node_ids saved (Group ID -> Node ID List)
        original_group_node_ids = {}

        for other_group in self.node_groups:
            if other_group != group:
                node_ids_in_other_groups.update(other_group.node_ids)
                # Save original node_ids list for future
                original_group_node_ids[other_group.id] = other_group.get_nodes(
                    self.nodes
                )

        # Only nodes belonging to a group that do not belong to another group are deleted.
        nodes_to_delete = [
            node for node in group_nodes if node.id not in node_ids_in_other_groups
        ]
        node_ids_to_delete = {node.id for node in nodes_to_delete}
        logger.debug(
            f"Will delete {len(nodes_to_delete)} nodes that don't belong to other groups"
        )

        # Remove edges connected to nodes that will be deleted
        orig_edge_count = len(self.edges)
        self.edges = [
            edge
            for edge in self.edges
            if edge[0] not in node_ids_to_delete and edge[1] not in node_ids_to_delete
        ]
        logger.debug(
            f"Removed {orig_edge_count - len(self.edges)} edges connected to deleted nodes"
        )

        # Remove only nodes that don't belong to any other group
        orig_node_count = len(self.nodes)
        self.nodes = [node for node in self.nodes if node not in nodes_to_delete]
        logger.debug(f"Removed {orig_node_count - len(self.nodes)} nodes")

        # Delete the group itself
        if group in self.node_groups:
            self.node_groups.remove(group)
            # Also remove from group_map
            if group.id in self.group_map:
                del self.group_map[group.id]
            logger.debug("Removed group from node_groups and group_map")

        # Update selection states - need to handle multiple selections correctly

        # Remove the group from selected_groups if present
        if group in self.selected_groups:
            self.selected_groups.remove(group)
            logger.debug("Removed group from selected_groups list")

        # Clear selection if it was part of the deleted group
        if self.selected_nodes and any(
            node.id in node_ids_to_delete for node in self.selected_nodes
        ):
            # Remove only the nodes that were in the deleted group
            self.selected_nodes = [
                node
                for node in self.selected_nodes
                if node.id not in node_ids_to_delete
            ]
            logger.debug(
                f"Updated selected_nodes list, {len(self.selected_nodes)} nodes remain selected"
            )

        # Reassign node IDs to ensure consistency after deletion
        self._reassign_node_ids(original_group_node_ids)

        # Ensuring continuity of group numbers
        self._recalculate_next_group_number()

        logger.info(f"Group deletion complete. {len(self.node_groups)} groups remain.")

    def rotate_group(self, nodes: List[BaseNode]) -> None:
        """
        Rotate a group of nodes 90 degrees clockwise around their center.

        Args:
            nodes (List[BaseNode]): The nodes to rotate
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

        # Update all affected node groups' node_ids
        # No additional operations needed as they are already properly set

    def rotate_node_groups(self, groups: List[NodeGroup]) -> None:
        """
        Rotate multiple node groups, each around its own center point.

        This method rotates each group independently around its local center,
        rather than rotating all nodes around a global center point.

        Args:
            groups (List[NodeGroup]): The groups to rotate
        """
        if not groups:
            return

        # Process each group independently to ensure local rotation
        for group in groups:
            # Get nodes belonging to this group
            group_nodes = group.get_nodes(self.nodes)
            if not group_nodes:
                continue

            # Calculate this group's center
            group_center_x = sum(node.x for node in group_nodes) / len(group_nodes)
            group_center_y = sum(node.y for node in group_nodes) / len(group_nodes)

            logger.info(
                f"Rotating group {group.name} (ID: {group.id}) around center: ({group_center_x:.2f}, {group_center_y:.2f})"
            )
            logger.debug(f"Group has {len(group_nodes)} nodes")

            # Rotate each node in this group around the group's center
            for node in group_nodes:
                # Save original position for debugging
                orig_x, orig_y = node.x, node.y

                # Convert to relative coordinates
                rel_x = node.x - group_center_x
                rel_y = node.y - group_center_y

                # Apply 90-degree rotation
                node.x = group_center_x - rel_y
                node.y = group_center_y + rel_x

                logger.debug(
                    f"  Node {node.id}: ({orig_x:.2f}, {orig_y:.2f}) -> ({node.x:.2f}, {node.y:.2f})"
                )

    def import_graph(self, data: Dict, mode: str = "force") -> None:
        """
        Import graph data with specified mode (e.g. "force", "overwrite", "insert_before", "insert_after").
        Each mode handles collisions and merges differently when there are existing node groups.

        Args:
            data (Dict): Graph data including "nodes", "edges", and optional "groups"
            mode (str): The import mode to use

        Available modes:
            "force": Completely reset the existing graph, then load the new data.
            "overwrite": Merge new data with existing data, ignoring any collisions (i.e., keep all).
            "insert_before": Insert new groups before existing groups (i.e. prepend them), reassign node IDs.
            "insert_after": Insert new groups after existing groups (i.e. append them), reassign node IDs.
        """
        if mode == "force":
            self.reset()
            self._load_graph_data(data)
        elif mode == "overwrite":
            self._load_graph_data(data, merge=True, overwrite=True)
        elif mode == "insert_before":
            self._insert_new_data(data, prepend=True)
        elif mode == "insert_after":
            self._insert_new_data(data, prepend=False)
        else:
            raise ValueError(f"Unknown import mode: {mode}")

    def _load_graph_data(
        self, data: Dict, merge: bool = False, overwrite: bool = False
    ) -> None:
        """
        Load or merge graph data into the current graph structure.

        Args:
            data (Dict): Graph data including "nodes", "edges", and optional "groups"
            merge (bool): Whether to merge with existing graph instead of resetting it.
            overwrite (bool): If true, overwrite existing nodes/groups on collisions.
        """
        # If not merging, reset everything first
        if not merge:
            self.reset()
            # Just load all data directly
            self.nodes = [node_from_dict(nd) for nd in data.get("nodes", [])]
            self.edges = data.get("edges", [])
            for group_data in data.get("groups", []):
                self._create_group_from_dict(group_data)
            return

        # ===== OVERWRITE IMPLEMENTATION =====

        # 1. Prepare node mappings and data structures
        node_id_map = {}  # Original imported node ID -> New node ID
        existing_node_ids = {node.id for node in self.nodes}
        next_id = max(existing_node_ids) + 1 if existing_node_ids else 0
        existing_groups_by_name = {group.name: group for group in self.node_groups}

        # 2. Check if we're dealing with same-name groups with similar structure
        incoming_groups = data.get("groups", [])
        for group_data in incoming_groups:
            group_name = group_data.get("name", "Unnamed Group")
            if group_name in existing_groups_by_name:
                # Found a group with the same name
                existing_group = existing_groups_by_name[group_name]
                incoming_node_ids = group_data.get("node_ids", [])

                # If the group has the same number of nodes, we'll map nodes directly
                # rather than creating new nodes for better edge combining
                if len(existing_group.node_ids) == len(incoming_node_ids):
                    # Create direct mapping from incoming nodes to existing nodes
                    for i, incoming_id in enumerate(incoming_node_ids):
                        if i < len(existing_group.node_ids):
                            node_id_map[incoming_id] = existing_group.node_ids[i]

        # 3. Process incoming nodes (only those that aren't already mapped)
        new_nodes = []
        for node_data in data.get("nodes", []):
            original_id = node_data["id"]

            # Skip nodes that already have a direct mapping
            if original_id in node_id_map:
                continue

            node_data = node_data.copy()  # Make a copy to avoid modifying original

            # Ensure row/col are present
            if "row" not in node_data:
                node_data["row"] = 0
            if "col" not in node_data:
                node_data["col"] = 0

            # If ID conflicts with existing nodes, assign new ID
            if overwrite and original_id in existing_node_ids:
                node_data["id"] = next_id
                node_id_map[original_id] = next_id
                next_id += 1
            else:
                node_id_map[original_id] = original_id

            # Create and add the node
            new_nodes.append(SingleNode(**node_data))

        # Add new nodes to the graph
        self.nodes.extend(new_nodes)

        # 4. Process incoming edges with proper ID mapping
        for edge in data.get("edges", []):
            src, dst = edge

            # Map to new IDs
            mapped_src = node_id_map.get(src)
            mapped_dst = node_id_map.get(dst)

            # Ensure both source and target nodes exist
            if mapped_src is not None and mapped_dst is not None:
                if (mapped_src, mapped_dst) not in self.edges:
                    self.edges.append((mapped_src, mapped_dst))

        # 5. Process groups that haven't been handled in step 2
        for group_data in data.get("groups", []):
            group_name = group_data.get("name", "Unnamed Group")
            incoming_node_ids = group_data.get("node_ids", [])

            # Skip if this is a directly mapped group (already handled in step 2)
            if group_name in existing_groups_by_name and len(
                existing_groups_by_name[group_name].node_ids
            ) == len(incoming_node_ids):
                continue

            # Map node IDs
            mapped_node_ids = [
                node_id_map.get(nid)
                for nid in incoming_node_ids
                if node_id_map.get(nid) is not None
            ]

            # If group exists and overwrite is enabled
            if group_name in existing_groups_by_name and overwrite:
                existing_group = existing_groups_by_name[group_name]

                # Merge the node IDs - add any that don't already exist
                for node_id in mapped_node_ids:
                    if node_id not in existing_group.node_ids:
                        existing_group.node_ids.append(node_id)
            else:
                # If overwrite mode and group exists, remove the old one
                if not overwrite and group_name in existing_groups_by_name:
                    existing_group = existing_groups_by_name[group_name]
                    self.node_groups.remove(existing_group)
                    del self.group_map[existing_group.id]

                # Create a new group
                new_group_data = {
                    "name": group_name,
                    "node_ids": mapped_node_ids,
                    "label_position": group_data.get(
                        "label_position", NodeGroup.POSITION_TOP
                    ),
                }

                # Create and add the group
                new_group = self._create_group_from_dict(new_group_data)
                existing_groups_by_name[group_name] = new_group

        # 6. Clean up invalid references - ensure nodes referenced by edges and groups exist
        valid_node_ids = {node.id for node in self.nodes}

        # Fix edges
        self.edges = [
            (src, dst)
            for src, dst in self.edges
            if src in valid_node_ids and dst in valid_node_ids
        ]

        # Fix groups
        for group in self.node_groups:
            group.node_ids = [nid for nid in group.node_ids if nid in valid_node_ids]

        # 7. Ensure node IDs are sequential - this fixes any gaps in numbering
        self._reassign_node_ids()

    def _insert_new_data(self, data: Dict, prepend: bool) -> None:
        """
        Insert new groups before or after existing groups, reassigning node IDs so the new
        groups either come first or last in the node ID order.

        Args:
            data (Dict): Graph data including "nodes", "edges", and optional "groups"
            prepend (bool): If True, new groups come before existing ones. If False, they come after.
        """
        # First, organize nodes by their groups to maintain group order
        incoming_groups = data.get("groups", [])
        nodes_by_group = {}
        ungrouped_nodes = []

        # Create a mapping of node IDs to their group
        node_to_group = {}
        for group in incoming_groups:
            for node_id in group.get("node_ids", []):
                node_to_group[node_id] = group.get("name", "")

        # Organize nodes by their groups
        for nd in data.get("nodes", []):
            group_name = node_to_group.get(nd["id"])
            if group_name:
                if group_name not in nodes_by_group:
                    nodes_by_group[group_name] = []
                nodes_by_group[group_name].append(nd)
            else:
                ungrouped_nodes.append(nd)

        # Get existing node IDs and count
        existing_node_ids = {n.id for n in self.nodes}
        incoming_node_count = len(data.get("nodes", []))

        # Create mapping from original IDs to new IDs
        original_to_new_node_id = {}

        if prepend:
            # For insert_before, new nodes get IDs starting from 0
            # and existing nodes are shifted up
            id_shift = incoming_node_count

            # First, shift existing node IDs up
            for node in self.nodes:
                node.id += id_shift

            # Update edges for existing nodes
            self.edges = [(src + id_shift, dst + id_shift) for src, dst in self.edges]

            # Update node_ids in existing groups
            for group in self.node_groups:
                group.node_ids = [nid + id_shift for nid in group.node_ids]

        # Process nodes group by group to maintain order
        incoming_nodes = []
        id_offset = (
            0 if prepend else (max(existing_node_ids) + 1 if existing_node_ids else 0)
        )

        # Process grouped nodes first, maintaining group order
        for group in incoming_groups:
            group_name = group.get("name", "")
            group_nodes = nodes_by_group.get(group_name, [])

            for nd in group_nodes:
                if "row" not in nd:
                    nd["row"] = 0
                if "col" not in nd:
                    nd["col"] = 0

                original_id = nd["id"]
                new_id = id_offset
                nd["id"] = new_id
                original_to_new_node_id[original_id] = new_id
                id_offset += 1

                incoming_nodes.append(node_from_dict(nd))

        # Process ungrouped nodes last
        for nd in ungrouped_nodes:
            if "row" not in nd:
                nd["row"] = 0
            if "col" not in nd:
                nd["col"] = 0

            original_id = nd["id"]
            new_id = id_offset
            nd["id"] = new_id
            original_to_new_node_id[original_id] = new_id
            id_offset += 1

            incoming_nodes.append(node_from_dict(nd))

        # Process edges - update IDs with new mapping
        incoming_edges = []
        for edge in data.get("edges", []):
            src, dst = edge
            # Apply ID mapping
            new_src = original_to_new_node_id.get(src)
            new_dst = original_to_new_node_id.get(dst)
            if new_src is not None and new_dst is not None:
                incoming_edges.append((new_src, new_dst))

        # First pass: Analyze groups and create rename mapping
        incoming_groups = data.get("groups", [])
        existing_group_names = {g.name for g in self.node_groups}
        group_name_mapping = {}  # Original name -> Final name
        group_order = []  # Maintain original order of groups

        # Create a mapping of base names to their groups for proper ordering
        base_name_groups = {}
        for grp in incoming_groups:
            original_name = grp.get("name", "")
            base_name = original_name.split("(")[0]
            if base_name not in base_name_groups:
                base_name_groups[base_name] = []
            base_name_groups[base_name].append(grp)
            group_order.append(original_name)

        # Assign new names while preserving order relationships
        for base_name, groups in base_name_groups.items():
            # Sort groups by their original order in the file
            groups.sort(key=lambda g: group_order.index(g.get("name", "")))

            for grp in groups:
                original_name = grp.get("name", "")
                if (
                    original_name in existing_group_names
                    and not config.allow_duplicate_names
                ):
                    # Use naming utility to generate unique name only if duplicates are not allowed
                    new_name = generate_unique_name(
                        original_name, list(existing_group_names)
                    )
                    group_name_mapping[original_name] = new_name
                    existing_group_names.add(new_name)
                else:
                    # Keep original name if duplicates are allowed or name doesn't exist
                    group_name_mapping[original_name] = original_name

        # Second pass: Create groups maintaining original order
        new_node_groups = []
        for original_name in group_order:
            grp = next(g for g in incoming_groups if g.get("name", "") == original_name)
            grp["name"] = group_name_mapping[original_name]

            # Update node IDs (apply new mapping)
            if "node_ids" in grp:
                new_node_ids = []
                for old_id in grp["node_ids"]:
                    new_id = original_to_new_node_id.get(old_id)
                    if new_id is not None:
                        new_node_ids.append(new_id)
                grp["node_ids"] = new_node_ids

            # Create group
            new_g = self._create_group_from_dict(grp, no_append=True)
            new_node_groups.append(new_g)
            self.group_map[new_g.id] = new_g

        # Set position of new groups
        if prepend:
            # new groups first, maintaining their original order
            self.node_groups = new_node_groups + self.node_groups
        else:
            # new groups last, maintaining their original order
            self.node_groups = self.node_groups + new_node_groups

        # Add nodes and edges
        self.nodes.extend(incoming_nodes)
        self.edges.extend(incoming_edges)

    def _create_group_from_dict(
        self, group_data: Dict, no_append: bool = False
    ) -> NodeGroup:
        """
        Helper to create a NodeGroup from dict data.

        group_data may contain:
            "id": unique identifier for the group
            "name": str
            "node_ids": list of node IDs that belong to this group
            "label_position": position of the label
            "rows", "cols": optional info about how this group was arranged

        Args:
            group_data (Dict): The dictionary describing the group
            no_append (bool): If True, don't automatically append to self.node_groups

        Returns:
            NodeGroup: The newly created group object
        """
        # Get group name and ensure it's unique
        default_name = f"ImportedGroup{self.next_group_number}"
        self.next_group_number += 1

        group_name = group_data.get("name", default_name)
        existing_names = [g.name for g in self.node_groups]

        # Use naming utility to generate a unique name if duplicates are not allowed
        # and this is not handled by the caller
        if (
            not no_append
            and group_name in existing_names
            and not config.allow_duplicate_names
        ):
            group_name = generate_unique_name(group_name, existing_names)

        node_ids = group_data.get("node_ids", [])
        label_position = group_data.get("label_position", NodeGroup.POSITION_TOP)
        group_id = group_data.get("id", None)  # Use existing ID if available

        # Generate new ID if existing group ID already exists
        if group_id and group_id in self.group_map:
            group_id = None

        new_group = NodeGroup(
            name=group_name,
            node_ids=node_ids,
            label_position=label_position,
            group_id=group_id,
        )

        if not no_append:
            self.node_groups.append(new_group)
            self.group_map[new_group.id] = new_group

        return new_group

    def reset(self) -> None:
        """Reset the graph to its initial empty state."""
        self.nodes.clear()
        self.edges.clear()
        self.node_groups.clear()
        self.group_map.clear()  # Also clear group map
        self.selected_nodes.clear()
        self.selected_groups.clear()
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

    def set_node_id_start(self, start_index: int) -> None:
        """
        Set the starting index for node IDs and reassign all node IDs.

        Args:
            start_index (int): The new starting index for node IDs
        """
        from ..config import config

        # Update the configuration
        config.node_id_start = start_index

        # Reassign all node IDs using the new start index
        self._reassign_node_ids()

    def get_node_id_start(self) -> int:
        """
        Get the current starting index for node IDs.

        Returns:
            int: The current starting index for node IDs
        """
        from ..config import config

        return config.node_id_start

    def _reassign_node_ids(self, original_group_nodes=None) -> None:
        """
        Reassign node IDs based on the current order of node groups.
        This preserves the edge connections by updating the edge references.
        Ensures all nodes (including those not in any group) have sequential IDs.
        Uses the configured node_id_start value as the starting index.

        Args:
            original_group_nodes (dict, optional): In the mapping (Group ID -> Node Object List), hold the nodes belonging to each group before deletion
        """
        from ..config import config

        if original_group_nodes is None:
            original_group_nodes = {}

        # Create a mapping (memory address -> node object) for currently existing nodes
        node_by_memory_addr = {id(node): node for node in self.nodes}

        # Save the nodes for each group before assigning a new ID
        node_groups_by_id = {}
        for group in self.node_groups:
            # If there is information in original_group_nodes, use it as priority
            if group.id in original_group_nodes:
                # A list of actual node objects belonging to this group
                nodes_in_group = [
                    node
                    for node in original_group_nodes[group.id]
                    if id(node)
                    in node_by_memory_addr  # Only nodes that have not been deleted
                ]
                node_groups_by_id[group.id] = nodes_in_group
            else:
                # If there is no information in original_group_nodes, then retrieved from current node_ids
                group_nodes = group.get_nodes(self.nodes)
                node_groups_by_id[group.id] = group_nodes

        # Create a new ID mapping
        old_to_new_id = {}
        # Start from the configured starting index
        new_id = config.node_id_start

        # Assign an ID first to a node belonging to a group
        processed_nodes = set()  # Track processed nodes by memory address
        for group in self.node_groups:
            for node in node_groups_by_id.get(group.id, []):
                node_addr = id(node)  # Use memory address as unique identifier
                if node_addr not in processed_nodes and node in self.nodes:
                    old_id = node.id
                    node.id = new_id
                    old_to_new_id[old_id] = new_id
                    new_id += 1
                    processed_nodes.add(node_addr)

        # Assign IDs to nodes that do not belong to the group
        for node in self.nodes:
            node_addr = id(node)  # Use memory address as unique identifier
            if node_addr not in processed_nodes:
                old_id = node.id
                node.id = new_id
                old_to_new_id[old_id] = new_id
                new_id += 1
                processed_nodes.add(node_addr)

        # Update Edge
        new_edges = []
        for source_id, target_id in self.edges:
            new_source_id = old_to_new_id.get(source_id)
            new_target_id = old_to_new_id.get(target_id)
            if new_source_id is not None and new_target_id is not None:
                new_edges.append((new_source_id, new_target_id))
            else:
                # Remove edges that refer to non-existent nodes
                logger.warning(
                    f"Edge ({source_id}, {target_id}) references non-existent nodes and will be removed."
                )

        self.edges = new_edges

        # Update node_ids list for each group
        for group in self.node_groups:
            # Get nodes belonging to this group
            nodes_in_group = node_groups_by_id.get(group.id, [])
            # Update node_ids with the new ID of the node object
            group.node_ids = [node.id for node in nodes_in_group if node in self.nodes]

        # Check if all groups and edges refer to actual nodes
        valid_node_ids = {node.id for node in self.nodes}

        # Just to be sure, you should only refer to valid node IDs for the edge.
        self.edges = [
            (src, dst)
            for src, dst in self.edges
            if src in valid_node_ids and dst in valid_node_ids
        ]

    def rename_group(self, group: NodeGroup, new_name: str) -> None:
        """
        Rename a node group. If duplicate names are allowed (controlled by global config),
        the new name will be used as-is without generating a unique variant.

        Args:
            group (NodeGroup): The group to rename
            new_name (str): The new name for the group
        """
        if group in self.node_groups:
            # Get existing names excluding the current group's name
            existing_names = [g.name for g in self.node_groups if g != group]

            # Use naming utility to handle renaming with proper name conflict resolution
            # Pass the duplicate names allowance flag from global config
            final_name = rename_node(
                group.name,
                new_name,
                existing_names,
                allow_duplicates=config.allow_duplicate_names,
            )
            group.name = final_name

    def _recalculate_next_group_number(self) -> None:
        """
        After the group is deleted, recalculate next_group_number to assign a sequential number to the new group.
        """
        import re

        max_number = 0
        pattern = re.compile(r"Node (\d+)")

        for group in self.node_groups:
            match = pattern.match(group.name)
            if match:
                try:
                    number = int(match.group(1))
                    max_number = max(max_number, number)
                except ValueError:
                    pass

        # Set the "maximum number +1" as the next group number
        self.next_group_number = max_number + 1

    def copy_groups(self, groups):
        """
        Create a deep copy of the specified groups to be used for pasting.

        Args:
            groups (List[NodeGroup]): The groups to copy

        Returns:
            dict: A dictionary containing the copied group data
        """
        from copy import deepcopy

        if not groups:
            return None

        copied_data = {"groups": [], "nodes": [], "edges": []}

        # Map of original node IDs to copied nodes
        node_id_mapping = {}

        # Copy nodes and create ID mapping
        for group in groups:
            group_nodes = group.get_nodes(self.nodes)
            group_data = {
                "name": group.name,
                "label_position": group.label_position,
                "node_ids": [],
            }

            # Copy nodes in this group
            for node in group_nodes:
                # Create a copy of the node's attributes
                node_data = {
                    "id": node.id,  # Temporary ID, will be reassigned during paste
                    "x": node.x,
                    "y": node.y,
                    "row": node.row,
                    "col": node.col,
                    "size": node.size,
                    # SingleNode doesn't have a color attribute
                }

                copied_data["nodes"].append(node_data)
                group_data["node_ids"].append(node.id)

            copied_data["groups"].append(group_data)

            # Copy edges between nodes within these groups
            for i, node1 in enumerate(group_nodes):
                for j, node2 in enumerate(group_nodes):
                    if i < j and self.has_edge(node1, node2):
                        copied_data["edges"].append((node1.id, node2.id))

        return copied_data

    def paste_groups(self, copied_data, offset_x=40, offset_y=40):
        """
        Paste the previously copied groups at a new position.
        The new groups will be positioned at the bottom right of the original groups.

        Args:
            copied_data (dict): The data returned by copy_groups
            offset_x (float): Horizontal offset for the pasted groups
            offset_y (float): Vertical offset for the pasted groups

        Returns:
            List[NodeGroup]: The newly created groups
        """
        if not copied_data:
            return []

        # Create a mapping from old node IDs to new node IDs
        old_to_new_id = {}

        # Find the maximum node ID to start assigning new IDs
        max_id = max(node.id for node in self.nodes) if self.nodes else -1
        next_id = max_id + 1

        # Create new nodes with offset positions
        new_nodes = []
        for node_data in copied_data["nodes"]:
            old_id = node_data["id"]
            # Get shape from node data or use default
            shape = node_data.get(
                "shape", config.get_constant("node_shapes.default", "rectangle")
            )
            new_node = create_node(
                id=next_id,
                x=node_data["x"] + offset_x,
                y=node_data["y"] + offset_y,
                row=node_data["row"],
                col=node_data["col"],
                size=node_data.get("size", None),
                shape=shape,
            )

            old_to_new_id[old_id] = next_id
            next_id += 1
            new_nodes.append(new_node)
            self.nodes.append(new_node)

        # Create new groups
        new_groups = []
        for group_data in copied_data["groups"]:
            # Map old node IDs to new node IDs
            new_node_ids = [
                old_to_new_id[old_id]
                for old_id in group_data["node_ids"]
                if old_id in old_to_new_id
            ]

            # Generate new UUID for the group
            new_group = NodeGroup(
                name=group_data["name"],
                node_ids=new_node_ids,
                label_position=group_data["label_position"],
                z_index=self.next_z_index,
            )

            self.next_z_index += 1
            new_groups.append(new_group)
            self.node_groups.append(new_group)
            self.group_map[new_group.id] = new_group

        # Create new edges
        for old_src, old_dst in copied_data["edges"]:
            if old_src in old_to_new_id and old_dst in old_to_new_id:
                self.edges.append((old_to_new_id[old_src], old_to_new_id[old_dst]))

        return new_groups

    def bring_group_to_front(self, group: NodeGroup) -> None:
        """
        Bring a node group to the front of the rendering order by
        assigning it the highest z-index.

        Args:
            group (NodeGroup): The group to bring to front
        """
        if group is None or group not in self.node_groups:
            return

        # Gets the current maximum z-index and sets a value greater than that
        # This ensures that it is displayed at the forefront
        if self.node_groups:
            max_z_index = max(g.z_index for g in self.node_groups)
            # I won't update it if it's already at the forefront
            if group.z_index >= max_z_index:
                return
            # Set z-index +1 higher than the front
            group.z_index = max_z_index + 1
        else:
            # Set the default value if there are no other groups
            group.z_index = 1

        # Update the next z-index counter to the latest maximum +1
        self.next_z_index = max(self.next_z_index, group.z_index + 1)

        logger.debug(
            f"Brought group '{group.name}' to front with z-index {group.z_index}"
        )

    def get_groups_by_z_index(self) -> List[NodeGroup]:
        """
        Get node groups sorted by z-index (lowest to highest).
        Groups with higher z-index will be drawn on top.

        Returns:
            List[NodeGroup]: Groups sorted by z-index
        """
        return sorted(self.node_groups, key=lambda g: g.z_index)

    def find_node_at_position(self, point: QPointF) -> Optional[BaseNode]:
        """
        Find a node at the given position.
        When multiple nodes overlap, returns the one in the frontmost group (highest z-index).

        Args:
            point (QPointF): The position to check

        Returns:
            Optional[BaseNode]: The node at the position, or None if no node is found
        """
        # First, sort groups by z-index by descending order (highest value = first from the front)
        sorted_groups = sorted(self.node_groups, key=lambda g: g.z_index, reverse=True)

        # Find nodes from the group on the front
        for group in sorted_groups:
            group_nodes = group.get_nodes(self.nodes)
            for node in group_nodes:
                if node.contains(point):
                    return node

        # Find nodes that do not belong to a group (final search)
        for node in self.nodes:
            if not any(node.id in group.node_ids for group in self.node_groups):
                if node.contains(point):
                    return node

        return None

    def get_group_for_node(self, node: BaseNode) -> Optional[NodeGroup]:
        """
        Find the group containing the given node.

        Args:
            node (BaseNode): The node to find the group for

        Returns:
            Optional[NodeGroup]: The group containing the node, or None if not found
        """
        if node is None:
            return None

        for group in self.node_groups:
            if node.id in group.node_ids:
                return group
        return None

    def create_node_group(
        self, nodes: List[BaseNode], name: Optional[str] = None
    ) -> str:
        """
        Create a group from a list of nodes.

        Args:
            nodes (List[BaseNode]): The nodes to include in the group
            name (Optional[str]): Name of the group, defaults to "Node {n}"

        Returns:
            str: The ID of the newly created group
        """

        # Create a default name if none provided
        if name is None:
            name = f"Node {self.next_group_number}"
            self.next_group_number += 1

        # Use naming utility to generate a unique name if duplicates are not allowed
        existing_names = [g.name for g in self.node_groups]
        name = generate_unique_name_if_needed(
            name, existing_names, allow_duplicates=config.allow_duplicate_names
        )

        # Assign the next z-index value to the new group
        new_group = NodeGroup(name=name, nodes=nodes, z_index=self.next_z_index)
        self.next_z_index += 1

        self.node_groups.append(new_group)
        # Add to group_map
        self.group_map[new_group.id] = new_group
        return new_group.id
