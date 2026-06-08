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
    """Index a repository, then watch it and keep the index live."""
    import asyncio

    from topolox.config import load_settings
    from topolox.daemon.service import DaemonService
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.index.indexer import Indexer
    from topolox.vectors.embedder import default_embedder
    from topolox.vectors.lancedb_store import LanceDBVectorStore

    root = path.resolve()
    if not root.exists():
        typer.echo(f"error: path does not exist: {root}", err=True)
        raise typer.Exit(code=1)

    data_dir = root / ".topolox"
    data_dir.mkdir(parents=True, exist_ok=True)
    graph = KuzuGraphStore(data_dir / "graph.kuzu")
    vectors = LanceDBVectorStore(data_dir / "vectors.lance")
    settings = load_settings()
    indexer = Indexer(settings, graph, vectors, default_embedder())

    typer.echo(f"Indexing {root} ...")
    stats = indexer.build(root)
    typer.echo(f"Indexed {stats.files} file(s). Watching for changes — Ctrl+C to stop.")
    try:
        asyncio.run(DaemonService(settings, indexer, root).run())
    except KeyboardInterrupt:
        typer.echo("\nStopped.")
    finally:
        graph.close()
        vectors.close()


mcp_app = typer.Typer(
    help="Run or install the MCP server for AI coding agents.",
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
    client: Annotated[
        str,
        typer.Option(
            help=(
                "Client to register: all (project-scoped), claude-code, cursor, "
                "gemini, codex, vscode, windsurf, claude-desktop."
            )
        ),
    ] = "all",
) -> None:
    """Register the Topolox MCP server with AI coding agents."""
    from topolox.mcp.install import ALL_CLIENTS, install_mcp

    targets = install_mcp(Path.cwd(), client=client)
    if not targets:
        choices = ", ".join(("all", *ALL_CLIENTS))
        typer.echo(f"error: unknown client {client!r}. Choices: {choices}", err=True)
        raise typer.Exit(code=1)
    for target in targets:
        typer.echo(f"✓ registered topolox in {target}")
    typer.echo("Restart your agent to pick up the new MCP server.")


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

    graph = KuzuGraphStore(graph_db, read_only=True)
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

    graph = KuzuGraphStore(data_dir / "graph.kuzu", read_only=True)
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

    graph = KuzuGraphStore(graph_db, read_only=True)
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


def _require_index() -> Path:
    graph_db = Path(".topolox") / "graph.kuzu"
    if not graph_db.exists():
        typer.echo("error: no index found here. Run 'topolox index .' first.", err=True)
        raise typer.Exit(code=1)
    return graph_db


@app.command()
def read(
    name: Annotated[str, typer.Argument(help="Symbol name or qualified name.")],
    path: Annotated[
        str | None, typer.Option(help="Restrict to this file (disambiguate a name).")
    ] = None,
) -> None:
    """Print the exact source of a symbol by name."""
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.query.source import SymbolReader

    graph = KuzuGraphStore(_require_index(), read_only=True)
    try:
        result = SymbolReader(graph, Path.cwd()).read(name, path=path)
    finally:
        graph.close()

    if not result.matches:
        typer.echo(f"(no symbol named {name!r} in the index)")
        return
    for match in result.matches:
        typer.echo(f"# {match.path}:{match.start_line}  ({match.kind} {match.qualified_name})")
        typer.echo(match.source or "    (source unavailable)")
        typer.echo("")


@app.command()
def outline(
    file: Annotated[str, typer.Argument(help="File to outline.")],
) -> None:
    """Show a file's symbols (its shape) without reading the file."""
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.query.outline import OutlineService

    graph = KuzuGraphStore(_require_index(), read_only=True)
    try:
        result = OutlineService(graph).of_file(file)
    finally:
        graph.close()

    typer.echo(f"{result.path} ({result.language or 'unknown'})")
    for symbol in result.symbols:
        label = symbol.signature or symbol.name
        doc = f"  — {symbol.docstring}" if symbol.docstring else ""
        typer.echo(f"  {symbol.start_line:>5}  {symbol.kind:<8} {label}{doc}")
    if not result.symbols:
        typer.echo("  (no symbols — is the file indexed?)")


@app.command()
def overview() -> None:
    """Summarize the indexed repo: size, languages, and hub files."""
    from topolox.graph.kuzu_store import KuzuGraphStore
    from topolox.query.overview import OverviewService

    graph = KuzuGraphStore(_require_index(), read_only=True)
    try:
        report = OverviewService(graph).summary()
    finally:
        graph.close()

    typer.echo(f"Files: {report.files}   Symbols: {report.symbols}")
    if report.languages:
        langs = ", ".join(f"{lang} {count}" for lang, count in report.languages.items())
        typer.echo(f"Languages: {langs}")
    typer.echo("Hub files (most imported):")
    for hub in report.hubs:
        typer.echo(f"  {hub.dependents:>4}  {hub.path}")
    if not report.hubs:
        typer.echo("  (none resolved)")


@app.command()
def ui() -> None:
    """Launch the Textual TUI dashboard."""
    typer.echo(_NOT_YET.format(phase="Phase 3"))


@app.command()
def benchmark(
    path: Annotated[Path, typer.Argument(help="Repository root to benchmark.")] = Path(),
    sample: Annotated[int, typer.Option(help="Files to sample for query/token metrics.")] = 50,
    json_out: Annotated[bool, typer.Option("--json", help="Print the report as JSON.")] = False,
) -> None:
    """Benchmark indexing speed, query latency, and token reduction."""
    from topolox.benchmark import run_benchmark

    root = path.resolve()
    if not root.exists():
        typer.echo(f"error: path does not exist: {root}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Benchmarking {root} (indexing into a temp database) ...")
    report = run_benchmark(root, sample=sample)
    if json_out:
        typer.echo(report.model_dump_json(indent=2))
        return
    typer.echo("")
    typer.echo(
        f"  Indexed:         {report.files} files -> {report.nodes} nodes, {report.edges} edges"
    )
    typer.echo(f"  Index time:      {report.index_seconds}s ({report.files_per_second} files/s)")
    typer.echo(
        f"  Query latency:   p50 {report.query_p50_ms}ms / p95 {report.query_p95_ms}ms "
        f"({report.sampled_files} files sampled)"
    )
    typer.echo(
        f"  Token reduction: {report.token_reduction_median}x median / "
        f"{report.token_reduction_mean}x mean"
    )
    typer.echo(
        f"                   {report.baseline_tokens:,} tokens (reading files) -> "
        f"{report.topolox_tokens:,} tokens (topolox)"
    )


def main() -> None:
    """Console-script entry point for ``topolox``."""
    app()
