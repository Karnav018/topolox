"""Builds and incrementally updates the Topolox index."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from topolox.parsing.discovery import discover_files
from topolox.parsing.pool import parse_repo
from topolox.parsing.worker import parse_file

if TYPE_CHECKING:
    from collections.abc import Sequence

    from topolox.config import Settings
    from topolox.graph.store import GraphStore
    from topolox.models.graph import ParseResult
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
        self._root: Path = settings.repo_root
        self._hashes: dict[str, str] = {}

    def build(self, root: Path) -> IndexStats:
        """Full index of ``root`` into the graph and vector stores."""
        start = time.perf_counter()
        self._root = root.resolve()
        self._graph.init_schema()
        self._vectors.init_schema(self._embedder.dim)

        files = discover_files(self._root)
        n_files = n_nodes = n_edges = n_errors = 0
        rows: list[dict[str, object]] = []
        for result in parse_repo(files, root=self._root, max_workers=self._settings.max_workers):
            n_files += 1
            if result.error:
                n_errors += 1
                continue
            self._graph.upsert(result)
            self._hashes[result.path] = result.content_hash
            n_nodes += len(result.nodes)
            n_edges += len(result.edges)
            rows.extend(self._vector_rows(result))

        if rows:
            self._vectors.upsert(rows)

        return IndexStats(n_files, n_nodes, n_edges, n_errors, time.perf_counter() - start)

    def update(self, changed: Sequence[Path], removed: Sequence[Path]) -> IndexStats:
        """Incrementally patch the index for changed/removed files."""
        start = time.perf_counter()
        n_files = n_nodes = n_edges = n_errors = 0

        for path in removed:
            rel = self._relpath(path)
            self._graph.delete_file(rel)
            self._vectors.delete_file(rel)
            self._hashes.pop(rel, None)

        for path in changed:
            rel = self._relpath(path)
            result = parse_file((str(Path(path).resolve()), rel))
            n_files += 1
            if result.error:
                n_errors += 1
                continue
            if self._hashes.get(rel) == result.content_hash:
                continue  # content unchanged — skip
            self._graph.delete_file(rel)
            self._vectors.delete_file(rel)
            self._graph.upsert(result)
            rows = self._vector_rows(result)
            if rows:
                self._vectors.upsert(rows)
            self._hashes[rel] = result.content_hash
            n_nodes += len(result.nodes)
            n_edges += len(result.edges)

        return IndexStats(n_files, n_nodes, n_edges, n_errors, time.perf_counter() - start)

    def _relpath(self, path: Path) -> str:
        resolved = Path(path).resolve()
        try:
            return resolved.relative_to(self._root).as_posix()
        except ValueError:
            return resolved.name

    def _vector_rows(self, result: ParseResult) -> list[dict[str, object]]:
        texts = [node.signature or node.qualified_name for node in result.nodes]
        embeddings = self._embedder.embed(texts)
        return [
            {
                "id": node.id,
                "path": node.path,
                "text": node.signature or node.qualified_name,
                "vector": vector,
            }
            for node, vector in zip(result.nodes, embeddings, strict=False)
        ]
