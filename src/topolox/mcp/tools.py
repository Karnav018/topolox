"""MCP tool definitions exposed to agents.

Each tool is async and offloads the synchronous graph/vector calls to a worker
thread so the event loop stays responsive.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from topolox.models.query import (
    BlastRadiusReport,
    CallReport,
    ClassHierarchy,
    DependencyMap,
    FileOutline,
    PrunedContext,
    RepoOverview,
    SymbolSource,
)

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

    async def read_symbol(name: str, path: str | None = None) -> SymbolSource:
        """The exact source of one function/class/method by name (or qualified name),
        instead of reading the whole file. Pass ``path`` to disambiguate a name that
        collides across files. Pair with prune_context / search_architecture_graph:
        find the symbol, then read only it."""
        return await asyncio.to_thread(ctx.reader.read, name, path=path)

    async def file_outline(path: str) -> FileOutline:
        """A file's shape — its classes/functions/methods with signatures, docstrings,
        and line ranges — without reading the file. Use to understand a file cheaply,
        then read_symbol the parts you need. ``path`` is repo-relative POSIX."""
        return await asyncio.to_thread(ctx.outline.of_file, path)

    async def repo_overview() -> RepoOverview:
        """Orient on an unfamiliar repo: file/symbol counts, language mix, and the hub
        files most other files import (the high-impact places to start)."""
        return await asyncio.to_thread(ctx.overview.summary)

    async def get_callers(name: str, path: str | None = None) -> CallReport:
        """Functions/methods that call ``name`` — the call graph upstream. More precise
        than file imports for "what breaks if I change this?". Pass ``path`` to
        disambiguate a name that exists in several files. (Resolved Python call graph.)"""
        return await asyncio.to_thread(ctx.calls.callers, name, path=path)

    async def get_callees(name: str, path: str | None = None) -> CallReport:
        """What ``name`` calls — the functions/methods/classes it invokes. Use to trace
        how a function works without reading it."""
        return await asyncio.to_thread(ctx.calls.callees, name, path=path)

    async def class_hierarchy(name: str, path: str | None = None) -> ClassHierarchy:
        """A class's direct supertypes and subtypes — what it extends and what extends it.
        Use to find overrides and the type's place in the hierarchy."""
        return await asyncio.to_thread(ctx.hierarchy.of_class, name, path=path)

    for tool in (
        get_file_dependencies,
        analyze_blast_radius,
        prune_context,
        search_architecture_graph,
        read_symbol,
        file_outline,
        repo_overview,
        get_callers,
        get_callees,
        class_hierarchy,
    ):
        server.tool(tool)
