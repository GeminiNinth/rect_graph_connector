"""
This module handles node connectivity operations for the graph.

It provides functions for establishing connections between nodes
in various patterns like 4-directional connections.
"""

from typing import Dict, List, Tuple

from .graph import Graph
from .rect_node import RectNode


def connect_nodes_in_4_directions(graph: Graph, nodes: List[RectNode]) -> None:
    """
    Connect all nodes in a list in 4 directions (up, down, left, right).

    Each node gets connected to its adjacent neighbors based on their
    row and column positions in the grid.

    Notes:
        - Connections are only created between nodes that belong to the same NodeGroup.
        - This prevents unintended connections between different NodeGroups.

    Args:
        graph (Graph): The graph where connections will be added
        nodes (List[RectNode]): The list of nodes to connect
    """
    if not nodes:
        return

    # Create a grid structure: store nodes with row and col as keys
    grid = {}
    # Create a mapping of nodes to their groups
    node_to_group = {}

    # Populate node_to_group mapping
    for node in nodes:
        grid[(node.row, node.col)] = node
        # Find the group this node belongs to
        group = graph.get_group_for_node(node)
        if group:
            node_to_group[node.id] = group.id

    # For each node, connect to adjacent nodes in four directions (up, down, left, right)
    for node in nodes:
        # Get the group of the current node
        node_group_id = node_to_group.get(node.id)

        # Skip nodes that don't belong to any group
        if node_group_id is None:
            continue

        # Calculate the coordinates of adjacent cells in four directions
        neighbors = [
            (node.row - 1, node.col),  # up
            (node.row + 1, node.col),  # down
            (node.row, node.col - 1),  # left
            (node.row, node.col + 1),  # right
        ]

        # Connect with adjacent nodes
        for neighbor_pos in neighbors:
            if neighbor_pos in grid:
                neighbor_node = grid[neighbor_pos]
                neighbor_group_id = node_to_group.get(neighbor_node.id)

                # Only connect if both nodes belong to the same group
                if (
                    neighbor_group_id is not None
                    and node_group_id == neighbor_group_id
                    and not graph.has_edge(node, neighbor_node)
                ):
                    graph.add_edge(node, neighbor_node)


def connect_nodes_in_8_directions(graph: Graph, nodes: List[RectNode]) -> None:
    """
    Connect all nodes in a list in 8 directions (including diagonals).

    Each node gets connected to its adjacent neighbors based on their
    row and column positions in the grid, including diagonal connections.

    Notes:
        - Connections are only created between nodes that belong to the same NodeGroup.
        - This prevents unintended connections between different NodeGroups.

    Args:
        graph (Graph): The graph where connections will be added
        nodes (List[RectNode]): The list of nodes to connect
    """
    if not nodes:
        return

    # Create a grid structure: store nodes with row and col as keys
    grid = {}
    # Create a mapping of nodes to their groups
    node_to_group = {}

    # Populate node_to_group mapping
    for node in nodes:
        grid[(node.row, node.col)] = node
        # Find the group this node belongs to
        group = graph.get_group_for_node(node)
        if group:
            node_to_group[node.id] = group.id

    # For each node, connect to adjacent nodes in eight directions
    for node in nodes:
        # Get the group of the current node
        node_group_id = node_to_group.get(node.id)

        # Skip nodes that don't belong to any group
        if node_group_id is None:
            continue

        # Calculate the coordinates of adjacent cells in eight directions
        neighbors = [
            (node.row - 1, node.col),  # up
            (node.row + 1, node.col),  # down
            (node.row, node.col - 1),  # left
            (node.row, node.col + 1),  # right
            (node.row - 1, node.col - 1),  # up-left
            (node.row - 1, node.col + 1),  # up-right
            (node.row + 1, node.col - 1),  # down-left
            (node.row + 1, node.col + 1),  # down-right
        ]

        # Connect with adjacent nodes
        for neighbor_pos in neighbors:
            if neighbor_pos in grid:
                neighbor_node = grid[neighbor_pos]
                neighbor_group_id = node_to_group.get(neighbor_node.id)

                # Only connect if both nodes belong to the same group
                if (
                    neighbor_group_id is not None
                    and node_group_id == neighbor_group_id
                    and not graph.has_edge(node, neighbor_node)
                ):
                    graph.add_edge(node, neighbor_node)


from ..config import config


def delete_edge_at_position(
    graph: Graph, point, threshold: float = None, tolerance: float = None
) -> bool:
    """
    Delete an edge that is close to the specified position.
    Only considers the visible part of edges between node boundaries.

    Args:
        graph (Graph): The graph containing the edges
        point: Either a QPointF object or a tuple of (x, y) coordinates
        threshold (float): Maximum distance to consider an edge as close
        tolerance (float): Alias for threshold, for backward compatibility

    Returns:
        bool: True if an edge was deleted, False otherwise
    """
    # Handle QPointF or tuple input
    if hasattr(point, "x") and hasattr(point, "y"):
        px = point.x()
        py = point.y()
    else:
        px, py = point

    # For backward compatibility with tests that use tolerance parameter
    if tolerance is not None:
        threshold = tolerance
    # Get default thresholds from configuration file
    if threshold is None:
        threshold = config.get_dimension("edge.detection_threshold", 10.0)
    # Find the closest edge
    closest_edge = None
    min_distance = float("inf")

    for source_id, target_id in graph.edges:
        # Get source and target nodes
        source_node = None
        target_node = None

        try:
            source_node = next(n for n in graph.nodes if n.id == source_id)
            target_node = next(n for n in graph.nodes if n.id == target_id)
        except StopIteration:
            continue

        if source_node and target_node:
            # Calculate actual edge endpoints considering node sizes
            (start_x, start_y), (end_x, end_y) = calculate_edge_endpoints(
                source_node, target_node
            )

            # Calculate distance from point to line segment (edge)
            distance = point_to_line_distance(px, py, start_x, start_y, end_x, end_y)

            if distance < min_distance:
                min_distance = distance
                closest_edge = (source_id, target_id)

    # Delete the edge if it's close enough
    if closest_edge and min_distance <= threshold:
        graph.edges.remove(closest_edge)
        return True

    return False


