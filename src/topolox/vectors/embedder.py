"""Embedding providers.

The default :class:`NullEmbedder` is deterministic and offline; real embeddings
(``fastembed``) ship behind the optional ``[embeddings]`` extra in Phase 2.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """Turns text into dense vectors for semantic search."""

    @property
    def dim(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class NullEmbedder:
    """A deterministic zero-vector embedder for tests and no-embeddings mode."""

    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.0] * self._dim for _ in texts]


class FastEmbedEmbedder:
    """Local ONNX embeddings via ``fastembed`` (the optional ``[embeddings]`` extra)."""

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5") -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model)
        self._dim = len(next(iter(self._model.embed(["topolox"]))))

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[float(x) for x in vector] for vector in self._model.embed(list(texts))]


def default_embedder() -> Embedder:
    """Return a real embedder if ``fastembed`` is installed, else the null one."""
    try:
        return FastEmbedEmbedder()
    except ImportError:
        return NullEmbedder()
