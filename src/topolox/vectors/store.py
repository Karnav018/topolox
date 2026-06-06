"""The vector-store port."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class VectorHit(BaseModel):
    """A single nearest-neighbor search result."""

    id: str
    path: str
    score: float


@runtime_checkable
class VectorStore(Protocol):
    """An embedded vector index over code symbols."""

    def init_schema(self, dim: int) -> None: ...

    def upsert(self, rows: Sequence[Mapping[str, object]]) -> None: ...

    def delete_file(self, path: str) -> None: ...

    def search(
        self,
        vector: Sequence[float],
        *,
        limit: int = 20,
        where: str | None = None,
    ) -> list[VectorHit]: ...

    def close(self) -> None: ...
