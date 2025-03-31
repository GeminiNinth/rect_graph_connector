"""
Selection model for managing selected nodes, groups, and edges.
"""

from .event import Event


class SelectionModel:
    """
    Model for managing the selection state of nodes, groups, and edges.

    This class encapsulates the selection state of the graph elements and provides
    methods for modifying the selection. It emits events when the selection changes
    to notify observers.

    Attributes:
        selected_nodes (list): List of currently selected nodes
        selected_groups (list): List of currently selected groups
        selected_edges (list): List of currently selected edges
        selection_changed (Event): Event emitted when the selection changes
    """

    def __init__(self):
        """Initialize the selection model with empty selections."""
        self.selected_nodes = []
        self.selected_groups = []
        self.selected_edges = []
        self.selection_changed = Event()

        # Deselection methods flags
        self.enabled_deselect_methods = {}

    def select_node(self, node, add_to_selection=False):
        """
        Select a node.

        Args:
            node: The node to select
            add_to_selection (bool): If True, add to current selection; if False, replace it
        """
        if not add_to_selection:
            self.selected_nodes.clear()

        if node not in self.selected_nodes:
            self.selected_nodes.append(node)
            self.selection_changed.emit()

    def select_nodes(self, nodes, add_to_selection=False):
        """
        Select multiple nodes.

        Args:
            nodes (list): The nodes to select
            add_to_selection (bool): If True, add to current selection; if False, replace it
        """
        if not add_to_selection:
            self.selected_nodes.clear()

        changed = False
        for node in nodes:
            if node not in self.selected_nodes:
                self.selected_nodes.append(node)
                changed = True

        if changed:
            self.selection_changed.emit()

    def deselect_node(self, node):
        """
        Deselect a node.

        Args:
            node: The node to deselect
        """
        if node in self.selected_nodes:
            self.selected_nodes.remove(node)
            self.selection_changed.emit()

    def select_group(self, group, add_to_selection=False):
        """
        Select a group.

        Args:
            group: The group to select
            add_to_selection (bool): If True, add to current selection; if False, replace it
        """
        if not add_to_selection:
            self.selected_groups.clear()

        if group not in self.selected_groups:
            self.selected_groups.append(group)
            self.selection_changed.emit()

    def select_groups(self, groups, add_to_selection=False):
        """
        Select multiple groups.

        Args:
            groups (list): The groups to select
            add_to_selection (bool): If True, add to current selection; if False, replace it
        """
        # Store the set of initially selected group IDs for comparison
        initial_selected_ids = {id(g) for g in self.selected_groups}

        if not add_to_selection:
            # If replacing selection and the new list is identical to the old, no change.
            # However, clearing and re-adding is simpler and covers edge cases.
            self.selected_groups.clear()
            for group in groups:
                # Avoid duplicates even when replacing, though clear() handles it mostly.
                if group not in self.selected_groups:
                    self.selected_groups.append(group)
        else:
            # Add to selection, only adding new groups
            for group in groups:
                if group not in self.selected_groups:
                    self.selected_groups.append(group)

        # Check if the final set of selected group IDs is different from the initial set
        final_selected_ids = {id(g) for g in self.selected_groups}
        if initial_selected_ids != final_selected_ids:
            self.selection_changed.emit()

    def deselect_group(self, group):
        """
        Deselect a group.

        Args:
            group: The group to deselect
        """
        if group in self.selected_groups:
            self.selected_groups.remove(group)
            self.selection_changed.emit()

    def select_edge(self, edge, add_to_selection=False):
        """
        Select an edge.

        Args:
            edge: The edge to select (tuple of source and target nodes)
            add_to_selection (bool): If True, add to current selection; if False, replace it
        """
        if not add_to_selection:
            self.selected_edges.clear()

        if edge not in self.selected_edges:
            self.selected_edges.append(edge)
            self.selection_changed.emit()

    def select_edges(self, edges, add_to_selection=False):
        """
        Select multiple edges.

        Args:
            edges (list): The edges to select
            add_to_selection (bool): If True, add to current selection; if False, replace it
        """
        if not add_to_selection:
            self.selected_edges.clear()

        changed = False
        for edge in edges:
            if edge not in self.selected_edges:
                self.selected_edges.append(edge)
                changed = True

        if changed:
            self.selection_changed.emit()

    def deselect_edge(self, edge):
        """
        Deselect an edge.

        Args:
            edge: The edge to deselect
        """
        if edge in self.selected_edges:
            self.selected_edges.remove(edge)
            self.selection_changed.emit()

    def clear_selection(self):
        """Clear all selections."""
        if self.selected_nodes or self.selected_groups or self.selected_edges:
            self.selected_nodes.clear()
            self.selected_groups.clear()
            self.selected_edges.clear()
            self.selection_changed.emit()

    def set_deselect_method(self, method, enabled=True):
        """
        Enable/disable a deselection method.

        Args:
            method (str): The deselection method to set
            enabled (bool): True to enable, False to disable
        """
        self.enabled_deselect_methods[method] = enabled

    def is_deselect_method_enabled(self, method):
        """
        Check if a deselection method is enabled.

        Args:
            method (str): The deselection method to check

        Returns:
            bool: True if the method is enabled, False otherwise
        """
        return self.enabled_deselect_methods.get(method, True)
