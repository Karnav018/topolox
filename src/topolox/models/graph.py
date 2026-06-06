"""The parser's output contract — must be picklable to cross process boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from topolox.models.edges import Edge
from topolox.models.nodes import SymbolNode


@dataclass(slots=True, frozen=True)
class ParseResult:
    """Nodes and edges extracted from a single source file."""

    path: str
    language: str
    nodes: tuple[SymbolNode, ...] = ()
    edges: tuple[Edge, ...] = ()
    content_hash: str = ""
    error: str | None = None
