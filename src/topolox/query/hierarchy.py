"""Class-hierarchy queries — the direct supertypes and subtypes of a class,
from resolved ``inherits`` edges.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import ClassHierarchy, SymbolRef
from topolox.query.scoring import as_int

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

_MATCH = (
    "MATCH (s:Symbol {kind: 'class'}) WHERE s.path <> '' "
    "AND (s.name = $q OR s.qualified_name = $q OR s.id = $q) "
    "RETURN s.id AS id, s.qualified_name AS qualified_name"
)

_MATCH_IN_FILE = (
    "MATCH (s:Symbol {path: $path, kind: 'class'}) "
    "WHERE (s.name = $q OR s.qualified_name = $q OR s.id = $q) "
    "RETURN s.id AS id, s.qualified_name AS qualified_name"
)

_SUPERTYPES = (
    "MATCH (s:Symbol {id: $id})-[r:Rel {kind: 'inherits'}]->(t:Symbol) WHERE t.path <> '' "
    "RETURN DISTINCT t.id AS id, t.name AS name, t.qualified_name AS qualified_name, "
    "t.kind AS kind, t.path AS path, t.start_line AS start_line"
)

_SUBTYPES = (
    "MATCH (sub:Symbol)-[r:Rel {kind: 'inherits'}]->(s:Symbol {id: $id}) WHERE sub.path <> '' "
    "RETURN DISTINCT sub.id AS id, sub.name AS name, sub.qualified_name AS qualified_name, "
    "sub.kind AS kind, sub.path AS path, sub.start_line AS start_line"
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


class HierarchyService:
    """Resolve a class by name and report its direct supertypes and subtypes."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def of_class(self, name: str, *, path: str | None = None) -> ClassHierarchy:
        """Return the direct base classes and direct subclasses of ``name``."""
        if path:
            matches = self._graph.query(_MATCH_IN_FILE, {"q": name, "path": path})
        else:
            matches = self._graph.query(_MATCH, {"q": name})

        supertypes: dict[str, SymbolRef] = {}
        subtypes: dict[str, SymbolRef] = {}
        for match in matches:
            mid = str(match["id"])
            for row in self._graph.query(_SUPERTYPES, {"id": mid}):
                ref = _ref(row)
                supertypes.setdefault(ref.id, ref)
            for row in self._graph.query(_SUBTYPES, {"id": mid}):
                ref = _ref(row)
                subtypes.setdefault(ref.id, ref)

        return ClassHierarchy(
            symbol=name,
            matched=[str(m["qualified_name"]) for m in matches],
            supertypes=sorted(supertypes.values(), key=lambda r: (r.path, r.start_line)),
            subtypes=sorted(subtypes.values(), key=lambda r: (r.path, r.start_line)),
        )
