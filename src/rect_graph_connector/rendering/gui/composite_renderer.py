"""
Composite renderer that coordinates all individual renderers.
"""

from PyQt5.QtGui import QPainter

from ...models.graph import Graph
from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.base_style import BaseStyle


class CompositeRenderer(BaseRenderer):
    """
    Composite renderer that coordinates all individual renderers.

    This class manages the rendering order and passes appropriate data to each renderer.
    It implements the Composite pattern to treat a group of renderers as a single renderer.

    Attributes:
        graph (Graph): The graph model to render
        renderers (list): List of renderers to coordinate
    """

    def __init__(
        self, view_state: ViewStateModel, graph: Graph, style: BaseStyle = None
    ):
        """
        Initialize the composite renderer with all individual renderers.

        Args:
            view_state (ViewStateModel): The view state model
            graph (Graph): The graph model to render
            style (BaseStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or BaseStyle())
        self.graph = graph
        self.renderers = []

    def add_renderer(self, renderer: BaseRenderer):
        """
        Add a renderer to the composite.

        Args:
            renderer (BaseRenderer): The renderer to add
        """
        self.renderers.append(renderer)

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
        bridge_data=None,
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
            bridge_data (dict, optional): Data for bridge connection mode
            **kwargs: Additional drawing parameters
        """
        # Save the painter state and apply zoom scaling for graph elements
        painter.save()

        # Apply pan offset and zoom scaling
        self.apply_transform(painter)

        # Prepare common drawing parameters
        draw_params = {
            "mode": mode,
            "temp_edge_data": temp_edge_data,
            "edit_target_groups": edit_target_groups,
            "knife_data": knife_data,
            "selected_edges": selected_edges,
            "all_for_one_selected_nodes": all_for_one_selected_nodes,
            "selection_rect_data": selection_rect_data,
            "parallel_data": parallel_data,
            "bridge_data": bridge_data,
            **kwargs,
        }

        # Draw all renderers in order
        for renderer in self.renderers:
            renderer.draw(painter, **draw_params)

        # Restore painter state
        painter.restore()
