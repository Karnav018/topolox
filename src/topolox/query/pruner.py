"""The Context Pruner — hybrid vector + graph relevance scoring."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore
    from topolox.models.query import PrunedContext
    from topolox.vectors.embedder import Embedder
    from topolox.vectors.store import VectorStore


class ContextPruner:
    """Return only the top-percentile of relevant symbols for a prompt."""

    def __init__(
        self,
        graph: GraphStore,
        vectors: VectorStore,
        embedder: Embedder,
    ) -> None:
        self._graph = graph
        self._vectors = vectors
        self._embedder = embedder

    def prune(self, prompt: str, *, token_budget: int = 8000) -> PrunedContext:
        """Hybrid context pruning: vector seeds → graph expansion → blend. Phase 2."""
        raise NotImplementedError("Phase 2: context pruner")
