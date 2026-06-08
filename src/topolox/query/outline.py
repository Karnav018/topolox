"""File outline — a file's symbols (classes, functions, methods) and their shape,
so an agent grasps a file without reading it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import FileOutline, OutlineSymbol
from topolox.query.scoring import as_int

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

_SYMBOLS = (
    "MATCH (s:Symbol {path: $path}) WHERE s.kind <> 'file' "
    "RETURN s.name AS name, s.qualified_name AS qualified_name, s.kind AS kind, "
    "s.signature AS signature, s.docstring AS docstring, "
    "s.start_line AS start_line, s.end_line AS end_line "
    "ORDER BY s.start_line"
)

_LANGUAGE = "MATCH (s:Symbol {path: $path, kind: 'file'}) RETURN s.language AS language LIMIT 1"

_SUMMARY_CHARS = 120


def _summary(docstring: object) -> str | None:
    if not docstring:
        return None
    first = str(docstring).strip().splitlines()
    if not first:
        return None
    line = first[0].strip()
    return line[: _SUMMARY_CHARS - 1] + "…" if len(line) > _SUMMARY_CHARS else line


class OutlineService:
    """Return the symbol outline of a single file."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def of_file(self, path: str) -> FileOutline:
        """Return the ordered outline of symbols defined in ``path``."""
        lang_rows = self._graph.query(_LANGUAGE, {"path": path})
        language = str(lang_rows[0].get("language") or "") if lang_rows else ""

        symbols = [
            OutlineSymbol(
                name=str(row.get("name") or ""),
                qualified_name=str(row.get("qualified_name") or ""),
                kind=str(row.get("kind") or ""),
                signature=str(row["signature"]) if row.get("signature") else None,
                docstring=_summary(row.get("docstring")),
                start_line=as_int(row.get("start_line")),
                end_line=as_int(row.get("end_line")),
            )
            for row in self._graph.query(_SYMBOLS, {"path": path})
        ]
        return FileOutline(path=path, language=language, symbols=symbols)
