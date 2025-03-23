"""
Helper functions for hover highlighting effects in the Canvas.
This includes support for regular, All-For-One, and Parallel connections.
"""


def get_hover_data(self):
    """
    Generate hover data for rendering based on current hover state.
    This is used by renderers to apply visual effects.

    Returns:
        dict: Hover data containing node, connected nodes, and edges, or None if no hover
    """
    # Only generate hover data when a node is hovered or when creating an edge
    if self.hovered_node or self.current_edge_start:
        # If creating an edge, maintain the original hover state
        if self.current_edge_start:
            # Use the edge start node as the primary hover node if no other node is hovered
            hover_node = self.hovered_node or self.current_edge_start
        else:
            hover_node = self.hovered_node

        hover_data = {
            "node": hover_node,
            "connected_nodes": self.hovered_connected_nodes.copy(),
            "edges": self.hovered_edges.copy(),
        }

        # Add potential target node if it exists
        if (
            self.potential_target_node
            and self.potential_target_node not in hover_data["connected_nodes"]
        ):
            hover_data["connected_nodes"].append(self.potential_target_node)

        return hover_data

    return None


def update_hover_state(self, new_hovered_node):
    """
    Update the hover state for a new hovered node, considering all connection types.
    This method handles regular connections, All-For-One, and Parallel connections.

    Args:
        new_hovered_node: The newly hovered node, or None if no node is hovered
    """
    if new_hovered_node != self.hovered_node:
        # Normal hover behavior when not creating an edge
        self.logger.debug(
            f"Hover state changed: {self.hovered_node} -> {new_hovered_node}"
        )
        self.hovered_node = new_hovered_node
        self.hovered_connected_nodes.clear()
        self.hovered_edges.clear()
        self.potential_target_node = None

        if self.hovered_node:
            self.logger.debug(f"Finding connections for node: {self.hovered_node.id}")
            # Find direct connected nodes and edges (regular connections)
            self.add_direct_connections_to_hover_state(self.hovered_node)

            # Handle All-For-One connections when in that mode
            if (
                self.edit_submode == self.EDIT_SUBMODE_ALL_FOR_ONE
                and self.hovered_node in self.all_for_one_selected_nodes
            ):
                # All selected nodes should be highlighted
                for node in self.all_for_one_selected_nodes:
                    if (
                        node != self.hovered_node
                        and node not in self.hovered_connected_nodes
                    ):
                        self.hovered_connected_nodes.append(node)

            # Handle Parallel connections when in that mode
            if (
                self.edit_submode == self.EDIT_SUBMODE_PARALLEL
                and self.hovered_node in self.parallel_selected_nodes
            ):
                # All selected nodes should be highlighted
                for node in self.parallel_selected_nodes:
                    if (
                        node != self.hovered_node
                        and node not in self.hovered_connected_nodes
                    ):
                        self.hovered_connected_nodes.append(node)


def add_direct_connections_to_hover_state(self, node):
    """
    Add all direct connections (nodes and edges) for the given node to the hover state.

    Args:
        node: The node to find connections for
    """
    # Find only direct connected nodes and edges
    for edge in self.graph.edges:
        if edge[0] == node.id:
            target_node = next((n for n in self.graph.nodes if n.id == edge[1]), None)
            if target_node:
                self.hovered_connected_nodes.append(target_node)
                self.hovered_edges.append((node, target_node))
        elif edge[1] == node.id:
            source_node = next((n for n in self.graph.nodes if n.id == edge[0]), None)
            if source_node:
                self.hovered_connected_nodes.append(source_node)
                self.hovered_edges.append((source_node, node))
