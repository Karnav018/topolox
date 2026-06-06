"""The Context Pruner — hybrid vector + graph relevance scoring."""

from __future__ import annotations

from typing import TYPE_CHECKING

from topolox.models.query import PrunedContext, ScoredSymbol
from topolox.query.scoring import estimate_tokens

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore
    from topolox.vectors.embedder import Embedder
    from topolox.vectors.store import VectorStore

_NEIGHBORS = "MATCH (s:Symbol {id: $id})-[r:Rel]-(n:Symbol) RETURN DISTINCT n.id AS id"

_METADATA = (
    "MATCH (s:Symbol {id: $id}) RETURN s.path AS path, s.name AS name, s.signature AS signature"
)

_EXPANSION_SCORE = 0.25


class ContextPruner:
    """Return only the top-percentile of relevant symbols for a prompt."""

    def __init__(self, graph: GraphStore, vectors: VectorStore, embedder: Embedder) -> None:
        self._graph = graph
        self._vectors = vectors
        self._embedder = embedder

    def prune(
        self,
        prompt: str,
        *,
        token_budget: int = 8000,
        top_k: int = 20,
    ) -> PrunedContext:
        """Vector seeds → graph expansion → blended score → token-budget cap."""
        query_vector = self._embedder.embed([prompt])[0]
        scores: dict[str, float] = {}
        for hit in self._vectors.search(query_vector, limit=top_k):
            scores[hit.id] = max(scores.get(hit.id, 0.0), hit.score)

        for seed_id in list(scores):
            for row in self._graph.query(_NEIGHBORS, {"id": seed_id}):
                neighbor_id = str(row["id"])
                if neighbor_id not in scores:
                    scores[neighbor_id] = _EXPANSION_SCORE

        symbols = [self._build_symbol(sid, score) for sid, score in scores.items()]
        symbols.sort(key=lambda symbol: symbol.score, reverse=True)

        selected: list[ScoredSymbol] = []
        files: list[str] = []
        seen_files: set[str] = set()
        total = 0
        for symbol in symbols:
            cost = estimate_tokens(symbol.signature or symbol.name)
            if selected and total + cost > token_budget:
                break
            selected.append(symbol)
            total += cost
            if symbol.path and symbol.path not in seen_files:
                seen_files.add(symbol.path)
                files.append(symbol.path)

        return PrunedContext(query=prompt, symbols=selected, files=files, token_estimate=total)

    def _build_symbol(self, symbol_id: str, score: float) -> ScoredSymbol:
        rows = self._graph.query(_METADATA, {"id": symbol_id})
        if not rows:
            return ScoredSymbol(id=symbol_id, path="", name=symbol_id, score=score)
        row = rows[0]
        signature = row.get("signature")
        return ScoredSymbol(
            id=symbol_id,
            path=str(row.get("path") or ""),
            name=str(row.get("name") or symbol_id),
            signature=str(signature) if signature else None,
            score=score,
        )
