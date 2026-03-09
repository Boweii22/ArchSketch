"""Utility functions for ArchSketch."""

import re


def sanitize_id(text: str) -> str:
    """Convert text to a valid identifier for Mermaid diagrams."""
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", text)
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized.strip("_")


def truncate(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
