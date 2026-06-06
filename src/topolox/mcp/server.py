"""FastMCP server entry point."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP


def build_server(repo_root: Path | None = None) -> FastMCP:
    """Build a FastMCP server backed by the index under ``repo_root``."""
    from fastmcp import FastMCP

    from topolox.config import load_settings
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.mcp.context import AppContext
    from topolox.mcp.tools import register_tools
    from topolox.query.blast_radius import BlastRadiusService
    from topolox.query.dependencies import DependencyService
    from topolox.query.pruner import ContextPruner
    from topolox.vectors.embedder import default_embedder
    from topolox.vectors.lancedb_store import LanceDBVectorStore

    root = (repo_root or Path.cwd()).resolve()
    data_dir = root / ".topolox"
    graph = KuzuGraphStore(data_dir / "graph.kuzu")
    graph.init_schema()
    vectors = LanceDBVectorStore(data_dir / "vectors.lance")
    context = AppContext(
        settings=load_settings(),
        graph=graph,
        vectors=vectors,
        dependencies=DependencyService(graph),
        pruner=ContextPruner(graph, vectors, default_embedder()),
        blast=BlastRadiusService(graph),
    )
    server = FastMCP("Topolox")
    register_tools(server, context)
    return server


def serve(repo_root: Path | None = None) -> None:
    """Run the MCP server over stdio."""
    build_server(repo_root).run()


def main() -> None:
    """Console-script entry point for ``topolox-mcp``."""
    serve()


if __name__ == "__main__":
    main()
