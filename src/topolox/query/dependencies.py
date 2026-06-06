"""Dependency-map queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore
    from topolox.models.query import DependencyMap


class DependencyService:
    """Compute dependencies and dependents for a file or symbol."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def of_file(self, path: str, *, depth: int = 1) -> DependencyMap:
        """Return the dependency map for ``path``. Phase 2."""
        raise NotImplementedError("Phase 2: dependency map")
