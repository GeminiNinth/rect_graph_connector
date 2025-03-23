"""
Bridge renderer for drawing bridge connections.
"""

from typing import Dict, List, Tuple
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainter, QPainterPath, QBrush

from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.bridge_style import BridgeStyle


class BridgeRenderer(BaseRenderer):
    """
    Renderer for drawing bridge connections.

    This class handles rendering of bridge connection previews,
    highlighted groups, and connection indicators.
    """

    def __init__(self, view_state: ViewStateModel, style: BridgeStyle = None):
        """
        Initialize the bridge renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (BridgeStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or BridgeStyle())

    def draw(self, painter: QPainter, bridge_data=None, **kwargs):
        """
        Draw bridge connection elements.

        Args:
            painter (QPainter): The painter to use for drawing
            bridge_data (dict, optional): Bridge connection data containing
                                      'selected_groups', 'preview_lines',
                                      'floating_menus', and 'edge_nodes'
            **kwargs: Additional drawing parameters
        """
        if not bridge_data:
            return

        # Save painter state
        painter.save()

        # Apply view transformations
        self.apply_transform(painter)

        # Draw highlighted groups
        self._draw_highlighted_groups(painter, bridge_data.get("selected_groups", []))

        # Draw preview lines
        self._draw_preview_lines(painter, bridge_data.get("preview_lines", []))

        # Draw edge nodes
        self._draw_edge_nodes(painter, bridge_data.get("edge_nodes", {}))

        # Draw floating menu indicators
        self._draw_floating_menu_indicators(
            painter, bridge_data.get("floating_menus", {})
        )

        # Restore painter state
        painter.restore()

    def _draw_highlighted_groups(self, painter: QPainter, groups: List):
        """
        Draw highlighted groups with special border style.

        Args:
            painter (QPainter): The painter to use for drawing
            groups (List): List of groups to highlight
        """
        if not groups:
            return

        painter.setPen(self.style.get_highlight_pen())

        for group in groups:
            # Calculate group bounds
            bounds = self._calculate_group_bounds(group)

            # Draw highlighted border
            path = QPainterPath()
            path.addRoundedRect(bounds, 10.0, 10.0)  # Corner radius
            painter.drawPath(path)

    def _draw_preview_lines(
        self, painter: QPainter, preview_lines: List[Tuple[QPointF, QPointF]]
    ):
        """
        Draw bridge connection preview lines.

        Args:
            painter (QPainter): The painter to use for drawing
            preview_lines (List[Tuple[QPointF, QPointF]]): List of line endpoints
        """
        if not preview_lines:
            return

        painter.setPen(self.style.get_preview_pen())

        for start_point, end_point in preview_lines:
            painter.drawLine(start_point, end_point)

    def _draw_edge_nodes(self, painter: QPainter, edge_nodes: Dict):
        """
        Draw edge nodes with indicators.

        Args:
            painter (QPainter): The painter to use for drawing
            edge_nodes (Dict): Dictionary of edge nodes and their positions
        """
        if not edge_nodes:
            return

        painter.setPen(self.style.get_indicator_pen())
        painter.setBrush(QBrush(self.style.indicator_color))

        size = self.style.indicator_size
        for position in edge_nodes.values():
            rect = QRectF(position.x() - size / 2, position.y() - size / 2, size, size)
            painter.drawEllipse(rect)

    def _draw_floating_menu_indicators(self, painter: QPainter, floating_menus: Dict):
        """
        Draw indicators for floating menu positions.

        Args:
            painter (QPainter): The painter to use for drawing
            floating_menus (Dict): Dictionary of floating menu positions
        """
        if not floating_menus:
            return

        painter.setPen(self.style.get_indicator_pen())

        size = self.style.indicator_size
        for position in floating_menus.values():
            # Draw a cross marker
            painter.drawLine(
                position.x() - size / 2,
                position.y(),
                position.x() + size / 2,
                position.y(),
            )
            painter.drawLine(
                position.x(),
                position.y() - size / 2,
                position.x(),
                position.y() + size / 2,
            )

    def _calculate_group_bounds(self, group) -> QRectF:
        """
        Calculate the bounding rectangle for a group.

        Args:
            group: The group to calculate bounds for

        Returns:
            QRectF: The calculated bounds
        """
        if not group.nodes:
            return QRectF()

        # Find min/max coordinates of nodes in the group
        min_x = min(node.x - node.size / 2 for node in group.nodes)
        min_y = min(node.y - node.size / 2 for node in group.nodes)
        max_x = max(node.x + node.size / 2 for node in group.nodes)
        max_y = max(node.y + node.size / 2 for node in group.nodes)

        # Add padding
        padding = 10.0
        return QRectF(
            min_x - padding,
            min_y - padding,
            max_x - min_x + 2 * padding,
            max_y - min_y + 2 * padding,
        )
