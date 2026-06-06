"""Blast-radius simulation — the downstream impact of a change."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore
    from topolox.models.query import BlastRadiusReport


class BlastRadiusService:
    """Trace the downstream impact of changing one or more files."""

    def __init__(self, graph: GraphStore) -> None:
        self._graph = graph

    def simulate(
        self,
        changed: Sequence[str],
        *,
        max_depth: int = 3,
    ) -> BlastRadiusReport:
        """Simulate the blast radius of changing ``changed``. Phase 2."""
        raise NotImplementedError("Phase 2: blast radius")
