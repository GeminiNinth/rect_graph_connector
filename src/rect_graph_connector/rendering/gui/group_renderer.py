"""
Group renderer for drawing node groups.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter

from ...models.graph import Graph
from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.group_style import GroupStyle


class GroupRenderer(BaseRenderer):
    """
    Renderer for drawing node groups.

    This class handles rendering of node groups, including their backgrounds,
    borders, and labels based on their state.

    Attributes:
        graph (Graph): The graph model to render
    """

    def __init__(
        self, view_state: ViewStateModel, graph: Graph, style: GroupStyle = None
    ):
        """
        Initialize the group renderer.

        Args:
            view_state (ViewStateModel): The view state model
            graph (Graph): The graph model to render
            style (GroupStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or GroupStyle())
        self.graph = graph

    def draw(
        self,
        painter: QPainter,
        selected_groups=None,
        draw_only_backgrounds=False,
        draw_only_borders=False,
        **kwargs,
    ):
        """
        Draw node groups on the canvas.

        Args:
            painter (QPainter): The painter to use for drawing
            selected_groups (list, optional): List of selected groups
            draw_only_backgrounds (bool): If True, only draw group backgrounds
            draw_only_borders (bool): If True, only draw group borders and labels
            **kwargs: Additional drawing parameters
        """
        # Use provided selected groups or get from graph
        selected_groups = selected_groups or self.graph.selected_groups
        selected_group_ids = [group.id for group in selected_groups]

        # Sort groups by z-index (lowest to highest)
        sorted_groups = sorted(self.graph.node_groups, key=lambda g: g.z_index)

        if draw_only_backgrounds:
            # Draw only group backgrounds
            for group in sorted_groups:
                self._draw_group_background(
                    painter, group, group.id in selected_group_ids
                )
        elif draw_only_borders:
            # Draw only group borders and labels
            for group in sorted_groups:
                self._draw_group_border_and_label(
                    painter, group, group.id in selected_group_ids
                )
        else:
            # Draw complete groups (backgrounds, borders, and labels)
            for group in sorted_groups:
                self._draw_group(painter, group, group.id in selected_group_ids)

    def _draw_group(self, painter: QPainter, group, is_selected):
        """
        Draw a complete group including background, border, and label.

        Args:
            painter (QPainter): The painter to use for drawing
            group: The group to draw
            is_selected (bool): Whether the group is selected
        """
        self._draw_group_background(painter, group, is_selected)
        self._draw_group_border_and_label(painter, group, is_selected)

    def _draw_group_background(self, painter: QPainter, group, is_selected):
        """
        Draw the background for a node group.

        Args:
            painter (QPainter): The painter to use for drawing
            group: The group to draw the background for
            is_selected (bool): Whether the group is selected
        """
        group_nodes = group.get_nodes(self.graph.nodes)
        if not group_nodes:
            return

        # Calculate group boundary
        border_margin = self.style.get_border_margin()
        min_x = min(node.x - node.size / 2 for node in group_nodes) - border_margin
        min_y = min(node.y - node.size / 2 for node in group_nodes) - border_margin
        max_x = max(node.x + node.size / 2 for node in group_nodes) + border_margin
        max_y = max(node.y + node.size / 2 for node in group_nodes) + border_margin
        group_width = max_x - min_x
        group_height = max_y - min_y

        # Get background color based on selection state
        bg_color = self.style.get_background_color(is_selected)

        # Convert to integer positions as required
        min_x_int = int(min_x)
        min_y_int = int(min_y)
        group_width_int = int(group_width)
        group_height_int = int(group_height)

        # Draw group background
        painter.fillRect(
            min_x_int, min_y_int, group_width_int, group_height_int, bg_color
        )

    def _draw_group_border_and_label(self, painter: QPainter, group, is_selected):
        """
        Draw the border and label for a node group.

        Args:
            painter (QPainter): The painter to use for drawing
            group: The group to draw the border and label for
            is_selected (bool): Whether the group is selected
        """
        group_nodes = group.get_nodes(self.graph.nodes)
        if not group_nodes:
            return

        # Calculate group boundary
        border_margin = self.style.get_border_margin()
        min_x = min(node.x - node.size / 2 for node in group_nodes) - border_margin
        min_y = min(node.y - node.size / 2 for node in group_nodes) - border_margin
        max_x = max(node.x + node.size / 2 for node in group_nodes) + border_margin
        max_y = max(node.y + node.size / 2 for node in group_nodes) + border_margin
        group_width = max_x - min_x
        group_height = max_y - min_y

        # Convert to integer positions
        min_x_int = int(min_x)
        min_y_int = int(min_y)
        group_width_int = int(group_width)
        group_height_int = int(group_height)

        # Get border pen based on selection state
        pen = self.style.get_border_pen(is_selected)
        painter.setPen(pen)

        # Draw group border
        painter.drawRect(min_x_int, min_y_int, group_width_int, group_height_int)

        # Draw group label
        self._draw_group_label(
            painter, group, is_selected, min_x_int, min_y_int, max_x, max_y
        )

    def _draw_group_label(
        self, painter: QPainter, group, is_selected, min_x, min_y, max_x, max_y
    ):
        """
        Draw the label for a node group.

        Args:
            painter (QPainter): The painter to use for drawing
            group: The group to draw the label for
            is_selected (bool): Whether the group is selected
            min_x, min_y: Top-left corner of the group
            max_x, max_y: Bottom-right corner of the group
        """
        if not group.name:
            return

        # Get label dimensions
        label_padding, label_height, label_max_width = self.style.get_label_dimensions()

        # Calculate label position (centered at the top of the group)
        label_width = min(label_max_width, max_x - min_x)
        label_x = min_x + (max_x - min_x - label_width) / 2
        label_y = min_y - label_height - label_padding

        # Get label colors
        label_bg_color = self.style.get_label_background_color(is_selected)

        # Draw label background
        label_rect = QRectF(label_x, label_y, label_width, label_height)
        painter.fillRect(label_rect, label_bg_color)

        # Draw label border
        painter.setPen(self.style.get_border_pen(is_selected))
        painter.drawRect(label_rect)

        # Draw label text
        painter.setPen(self.style.get_label_text_pen())
        painter.drawText(label_rect, Qt.AlignCenter, group.name)
