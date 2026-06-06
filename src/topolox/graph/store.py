"""The graph-store port.

Quarantines the backend (Kùzu, pinned 0.11.3) behind a Protocol so it can be
swapped later — the graph is a rebuildable cache, not a system of record.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from topolox.models.edges import Edge, EdgeKind
    from topolox.models.graph import ParseResult
    from topolox.models.nodes import SymbolNode


class Direction(StrEnum):
    """Edge traversal direction."""

    OUT = "out"
    IN = "in"
    BOTH = "both"


@runtime_checkable
class GraphStore(Protocol):
    """A persistent property graph of code symbols and their relationships."""

    def init_schema(self) -> None: ...

    def upsert(self, fragment: ParseResult) -> None: ...

    def delete_file(self, path: str) -> None: ...

    def neighbors(
        self,
        node_id: str,
        *,
        kinds: Collection[EdgeKind],
        direction: Direction = Direction.OUT,
        depth: int = 1,
    ) -> list[Edge]: ...

    def subgraph(
        self,
        seed_ids: Sequence[str],
        *,
        depth: int = 1,
    ) -> tuple[list[SymbolNode], list[Edge]]: ...

    def query(
        self,
        cypher: str,
        params: Mapping[str, object] | None = None,
    ) -> list[dict[str, object]]: ...

    def close(self) -> None: ...
