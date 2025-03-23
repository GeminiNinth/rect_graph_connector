"""
Knife renderer for drawing knife tool paths.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath

from ...models.view_state_model import ViewStateModel
from ...config import config
from .base_renderer import BaseRenderer


class KnifeRenderer(BaseRenderer):
    """
    Renderer for drawing knife tool paths.

    This class handles rendering of the knife tool path and highlighted edges.
    """

    def __init__(self, view_state: ViewStateModel, style=None):
        """
        Initialize the knife renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (BaseStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style)

    def draw(self, painter: QPainter, knife_data=None, **kwargs):
        """
        Draw the knife tool path and highlighted edges.

        Args:
            painter (QPainter): The painter to use for drawing
            knife_data (dict, optional): Data for knife tool rendering
            **kwargs: Additional drawing parameters
        """
        if not knife_data:
            return

        # Save painter state
        painter.save()

        # Get knife data
        path_points = knife_data.get("path", [])
        highlighted_edges = knife_data.get("highlighted_edges", [])

        # Draw knife path
        if len(path_points) > 1:
            # Set up knife path appearance
            path_color = config.get_color("knife.path", "#FF0000")  # Red
            path_width = config.get_dimension("knife.path_width", 2)

            # Create path
            path = QPainterPath()
            path.moveTo(path_points[0][0], path_points[0][1])
            for point in path_points[1:]:
                path.lineTo(point[0], point[1])

            # Draw path
            painter.setPen(QPen(QColor(path_color), path_width, Qt.SolidLine))
            painter.drawPath(path)

        # Draw highlighted edges
        if highlighted_edges:
            # Set up highlighted edge appearance
            edge_color = config.get_color("knife.highlighted_edge", "#FF0000")  # Red
            edge_width = config.get_dimension("knife.highlighted_edge_width", 3)

            # Draw each highlighted edge
            painter.setPen(QPen(QColor(edge_color), edge_width, Qt.SolidLine))
            for edge in highlighted_edges:
                # Get the actual node objects
                source_id, target_id = edge

                # Find the nodes in the graph
                source_node = None
                target_node = None
                for node in kwargs.get("graph", {}).nodes:
                    if node.id == source_id:
                        source_node = node
                    elif node.id == target_id:
                        target_node = node

                    if source_node and target_node:
                        break

                if source_node and target_node:
                    # Calculate edge endpoints
                    start_point, end_point = self.calculate_edge_endpoints(
                        source_node, target_node
                    )

                    # Draw the edge
                    painter.drawLine(start_point, end_point)

        # Restore painter state
        painter.restore()
