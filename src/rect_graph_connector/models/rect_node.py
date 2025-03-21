"""
This module provides backward compatibility for the SingleNode class.
It re-exports the RectangleNode class as SingleNode for compatibility with existing code.
"""

from .node import RectangleNode, node_from_dict

# For backward compatibility, SingleNode is now just an alias for RectangleNode
SingleNode = RectangleNode

# Override the from_dict classmethod to maintain backward compatibility
SingleNode.from_dict = node_from_dict
