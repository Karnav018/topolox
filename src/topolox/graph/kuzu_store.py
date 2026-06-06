"""Kùzu-backed :class:`~topolox.graph.store.GraphStore` (pinned ``kuzu==0.11.3``)."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from topolox.graph.schema import SCHEMA_STATEMENTS
from topolox.graph.store import Direction

if TYPE_CHECKING:
    from pathlib import Path

    from topolox.models.edges import Edge, EdgeKind
    from topolox.models.graph import ParseResult
    from topolox.models.nodes import SymbolNode

_MERGE_NODE = """
MERGE (s:Symbol {id: $id})
SET s.kind = $kind,
    s.name = $name,
    s.qualified_name = $qualified_name,
    s.path = $path,
    s.language = $language,
    s.signature = $signature,
    s.start_line = $start_line,
    s.end_line = $end_line
"""

_MERGE_PLACEHOLDER = "MERGE (s:Symbol {id: $id})"

_MERGE_REL = """
MATCH (a:Symbol {id: $src}), (b:Symbol {id: $dst})
MERGE (a)-[r:Rel {kind: $kind}]->(b)
SET r.weight = $weight
"""


class KuzuGraphStore:
    """Embedded Kùzu adapter implementing the ``GraphStore`` protocol."""

    def __init__(self, db_path: Path, *, read_only: bool = False) -> None:
        import kuzu

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db: Any = kuzu.Database(str(db_path), read_only=read_only)
        self._conn: Any = kuzu.Connection(self._db)

    def init_schema(self) -> None:
        for statement in SCHEMA_STATEMENTS:
            self._conn.execute(statement)

    def upsert(self, fragment: ParseResult) -> None:
        for node in fragment.nodes:
            self._conn.execute(
                _MERGE_NODE,
                parameters={
                    "id": node.id,
                    "kind": node.kind.value,
                    "name": node.name,
                    "qualified_name": node.qualified_name,
                    "path": node.path,
                    "language": node.language,
                    "signature": node.signature or "",
                    "start_line": node.span.start_line,
                    "end_line": node.span.end_line,
                },
            )
        for edge in fragment.edges:
            self._conn.execute(_MERGE_PLACEHOLDER, parameters={"id": edge.dst_id})
            self._conn.execute(
                _MERGE_REL,
                parameters={
                    "src": edge.src_id,
                    "dst": edge.dst_id,
                    "kind": edge.kind.value,
                    "weight": edge.weight,
                },
            )

    def delete_file(self, path: str) -> None:
        self._conn.execute(
            "MATCH (s:Symbol {path: $path}) DETACH DELETE s",
            parameters={"path": path},
        )

    def neighbors(
        self,
        node_id: str,
        *,
        kinds: Collection[EdgeKind],
        direction: Direction = Direction.OUT,
        depth: int = 1,
    ) -> list[Edge]:
        raise NotImplementedError("Phase 2: Kùzu neighbors")

    def subgraph(
        self,
        seed_ids: Sequence[str],
        *,
        depth: int = 1,
    ) -> tuple[list[SymbolNode], list[Edge]]:
        raise NotImplementedError("Phase 2: Kùzu subgraph")

    def query(
        self,
        cypher: str,
        params: Mapping[str, object] | None = None,
    ) -> list[dict[str, object]]:
        result = self._conn.execute(cypher, parameters=dict(params) if params else {})
        columns: list[str] = list(result.get_column_names())
        rows: list[dict[str, object]] = []
        while result.has_next():
            rows.append(dict(zip(columns, result.get_next(), strict=False)))
        return rows

    def close(self) -> None:
        for obj in (self._conn, self._db):
            closer = getattr(obj, "close", None)
            if callable(closer):
                closer()


def open_readonly(db_path: Path) -> KuzuGraphStore:
    """Open the graph read-only, creating an empty schema first if it's missing.

    Read-only opens coexist with a running ``topolox daemon`` (Kùzu's single
    read-writer) and with other readers (multiple agents), so the MCP server and
    query CLIs never fight over the write lock.
    """
    if not db_path.exists():
        seed = KuzuGraphStore(db_path)
        seed.init_schema()
        seed.close()
    return KuzuGraphStore(db_path, read_only=True)
