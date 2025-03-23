"""
Node renderer for drawing nodes.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter

from ...models.graph import Graph
from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.node_style import NodeStyle


class NodeRenderer(BaseRenderer):
    """
    Renderer for drawing nodes.

    This class handles rendering of individual nodes with their shapes, colors,
    and labels based on their state.

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
        all_for_one_selected_nodes=None,
        parallel_selected_nodes=None,
        bridge_highlighted_nodes=None,
        hover_data=None,
        **kwargs,
    ):
        """
        Draw nodes on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_nodes (list, optional): List of selected nodes
            all_for_one_selected_nodes (list, optional): List of nodes selected in All-For-One mode
            parallel_selected_nodes (list, optional): List of nodes selected in Parallel mode
            bridge_highlighted_nodes (dict, optional): Dict of nodes highlighted in Bridge mode
            hover_data (dict, optional): Data about hover state
            **kwargs: Additional drawing parameters
        """
        # Use provided selected nodes or get from graph
        selected_nodes = selected_nodes or self.graph.selected_nodes

        # Default empty collections if not provided
        all_for_one_selected_nodes = all_for_one_selected_nodes or []
        parallel_selected_nodes = parallel_selected_nodes or []
        bridge_highlighted_nodes = bridge_highlighted_nodes or {}

        # Draw all nodes
        for node in self.graph.nodes:
            self._draw_node(
                painter,
                node,
                selected_nodes,
                all_for_one_selected_nodes,
                parallel_selected_nodes,
                bridge_highlighted_nodes,
                hover_data,
            )

    def _draw_node(
        self,
        painter: QPainter,
        node,
        selected_nodes,
        all_for_one_selected_nodes,
        parallel_selected_nodes,
        bridge_highlighted_nodes,
        hover_data,
    ):
        """
        Draw a single node with its fill, border, and label.

        Args:
            painter (QPainter): The painter to use for drawing
            node: The node to draw
            selected_nodes: List of selected nodes
            all_for_one_selected_nodes: List of nodes selected in All-For-One mode
            parallel_selected_nodes: List of nodes selected in Parallel mode
            bridge_highlighted_nodes: Dict of nodes highlighted in Bridge mode
            hover_data: Data about hover state
        """
        rect = QRectF(
            node.x - node.size / 2, node.y - node.size / 2, node.size, node.size
        )

        # Save painter state before drawing
        painter.save()

        # Check if node should be highlighted based on hover state
        is_highlighted = False
        if hover_data:
            # Check if this is the hovered node
            if hover_data.get("node") and node.id == hover_data["node"].id:
                is_highlighted = True
            else:
                # Check if node is in the connected_nodes list
                for connected_node in hover_data.get("connected_nodes", []):
                    if node.id == connected_node.id:
                        is_highlighted = True
                        break

                # If not already highlighted, check edges
                if not is_highlighted:
                    for edge in hover_data.get("edges", []):
                        if (
                            edge[0].id == hover_data.get("node", {}).id
                            and edge[1].id == node.id
                        ) or (
                            edge[1].id == hover_data.get("node", {}).id
                            and edge[0].id == node.id
                        ):
                            is_highlighted = True
                            break

        # Apply transparency for non-highlighted nodes in edit mode when hovering
        if hover_data and not is_highlighted:
            painter.setOpacity(self.style.get_hover_opacity())

        # Determine node selection state
        is_node_selected = node in selected_nodes
        is_all_for_one_selected = node in all_for_one_selected_nodes
        is_parallel_selected = node in parallel_selected_nodes
        is_bridge_source = bridge_highlighted_nodes.get("source") == node
        is_bridge_target = bridge_highlighted_nodes.get("target") == node

        # Get fill color based on selection state
        node_color = self.style.get_fill_color(
            is_selected=is_node_selected,
            is_all_for_one_selected=is_all_for_one_selected,
            is_parallel_selected=is_parallel_selected,
            is_bridge_source=is_bridge_source,
            is_bridge_target=is_bridge_target,
        )

        # Get border pen based on selection state
        pen = self.style.get_border_pen(
            is_selected=is_node_selected,
            is_all_for_one_selected=is_all_for_one_selected,
            is_parallel_selected=is_parallel_selected,
            is_bridge_source=is_bridge_source,
            is_bridge_target=is_bridge_target,
        )

        # Draw the node based on its shape
        shape = getattr(node, "shape", "rectangle")

        if shape == "circle":
            # Draw circular node
            painter.setBrush(node_color)
            painter.setPen(pen)
            painter.drawEllipse(rect)
        else:
            # Draw rectangular node (default)
            painter.fillRect(rect, node_color)
            painter.setPen(pen)
            painter.drawRect(rect)

        # Draw node ID
        painter.setPen(self.style.get_text_pen())
        painter.drawText(rect, Qt.AlignCenter, str(node.id))

        # Restore painter state
        painter.restore()
