"""FastMCP server entry point."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP

_INSTRUCTIONS = (
    "Topolox indexes this repository into a dependency + symbol graph. Prefer these tools "
    "over grepping or reading files when answering questions about the codebase: use "
    "get_file_dependencies for a file's imports/importers, analyze_blast_radius before edits "
    "to gauge impact, and prune_context / search_architecture_graph to find relevant code. "
    "Paths are repo-relative POSIX (e.g. apps/api/app/db.py); an empty result means the "
    "path or query isn't in the index."
)


def build_server(repo_root: Path | None = None) -> FastMCP:
    """Build a FastMCP server backed by the index under ``repo_root``."""
    from fastmcp import FastMCP

    from topolox.config import load_settings
    from topolox.graph.kuzu_store import open_readonly
    from topolox.mcp.context import AppContext
    from topolox.mcp.tools import register_tools
    from topolox.query.blast_radius import BlastRadiusService
    from topolox.query.dependencies import DependencyService
    from topolox.query.pruner import ContextPruner
    from topolox.vectors.embedder import default_embedder
    from topolox.vectors.lancedb_store import LanceDBVectorStore

    root = (repo_root or Path.cwd()).resolve()
    data_dir = root / ".topolox"
    graph = open_readonly(data_dir / "graph.kuzu")  # read-only: coexists with the daemon
    vectors = LanceDBVectorStore(data_dir / "vectors.lance")
    context = AppContext(
        settings=load_settings(),
        graph=graph,
        vectors=vectors,
        dependencies=DependencyService(graph),
        pruner=ContextPruner(graph, vectors, default_embedder()),
        blast=BlastRadiusService(graph),
    )
    server = FastMCP("Topolox", instructions=_INSTRUCTIONS)
    register_tools(server, context)
    return server


def serve(repo_root: Path | None = None) -> None:
    """Run the MCP server over stdio."""
    build_server(repo_root).run(show_banner=False)


def main() -> None:
    """Console-script entry point for ``topolox-mcp``."""
    serve()


if __name__ == "__main__":
    main()
