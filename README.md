# Topolox

> **The topological memory and architecture layer for AI coding agents.**

[![CI](https://github.com/Karnav018/topolox/actions/workflows/ci.yml/badge.svg)](https://github.com/Karnav018/topolox/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)](ROADMAP.md)

Topolox gives AI coding agents (Claude Code, Cursor) **instant, deep understanding of large codebases**. Instead of burning tokens reading thousands of files, it feeds an agent exactly the context it needs using an embedded **hybrid graph + vector engine** — kept live by a background daemon and exposed over **MCP** and an optional terminal cockpit.

> ⚠️ **Pre-alpha.** The scaffold and contracts are in place; the engine is being built phase by phase. See [ROADMAP.md](ROADMAP.md).

## Why

On a big repo, an AI agent is *smart but blind*: it either reads dozens of files (slow, expensive) or misses a downstream caller and breaks something. Topolox is the **memory + map** the agent reads from — deterministic, instantly rebuildable, and zero-token to build.

## How it works

```
discover → parse (multiprocessing tree-sitter) → ParseResult
        → index → Kùzu (graph) + LanceDB (vectors)
        → query (dependencies · context pruner · blast radius)
        → MCP tools  +  CLI  +  Textual TUI
   ┌ watchdog daemon patches the graph live on every file save ┐
```

## Two ways to use it

1. **Invisible backend (MCP).** Index once, register with your agent, and Claude Code / Cursor silently pull grounded, cheap context.
   ```bash
   topolox index .
   topolox mcp install      # writes MCP config for Claude Code / Cursor
   topolox daemon           # keep the graph live in the background
   ```
2. **The TUI cockpit.** A 3-pane terminal dashboard (agent chat · live knowledge graph · daemon log).
   ```bash
   topolox                  # launches the dashboard in the current repo
   ```

## Install (from source)

```bash
git clone https://github.com/Karnav018/topolox.git
cd topolox
uv sync
uv run topolox --help
```

## Development

```bash
uv sync                       # create the env + install dev tools
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy src               # type-check (strict)
uv run pytest                 # tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributions welcome once the engine lands.

## Tech stack

Python 3.11+ · [Kùzu](https://kuzudb.com) (graph) · [LanceDB](https://lancedb.com) (vectors) · [tree-sitter](https://tree-sitter.github.io) (AST) · [FastMCP](https://gofastmcp.com) (MCP server) · [watchdog](https://github.com/gorakhargosh/watchdog) (daemon) · [Textual](https://textual.textualize.io) (TUI) · [Typer](https://typer.tiangolo.com) (CLI). Optional: `fastembed` (local embeddings), `anthropic` (TUI chat).

## License

[MIT](LICENSE)
