"""Shared application context owned by the MCP server lifespan. Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.config import Settings
    from topolox.graph.store import GraphStore
    from topolox.query.blast_radius import BlastRadiusService
    from topolox.query.calls import CallGraphService
    from topolox.query.dependencies import DependencyService
    from topolox.query.hierarchy import HierarchyService
    from topolox.query.impact import SymbolImpactService
    from topolox.query.outline import OutlineService
    from topolox.query.overview import OverviewService
    from topolox.query.pruner import ContextPruner
    from topolox.query.source import SymbolReader
    from topolox.vectors.store import VectorStore


@dataclass(slots=True)
class AppContext:
    """Holds the live stores and query services for the MCP tools."""

    settings: Settings
    graph: GraphStore
    vectors: VectorStore
    dependencies: DependencyService
    pruner: ContextPruner
    blast: BlastRadiusService
    reader: SymbolReader
    outline: OutlineService
    overview: OverviewService
    calls: CallGraphService
    hierarchy: HierarchyService
    impact: SymbolImpactService
