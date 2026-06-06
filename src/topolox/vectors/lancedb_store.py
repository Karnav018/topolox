"""LanceDB-backed :class:`~topolox.vectors.store.VectorStore`."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from topolox.errors import StoreError
from topolox.vectors.store import VectorHit

if TYPE_CHECKING:
    from pathlib import Path


class LanceDBVectorStore:
    """Embedded LanceDB adapter implementing the ``VectorStore`` protocol."""

    def __init__(self, uri: Path, table: str = "symbols") -> None:
        self._uri = uri
        self._table_name = table
        self._db: Any = None
        self._table: Any = None

    def _ensure_db(self) -> Any:
        if self._db is None:
            import lancedb

            self._db = lancedb.connect(str(self._uri))
        return self._db

    def init_schema(self, dim: int) -> None:
        import pyarrow as pa

        schema = pa.schema(
            [
                pa.field("id", pa.string()),
                pa.field("path", pa.string()),
                pa.field("text", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), dim)),
            ]
        )
        self._table = self._ensure_db().create_table(self._table_name, schema=schema, exist_ok=True)

    def upsert(self, rows: Sequence[Mapping[str, object]]) -> None:
        if self._table is None:
            raise StoreError("vector store not initialized; call init_schema() first")
        if not rows:
            return
        self._table.add(list(rows))

    def delete_file(self, path: str) -> None:
        if self._table is not None:
            self._table.delete(f"path = '{path}'")

    def search(
        self,
        vector: Sequence[float],
        *,
        limit: int = 20,
        where: str | None = None,
    ) -> list[VectorHit]:
        raise NotImplementedError("Phase 2: LanceDB search")

    def close(self) -> None:
        self._table = None
        self._db = None
