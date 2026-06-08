# Topolox

> **The topological memory and architecture layer for AI coding agents.**

[![CI](https://github.com/Karnav018/topolox/actions/workflows/ci.yml/badge.svg)](https://github.com/Karnav018/topolox/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)](ROADMAP.md)

Topolox gives AI coding agents (Claude Code, Cursor) **instant, deep understanding of large codebases**. Instead of burning tokens reading thousands of files, it feeds an agent exactly the context it needs using an embedded **hybrid graph + vector engine** — kept live by a background daemon and exposed over **MCP** and an optional terminal cockpit.

> ⚠️ **Pre-alpha but usable.** The engine — multiprocessing parser, Kùzu + LanceDB index, query layer, MCP server, daemon, and 14-language support — is built and **on PyPI**. The TUI and benchmarks are next; see [ROADMAP.md](ROADMAP.md).

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

## Topolox vs. Graphify

Graphify pioneered "drop in a folder, get a knowledge graph." Topolox takes that idea in a different direction: an **always-on, agent-native engine for code**. They're built for different jobs.

| | **Graphify** | **Topolox** |
| :--- | :--- | :--- |
| **Form factor** | A Claude Code *skill* (`/graphify`) | A standalone *service*: CLI + MCP server + daemon |
| **Graph build** | AST **+ LLM extraction** (Claude subagents / Gemini) | **Pure deterministic** AST (multiprocessing tree-sitter) |
| **When the LLM runs** | At **build** time — spends tokens on every build | Only at **query** time (the consuming agent); build is **zero-token** |
| **Storage** | Static `graph.json` + in-memory NetworkX | Embedded **Kùzu** (graph) + **LanceDB** (vectors), on disk |
| **Retrieval** | Lexical substring + IDF + BFS/DFS traversal | **Vector** semantic search + graph traversal (hybrid) |
| **Live updates** | Opt-in `--watch` / git hook / manual `--update` | **watchdog daemon**, ms-level incremental patches |
| **Agent access** | Optional MCP (7 read-only tools) + Markdown reports | **MCP-native** (11 tools), `mcp install` for every agent |
| **Inputs** | Code **+ docs + papers + images + video** | Code — 14 languages richly, 300+ at the file level |
| **Signature features** | Community detection, "god nodes", multi-modal RAG | Blast radius, dependency maps, context pruner, resolved call graph |
| **Concurrency** | Single graph, in-memory | Multiprocessing + asyncio, embedded DBs |

**In short:** Graphify is a broad, **multi-modal, LLM-enriched** knowledge-graph builder you invoke as a skill — its graph is *richer* on inferred relationships. Topolox is a narrow, **deterministic, zero-token, always-live code engine** that any MCP agent reads from — *faster, cheaper, and instantly rebuildable*. That's the trade Topolox makes to be an always-on backend.

## Two ways to use it

1. **Invisible backend (MCP).** Index once, register with your agent, and any MCP client silently pulls grounded, cheap context.
   ```bash
   topolox index .
   topolox mcp install      # registers with Claude Code, Cursor, Codex, Gemini CLI, VS Code, ...
   ```
   Then connect your agent — its MCP server reads the index **read-only**, so several agents
   (Claude Code, Cursor, …) can connect at once. Re-run `topolox index` to refresh.

   > ⚠️ **One writer at a time.** Kùzu lets only one process write the database, so **don't run
   > `topolox daemon` while an agent is connected** — they'd fight over the lock (`MCP error
   > -32000: Connection closed`). A combined always-live server (one process that watches *and*
   > serves over HTTP) is on the [roadmap](ROADMAP.md).
2. **The TUI cockpit** *(planned — Phase 3).* A 3-pane terminal dashboard (agent chat · live knowledge graph · daemon log), `topolox ui`. See [ROADMAP.md](ROADMAP.md).

## Supported languages & agents

**Languages** — symbol + import extraction for Python, JavaScript/JSX, TypeScript/TSX, Go, Rust, Java, C, C++, C#, Ruby, PHP, Kotlin, Swift, and Scala; any other [tree-sitter-language-pack](https://github.com/Goldziher/tree-sitter-language-pack) grammar (300+) is still parsed and indexed at the file level.

**Agents** — `topolox mcp install` registers the MCP server with **Claude Code, Cursor, OpenAI Codex CLI, Gemini CLI, VS Code, Windsurf, and Claude Desktop** (and any other MCP client — it's a standard stdio MCP server).

## The tools your agent gets

| Tool | Use it for |
| :--- | :--- |
| `get_file_dependencies(path, depth)` | what a file imports, and what imports it |
| `analyze_blast_radius(changed_files, max_depth)` | which files/tests a change would impact |
| `prune_context(prompt, token_budget)` | the most relevant symbols/files for a prompt |
| `search_architecture_graph(query, limit)` | semantic + structural search over the codebase |
| `read_symbol(name, path)` | the exact source of one function/class — read just it, not the whole file |
| `file_outline(path)` | a file's shape (classes/functions, signatures, docstrings) without reading it |
| `repo_overview()` | orient on an unfamiliar repo — size, languages, and the hub files everything imports |
| `get_callers(name, path)` | functions/methods that call a symbol — precise "what breaks if I change this?" |
| `get_callees(name, path)` | what a function calls — trace how it works without reading it |
| `class_hierarchy(name, path)` | a class's direct supertypes and subtypes (what it extends, what extends it) |
| `analyze_symbol_impact(name, path, max_depth)` | symbol-level blast radius — the exact functions/tests that transitively reach a symbol |

Nudge the agent with *"Using topolox, …"* so it reaches for these instead of grepping. `deps`, `blast`, `outline`, `overview`, and the call-graph/hierarchy tools are graph-based and most reliable; `search`/`prune` ranking improves with the `[embeddings]` extra. The natural loop: `search`/`prune` or `outline` to find the symbol, then `read_symbol` to pull only its source. The call-graph tools (`get_callers`/`get_callees`, `class_hierarchy`, `analyze_symbol_impact`) run on a resolved Python call graph — links are best-effort (same-file first, then a unique repo-wide match), so ambiguous or external calls are omitted rather than guessed. `analyze_symbol_impact` is the symbol-precise complement to the file-level `analyze_blast_radius`: it walks transitive callers (and subclasses) and flags which impacted files are tests, so an agent runs just the tests a change can reach.

## CLI

```bash
topolox index .                 # build / refresh the index in .topolox/
topolox index --dry-run .       # preview what gets parsed (no writes)
topolox deps     <file>         # dependencies + dependents of a file
topolox blast    <file...>      # blast radius of changing file(s)
topolox prune    "<question>"   # pruned, token-budgeted context
topolox outline  <file>         # a file's symbols (its shape) without reading it
topolox read     <symbol>       # the exact source of a symbol by name
topolox overview                # repo size, languages, and hub files
topolox callers  <symbol>       # functions/methods that call a symbol
topolox callees  <symbol>       # what a symbol calls
topolox hierarchy <class>       # a class's supertypes and subtypes
topolox impact   <symbol>       # symbol-level blast radius (callers/subclasses + tests)
topolox mcp install [--client claude-code|cursor|codex|gemini|vscode|windsurf|claude-desktop|all]
topolox mcp serve               # run the MCP server over stdio (agents usually spawn this)
```

## Install

```bash
pip install topolox                 # from PyPI  (or: uv tool install topolox)
pip install 'topolox[embeddings]'   # optional — local embeddings for semantic search / prune
```

From source:

```bash
git clone https://github.com/Karnav018/topolox.git
cd topolox && uv sync && uv run topolox --help
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
