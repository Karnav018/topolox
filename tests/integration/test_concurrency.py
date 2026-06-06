"""Read-only graph access — lets the MCP server coexist with the daemon's writer."""

from __future__ import annotations

from pathlib import Path

from topolox.graph.kuzu_store import KuzuGraphStore, open_readonly
from topolox.models.graph import ParseResult
from topolox.models.nodes import NodeKind, Span, SymbolNode


def _fragment(path: str) -> ParseResult:
    node = SymbolNode(
        id=path,
        kind=NodeKind.FILE,
        name=Path(path).name,
        qualified_name=path.replace("/", "."),
        path=path,
        language="python",
        span=Span(0, 0, 1, 1),
    )
    return ParseResult(path=path, language="python", nodes=(node,), edges=())


def test_read_only_open_reads_data(tmp_path: Path) -> None:
    path = tmp_path / "graph.kuzu"
    writer = KuzuGraphStore(path)
    writer.init_schema()
    writer.upsert(_fragment("a.py"))
    writer.close()

    reader = KuzuGraphStore(path, read_only=True)
    rows = reader.query("MATCH (s:Symbol) RETURN count(*) AS n")
    assert rows[0]["n"] == 1
    reader.close()


def test_open_readonly_creates_missing_db(tmp_path: Path) -> None:
    # No index yet: open_readonly should seed an empty schema, then read it.
    store = open_readonly(tmp_path / "graph.kuzu")
    rows = store.query("MATCH (s:Symbol) RETURN count(*) AS n")
    assert rows[0]["n"] == 0
    store.close()
