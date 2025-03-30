"""
Node renderer for drawing nodes.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter, QPainterPath, QPen

from ...models.base_node import BaseNode
from ...models.graph import Graph
from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.node_style import NodeStyle


class NodeRenderer(BaseRenderer):
    """
    Renderer for drawing nodes.

    This class handles rendering of individual nodes with their shapes, colors,
    and labels based on their state and style configuration.

    Attributes:
        graph (Graph): The graph model to render
    """

    def __init__(
        self, view_state: ViewStateModel, graph: Graph, style: NodeStyle = None
    ):
        """
        Initialize the node renderer.

        Args:
            view_state (ViewStateModel): The view state model
            graph (Graph): The graph model to render
            style (NodeStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or NodeStyle())
        self.graph = graph

    def draw(
        self,
        painter: QPainter,
        selected_nodes=None,
        hover_node=None,
        nodes_to_draw=None,
        edit_target_groups=None,
        potential_target_node=None,  # Add potential_target_node parameter
        **kwargs,
    ):
        """
        Draw specified nodes on the canvas. If nodes_to_draw is None, draw all nodes.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_nodes (list, optional): List of selected nodes
            hover_node (Node, optional): Currently hovered node
            **kwargs: Additional drawing parameters
        """
        selected_nodes = selected_nodes or []

        # Get connected nodes and edges if a node is hovered
        hovered_connected_nodes = kwargs.get("hover_connected_nodes", [])
        if hover_node and not hovered_connected_nodes:
            # If connected nodes not provided but we have a hover node,
            # we can get connected nodes from the graph
            hovered_connected_nodes = self.graph.get_connected_nodes(hover_node)

        # Determine which nodes to draw
        target_nodes = nodes_to_draw if nodes_to_draw is not None else self.graph.nodes

        # Draw the target nodes
        for node in target_nodes:
            is_highlighted = node == hover_node or node in hovered_connected_nodes
            is_potential_target = node == potential_target_node

            # Apply opacity based on hover state, unless it's the potential target
            opacity = 1.0
            if is_potential_target:
                opacity = 1.0  # Force full opacity for potential target
            elif hover_node and not is_highlighted:
                # Apply reduced opacity to non-highlighted nodes when hovering
                opacity = self.style.get_hover_opacity()

            self._draw_node(
                painter,
                node,
                node in selected_nodes,
                node == hover_node,
                opacity=opacity,
            )

    def _draw_node(
        self,
        painter: QPainter,
        node: BaseNode,
        is_selected: bool,
        is_hovered: bool,
        opacity: float = 1.0,
        edit_target_groups: list = None,  # Add edit_target_groups parameter
    ):
        """
        Draw a single node with its background, border, and label.

        Args:
            painter (QPainter): The painter to use for drawing
            node: The node to draw
            is_selected (bool): Whether the node is selected
            is_hovered (bool): Whether the node is being hovered over
            opacity (float): Opacity level for the node (0.0-1.0)
        """
        # Calculate node dimensions
        width = node.size
        height = node.size

        # Create node rectangle
        rect = QRectF(node.x - width / 2, node.y - height / 2, width, height)

        # Save painter state
        painter.save()

        # Apply overall opacity for hover effect
        painter.setOpacity(opacity)

        # Create path for node shape
        path = QPainterPath()
        if getattr(node, "shape", "rectangle") == "circle":
            path.addEllipse(rect)
        else:
            # Draw rounded rectangle
            path.addRoundedRect(
                rect, self.style.corner_radius, self.style.corner_radius
            )

        # Determine if the node is part of a target group in edit mode
        is_edit_target_node = False
        if edit_target_groups:
            # Need to get the group the node belongs to
            # Assuming self.graph is accessible and has get_group_for_node
            node_group = self.graph.get_group_for_node(node)
            if node_group and node_group in edit_target_groups:
                is_edit_target_node = True

        # Set colors based on state
        background_color = self.style.get_background_color(
            is_selected=is_selected,
            is_hovered=is_hovered,
            is_edit_target=is_edit_target_node,  # Pass edit target status
        )

        # Opacity is now handled by painter.setOpacity()

        # Draw node background
        painter.fillPath(path, background_color)  # Use original color

        # Draw node border
        border_pen = self.style.get_border_pen(
            is_selected=is_selected,
            is_hovered=is_hovered,
            is_edit_target=is_edit_target_node,  # Pass edit target status
        )

        # Opacity is now handled by painter.setOpacity()

        painter.setPen(border_pen)  # Use original pen
        painter.drawPath(path)

        # Draw node label
        painter.setFont(self.style.font)
        text_color = self.style.get_text_color()

        # Opacity is now handled by painter.setOpacity()

        painter.setPen(text_color)  # Use original text color

        # Add padding to text rectangle
        text_rect = rect.adjusted(
            self.style.padding,
            self.style.padding,
            -self.style.padding,
            -self.style.padding,
        )
        painter.drawText(text_rect, Qt.AlignCenter, str(node.id))

        # Restore painter state (opacity is automatically restored by painter.restore())
        painter.restore()
