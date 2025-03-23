"""
Group renderer for drawing node groups.
"""

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainter, QPainterPath

from ...models.graph import Graph
from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.group_style import GroupStyle


class GroupRenderer(BaseRenderer):
    """
    Renderer for drawing node groups.

    This class handles rendering of group containers that visually
    organize related nodes with backgrounds, borders, and titles.

    Attributes:
        graph (Graph): The graph model containing groups to render
    """

    def __init__(
        self, view_state: ViewStateModel, graph: Graph, style: GroupStyle = None
    ):
        """
        Initialize the group renderer.

        Args:
            view_state (ViewStateModel): The view state model
            graph (Graph): The graph model containing groups
            style (GroupStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or GroupStyle())
        self.graph = graph

    def draw(
        self,
        painter: QPainter,
        selected_groups=None,
        hover_group=None,
        **kwargs,
    ):
        """
        Draw all groups on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_groups (list, optional): List of selected groups
            hover_group (Group, optional): Currently hovered group
            **kwargs: Additional drawing parameters
        """
        selected_groups = selected_groups or []

        # Draw groups in reverse order to ensure proper layering
        for group in reversed(self.graph.groups):
            self._draw_group(
                painter,
                group,
                group in selected_groups,
                group == hover_group,
            )

    def _draw_group(
        self,
        painter: QPainter,
        group,
        is_selected: bool,
        is_hovered: bool,
    ):
        """
        Draw a single group with its background, border, and title.

        Args:
            painter (QPainter): The painter to use for drawing
            group: The group to draw
            is_selected (bool): Whether the group is selected
            is_hovered (bool): Whether the group is being hovered over
        """
        # Calculate group bounds including padding
        bounds = self._calculate_group_bounds(group)

        # Save painter state
        painter.save()

        # Create path for group shape
        path = QPainterPath()
        path.addRoundedRect(bounds, self.style.corner_radius, self.style.corner_radius)

        # Set colors based on state
        background_color = self.style.get_background_color(
            is_selected=is_selected, is_hovered=is_hovered
        )

        # Draw group background
        painter.fillPath(path, background_color)

        # Draw group border
        painter.setPen(self.style.get_border_pen())
        painter.drawPath(path)

        # Draw group title
        if hasattr(group, "title") and group.title:
            title_rect = QRectF(
                bounds.x(), bounds.y(), bounds.width(), self.style.title_height
            )

            painter.setFont(self.style.title_font)
            painter.setPen(self.style.title_color)
            painter.drawText(
                title_rect,
                Qt.AlignLeft | Qt.AlignVCenter,
                f" {group.title}",  # Add some left padding
            )

        # Restore painter state
        painter.restore()

    def _calculate_group_bounds(self, group) -> QRectF:
        """
        Calculate the bounding rectangle for a group including all its nodes
        and padding.

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
        padding = self.style.padding
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding

        # Add extra height for title if present
        if hasattr(group, "title") and group.title:
            min_y -= self.style.title_height

        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
