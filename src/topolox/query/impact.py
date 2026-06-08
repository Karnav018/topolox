"""Symbol-level blast radius — the downstream impact of changing one symbol.

Where :class:`~topolox.query.blast_radius.BlastRadiusService` works at file
granularity (who imports this file), this traverses the resolved call graph: who
*transitively calls* a function/method, and who *subclasses* a class. The result
is the precise set of symbols, files, and tests a change could reach.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import SymbolImpact, SymbolRef
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

# Who depends on this symbol: callers (calls) and subclasses (inherits).
_DEPENDENTS = (
    "MATCH (src:Symbol)-[r:Rel]->(s:Symbol {id: $id}) "
    "WHERE src.path <> '' AND r.kind IN ['calls', 'inherits'] "
    "RETURN DISTINCT src.id AS id, src.name AS name, src.qualified_name AS qualified_name, "
    "src.kind AS kind, src.path AS path, src.start_line AS start_line"
)


def _is_test(path: str) -> bool:
    lower = path.lower()
    return "test" in lower or "spec" in lower


class SymbolImpactService:
    """Trace the transitive callers/subclasses of a symbol through the call graph."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def analyze(self, name: str, *, path: str | None = None, max_depth: int = 4) -> SymbolImpact:
        """Return the symbols, files, and tests that transitively depend on ``name``."""
        if path:
            seeds = self._graph.query(_MATCH_IN_FILE, {"q": name, "path": path})
        else:
            seeds = self._graph.query(_MATCH, {"q": name})

        seed_ids = {str(row["id"]) for row in seeds}
        impacted: dict[str, SymbolRef] = {}
        seen = set(seed_ids)
        frontier = set(seed_ids)
        depth = 0
        while frontier and depth < max_depth:
            depth += 1
            nxt: set[str] = set()
            for sid in frontier:
                for row in self._graph.query(_DEPENDENTS, {"id": sid}):
                    rid = str(row["id"])
                    if rid in seed_ids:
                        continue
                    if rid not in impacted:
                        impacted[rid] = SymbolRef(
                            id=rid,
                            name=str(row.get("name") or ""),
                            qualified_name=str(row.get("qualified_name") or ""),
                            kind=str(row.get("kind") or ""),
                            path=str(row.get("path") or ""),
                            start_line=as_int(row.get("start_line")),
                        )
                    if rid not in seen:
                        seen.add(rid)
                        nxt.add(rid)
            frontier = nxt

        symbols = sorted(impacted.values(), key=lambda r: (r.path, r.start_line))
        files = sorted({r.path for r in symbols if r.path})
        tests = [f for f in files if _is_test(f)]
        return SymbolImpact(
            symbol=name,
            matched=[str(row["qualified_name"]) for row in seeds],
            impacted_symbols=symbols,
            impacted_files=files,
            impacted_tests=tests,
            max_depth=depth,
        )
