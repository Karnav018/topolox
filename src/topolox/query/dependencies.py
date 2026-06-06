"""Dependency-map queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import DependencyMap, ScoredSymbol

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

_QUALNAME = "MATCH (s:Symbol {id: $id}) RETURN s.qualified_name AS qualified_name"

_DEPENDENCIES = (
    "MATCH (s:Symbol {id: $id})-[r:Rel {kind: $kind}]->(t) "
    "RETURN DISTINCT t.id AS id, t.name AS name, t.path AS path"
)

_DEPENDENTS = (
    "MATCH (src)-[r:Rel {kind: $kind}]->(t:Symbol {id: $qual}) "
    "RETURN DISTINCT src.id AS id, src.name AS name, src.path AS path"
)


def _to_symbol(row: dict[str, object]) -> ScoredSymbol:
    rid = str(row.get("id") or "")
    name = row.get("name")
    path = row.get("path")
    return ScoredSymbol(
        id=rid,
        path=str(path) if path else "",
        name=str(name) if name else rid,
        score=1.0,
    )


class DependencyService:
    """Compute dependencies and dependents for a file or symbol."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def of_file(self, path: str, *, depth: int = 1) -> DependencyMap:
        """Return the dependency map for ``path`` (module-level for Phase 1)."""
        qual_rows = self._graph.query(_QUALNAME, {"id": path})
        qualified = str(qual_rows[0]["qualified_name"]) if qual_rows else path
        dependencies = self._graph.query(_DEPENDENCIES, {"id": path, "kind": "imports"})
        dependents = self._graph.query(_DEPENDENTS, {"qual": qualified, "kind": "imports"})
        return DependencyMap(
            root=path,
            dependencies=[_to_symbol(row) for row in dependencies],
            dependents=[_to_symbol(row) for row in dependents],
        )
