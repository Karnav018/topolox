"""LanceDB-backed :class:`~topolox.vectors.store.VectorStore`."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from topolox.vectors.store import VectorHit

if TYPE_CHECKING:
    from pathlib import Path


class LanceDBVectorStore:
    """Embedded LanceDB adapter implementing the ``VectorStore`` protocol."""

    def __init__(self, uri: Path, table: str = "symbols") -> None:
        self._uri = uri
        self._table = table

    def init_schema(self, dim: int) -> None:
        raise NotImplementedError("Phase 1: LanceDB schema")

    def upsert(self, rows: Sequence[Mapping[str, object]]) -> None:
        raise NotImplementedError("Phase 1: LanceDB upsert")

    def delete_file(self, path: str) -> None:
        raise NotImplementedError("Phase 2: LanceDB delete_file")

    def search(
        self,
        vector: Sequence[float],
        *,
        limit: int = 20,
        where: str | None = None,
    ) -> list[VectorHit]:
        raise NotImplementedError("Phase 2: LanceDB search")

    def close(self) -> None:
        return None
