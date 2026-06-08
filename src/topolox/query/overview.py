"""Repo overview — a fast architectural read on an unfamiliar codebase:
size, language mix, and the hub files everything imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import HubFile, RepoOverview
from topolox.query.scoring import as_int

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

_FILE_COUNT = "MATCH (s:Symbol {kind: 'file'}) RETURN count(s) AS n"

# Exclude file nodes and bare-name placeholders (unresolved imports/calls/bases),
# which carry no path — count only real extracted symbols.
_SYMBOL_COUNT = (
    "MATCH (s:Symbol) WHERE s.kind <> 'file' AND s.path IS NOT NULL AND s.path <> '' "
    "RETURN count(s) AS n"
)

_LANGUAGES = (
    "MATCH (s:Symbol {kind: 'file'}) WHERE s.language <> '' "
    "RETURN s.language AS language, count(s) AS n ORDER BY n DESC"
)

# Hub files = internal files with the most resolved importers.
_HUBS = (
    "MATCH (src:Symbol)-[r:Rel {kind: 'imports'}]->(t:Symbol {kind: 'file'}) "
    "RETURN t.path AS path, count(DISTINCT src.id) AS dependents "
    "ORDER BY dependents DESC, path LIMIT $limit"
)


class OverviewService:
    """Summarize the indexed repository at a glance."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def summary(self, *, hub_limit: int = 15) -> RepoOverview:
        """Return file/symbol counts, language mix, and the top hub files."""
        files = self._scalar(_FILE_COUNT)
        symbols = self._scalar(_SYMBOL_COUNT)
        languages = {
            str(row.get("language") or ""): as_int(row.get("n"))
            for row in self._graph.query(_LANGUAGES)
        }
        hubs = [
            HubFile(
                path=str(row.get("path") or ""),
                dependents=as_int(row.get("dependents")),
            )
            for row in self._graph.query(_HUBS, {"limit": hub_limit})
        ]
        return RepoOverview(files=files, symbols=symbols, languages=languages, hubs=hubs)

    def _scalar(self, cypher: str) -> int:
        rows = self._graph.query(cypher)
        return as_int(rows[0].get("n")) if rows else 0
