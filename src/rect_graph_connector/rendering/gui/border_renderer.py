"""
Border renderer for drawing canvas border.
"""

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QBrush, QPainter

from ...models.view_state_model import ViewStateModel
from .base_renderer import BaseRenderer
from .styles.border_style import BorderStyle


class BorderRenderer(BaseRenderer):
    """
    Renderer for drawing the canvas border and background.

    This class handles rendering of the canvas border and background,
    providing visual boundaries for the drawing area.
    """

    def __init__(self, view_state: ViewStateModel, style: BorderStyle = None):
        """
        Initialize the border renderer.

        Args:
            view_state (ViewStateModel): The view state model
            style (BorderStyle, optional): The style object for this renderer
        """
        super().__init__(view_state, style or BorderStyle())

    def draw(self, painter: QPainter, **kwargs):
        """
        Draw the canvas border and background.

        Args:
            painter (QPainter): The painter to use for drawing
            **kwargs: Additional drawing parameters
        """
        # Save painter state
        painter.save()

        # Get the viewport rectangle
        viewport_rect = painter.viewport()

        # Draw background
        painter.fillRect(viewport_rect, QBrush(self.style.background_color))

        # Draw border directly on the viewport edges
        # Adjust slightly inwards by half the pen width for visual alignment
        pen = self.style.get_border_pen()
        half_pen_width = pen.widthF() / 2.0
        border_rect = QRectF(viewport_rect).adjusted(
            half_pen_width, half_pen_width, -half_pen_width, -half_pen_width
        )

        # Draw border
        painter.setPen(pen)
        painter.drawRect(border_rect)

        # Restore painter state
        painter.restore()

    def get_content_rect(self, viewport_rect) -> QRectF:
        """
        Calculate the content rectangle inside the border.

        Args:
            viewport_rect: The viewport rectangle

        Returns:
            QRectF: The content rectangle
        """
        margin = self.style.margin
        return QRectF(
            viewport_rect.x() + margin,
            viewport_rect.y() + margin,
            viewport_rect.width() - 2 * margin,
            viewport_rect.height() - 2 * margin,
        )
