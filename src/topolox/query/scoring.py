"""Scoring helpers for the query layer.

Traversal/ranking is done in Kùzu Cypher by default; ``networkx`` is added only
if personalized-PageRank-style scoring is needed later.
"""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 characters per token)."""
    return max(1, len(text) // 4)


def as_int(value: object) -> int:
    """Coerce a graph-query cell (``object``) to ``int``, defaulting to 0."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.lstrip("-").isdigit():
        return int(value)
    return 0
