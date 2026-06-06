"""MCP tool definitions exposed to agents.

Each tool is async and offloads the synchronous graph/vector calls to a worker
thread so the event loop stays responsive.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from topolox.models.query import BlastRadiusReport, DependencyMap, PrunedContext

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from topolox.mcp.context import AppContext


def register_tools(server: FastMCP, ctx: AppContext) -> None:
    """Register the Topolox tools on ``server``."""

    async def get_file_dependencies(path: str, depth: int = 1) -> DependencyMap:
        """What a file imports and what imports it. Call this to understand a file's
        place in the codebase before reading it. ``path`` is repo-relative POSIX
        (e.g. ``apps/api/app/db.py``)."""
        return await asyncio.to_thread(ctx.dependencies.of_file, path, depth=depth)

    async def analyze_blast_radius(
        changed_files: list[str], max_depth: int = 3
    ) -> BlastRadiusReport:
        """Downstream impact of changing files — the files and tests that transitively
        import them. Call this BEFORE editing to gauge risk. Paths are repo-relative."""
        return await asyncio.to_thread(ctx.blast.simulate, changed_files, max_depth=max_depth)

    async def prune_context(prompt: str, token_budget: int = 8000) -> PrunedContext:
        """The most relevant symbols/files for a task or question, token-budgeted.
        Use this to gather context instead of reading many files."""
        return await asyncio.to_thread(ctx.pruner.prune, prompt, token_budget=token_budget)

    async def search_architecture_graph(query: str, limit: int = 20) -> PrunedContext:
        """Find where something lives by meaning + structure — use instead of grepping."""
        return await asyncio.to_thread(ctx.pruner.prune, query, token_budget=100_000, top_k=limit)

    for tool in (
        get_file_dependencies,
        analyze_blast_radius,
        prune_context,
        search_architecture_graph,
    ):
        server.tool(tool)
