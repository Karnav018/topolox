"""Dependency-map queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import DependencyMap, ScoredSymbol

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

# Outgoing imports: bare module names this file imports (exclude resolved file links).
_DEPENDENCIES = (
    "MATCH (s:Symbol {id: $id})-[r:Rel {kind: $kind}]->(t) "
    "RETURN DISTINCT t.id AS id, t.name AS name, t.path AS path, t.kind AS kind"
)

# Incoming: files that import this file (via resolved file-id edges).
_DEPENDENTS = (
    "MATCH (src)-[r:Rel {kind: $kind}]->(t:Symbol {id: $id}) "
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
    """Compute dependencies and dependents for a file."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def of_file(self, path: str, *, depth: int = 1) -> DependencyMap:
        """Return the dependency map for ``path``."""
        dep_rows = self._graph.query(_DEPENDENCIES, {"id": path, "kind": "imports"})
        dependencies = [_to_symbol(row) for row in dep_rows if str(row.get("kind") or "") != "file"]
        dependents = [
            _to_symbol(row)
            for row in self._graph.query(_DEPENDENTS, {"id": path, "kind": "imports"})
        ]
        return DependencyMap(root=path, dependencies=dependencies, dependents=dependents)
