"""Call-graph queries — who calls a function, and what it calls.

Built on resolved ``calls`` edges (see :mod:`topolox.graph.resolve`), so results
are the deterministic subset that could be linked to a concrete symbol; ambiguous
or external calls are intentionally omitted rather than guessed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import CallReport, SymbolRef
from topolox.query.scoring import as_int

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

_CALLABLE_KINDS = "['function', 'method', 'class']"

_MATCH = (
    f"MATCH (s:Symbol) WHERE s.path <> '' AND s.kind IN {_CALLABLE_KINDS} "
    "AND (s.name = $q OR s.qualified_name = $q OR s.id = $q) "
    "RETURN s.id AS id, s.qualified_name AS qualified_name"
)

_MATCH_IN_FILE = (
    f"MATCH (s:Symbol {{path: $path}}) WHERE s.kind IN {_CALLABLE_KINDS} "
    "AND (s.name = $q OR s.qualified_name = $q OR s.id = $q) "
    "RETURN s.id AS id, s.qualified_name AS qualified_name"
)

_CALLEES = (
    "MATCH (s:Symbol {id: $id})-[r:Rel {kind: 'calls'}]->(t:Symbol) WHERE t.path <> '' "
    "RETURN DISTINCT t.id AS id, t.name AS name, t.qualified_name AS qualified_name, "
    "t.kind AS kind, t.path AS path, t.start_line AS start_line"
)

_CALLERS = (
    "MATCH (src:Symbol)-[r:Rel {kind: 'calls'}]->(s:Symbol {id: $id}) WHERE src.path <> '' "
    "RETURN DISTINCT src.id AS id, src.name AS name, src.qualified_name AS qualified_name, "
    "src.kind AS kind, src.path AS path, src.start_line AS start_line"
)


def _ref(row: dict[str, object]) -> SymbolRef:
    return SymbolRef(
        id=str(row.get("id") or ""),
        name=str(row.get("name") or ""),
        qualified_name=str(row.get("qualified_name") or ""),
        kind=str(row.get("kind") or ""),
        path=str(row.get("path") or ""),
        start_line=as_int(row.get("start_line")),
    )


class CallGraphService:
    """Resolve a symbol by name, then report its callers or callees."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def callees(self, name: str, *, path: str | None = None) -> CallReport:
        """Functions/methods/classes that ``name`` calls."""
        return self._report(name, path, _CALLEES, "callees")

    def callers(self, name: str, *, path: str | None = None) -> CallReport:
        """Functions/methods that call ``name``."""
        return self._report(name, path, _CALLERS, "callers")

    def _report(self, name: str, path: str | None, cypher: str, direction: str) -> CallReport:
        if path:
            matches = self._graph.query(_MATCH_IN_FILE, {"q": name, "path": path})
        else:
            matches = self._graph.query(_MATCH, {"q": name})

        neighbors: dict[str, SymbolRef] = {}
        for match in matches:
            for row in self._graph.query(cypher, {"id": str(match["id"])}):
                ref = _ref(row)
                neighbors.setdefault(ref.id, ref)

        return CallReport(
            symbol=name,
            direction=direction,
            matched=[str(m["qualified_name"]) for m in matches],
            neighbors=sorted(neighbors.values(), key=lambda r: (r.path, r.start_line)),
        )
