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
        id (str): Unique identifier for the node group
        name (str): Name of the node group
        node_ids (List[int]): List of node IDs in the group
        nodes (List[RectNode]): List of nodes in the group (computed property)
        label_position (str): Position of the group name label ('top-left', 'top-center', etc.)
    """

    # Label position constants
    POSITION_TOP = "top"
    POSITION_RIGHT = "right"
    POSITION_BOTTOM = "bottom"

    def __init__(
        self,
        name: str,
        nodes: Optional[List[RectNode]] = None,
        node_ids: Optional[List[int]] = None,
        label_position: str = POSITION_TOP,
        group_id: Optional[str] = None,
    ):
        """
        Initialize a node group.

        Args:
            name (str): Name of the node group
            nodes (List[RectNode], optional): List of nodes in the group
            node_ids (List[int], optional): List of node IDs in the group
            label_position (str): Position of the group name label
            group_id (str, optional): Unique identifier for the group
        """
        import uuid

        self.id = group_id if group_id else str(uuid.uuid4())
        self.name = name
        self.label_position = label_position

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
    def nodes(self) -> List[RectNode]:
        """
        Property maintained for compatibility, but should be used with caution.
        This property returns a cached list, so to get the latest node list,
        you should use get_nodes(graph.nodes).

        Returns:
            List[RectNode]: Cached node list if it exists, or an empty list
        """
        if hasattr(self, "_nodes_cache") and self._nodes_cache:
            return self._nodes_cache
        return []

    def get_nodes(self, all_nodes: List[RectNode]) -> List[RectNode]:
        """
        Get the nodes in this group from the full list of nodes.

        Args:
            all_nodes (List[RectNode]): All nodes in the graph

        Returns:
            List[RectNode]: Nodes that belong to this group
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
        self.group_map: Dict[str, NodeGroup] = {}  # Map with group ID as key
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

        # Add sequential number if a group with the same name exists
        original_name = name
        existing_names = {g.name for g in self.node_groups}
        counter = 1
        while name in existing_names:
            name = f"{original_name}({counter})"
            counter += 1

        new_group = NodeGroup(name=name, nodes=new_nodes)
        self.node_groups.append(new_group)
        # Add to group_map
        self.group_map[new_group.id] = new_group
        return new_group

    def has_edge(self, source_node: RectNode, target_node: RectNode) -> bool:
        """
        Check if there is an edge between two nodes.

        Args:
            source_node (RectNode): Source node of the edge
            target_node (RectNode): Target node of the edge

        Returns:
            bool: True if an edge exists between the nodes, False otherwise
        """
        return (source_node.id, target_node.id) in self.edges or (
            target_node.id,
            source_node.id,
        ) in self.edges

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
        After deletion, reassigns all node IDs to maintain consistency.

        Args:
            group (NodeGroup): The group of nodes to delete
        """
        # Get nodes from the group
        group_nodes = group.get_nodes(self.nodes)

        # Remove edges connected to any node in the group
        node_ids = {node.id for node in group_nodes}
        self.edges = [
            edge
            for edge in self.edges
            if edge[0] not in node_ids and edge[1] not in node_ids
        ]

        # Remove nodes
        self.nodes = [node for node in self.nodes if node.id not in node_ids]

        # Remove group
        if group in self.node_groups:
            self.node_groups.remove(group)
            # Also remove from group_map
            if group.id in self.group_map:
                del self.group_map[group.id]

        # Clear selection if it was part of the deleted group
        if self.selected_nodes and any(
            node.id in node_ids for node in self.selected_nodes
        ):
            self.selected_nodes.clear()

        # Clear selected group if it was the deleted group
        if self.selected_group == group:
            self.selected_group = None

        # Reassign node IDs to ensure consistency after deletion
        self._reassign_node_ids()

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

        # Update all affected node groups' node_ids
        # No additional operations needed as they are already properly set

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
            self.nodes = [RectNode(**nd) for nd in data.get("nodes", [])]
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
            new_nodes.append(RectNode(**node_data))

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

                incoming_nodes.append(RectNode(**nd))

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

            incoming_nodes.append(RectNode(**nd))

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
                if original_name in existing_group_names:
                    counter = 1
                    new_name = original_name
                    while new_name in existing_group_names:
                        new_name = f"{base_name}({counter})"
                        counter += 1
                    group_name_mapping[original_name] = new_name
                    existing_group_names.add(new_name)
                else:
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
        # Get group name (duplicate check and sequential numbering already done in _load_graph_data)
        group_name = group_data.get("name", f"ImportedGroup{self.next_group_number}")
        self.next_group_number += 1

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
        Ensures all nodes (including those not in any group) have sequential IDs.
        """
        # Save original ID and object ID for each node
        original_node_ids = {id(node): node.id for node in self.nodes}
        node_id_to_object = {node.id: node for node in self.nodes}

        # Save node ID list for each group
        group_node_ids = {group.id: group.node_ids.copy() for group in self.node_groups}

        # Create a mapping from old IDs to new IDs
        old_to_new_id = {}
        new_id = 0

        # First, assign new IDs to nodes in groups based on group order
        grouped_node_ids = set()  # Track node IDs that are in groups
        for group in self.node_groups:
            for node_id in group.node_ids:
                if (
                    node_id not in grouped_node_ids
                ):  # Avoid assigning IDs to the same node twice
                    node = node_id_to_object.get(node_id)
                    if node:
                        old_to_new_id[node_id] = new_id
                        node.id = new_id
                        new_id += 1
                        grouped_node_ids.add(node_id)

        # Then, assign new IDs to any nodes not in groups
        for node in self.nodes:
            if node.id not in grouped_node_ids and node.id not in old_to_new_id:
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
            else:
                # Remove edge if referenced nodes are not found
                print(
                    f"Warning: Edge ({source_id}, {target_id}) references non-existent nodes and will be removed."
                )

        self.edges = new_edges

        # Update the node_ids list for a group
        for group in self.node_groups:
            # Get original node_ids list
            original_node_ids_list = group_node_ids.get(group.id, [])
            new_node_ids = []

            for old_id in original_node_ids_list:
                new_id = old_to_new_id.get(old_id)
                if new_id is not None:
                    new_node_ids.append(new_id)

            # Update the node_ids list for a group
            group.node_ids = new_node_ids

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
        if node is None:
            return None

        for group in self.node_groups:
            if node.id in group.node_ids:
                return group
        return None
