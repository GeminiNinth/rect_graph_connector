"""
Node renderer for drawing nodes.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter, QPainterPath

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
        **kwargs,
    ):
        """
        Draw nodes on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_nodes (list, optional): List of selected nodes
            hover_node (Node, optional): Currently hovered node
            **kwargs: Additional drawing parameters
        """
        selected_nodes = selected_nodes or []

        # Draw all nodes
        for node in self.graph.nodes:
            self._draw_node(
                painter,
                node,
                node in selected_nodes,
                node == hover_node,
            )

    def _draw_node(
        self,
        painter: QPainter,
        node,
        is_selected: bool,
        is_hovered: bool,
    ):
        """
        Draw a single node with its background, border, and label.

        Args:
            painter (QPainter): The painter to use for drawing
            node: The node to draw
            is_selected (bool): Whether the node is selected
            is_hovered (bool): Whether the node is being hovered over
        """
        # Calculate node dimensions
        width = max(self.style.min_width, node.size)
        height = max(self.style.min_height, node.size)

        # Create node rectangle
        rect = QRectF(node.x - width / 2, node.y - height / 2, width, height)

        # Save painter state
        painter.save()

        # Create path for node shape
        path = QPainterPath()
        if getattr(node, "shape", "rectangle") == "circle":
            path.addEllipse(rect)
        else:
            # Draw rounded rectangle
            path.addRoundedRect(
                rect, self.style.corner_radius, self.style.corner_radius
            )

        # Set colors based on state
        background_color = self.style.get_background_color(
            is_selected=is_selected, is_hovered=is_hovered
        )

        # Draw node background
        painter.fillPath(path, background_color)

        # Draw node border
        painter.setPen(QPen(self.style.border_color, self.style.border_width))
        painter.drawPath(path)

        # Draw node label
        painter.setFont(self.style.font)
        painter.setPen(self.style.text_color)

        # Add padding to text rectangle
        text_rect = rect.adjusted(
            self.style.padding,
            self.style.padding,
            -self.style.padding,
            -self.style.padding,
        )
        painter.drawText(text_rect, Qt.AlignCenter, str(node.id))

        # Restore painter state
        painter.restore()
