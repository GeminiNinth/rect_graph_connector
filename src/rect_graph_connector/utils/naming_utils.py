"""
Node naming utilities for the rect_graph_connector application.

This module provides centralized logic for naming and renaming nodes with
consistent patterns and behavior. It handles cases like duplicate names,
incrementing suffixes, and ensures spacing consistency.
"""

import re
from typing import List, Optional, Dict, Any, Tuple


def get_base_name_and_suffix(name: str) -> Tuple[str, Optional[int]]:
    """
    Parse a name to extract the base name and numeric suffix (if present).

    Args:
        name: The node name to parse

    Returns:
        A tuple containing (base_name, suffix)
        If no suffix is present, suffix will be None
    """
    # Match both patterns: "name(1)" and "name (1)"
    match = re.match(r"^(.*?)(?:\s*\((\d+)\))$", name)
    if match:
        base_name, suffix_str = match.groups()
        return base_name, int(suffix_str)
    return name, None


def generate_unique_name(base_name: str, existing_names: List[str]) -> str:
    """
    Generate a unique name based on a base name and a list of existing names.

    Args:
        base_name: The base name to use
        existing_names: A list of existing names to check against

    Returns:
        A unique name in the format "base_name (n)" where n is the smallest
        positive integer that makes the name unique
    """
    # Remove any existing suffix
    clean_base_name, _ = get_base_name_and_suffix(base_name)

    # If the clean base name is not in existing names, return it
    if clean_base_name not in existing_names:
        return clean_base_name

    # Parse all existing names with the same base
    relevant_names = [
        name
        for name in existing_names
        if get_base_name_and_suffix(name)[0] == clean_base_name
    ]

    # Extract all suffixes
    suffixes = [get_base_name_and_suffix(name)[1] for name in relevant_names]
    suffixes = [s for s in suffixes if s is not None]

    # Find the smallest unused suffix
    if not suffixes:
        next_suffix = 1
    else:
        # Create a set of used suffixes
        used_suffixes = set(suffixes)

        # Find the smallest unused suffix starting from 1
        next_suffix = 1
        while next_suffix in used_suffixes:
            next_suffix += 1

    # Ensure consistent spacing format with a space before the parenthesis
    return f"{clean_base_name} ({next_suffix})"


def rename_node(
    current_name: str,
    new_name: str,
    existing_names: List[str],
    allow_duplicates: bool = False,
) -> str:
    """
    Rename a node with proper handling of suffixes and uniqueness constraints.

    Args:
        current_name: The current name of the node
        new_name: The requested new name
        existing_names: List of all existing names (excluding current_name)
        allow_duplicates: If True, allows duplicate names without adding suffixes

    Returns:
        The final name to use, with uniqueness enforced only if allow_duplicates is False
    """
    # If the new name is the same as the current name, return it without changes
    if new_name == current_name:
        return current_name

    # If duplicates are allowed, return the new name as-is
    if allow_duplicates:
        return new_name

    # If the new name already exists, generate a unique name
    if new_name in existing_names:
        return generate_unique_name(new_name, existing_names)

    return new_name


def generate_unique_name_if_needed(
    name: str, existing_names: List[str], allow_duplicates: bool = False
) -> str:
    """
    Generate a unique name only if duplicates are not allowed.

    Args:
        name: The base name to use
        existing_names: A list of existing names to check against
        allow_duplicates: If True, allows duplicate names without adding suffixes

    Returns:
        Either the original name (if duplicates allowed or name is unique)
        or a unique name with a numeric suffix
    """
    if allow_duplicates or name not in existing_names:
        return name
    return generate_unique_name(name, existing_names)


def extract_number_from_name(name: str) -> int:
    """
    Extract the numeric suffix from a node name if present, otherwise return 0.

    Args:
        name: The node name

    Returns:
        The numeric suffix as an integer, or 0 if not present
    """
    _, suffix = get_base_name_and_suffix(name)
    return suffix if suffix is not None else 0
