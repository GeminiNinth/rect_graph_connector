"""
Hover state model for managing hover interactions.
"""

from .event import Event


class HoverStateModel:
    """
    Model for managing the hover state of nodes and edges.

    This class encapsulates the hover state of graph elements and provides
    methods for updating the hover state. It emits events when the hover state
    changes to notify observers.

    Attributes:
        hovered_node: The currently hovered node, or None
        hovered_connected_nodes: List of nodes connected to the hovered node
        hovered_edges: List of edges connected to the hovered node
        potential_target_node: Potential target node when creating an edge
        hover_changed (Event): Event emitted when the hover state changes
    """

    def __init__(self):
        """Initialize the hover state model with empty state."""
        self.hovered_node = None
        self.hovered_connected_nodes = []
        self.hovered_edges = []
        self.potential_target_node = None
        self.hover_changed = Event()

    def update_hover_state(self, node, connected_nodes=None, edges=None):
        """
        Update the hover state with a new hovered node and its connections.

        Args:
            node: The newly hovered node, or None if no node is hovered
            connected_nodes (list, optional): List of nodes connected to the hovered node
            edges (list, optional): List of edges connected to the hovered node
        """
        changed = False

        if self.hovered_node != node:
            self.hovered_node = node
            changed = True

        if connected_nodes is not None:
            self.hovered_connected_nodes = connected_nodes
            changed = True

        if edges is not None:
            self.hovered_edges = edges
            changed = True

        if changed:
            self.hover_changed.emit()

    def set_potential_target(self, node):
        """
        Set the potential target node when creating an edge.

        Args:
            node: The potential target node, or None
        """
        if self.potential_target_node != node:
            self.potential_target_node = node
            self.hover_changed.emit()

    def clear(self):
        """Clear all hover state."""
        if (
            self.hovered_node
            or self.hovered_connected_nodes
            or self.hovered_edges
            or self.potential_target_node
        ):
            self.hovered_node = None
            self.hovered_connected_nodes = []
            self.hovered_edges = []
            self.potential_target_node = None
            self.hover_changed.emit()

    def get_hover_data(self):
        """
        Get the current hover data as a dictionary.

        Returns:
            dict: Dictionary containing the current hover state
        """
        return {
            "node": self.hovered_node,
            "connected_nodes": self.hovered_connected_nodes,
            "edges": self.hovered_edges,
            "potential_target": self.potential_target_node,
        }
