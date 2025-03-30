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
        Abstract method implementation.
        Actual drawing is handled by draw_background and draw_border.
        """
        # This method is required by BaseRenderer but the logic is split.
        # Depending on usage, it might call both sub-methods or do nothing.
        # For current usage from CanvasView, this can be empty.
        pass
        # Alternatively, if needed elsewhere:
        # self.draw_background(painter)
        # self.draw_border(painter)

    def draw_background(self, painter: QPainter):
        """Draw only the canvas background."""
        viewport_rect = painter.viewport()
        painter.fillRect(viewport_rect, QBrush(self.style.background_color))

    def draw_border(self, painter: QPainter):
        """Draw only the canvas border line."""
        # Save painter state to isolate pen changes
        painter.save()

        viewport_rect = painter.viewport()
        pen = self.style.get_border_pen()
        half_pen_width = pen.widthF() / 2.0
        # Draw slightly inside the viewport for better visibility
        border_rect = QRectF(viewport_rect).adjusted(
            half_pen_width, half_pen_width, -half_pen_width, -half_pen_width
        )

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
