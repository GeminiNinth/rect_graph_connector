"""
Bridge renderer for drawing bridge connection elements.
"""

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor

from ...models.view_state_model import ViewStateModel
from ...config import config
from .base_renderer import BaseRenderer


class BridgeRenderer(BaseRenderer):
    """
    Renderer for drawing bridge connection elements.

    This class handles rendering of bridge connection preview lines and highlighted nodes.
    """

    def __init__(self, view_state: ViewStateModel, style=None):
        """
        Initialize the bridge renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (BaseStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style)

    def draw(self, painter: QPainter, bridge_data=None, **kwargs):
        """
        Draw bridge connection elements.

        Args:
            painter (QPainter): The painter to use for drawing
            bridge_data (dict, optional): Data for bridge connection rendering
            **kwargs: Additional drawing parameters
        """
        if not bridge_data:
            return

        # Save painter state
        painter.save()

        # Get bridge data
        preview_lines = bridge_data.get("preview_lines", [])
        floating_menus = bridge_data.get("floating_menus", {})
        selected_groups = bridge_data.get("selected_groups", [])
        edge_nodes = bridge_data.get("edge_nodes", {})

        # Draw preview lines
        if preview_lines:
            # Set up preview line appearance
            line_color = config.get_color("bridge.preview_line", "#FF00FF")  # Magenta
            line_width = config.get_dimension("bridge.preview_line_width", 2)

            # Draw each preview line
            painter.setPen(QPen(QColor(line_color), line_width, Qt.DashLine))
            for line in preview_lines:
                start_point = QPointF(line[0][0], line[0][1])
                end_point = QPointF(line[1][0], line[1][1])
                painter.drawLine(start_point, end_point)

        # Draw highlighted edge nodes
        if edge_nodes:
            # Set up highlighted node appearance
            source_color = config.get_color(
                "bridge.source_node", "#FFD0E0"
            )  # Light pink
            target_color = config.get_color(
                "bridge.target_node", "#50FCC0"
            )  # Light blue

            # Draw each group's edge nodes
            for i, group_id in enumerate(edge_nodes):
                nodes = edge_nodes[group_id]
                if not nodes:
                    continue

                # Determine if this is source or target group
                is_source = i == 0 if i < len(selected_groups) else False

                # Draw each node with appropriate highlight
                for node in nodes:
                    # Calculate node rectangle
                    rect = QPointF(
                        node.x - node.size / 2,
                        node.y - node.size / 2,
                        node.size,
                        node.size,
                    )

                    # Draw highlight
                    if is_source:
                        painter.fillRect(rect, QColor(source_color))
                    else:
                        painter.fillRect(rect, QColor(target_color))

        # Draw floating menus
        if floating_menus:
            for group_id, menu in floating_menus.items():
                menu.draw(painter)

        # Restore painter state
        painter.restore()
