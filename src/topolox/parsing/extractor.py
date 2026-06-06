"""Extract symbols and edges from a parsed file using tree-sitter queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.models.graph import ParseResult


class SymbolExtractor:
    """Run tree-sitter ``.scm`` queries over a file to produce nodes/edges."""

    def __init__(self, language: str) -> None:
        self._language = language

    def extract(self, path: str, source: bytes) -> ParseResult:
        """Extract a :class:`ParseResult` from ``source``. Phase 1."""
        raise NotImplementedError("Phase 1: symbol extraction")
