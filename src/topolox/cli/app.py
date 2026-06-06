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
) -> None:
    """Index a repository into the graph + vector store."""
    typer.echo(_NOT_YET.format(phase="Phase 1"))


@app.command()
def daemon(
    path: Annotated[Path, typer.Argument(help="Repository root to watch.")] = Path(),
) -> None:
    """Watch a repository and keep the index live."""
    typer.echo(_NOT_YET.format(phase="Phase 2"))


@app.command()
def mcp() -> None:
    """Start the FastMCP server for Claude Code / Cursor."""
    typer.echo(_NOT_YET.format(phase="Phase 2"))


@app.command()
def deps(
    file: Annotated[str, typer.Argument(help="File to inspect.")],
    depth: Annotated[int, typer.Option(help="Traversal depth.")] = 1,
) -> None:
    """Show dependencies and dependents of a file."""
    typer.echo(_NOT_YET.format(phase="Phase 2"))


@app.command()
def prune(
    prompt: Annotated[str, typer.Argument(help="The agent prompt.")],
    budget: Annotated[int, typer.Option(help="Token budget.")] = 8000,
) -> None:
    """Return pruned context for a prompt."""
    typer.echo(_NOT_YET.format(phase="Phase 2"))


@app.command()
def blast(
    files: Annotated[list[str], typer.Argument(help="Changed files.")],
    depth: Annotated[int, typer.Option(help="Max traversal depth.")] = 3,
) -> None:
    """Simulate the blast radius of changing files."""
    typer.echo(_NOT_YET.format(phase="Phase 2"))


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
