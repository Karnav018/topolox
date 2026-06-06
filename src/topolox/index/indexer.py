"""Builds and incrementally updates the Topolox index."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from topolox.config import Settings
    from topolox.graph.store import GraphStore
    from topolox.vectors.embedder import Embedder
    from topolox.vectors.store import VectorStore


@dataclass(slots=True, frozen=True)
class IndexStats:
    """Summary of an indexing run."""

    files: int = 0
    nodes: int = 0
    edges: int = 0
    errors: int = 0
    seconds: float = 0.0


class Indexer:
    """Coordinates parsing and persistence into the graph + vector stores."""

    def __init__(
        self,
        settings: Settings,
        graph: GraphStore,
        vectors: VectorStore,
        embedder: Embedder,
    ) -> None:
        self._settings = settings
        self._graph = graph
        self._vectors = vectors
        self._embedder = embedder

    def build(self, root: Path) -> IndexStats:
        """Full index of ``root``. Phase 1."""
        raise NotImplementedError("Phase 1: full index")

    def update(
        self,
        changed: Sequence[Path],
        removed: Sequence[Path],
    ) -> IndexStats:
        """Incremental update for changed/removed files. Phase 2 (daemon)."""
        raise NotImplementedError("Phase 2: incremental update")
