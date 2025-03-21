"""
Composite renderer that coordinates all individual renderers.
"""

from PyQt5.QtGui import QPainter

from ...models.graph import Graph
from .base_renderer import BaseRenderer
from .border_renderer import BorderRenderer
from .edge_renderer import EdgeRenderer
from .grid_renderer import GridRenderer
from .knife_renderer import KnifeRenderer
from .node_renderer import NodeRenderer
from .selection_renderer import SelectionRenderer


class CompositeRenderer(BaseRenderer):
    """
    Composite renderer that coordinates all individual renderers.
    Manages the rendering order and passes appropriate data to each renderer.
    """

    def __init__(self, canvas, graph: Graph):
        """
        Initialize the composite renderer with all individual renderers.

        Args:
            canvas: The canvas widget to draw on
            graph (Graph): The graph model to render
        """
        super().__init__(canvas, graph)

        # Initialize individual renderers
        self.border_renderer = BorderRenderer(canvas, graph)
        self.grid_renderer = GridRenderer(canvas, graph)
        self.edge_renderer = EdgeRenderer(canvas, graph)
        self.node_renderer = NodeRenderer(canvas, graph)
        self.selection_renderer = SelectionRenderer(canvas, graph)
        self.knife_renderer = KnifeRenderer(canvas, graph)

    def draw(
        self,
        painter: QPainter,
        mode: str = "normal",
        temp_edge_data=None,
        edit_target_groups=None,
        knife_data=None,
        selected_edges=None,
        all_for_one_selected_nodes=None,
        selection_rect_data=None,
        parallel_data=None,
        **kwargs,
    ):
        """
        Draw the complete graph on the canvas.
        Coordinates all renderers in the correct order to maintain proper visual layering.

        Args:
            painter (QPainter): The painter to use for drawing
            mode (str): The current mode ("normal" or "edit")
            temp_edge_data (tuple, optional): Temporary edge data (start_node, end_point)
            edit_target_groups: List of groups being edited in edit mode
            knife_data (dict, optional): Data for knife tool rendering
            selected_edges (list, optional): List of edges that are selected
            all_for_one_selected_nodes (list, optional): List of nodes selected in All-For-One mode
            selection_rect_data (dict, optional): Data for the selection rectangle
            parallel_data (dict, optional): Data for parallel connection mode
            **kwargs: Additional drawing parameters
        """
        # Draw grid if enabled
        self.grid_renderer.draw(painter)

        # Save the painter state and apply zoom scaling for graph elements
        painter.save()

        # Apply pan offset and zoom scaling
        self.apply_transform(painter)

        # Rendering order (visual context):
        # 1. Grid (if enabled)
        # 2. Edges (backmost of scaled elements)
        # 3. Node groups and nodes
        # 4. Selection rectangle
        # 5. Knife tool path
        # 6. Canvas border (most front) - drawn after everything else

        # Draw node group backgrounds first
        self.node_renderer.draw(
            painter,
            all_for_one_selected_nodes=all_for_one_selected_nodes,
            draw_only_backgrounds=True,
        )

        # Draw all types of edges
        self.edge_renderer.draw(
            painter,
            selected_edges=selected_edges,
            temp_edge_data=temp_edge_data,
            knife_data=knife_data,
            all_for_one_selected_nodes=all_for_one_selected_nodes,
            parallel_data=parallel_data,
        )

        # Draw node groups and nodes (without backgrounds)
        self.node_renderer.draw(
            painter,
            all_for_one_selected_nodes=all_for_one_selected_nodes,
            draw_only_nodes=True,
        )

        # Draw selection rectangle if active
        self.selection_renderer.draw(
            painter,
            selection_rect_data=selection_rect_data,
        )

        # Draw knife tool path if active
        self.knife_renderer.draw(
            painter,
            knife_data=knife_data,
        )

        # Restore painter state
        painter.restore()

        # Draw canvas border without scaling (drawn last to appear on top of everything)
        self.border_renderer.draw(painter, mode=mode)
