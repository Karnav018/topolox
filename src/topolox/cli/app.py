"""The ``topolox`` command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from topolox import __version__

app = typer.Typer(
    name="topolox",
    help="The topological memory and architecture layer for AI coding agents.",
    no_args_is_help=True,
    add_completion=False,
)

_NOT_YET = "🚧 Not implemented yet — arrives in {phase}. See ROADMAP.md."


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"topolox {__version__}")
        raise typer.Exit


@app.callback()
def _main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Topolox CLI."""


@app.command()
def index(
    path: Annotated[Path, typer.Argument(help="Repository root to index.")] = Path(),
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Parse and print symbols/edges without persisting."),
    ] = False,
) -> None:
    """Index a repository into the graph + vector store."""
    root = path.resolve()
    if not root.exists():
        typer.echo(f"error: path does not exist: {root}", err=True)
        raise typer.Exit(code=1)

    if dry_run:
        from topolox.parsing.discovery import discover_files
        from topolox.parsing.pool import parse_repo

        files = discover_files(root)
        total_nodes = 0
        total_edges = 0
        errors = 0
        for result in parse_repo(files, root=root):
            if result.error:
                errors += 1
                typer.echo(f"  ! {result.path}: {result.error}", err=True)
                continue
            total_nodes += len(result.nodes)
            total_edges += len(result.edges)
            typer.echo(f"  {result.path}: {len(result.nodes)} nodes, {len(result.edges)} edges")
        summary = f"Parsed {len(files)} file(s) -> {total_nodes} nodes, {total_edges} edges"
        if errors:
            summary += f", {errors} error(s)"
        typer.echo(summary)
        return

    from topolox.config import load_settings
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.index.indexer import Indexer
    from topolox.vectors.embedder import default_embedder
    from topolox.vectors.lancedb_store import LanceDBVectorStore

    data_dir = root / ".topolox"
    data_dir.mkdir(parents=True, exist_ok=True)
    graph = KuzuGraphStore(data_dir / "graph.kuzu")
    vectors = LanceDBVectorStore(data_dir / "vectors.lance")
    indexer = Indexer(load_settings(), graph, vectors, default_embedder())
    try:
        stats = indexer.build(root)
    finally:
        graph.close()
        vectors.close()
    typer.echo(
        f"Indexed {stats.files} file(s) -> {stats.nodes} nodes, {stats.edges} edges "
        f"in {stats.seconds:.2f}s ({stats.errors} error(s)) -> {data_dir}"
    )


@app.command()
def daemon(
    path: Annotated[Path, typer.Argument(help="Repository root to watch.")] = Path(),
) -> None:
    """Watch a repository and keep the index live."""
    typer.echo(_NOT_YET.format(phase="Phase 2"))


mcp_app = typer.Typer(
    help="Run or install the MCP server for Claude Code / Cursor.",
    no_args_is_help=True,
)
app.add_typer(mcp_app, name="mcp")


@mcp_app.command("serve")
def mcp_serve() -> None:
    """Run the Topolox MCP server over stdio."""
    from topolox.mcp.server import serve

    serve()


@mcp_app.command("install")
def mcp_install(
    client: Annotated[str, typer.Option(help="Which client: claude-code, cursor, or all.")] = "all",
) -> None:
    """Register the Topolox MCP server with Claude Code and/or Cursor."""
    from topolox.mcp.install import install_mcp

    targets = install_mcp(Path.cwd(), client=client)
    if not targets:
        typer.echo(f"error: unknown client {client!r} (use claude-code, cursor, or all)", err=True)
        raise typer.Exit(code=1)
    for target in targets:
        typer.echo(f"✓ registered topolox in {target}")
    typer.echo("Restart your client to pick up the new MCP server.")


@app.command()
def deps(
    file: Annotated[str, typer.Argument(help="File to inspect.")],
    depth: Annotated[int, typer.Option(help="Traversal depth.")] = 1,
) -> None:
    """Show dependencies and dependents of a file."""
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.query.dependencies import DependencyService

    graph_db = Path(".topolox") / "graph.kuzu"
    if not graph_db.exists():
        typer.echo("error: no index found here. Run 'topolox index .' first.", err=True)
        raise typer.Exit(code=1)

    graph = KuzuGraphStore(graph_db)
    try:
        result = DependencyService(graph).of_file(file, depth=depth)
    finally:
        graph.close()

    typer.echo(file)
    typer.echo("  imports:")
    for dependency in result.dependencies:
        typer.echo(f"    -> {dependency.name}")
    if not result.dependencies:
        typer.echo("    (none)")
    typer.echo("  imported by:")
    for dependent in result.dependents:
        typer.echo(f"    <- {dependent.path or dependent.name}")
    if not result.dependents:
        typer.echo("    (none)")


@app.command()
def prune(
    prompt: Annotated[str, typer.Argument(help="The agent prompt.")],
    budget: Annotated[int, typer.Option(help="Token budget.")] = 8000,
) -> None:
    """Return pruned context for a prompt."""
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.query.pruner import ContextPruner
    from topolox.vectors.embedder import default_embedder
    from topolox.vectors.lancedb_store import LanceDBVectorStore

    data_dir = Path(".topolox")
    if not (data_dir / "graph.kuzu").exists():
        typer.echo("error: no index found here. Run 'topolox index .' first.", err=True)
        raise typer.Exit(code=1)

    graph = KuzuGraphStore(data_dir / "graph.kuzu")
    vectors = LanceDBVectorStore(data_dir / "vectors.lance")
    try:
        context = ContextPruner(graph, vectors, default_embedder()).prune(
            prompt, token_budget=budget
        )
    finally:
        graph.close()
        vectors.close()

    typer.echo(
        f"Context for {prompt!r} (~{context.token_estimate} tokens, {len(context.symbols)} symbols)"
    )
    for symbol in context.symbols:
        location = f"  {symbol.path}" if symbol.path else ""
        typer.echo(f"    [{symbol.score:.2f}] {symbol.name}{location}")
    if not context.symbols:
        typer.echo("    (no matches — was the index built with the [embeddings] extra?)")


@app.command()
def blast(
    files: Annotated[list[str], typer.Argument(help="Changed files.")],
    depth: Annotated[int, typer.Option(help="Max traversal depth.")] = 3,
) -> None:
    """Simulate the blast radius of changing files."""
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.query.blast_radius import BlastRadiusService

    graph_db = Path(".topolox") / "graph.kuzu"
    if not graph_db.exists():
        typer.echo("error: no index found here. Run 'topolox index .' first.", err=True)
        raise typer.Exit(code=1)

    graph = KuzuGraphStore(graph_db)
    try:
        report = BlastRadiusService(graph).simulate(files, max_depth=depth)
    finally:
        graph.close()

    typer.echo(f"Changed: {', '.join(report.changed)}")
    typer.echo(f"Impacted files ({len(report.impacted_files)}, depth {report.max_depth}):")
    for impacted in report.impacted_files:
        marker = "  [test]" if impacted in report.impacted_tests else ""
        typer.echo(f"    {impacted}{marker}")
    if not report.impacted_files:
        typer.echo("    (none)")


@app.command()
def ui() -> None:
    """Launch the Textual TUI dashboard."""
    typer.echo(_NOT_YET.format(phase="Phase 3"))


@app.command()
def benchmark() -> None:
    """Run the token-reduction / retrieval benchmark."""
    typer.echo(_NOT_YET.format(phase="Phase 3"))


def main() -> None:
    """Console-script entry point for ``topolox``."""
    app()
