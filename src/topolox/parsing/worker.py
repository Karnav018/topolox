"""Subprocess entry point for parsing a single file.

This must stay a top-level function so it is picklable by ``ProcessPoolExecutor``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.models.graph import ParseResult


def parse_file(path: str) -> ParseResult:
    """Parse one file into a :class:`ParseResult`.

    Runs inside a worker process and builds/caches its parser in-process
    (tree-sitter parsers are not picklable). Phase 1.
    """
    raise NotImplementedError("Phase 1: worker parse_file")
