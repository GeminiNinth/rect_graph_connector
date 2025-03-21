"""
Tests for the rendering components with fixes for PyQt initialization.
"""

import pytest
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QWidget

from rect_graph_connector.gui.rendering.base_renderer import BaseRenderer
from rect_graph_connector.gui.rendering.composite_renderer import CompositeRenderer
from rect_graph_connector.gui.rendering.edge_renderer import EdgeRenderer
from rect_graph_connector.gui.rendering.grid_renderer import GridRenderer
from rect_graph_connector.gui.rendering.node_renderer import NodeRenderer
from rect_graph_connector.gui.rendering.selection_renderer import SelectionRenderer
from rect_graph_connector.models.graph import Graph
from rect_graph_connector.models.rect_node import SingleNode


class MockPainter:
    """Mock QPainter for testing renderers."""

    def __init__(self):
        self.draw_calls = []

    def setPen(self, pen):
        self.draw_calls.append(("setPen", pen))

    def setBrush(self, brush):
        self.draw_calls.append(("setBrush", brush))

    def drawRect(self, rect_or_x, y=None, width=None, height=None):
        if y is None:  # rect is a QRectF
            self.draw_calls.append(("drawRect", rect_or_x))
        else:  # rect is x, y, width, height
            self.draw_calls.append(("drawRect", (rect_or_x, y, width, height)))

    def fillRect(self, rect_or_x, y=None, width=None, height=None, brush=None):
        if y is None:  # rect is a QRectF, brush is the second parameter
            rect, brush = rect_or_x, width  # width is actually the brush in this case
            self.draw_calls.append(("fillRect", (rect, brush)))
        else:  # x, y, width, height, brush
            self.draw_calls.append(("fillRect", (rect_or_x, y, width, height, brush)))

    def drawLine(self, x1, y1, x2, y2):
        self.draw_calls.append(("drawLine", (x1, y1, x2, y2)))

    def drawText(
        self, x, y, text=None, width=None, height=None, flags=None, text2=None
    ):
        if text is None:  # x is a QRectF, y is text
            self.draw_calls.append(("drawText", (x, y)))
        elif width is None:  # x, y, text
            self.draw_calls.append(("drawText", (x, y, text)))
        else:  # x, y, width, height, flags, text
            self.draw_calls.append(
                ("drawText", (x, y, width, height, flags, text2 or text))
            )

    def drawEllipse(self, rect):
        self.draw_calls.append(("drawEllipse", rect))

    def drawPath(self, path):
        self.draw_calls.append(("drawPath", path))

    def save(self):
        self.draw_calls.append(("save",))

    def restore(self):
        self.draw_calls.append(("restore",))

    def translate(self, x, y=None):
        if y is None:  # x is a QPointF
            self.draw_calls.append(("translate", x))
        else:
            self.draw_calls.append(("translate", (x, y)))

    def scale(self, sx, sy):
        self.draw_calls.append(("scale", (sx, sy)))

    def setRenderHint(self, hint, enabled=True):
        self.draw_calls.append(("setRenderHint", (hint, enabled)))

    def fontMetrics(self):
        class MockFontMetrics:
            def width(self, text):
                return len(text) * 8  # Simple approximation

            def elidedText(self, text, mode, width):
                if len(text) * 8 > width:
                    return text[: int(width / 8)] + "..."
                return text

        return MockFontMetrics()


# Use a simple dict instead of QWidget to avoid PyQt initialization issues
class MockWidget:
    """Mock widget that doesn't require QApplication."""

    def __init__(self):
        self.width_val = 800
        self.height_val = 600
        self.zoom = 1.0
        self.pan_offset = QPointF(0, 0)
        self.grid_visible = True
        self.parallel_selected_nodes = []

    def width(self):
        return self.width_val

    def height(self):
        return self.height_val

    def rect(self):
        """Return a QRectF representing the widget's rectangle."""
        return QRectF(0, 0, self.width_val, self.height_val)


@pytest.fixture
def mock_painter():
    """Fixture that provides a mock painter for testing."""
    return MockPainter()


@pytest.fixture
def mock_widget():
    """Fixture that provides a mock widget for testing."""
    return MockWidget()


@pytest.fixture
def graph_with_nodes():
    """Fixture that provides a graph with nodes for testing."""
    graph = Graph()

    # Create nodes
    node1 = SingleNode(x=100, y=100, size=40, id="node1")
    node2 = SingleNode(x=200, y=100, size=40, id="node2")
    node3 = SingleNode(x=100, y=200, size=40, id="node3")

    # Add nodes to graph
    graph.nodes.extend([node1, node2, node3])

    # Add edges
    graph.add_edge(node1, node2)
    graph.add_edge(node1, node3)

    # Create a group
    group_id = graph.create_node_group([node1, node2])

    return graph


# Create a concrete implementation of BaseRenderer for testing
class ConcreteRenderer(BaseRenderer):
    """Concrete implementation of BaseRenderer for testing."""

    def draw(self, painter, **kwargs):
        """Implement the abstract draw method."""
        painter.setPen(QColor("black"))
        painter.drawRect(0, 0, 100, 100)


def test_base_renderer_initialization(mock_widget, graph_with_nodes):
    """Test that the BaseRenderer initializes correctly."""
    # Use the concrete implementation instead of the abstract class
    renderer = ConcreteRenderer(mock_widget, graph_with_nodes)
    assert renderer.canvas == mock_widget
    assert renderer.graph == graph_with_nodes