def point_to_line_distance(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    """
    Calculate the minimum distance from a point to a line segment.

    Args:
        px, py: Point coordinates
        x1, y1: Line segment start coordinates
        x2, y2: Line segment end coordinates

    Returns:
        float: The minimum distance from the point to the line segment
    """
    # Line length squared
    line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2

    # If the line is actually a point
    if line_length_sq == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

    # Calculate projection of point onto line
    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))

    # Calculate closest point on line segment
    closest_x = x1 + t * (x2 - x1)
    closest_y = y1 + t * (y2 - y1)

    # Return distance to closest point
    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5


def line_segments_intersect(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    x3: float,
    y3: float,
    x4: float,
    y4: float,
) -> bool:
    """
    Check if two line segments intersect.

    Args:
        x1, y1: First line segment start point
        x2, y2: First line segment end point
        x3, y3: Second line segment start point
        x4, y4: Second line segment end point

    Returns:
        bool: True if the line segments intersect, False otherwise
    """
    # Calculate the denominator
    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0:  # Lines are parallel
        return False

    # Calculate ua and ub
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

    # Return true if the intersection is within both line segments
    return (0 <= ua <= 1) and (0 <= ub <= 1)


def calculate_edge_endpoints(
    source_node: RectNode, target_node: RectNode
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Calculate the actual visual endpoints of an edge considering node sizes.

    Args:
        source_node (RectNode): The source node
        target_node (RectNode): The target node

    Returns:
        Tuple[Tuple[float, float], Tuple[float, float]]: ((start_x, start_y), (end_x, end_y))
    """
    # Calculate direction vector
    dx = target_node.x - source_node.x
    dy = target_node.y - source_node.y
    length = (dx * dx + dy * dy) ** 0.5

    if length == 0:
        return ((source_node.x, source_node.y), (target_node.x, target_node.y))

    # Normalize direction vector
    dx /= length
    dy /= length

    # Calculate actual endpoints considering node sizes
    start_x = source_node.x + dx * source_node.size / 2
    start_y = source_node.y + dy * source_node.size / 2
    end_x = target_node.x - dx * target_node.size / 2
    end_y = target_node.y - dy * target_node.size / 2

    return ((start_x, start_y), (end_x, end_y))


def connect_all_for_one_edge_selection(
    graph: Graph, source_nodes: List[RectNode], target_node: RectNode
) -> None:
    """
    Connect multiple source nodes to a single target node.

    This function creates edges from all source nodes to the target node.
    It's used by the All-For-One connection mode to establish multiple connections simultaneously.

    Args:
        graph (Graph): The graph where connections will be added
        source_nodes (List[RectNode]): List of source nodes to connect from
        target_node (RectNode): The target node to connect to
    """
    if not source_nodes or not target_node:
        return

    # Create connections from each source node to the target node
    for source_node in source_nodes:
        # Skip self-connections
        if source_node != target_node and not graph.has_edge(source_node, target_node):
            graph.add_edge(source_node, target_node)


def find_intersecting_edges(
    graph: Graph, path_points: List[Tuple[float, float]], target_groups=None
) -> List[Tuple[str, str]]:
    """
    Find all edges that intersect with a given path.
    Only considers the visible part of edges between node boundaries.
    If target_groups is provided, only returns edges where at least one endpoint
    belongs to one of the target groups.

    Args:
        graph (Graph): The graph containing the edges
        path_points (List[Tuple[float, float]]): List of points forming the path
        target_groups (List, optional): List of target NodeGroups to filter edges by

    Returns:
        List[Tuple[str, str]]: List of edge tuples (source_id, target_id) that intersect with the path
    """
    intersecting_edges = []

    # Need at least 2 points to form a line segment
    if len(path_points) < 2:
        return intersecting_edges

    # Check each edge against each path segment
    for source_id, target_id in graph.edges:
        # Get source and target nodes
        try:
            source_node = next(n for n in graph.nodes if n.id == source_id)
            target_node = next(n for n in graph.nodes if n.id == target_id)
        except StopIteration:
            continue

        # If target_groups is provided, check if at least one endpoint belongs to a target group
        if target_groups:
            source_group = graph.get_group_for_node(source_node)
            target_group = graph.get_group_for_node(target_node)

            # Skip this edge if neither endpoint belongs to a target group
            if source_group not in target_groups and target_group not in target_groups:
                continue

        # Calculate actual edge endpoints considering node sizes
        (start_x, start_y), (end_x, end_y) = calculate_edge_endpoints(
            source_node, target_node
        )

        # Check intersection with each path segment
        for i in range(len(path_points) - 1):
            x1, y1 = path_points[i]
            x2, y2 = path_points[i + 1]

            if line_segments_intersect(
                x1,
                y1,
                x2,
                y2,
                start_x,
                start_y,
                end_x,
                end_y,
            ):
                intersecting_edges.append((source_id, target_id))
                break  # One intersection is enough to mark this edge

    return intersecting_edges
