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
