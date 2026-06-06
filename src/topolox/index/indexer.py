"""Builds and incrementally updates the Topolox index."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from topolox.parsing.discovery import discover_files
from topolox.parsing.pool import parse_repo

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
        """Full index of ``root`` into the graph and vector stores."""
        start = time.perf_counter()
        self._graph.init_schema()
        self._vectors.init_schema(self._embedder.dim)

        files = discover_files(root)
        n_files = n_nodes = n_edges = n_errors = 0
        rows: list[dict[str, object]] = []

        for result in parse_repo(files, root=root, max_workers=self._settings.max_workers):
            n_files += 1
            if result.error:
                n_errors += 1
                continue
            self._graph.upsert(result)
            n_nodes += len(result.nodes)
            n_edges += len(result.edges)
            texts = [node.signature or node.qualified_name for node in result.nodes]
            embeddings = self._embedder.embed(texts)
            for node, vector in zip(result.nodes, embeddings, strict=False):
                rows.append(
                    {
                        "id": node.id,
                        "path": node.path,
                        "text": node.signature or node.qualified_name,
                        "vector": vector,
                    }
                )

        if rows:
            self._vectors.upsert(rows)

        return IndexStats(
            files=n_files,
            nodes=n_nodes,
            edges=n_edges,
            errors=n_errors,
            seconds=time.perf_counter() - start,
        )

    def update(
        self,
        changed: Sequence[Path],
        removed: Sequence[Path],
    ) -> IndexStats:
        """Incremental update for changed/removed files. Phase 2 (daemon)."""
        raise NotImplementedError("Phase 2: incremental update")
