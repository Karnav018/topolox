"""Blast-radius simulation — the downstream impact of a change."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from topolox.models.query import BlastRadiusReport

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

_QUALNAME = "MATCH (s:Symbol {id: $id}) RETURN s.qualified_name AS qualified_name"

_IMPORTERS = (
    "MATCH (src)-[r:Rel {kind: $kind}]->(t:Symbol {id: $qual}) "
    "RETURN DISTINCT src.id AS id, src.qualified_name AS qualified_name"
)

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
        """Return the transitive set of files/tests that depend on ``changed``."""
        frontier: set[str] = set()
        for path in changed:
            rows = self._graph.query(_QUALNAME, {"id": path})
            if rows:
                frontier.add(str(rows[0]["qualified_name"]))

        impacted_files: set[str] = set()
        impacted_tests: set[str] = set()
        seen_quals: set[str] = set(frontier)
        depth = 0
        while frontier and depth < max_depth:
            depth += 1
            next_frontier: set[str] = set()
            for qual in frontier:
                for row in self._graph.query(_IMPORTERS, {"qual": qual, "kind": "imports"}):
                    file_id = str(row["id"])
                    if file_id in impacted_files or file_id in changed:
                        continue
                    impacted_files.add(file_id)
                    if _is_test(file_id):
                        impacted_tests.add(file_id)
                    importer_qual = str(row["qualified_name"] or "")
                    if importer_qual and importer_qual not in seen_quals:
                        seen_quals.add(importer_qual)
                        next_frontier.add(importer_qual)
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
