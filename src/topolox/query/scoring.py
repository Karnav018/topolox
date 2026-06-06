"""Scoring helpers for the query layer.

Traversal/ranking is done in Kùzu Cypher by default; ``networkx`` is added only
if personalized-PageRank-style scoring is needed later.
"""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 characters per token)."""
    return max(1, len(text) // 4)
