"""Kùzu-backed :class:`~topolox.graph.store.GraphStore` (pinned ``kuzu==0.11.3``)."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import TYPE_CHECKING

from topolox.graph.store import Direction

if TYPE_CHECKING:
    from pathlib import Path

    from topolox.models.edges import Edge, EdgeKind
    from topolox.models.graph import ParseResult
    from topolox.models.nodes import SymbolNode


class KuzuGraphStore:
    """Embedded Kùzu adapter implementing the ``GraphStore`` protocol."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def init_schema(self) -> None:
        raise NotImplementedError("Phase 1: Kùzu schema")

    def upsert(self, fragment: ParseResult) -> None:
        raise NotImplementedError("Phase 1: Kùzu upsert")

    def delete_file(self, path: str) -> None:
        raise NotImplementedError("Phase 2: Kùzu delete_file")

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
        raise NotImplementedError("Phase 1: Kùzu query")

    def close(self) -> None:
        return None