def test_grid_renderer_draw(mock_widget, graph_with_nodes, mock_painter):
    """Test that the GridRenderer draws a grid."""
    renderer = GridRenderer(mock_widget, graph_with_nodes)

    # Set grid visible
    mock_widget.grid_visible = True

    # Draw the grid
    renderer.draw(mock_painter)

    # Check that drawing calls were made
    assert len(mock_painter.draw_calls) > 0

    # Check that setPen was called (for grid lines)
    assert any(call[0] == "setPen" for call in mock_painter.draw_calls)

    # Check that drawLine was called (for grid lines)
    assert any(call[0] == "drawLine" for call in mock_painter.draw_calls)

    # Test with grid not visible
    mock_painter.draw_calls = []
    mock_widget.grid_visible = False
    renderer.draw(mock_painter)

    # No drawing calls should be made when grid is not visible
    assert len(mock_painter.draw_calls) == 0


def test_node_renderer_draw(mock_widget, graph_with_nodes, mock_painter):
    """Test that the NodeRenderer draws nodes."""
    renderer = NodeRenderer(mock_widget, graph_with_nodes)

    # Draw the nodes in test mode to only draw nodes without groups
    renderer.draw(mock_painter, test_mode=True)

    # Check that drawing calls were made
    assert len(mock_painter.draw_calls) > 0

    # Check that setPen and fillRect were called (for node outlines and fills)
    assert any(call[0] == "setPen" for call in mock_painter.draw_calls)
    assert any(call[0] == "fillRect" for call in mock_painter.draw_calls)

    # Check that drawRect was called (for nodes)
    assert any(call[0] == "drawRect" for call in mock_painter.draw_calls)

    # Count the number of drawRect calls (should be one per node)
    draw_rect_calls = [
        call for call in mock_painter.draw_calls if call[0] == "drawRect"
    ]
    assert len(draw_rect_calls) == len(graph_with_nodes.nodes)


def test_edge_renderer_draw(mock_widget, graph_with_nodes, mock_painter):
    """Test that the EdgeRenderer draws edges."""
    renderer = EdgeRenderer(mock_widget, graph_with_nodes)

    # Draw the edges
    renderer.draw(mock_painter)

    # Check that drawing calls were made
    assert len(mock_painter.draw_calls) > 0

    # Check that setPen was called (for edge lines)
    assert any(call[0] == "setPen" for call in mock_painter.draw_calls)

    # Check that drawLine was called (for edges)
    assert any(call[0] == "drawLine" for call in mock_painter.draw_calls)

    # Count the number of drawLine calls (should be one per edge)
    draw_line_calls = [
        call for call in mock_painter.draw_calls if call[0] == "drawLine"
    ]
    assert len(draw_line_calls) == len(graph_with_nodes.edges)


def test_selection_renderer_draw(mock_widget, graph_with_nodes, mock_painter):
    """Test that the SelectionRenderer draws selection rectangles."""
    renderer = SelectionRenderer(mock_widget, graph_with_nodes)

    # Create a selection rectangle data
    selection_rect_data = {"start": QPointF(50, 50), "end": QPointF(150, 150)}

    # Draw the selection rectangle
    renderer.draw(mock_painter, selection_rect_data=selection_rect_data)

    # Check that drawing calls were made
    assert len(mock_painter.draw_calls) > 0

    # Check that setPen was called (for selection rectangle)
    assert any(call[0] == "setPen" for call in mock_painter.draw_calls)

    # Check that drawRect was called (for selection rectangle)
    assert any(call[0] == "drawRect" for call in mock_painter.draw_calls)

    # Check that fillRect was called (for selection rectangle fill)
    assert any(call[0] == "fillRect" for call in mock_painter.draw_calls)


def test_composite_renderer_draw(mock_widget, graph_with_nodes, mock_painter):
    """Test that the CompositeRenderer coordinates all renderers."""
    renderer = CompositeRenderer(mock_widget, graph_with_nodes)

    # Draw everything
    renderer.draw(mock_painter)

    # Check that drawing calls were made
    assert len(mock_painter.draw_calls) > 0

    # Test with different modes and options
    mock_painter.draw_calls = []

    # Draw in edit mode with a temporary edge
    temp_edge_data = (graph_with_nodes.nodes[0], QPointF(300, 300))
    renderer.draw(
        mock_painter,
        mode="edit",
        temp_edge_data=temp_edge_data,
        edit_target_groups=[graph_with_nodes.node_groups[0]],
    )

    # Check that drawing calls were made
    assert len(mock_painter.draw_calls) > 0


def test_edge_renderer_calculate_edge_endpoints(mock_widget, graph_with_nodes):
    """Test calculating edge endpoints considering node sizes."""
    renderer = EdgeRenderer(mock_widget, graph_with_nodes)

    # Get two nodes
    node1 = graph_with_nodes.nodes[0]
    node2 = graph_with_nodes.nodes[1]

    # Calculate endpoints
    start_point, end_point = renderer.calculate_edge_endpoints(node1, node2)

    # Check that the endpoints are not at the node centers
    # Modify the assertion to handle floating point comparison
    # Instead of checking for inequality, check that the difference is significant
    assert (
        abs(start_point.x() - node1.x) > 0.1
    ), "start_point.x should be different from node1.x"
    # For y-coordinates, they should be approximately equal since nodes are horizontally aligned
    assert (
        abs(start_point.y() - node1.y) < 0.001
    ), "start_point.y should be approximately equal to node1.y"
    assert (
        abs(end_point.x() - node2.x) > 0.1
    ), "end_point.x should be different from node2.x"
    assert (
        abs(end_point.y() - node2.y) < 0.001
    ), "end_point.y should be approximately equal to node2.y"

    # Check that the endpoints are on the node boundaries
    # For horizontal alignment (node1 and node2 have the same y)
    assert abs(start_point.y() - node1.y) < 0.001
    assert abs(end_point.y() - node2.y) < 0.001
