"""
Group renderer for drawing node groups.
"""

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainter, QPainterPath

from ...config import config  # Import config
from ...models.graph import Graph, NodeGroup  # Import NodeGroup for constants
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

        # Sort groups by z-index (lowest first) to draw back-to-front
        sorted_groups = sorted(self.graph.node_groups, key=lambda g: g.z_index)

        # Draw groups
        for group in sorted_groups:
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
        background_color = self.style.get_background_color(is_selected=is_selected)

        # Draw group background
        painter.fillPath(path, background_color)

        # Draw group border
        painter.setPen(self.style.get_border_pen(is_selected=is_selected))
        painter.drawPath(path)

        # Draw group name (title)
        if hasattr(group, "name") and group.name:  # Check for 'name' attribute
            # Get label dimensions from config
            label_height = config.get_dimension("group.label.height", 20)
            label_width = config.get_dimension(
                "group.label.fixed_width", 100
            )  # Use fixed width for now
            position_margin = config.get_dimension(
                "group.label.position_margin", 5
            )  # Margin from group edge
            text_margin = config.get_dimension(
                "group.label.text_margin", 5
            )  # Padding inside label rect

            # Calculate label position based on group.label_position
            label_x = 0
            label_y = 0
            alignment = Qt.AlignCenter  # Default alignment

            if group.label_position == NodeGroup.POSITION_TOP:
                label_x = bounds.x() + (bounds.width() - label_width) / 2
                label_y = bounds.y() - label_height - position_margin
                alignment = Qt.AlignCenter
            elif group.label_position == NodeGroup.POSITION_BOTTOM:
                label_x = bounds.x() + (bounds.width() - label_width) / 2
                label_y = bounds.y() + bounds.height() + position_margin
                alignment = Qt.AlignCenter
            elif group.label_position == NodeGroup.POSITION_RIGHT:
                label_x = bounds.x() + bounds.width() + position_margin
                label_y = bounds.y() + (bounds.height() - label_height) / 2
                alignment = Qt.AlignLeft | Qt.AlignVCenter
            # Add more positions like 'left', 'top-left' etc. if needed

            title_rect = QRectF(label_x, label_y, label_width, label_height)
            text_rect = title_rect.adjusted(
                text_margin, 0, -text_margin, 0
            )  # Adjust for text padding

            # Draw label background (optional, can be styled)
            # painter.fillRect(title_rect, QColor(240, 240, 240, 180))

            painter.setFont(self.style.title_font)
            text_color, _ = self.style.get_label_colors(is_selected=is_selected)
            painter.setPen(text_color)
            painter.drawText(
                text_rect,  # Use adjusted rect for text drawing
                alignment,
                group.name,
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
