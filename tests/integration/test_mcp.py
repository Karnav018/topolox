"""Integration test for the FastMCP server (in-memory client)."""

from __future__ import annotations

import json
from pathlib import Path

from fastmcp import Client

from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.graph.resolve import resolve_imports
from topolox.mcp.install import install_mcp
from topolox.mcp.server import build_server
from topolox.models.edges import Edge, EdgeKind
from topolox.models.graph import ParseResult
from topolox.models.nodes import NodeKind, Span, SymbolNode


def _seed_index(repo: Path) -> None:
    store = KuzuGraphStore(repo / ".topolox" / "graph.kuzu")
    store.init_schema()
    for path, qualified, imports in [
        ("app/main.py", "app.main", ["app.db"]),
        ("app/db.py", "app.db", []),
    ]:
        node = SymbolNode(
            id=path,
            kind=NodeKind.FILE,
            name=Path(path).name,
            qualified_name=qualified,
            path=path,
            language="python",
            span=Span(0, 0, 1, 1),
        )
        edges = tuple(Edge(src_id=path, dst_id=m, kind=EdgeKind.IMPORTS) for m in imports)
        store.upsert(ParseResult(path=path, language="python", nodes=(node,), edges=edges))
    resolve_imports(store)
    store.close()


async def test_mcp_server_exposes_and_runs_tools(tmp_path: Path) -> None:
    _seed_index(tmp_path)
    server = build_server(tmp_path)
    async with Client(server) as client:
        names = {tool.name for tool in await client.list_tools()}
        assert {
            "get_file_dependencies",
            "analyze_blast_radius",
            "prune_context",
            "search_architecture_graph",
        } <= names

        deps = await client.call_tool("get_file_dependencies", {"path": "app/main.py"})
        assert "app.db" in str(deps.data)

        blast = await client.call_tool("analyze_blast_radius", {"changed_files": ["app/db.py"]})
        assert "app/main.py" in str(blast.data)


def test_install_writes_client_configs(tmp_path: Path) -> None:
    targets = install_mcp(tmp_path, client="all")
    assert (tmp_path / ".mcp.json") in targets
    assert (tmp_path / ".cursor" / "mcp.json") in targets

    config = json.loads((tmp_path / ".mcp.json").read_text())
    assert "topolox" in config["mcpServers"]
    assert config["mcpServers"]["topolox"]["args"] == ["-m", "topolox.mcp.server"]

    assert install_mcp(tmp_path, client="unknown") == []
