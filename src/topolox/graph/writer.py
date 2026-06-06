"""Translate :class:`ParseResult` fragments into idempotent Kùzu upserts."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore
    from topolox.models.graph import ParseResult


def write_fragment(store: GraphStore, fragment: ParseResult) -> None:
    """Upsert a single parsed file's nodes and edges into the graph. Phase 1."""
    raise NotImplementedError("Phase 1: graph writer")
