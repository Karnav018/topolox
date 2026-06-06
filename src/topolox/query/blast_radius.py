"""Blast-radius simulation — the downstream impact of a change."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from topolox.models.query import BlastRadiusReport

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

_IMPORTERS = "MATCH (src)-[r:Rel {kind: $kind}]->(t:Symbol {id: $id}) RETURN DISTINCT src.id AS id"

_DEFINED = (
    "MATCH (s:Symbol {path: $path}) RETURN s.qualified_name AS qualified_name, s.kind AS kind"
)


def _is_test(path: str) -> bool:
    lower = path.lower()
    return "test" in lower or lower.endswith("_test.py")


class BlastRadiusService:
    """Trace the downstream impact of changing one or more files."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def simulate(self, changed: Sequence[str], *, max_depth: int = 3) -> BlastRadiusReport:
        """Return the transitive set of files/tests that import ``changed`` (by file id)."""
        changed_set = set(changed)
        frontier: set[str] = set(changed)
        impacted_files: set[str] = set()
        impacted_tests: set[str] = set()
        seen: set[str] = set(changed)
        depth = 0
        while frontier and depth < max_depth:
            depth += 1
            next_frontier: set[str] = set()
            for file_id in frontier:
                for row in self._graph.query(_IMPORTERS, {"id": file_id, "kind": "imports"}):
                    importer = str(row["id"])
                    if importer in impacted_files or importer in changed_set:
                        continue
                    impacted_files.add(importer)
                    if _is_test(importer):
                        impacted_tests.add(importer)
                    if importer not in seen:
                        seen.add(importer)
                        next_frontier.add(importer)
            frontier = next_frontier

        impacted_symbols: set[str] = set()
        for path in changed:
            for row in self._graph.query(_DEFINED, {"path": path}):
                if str(row["kind"]) != "file":
                    impacted_symbols.add(str(row["qualified_name"]))

        return BlastRadiusReport(
            changed=list(changed),
            impacted_files=sorted(impacted_files),
            impacted_tests=sorted(impacted_tests),
            impacted_symbols=sorted(impacted_symbols),
            max_depth=depth,
        )
