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

            self._uri.parent.mkdir(parents=True, exist_ok=True)
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

    def _ensure_table(self) -> Any:
        if self._table is None:
            try:
                self._table = self._ensure_db().open_table(self._table_name)
            except Exception:
                return None
        return self._table

    def search(
        self,
        vector: Sequence[float],
        *,
        limit: int = 20,
        where: str | None = None,
    ) -> list[VectorHit]:
        table = self._ensure_table()
        if table is None:
            return []
        query = table.search(list(vector)).limit(limit)
        if where:
            query = query.where(where)
        hits: list[VectorHit] = []
        for row in query.to_list():
            distance = float(row.get("_distance", 0.0))
            hits.append(
                VectorHit(
                    id=str(row["id"]),
                    path=str(row.get("path", "") or ""),
                    score=1.0 / (1.0 + distance),
                )
            )
        return hits

    def close(self) -> None:
        self._table = None
        self._db = None
