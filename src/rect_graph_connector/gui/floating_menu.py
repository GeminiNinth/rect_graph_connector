"""
This module contains the FloatingMenu for bridge connection node highlighting.

The FloatingMenu is displayed above node groups in bridge connection mode
and allows users to change which edge nodes are highlighted for connection.
"""

from typing import Callable, Dict, List, Optional, Tuple

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QFontMetrics
from PyQt5.QtWidgets import QApplication

from ..config import config
from ..models.graph import NodeGroup
from ..models.special.bridge_connection import BridgeConnector
from ..utils.logging_utils import get_logger
from ..gui.rendering.base_renderer import parse_rgba

logger = get_logger(__name__)


class FloatingMenu:
    """
    A floating menu displayed above a node group in bridge connection mode.

    The menu provides buttons to change which edge nodes are highlighted
    for bridge connections.
    """

    def __init__(
        self, node_group: NodeGroup, theme: str = "light", group_type: str = "source"
    ):
        """
        Initialize the floating menu.

        Args:
            node_group: The node group this menu is attached to
            theme: The color theme to use (light or dark)
            group_type: The type of group ("source" or "target")
        """
        self.node_group = node_group
        self.theme = theme
        self.group_type = group_type
        self.visible = True
        self.highlight_position = config.get_constant(
            "bridge_connection.highlight_positions.default", "row_first"
        )

        # Get position strings for display
        self.position_strings = {
            BridgeConnector.POS_ROW_FIRST: config.get_string(
                "bridge_connection.floating_menu.position_label.row_first", "Row First"
            ),
            BridgeConnector.POS_ROW_LAST: config.get_string(
                "bridge_connection.floating_menu.position_label.row_last", "Row Last"
            ),
            BridgeConnector.POS_COL_FIRST: config.get_string(
                "bridge_connection.floating_menu.position_label.col_first",
                "Column First",
            ),
            BridgeConnector.POS_COL_LAST: config.get_string(
                "bridge_connection.floating_menu.position_label.col_last", "Column Last"
            ),
        }

        # Button labels
        self.prev_button_text = config.get_string(
            "bridge_connection.floating_menu.prev_button", "◀"
        )
        self.next_button_text = config.get_string(
            "bridge_connection.floating_menu.next_button", "▶"
        )

        # Menu title based on group type
        if group_type == "source":
            self.title = config.get_string(
                "bridge_connection.floating_menu.source_title", "Source Nodes"
            )
        else:  # target
            self.title = config.get_string(
                "bridge_connection.floating_menu.target_title", "Target Nodes"
            )

        # UI dimensions
        self.padding = 5
        self.button_size = 24
        self.button_padding = 5

        # Calculate menu dimensions based on content
        self._calculate_dimensions()

        # Interactive elements
        self.prev_button_rect = None
        self.next_button_rect = None

        # Position order for cycling through highlight positions
        self.position_order = [
            BridgeConnector.POS_ROW_FIRST,
            BridgeConnector.POS_COL_FIRST,
            BridgeConnector.POS_ROW_LAST,
            BridgeConnector.POS_COL_LAST,
        ]

    def set_highlight_position(self, position: str) -> None:
        """
        Set the highlight position.

        Args:
            position: The highlight position to set
        """
        if position in self.position_strings:
            self.highlight_position = position

    def next_highlight_position(self) -> str:
        """
        Move to the next highlight position.

        Returns:
            The new highlight position
        """
        current_idx = (
            self.position_order.index(self.highlight_position)
            if self.highlight_position in self.position_order
            else 0
        )
        next_idx = (current_idx + 1) % len(self.position_order)
        self.highlight_position = self.position_order[next_idx]
        return self.highlight_position

    def prev_highlight_position(self) -> str:
        """
        Move to the previous highlight position.

        Returns:
            The new highlight position
        """
        current_idx = (
            self.position_order.index(self.highlight_position)
            if self.highlight_position in self.position_order
            else 0
        )
        prev_idx = (current_idx - 1) % len(self.position_order)
        self.highlight_position = self.position_order[prev_idx]
        return self.highlight_position

    def _calculate_dimensions(self) -> None:
        """
        Calculate the dimensions of the menu based on content.
        """
        # Create a font metrics object for text measurements
        font = QFont()
        font.setPointSize(10)
        font_metrics = QFontMetrics(font)

        # Calculate title width
        title_width = font_metrics.horizontalAdvance(self.title) + 2 * self.padding

        # Calculate position text width
        position_width = 0
        for pos_text in self.position_strings.values():
            width = font_metrics.horizontalAdvance(pos_text)
            position_width = max(position_width, width)

        position_width += 2 * self.padding

        # Calculate total width
        self.width = max(
            title_width, position_width + 2 * self.button_size + 4 * self.button_padding
        )

        # Calculate height (title + position text + padding)
        self.height = 3 * font_metrics.height() + 4 * self.padding

        # Store font and font metrics for drawing
        self.font = font
        self.font_metrics = font_metrics

    def get_position(self, nodes_positions: List[Tuple[float, float]]) -> QPointF:
        """
        Calculate the position of the floating menu above the node group.

        Args:
            nodes_positions: List of (x, y) positions of all nodes in the group

        Returns:
            Position for the top-left corner of the menu
        """
        if not nodes_positions:
            return QPointF(0, 0)

        # Calculate the bounding box of the node group
        xs = [pos[0] for pos in nodes_positions]
        ys = [pos[1] for pos in nodes_positions]

        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)

        # Position the menu horizontally centered above the group
        x = min_x + (max_x - min_x) / 2 - self.width / 2
        y = (
            min_y - self.height - 10
        )  # Position above the top of the group with some margin

        return QPointF(x, y)

    def draw(self, painter: QPainter, position: QPointF) -> None:
        """
        Draw the floating menu.

        Args:
            painter: The QPainter to draw with
            position: The position for the top-left corner of the menu
        """
        if not self.visible:
            return

        # Get colors from config
        bg_color_text = config.get_color(
            "bridge.floating_menu.background",
            "rgba(60, 60, 60, 220)",
        )
        bg_color = parse_rgba(bg_color_text)
        text_color = QColor(config.get_color("bridge.floating_menu.text", "#FFFFFF"))
        button_bg = QColor(
            config.get_color("bridge.floating_menu.button.background", "#505050")
        )
        button_hover_bg = QColor(
            config.get_color("bridge.floating_menu.button.hover", "#606060")
        )
        button_text = QColor(
            config.get_color("bridge.floating_menu.button.text", "#FFFFFF")
        )

        # Get border color based on group type
        if hasattr(self, "group_type") and self.group_type == "source":
            button_border = QColor(
                config.get_color("bridge.floating_menu.source_border", "#FF5080")
            )
        else:  # target or default
            button_border = QColor(
                config.get_color("bridge.floating_menu.target_border", "#FFA500")
            )

        # Save current painter state
        painter.save()

        # Draw menu background with rounded corners
        menu_rect = QRectF(position.x(), position.y(), self.width, self.height)

        # Create a path for rounded rectangle
        path = QPainterPath()
        path.addRoundedRect(menu_rect, 8, 8)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillPath(path, bg_color)

        # Draw menu border
        painter.setPen(QPen(button_border, 1))
        painter.drawPath(path)

        # Set font for text
        painter.setFont(self.font)
        painter.setPen(text_color)

        # Draw title
        title_y = position.y() + self.padding + self.font_metrics.height()
        painter.drawText(
            QRectF(position.x(), position.y(), self.width, self.height),
            Qt.AlignHCenter | Qt.AlignTop | Qt.TextDontClip,
            self.title,
        )

        # Calculate position text position
        text_y = title_y + self.font_metrics.height() + self.padding
        position_text = self.position_strings.get(
            self.highlight_position,
            self.position_strings[BridgeConnector.POS_ROW_FIRST],
        )

        # Draw position text
        text_rect = QRectF(
            position.x() + self.button_size + 2 * self.button_padding,
            text_y - self.font_metrics.height(),
            self.width - 2 * (self.button_size + 2 * self.button_padding),
            self.font_metrics.height(),
        )
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextDontClip, position_text)

        # Draw previous button
        prev_x = position.x() + self.button_padding
        prev_y = text_y - self.font_metrics.height() / 2 - self.button_size / 2
        self.prev_button_rect = QRectF(
            prev_x, prev_y, self.button_size, self.button_size
        )

        # Draw button background
        button_path = QPainterPath()
        button_path.addRoundedRect(self.prev_button_rect, 4, 4)
        painter.fillPath(button_path, button_bg)
        painter.setPen(QPen(button_border, 1))
        painter.drawPath(button_path)

        # Draw button text
        painter.setPen(button_text)
        painter.drawText(self.prev_button_rect, Qt.AlignCenter, self.prev_button_text)

        # Draw next button
        next_x = position.x() + self.width - self.button_size - self.button_padding
        self.next_button_rect = QRectF(
            next_x, prev_y, self.button_size, self.button_size
        )

        # Draw button background
        button_path = QPainterPath()
        button_path.addRoundedRect(self.next_button_rect, 4, 4)
        painter.fillPath(button_path, button_bg)
        painter.setPen(QPen(button_border, 1))
        painter.drawPath(button_path)

        # Draw button text
        painter.setPen(button_text)
        painter.drawText(self.next_button_rect, Qt.AlignCenter, self.next_button_text)

        # Restore painter state
        painter.restore()

    def handle_click(self, point: QPointF) -> Optional[str]:
        """
        Handle click events on the floating menu.

        Args:
            point: The click position

        Returns:
            The new highlight position if a button was clicked, None otherwise
        """
        if not self.visible:
            return None

        if self.prev_button_rect and self.prev_button_rect.contains(point):
            return self.prev_highlight_position()

        if self.next_button_rect and self.next_button_rect.contains(point):
            return self.next_highlight_position()

        return None

    def contains(self, point: QPointF) -> bool:
        """
        Check if the floating menu contains a point.

        Args:
            point: The point to check

        Returns:
            True if the menu contains the point, False otherwise
        """
        if not self.visible:
            return False

        # Calculate menu rect based on the last drawn position
        if hasattr(self, "last_position") and self.last_position:
            menu_rect = QRectF(
                self.last_position.x(), self.last_position.y(), self.width, self.height
            )
            return menu_rect.contains(point)

        return False
