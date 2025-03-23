"""
Composite renderer that combines multiple renderers.
"""

from PyQt5.QtGui import QPainter

from ...models.graph import Graph
from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .node_renderer import NodeRenderer
from .edge_renderer import EdgeRenderer
from .group_renderer import GroupRenderer
from .grid_renderer import GridRenderer
from .border_renderer import BorderRenderer
from .selection_renderer import SelectionRenderer
from .knife_renderer import KnifeRenderer
from .bridge_renderer import BridgeRenderer


class CompositeRenderer(BaseRenderer):
    """
    Composite renderer that manages and coordinates multiple renderers.

    This class combines all renderers to create the complete graph visualization.
    It handles the proper drawing order and state management across all renderers.

    The drawing order is:
    1. Border (background and border)
    2. Grid (if visible)
    3. Groups (bottom layer)
    4. Edges
    5. Nodes (top layer)
    6. Selection rectangle (if selecting)
    7. Knife path (if in knife mode)
    8. Bridge connections (if in bridge mode)
    """

    def __init__(
        self,
        view_state: ViewStateModel,
        graph: Graph,
        grid_renderer: GridRenderer = None,
        border_renderer: BorderRenderer = None,
        group_renderer: GroupRenderer = None,
        edge_renderer: EdgeRenderer = None,
        node_renderer: NodeRenderer = None,
        selection_renderer: SelectionRenderer = None,
        knife_renderer: KnifeRenderer = None,
        bridge_renderer: BridgeRenderer = None,
    ):
        """
        Initialize the composite renderer.

        Args:
            view_state (ViewStateModel): The view state model
            graph (Graph): The graph model to render
            grid_renderer (GridRenderer, optional): Custom grid renderer
            border_renderer (BorderRenderer, optional): Custom border renderer
            group_renderer (GroupRenderer, optional): Custom group renderer
            edge_renderer (EdgeRenderer, optional): Custom edge renderer
            node_renderer (NodeRenderer, optional): Custom node renderer
            selection_renderer (SelectionRenderer, optional): Custom selection renderer
            knife_renderer (KnifeRenderer, optional): Custom knife renderer
            bridge_renderer (BridgeRenderer, optional): Custom bridge renderer
        """
        super().__init__(view_state, None)  # Composite doesn't need its own style
        self.graph = graph

        # Initialize renderers with defaults if not provided
        self.border_renderer = border_renderer or BorderRenderer(view_state)
        self.grid_renderer = grid_renderer or GridRenderer(view_state)
        self.group_renderer = group_renderer or GroupRenderer(view_state, graph)
        self.edge_renderer = edge_renderer or EdgeRenderer(view_state, graph)
        self.node_renderer = node_renderer or NodeRenderer(view_state, graph)
        self.selection_renderer = selection_renderer or SelectionRenderer(view_state)
        self.knife_renderer = knife_renderer or KnifeRenderer(view_state)
        self.bridge_renderer = bridge_renderer or BridgeRenderer(view_state)

    def draw(
        self,
        painter: QPainter,
        selected_nodes=None,
        selected_edges=None,
        selected_groups=None,
        hover_node=None,
        hover_edge=None,
        hover_group=None,
        selection_rect_data=None,
        knife_data=None,
        bridge_data=None,
        **kwargs,
    ):
        """
        Draw all graph elements in the correct order.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_nodes (list, optional): List of selected nodes
            selected_edges (list, optional): List of selected edges
            selected_groups (list, optional): List of selected groups
            hover_node (Node, optional): Currently hovered node
            hover_edge (tuple, optional): Currently hovered edge
            hover_group (Group, optional): Currently hovered group
            selection_rect_data (dict, optional): Selection rectangle data
            knife_data (dict, optional): Knife tool data
            bridge_data (dict, optional): Bridge connection data
            **kwargs: Additional drawing parameters
        """
        # Draw border and background first
        self.border_renderer.draw(painter)

        # Draw grid if visible
        if self.view_state.grid_visible:
            self.grid_renderer.draw(painter)

        # Draw groups (bottom layer)
        self.group_renderer.draw(
            painter, selected_groups=selected_groups, hover_group=hover_group
        )

        # Draw edges
        self.edge_renderer.draw(
            painter,
            selected_edges=selected_edges,
            hover_edge=hover_edge,
            hover_node=hover_node,
        )

        # Draw nodes (top layer)
        self.node_renderer.draw(
            painter,
            selected_nodes=selected_nodes,
            hover_node=hover_node,
            hover_connected_nodes=kwargs.get("hover_connected_nodes", []),
        )

        # Draw selection rectangle if selecting
        if selection_rect_data:
            self.selection_renderer.draw(
                painter, selection_rect_data=selection_rect_data
            )

        # Draw knife path and highlights if in knife mode
        if knife_data:
            self.knife_renderer.draw(painter, knife_data=knife_data)

        # Draw bridge connections if in bridge mode
        if bridge_data:
            self.bridge_renderer.draw(painter, bridge_data=bridge_data)

    def update_graph(self, graph: Graph):
        """
        Update the graph model for all renderers.

        Args:
            graph (Graph): The new graph model
        """
        self.graph = graph
        self.group_renderer.graph = graph
        self.edge_renderer.graph = graph
        self.node_renderer.graph = graph
