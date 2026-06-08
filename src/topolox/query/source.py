"""Read a single symbol's exact source — the precise slice of a file.

Closes the loop from "find the relevant symbol" (prune / search) to "read only
that symbol", instead of pulling the whole file into the agent's context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import SymbolDetail, SymbolSource
from topolox.query.scoring import as_int

if TYPE_CHECKING:
    from pathlib import Path

    from topolox.graph.store import GraphStore

_MATCH = (
    "MATCH (s:Symbol) "
    "WHERE s.kind <> 'file' AND (s.name = $q OR s.qualified_name = $q OR s.id = $q "
    "OR s.qualified_name ENDS WITH $qsuffix) "
    "RETURN s.id AS id, s.name AS name, s.qualified_name AS qualified_name, s.kind AS kind, "
    "s.path AS path, s.language AS language, s.signature AS signature, "
    "s.start_line AS start_line, s.end_line AS end_line "
    "ORDER BY s.path, s.start_line"
)

_MATCH_IN_FILE = (
    "MATCH (s:Symbol {path: $path}) "
    "WHERE s.kind <> 'file' AND (s.name = $q OR s.qualified_name = $q OR s.id = $q "
    "OR s.qualified_name ENDS WITH $qsuffix) "
    "RETURN s.id AS id, s.name AS name, s.qualified_name AS qualified_name, s.kind AS kind, "
    "s.path AS path, s.language AS language, s.signature AS signature, "
    "s.start_line AS start_line, s.end_line AS end_line "
    "ORDER BY s.start_line"
)

_MAX_MATCHES = 5


class SymbolReader:
    """Locate a symbol by name (or qualified name) and return its source."""

    def __init__(self, graph: GraphStore, repo_root: Path) -> None:
        self._graph = graph
        self._repo_root = repo_root

    def read(self, name: str, *, path: str | None = None) -> SymbolSource:
        """Return the matching symbol(s) and the exact source of each.

        ``name`` may be a bare name (``parse``), a qualified name
        (``SymbolExtractor.extract``), or a full symbol id. Pass ``path`` to
        disambiguate when a bare name collides across files.
        """
        qsuffix = "." + name
        if path:
            rows = self._graph.query(_MATCH_IN_FILE, {"q": name, "qsuffix": qsuffix, "path": path})
        else:
            rows = self._graph.query(_MATCH, {"q": name, "qsuffix": qsuffix})

        matches = [self._detail(row) for row in rows[:_MAX_MATCHES]]
        return SymbolSource(query=name, matches=matches)

    def _detail(self, row: dict[str, object]) -> SymbolDetail:
        rel_path = str(row.get("path") or "")
        start = as_int(row.get("start_line"))
        end = as_int(row.get("end_line"))
        signature = row.get("signature")
        return SymbolDetail(
            id=str(row.get("id") or ""),
            name=str(row.get("name") or ""),
            qualified_name=str(row.get("qualified_name") or ""),
            kind=str(row.get("kind") or ""),
            path=rel_path,
            language=str(row.get("language") or ""),
            signature=str(signature) if signature else None,
            start_line=start,
            end_line=end,
            source=self._slice(rel_path, start, end),
        )

    def _slice(self, rel_path: str, start: int, end: int) -> str:
        if not rel_path or start < 1 or end < start:
            return ""
        file_path = self._repo_root / rel_path
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return ""
        return "\n".join(lines[start - 1 : end])
