# Topolox — Roadmap

> **The topological memory and architecture layer for AI coding agents.**

Topolox gives AI coding agents (Claude Code, Cursor) instant, deep understanding of large codebases. Instead of burning tokens reading thousands of files, it feeds an agent exactly the context it needs using an **embedded hybrid graph + vector engine** — kept live by a background daemon and exposed over MCP and an optional terminal cockpit.

**Status:** 🌱 Pre-alpha — greenfield. Phase 1 in progress.
**License:** MIT · **Language:** Python 3.11+ (open source)

---

## How it's used (two modes)

1. **Invisible backend (MCP)** — `topolox index .`, register once (`topolox mcp install`), and your existing agent (Claude Code / Cursor) silently pulls grounded, cheap context. You never see Topolox; your agent just gets smart on a big repo.
2. **The TUI cockpit** — `topolox` opens a 3-pane terminal dashboard (agent chat · live knowledge graph · daemon log) to *see* what the agent sees and explore the architecture.

---

## Architecture at a glance

```
discover → parse (multiprocessing tree-sitter) → ParseResult
        → index → Kùzu (graph) + LanceDB (vectors)
        → query (dependencies · context pruner · blast radius)
        → MCP tools  +  CLI  +  Textual TUI
   ┌ watchdog daemon patches the graph live on every file save ┐
```

**Tech stack (verified, mid-2026):** `kuzu==0.11.3` (graph) · `lancedb>=0.33` (vectors) · `tree-sitter>=0.25` + `tree-sitter-language-pack>=1.8` (AST) · `fastmcp>=3.4` (MCP server) · `watchdog>=6` (daemon) · `textual>=8.2` (TUI) · `typer>=0.12` (CLI) · `pydantic>=2.7` + `pydantic-settings`. Optional: `fastembed>=0.8` (`[embeddings]`), `anthropic>=0.105` (`[llm]`). Tooling: **uv** + **hatchling**, **ruff**, **mypy**, **pytest**.

---

## The 3 Phases

### 🧱 Phase 1 — Core Engine: Index & Store
**Goal:** turn any repo into a persistent, queryable architecture graph — fast and GIL-free.

**Build:**
- **Open-source scaffold** — `src/` layout, `pyproject.toml` (PyPI metadata, scripts, tool config), `README` / `LICENSE` / `CONTRIBUTING` / `CODE_OF_CONDUCT` / `CHANGELOG` / `SECURITY`, `.github/` CI (ruff + mypy + pytest, py3.11–3.13) + release workflow, pre-commit, `git init`.
- **Contracts** — `models/` (`SymbolNode`, `Edge`, picklable `ParseResult`, query DTOs) + store **Protocols** (`GraphStore`, `VectorStore`, `Embedder`).
- **Parser** — gitignore-aware discovery → tree-sitter extraction (`.scm` queries) → picklable `parse_file` worker → `ProcessPoolExecutor` pool. Python-first.
- **Storage & indexing** — Kùzu schema/writer (behind the `GraphStore` port) + LanceDB store + `Indexer.build()`.

**Deliverable:** `topolox index .` parses the repo across all cores and persists the graph + vectors to `.topolox/`; `topolox deps <file>` lists dependencies/dependents.

**Exit:** `uv sync` + `topolox --help` work · `index` persists to embedded DBs · ruff + mypy(strict) + pytest green · CI passing · repo publishable.

---

### ⚡ Phase 2 — Live Intelligence & Agent Interface
**Goal:** the core product — AI agents get live, grounded, low-token context.

**Build:**
- **Query engine** — `dependencies`, **context pruner** (vector seeds → k-hop graph expansion → blended score, token-budget aware), **blast radius** (downstream traversal in Kùzu Cypher). Enable `fastembed` embeddings + real LanceDB semantic search.
- **The daemon** — watchdog observer → debounced → `Indexer.update()` (content-hash skip, ms-level patches, deletions).
- **MCP server** — FastMCP exposing `get_file_dependencies`, `prune_context`, `analyze_blast_radius`, `search_architecture_graph` (async). **Frictionless registration:** `topolox mcp install` auto-writes config for Claude Code / Cursor + a committable `.mcp.json`.

**Deliverable:** `topolox daemon` keeps the graph live; `topolox mcp` serves the tools; Claude Code / Cursor make accurate, cheap edits using Topolox context.

**Exit:** daemon patches on save in ms · all four MCP tools return valid typed output to a real client · measurable token reduction with maintained answer quality on a test repo.

---

### 🪟 Phase 3 — Cockpit & Release
**Goal:** the human-facing dashboard, proof of value, and a public release.

**Build:**
- **Textual TUI** — `tmux`-style 3-pane dashboard (left: agent chat via the `anthropic` `[llm]` extra or stub · top-right: live knowledge-graph / blast-radius view · bottom-right: daemon log). Decoupled data-providers so it runs offline against stubs. `topolox` / `topolox ui`.
- **Benchmarks** — `topolox benchmark`: token-reduction + retrieval recall@k vs naive/RAG baselines; optional SWE-bench-style A/B harness.
- **Hardening & release** — perf passes (parser throughput, incremental correctness, MCP p95, TUI <16ms), docs, `CHANGELOG`, **tag → PyPI** via trusted publishing.

**Deliverable:** `pip install topolox` from PyPI; `topolox` opens the cockpit; benchmarks documented in the README.

**Exit:** TUI reflects live changes (`run_test` Pilot tests pass) · benchmark numbers published · package on PyPI.

---

## Key design decisions
- **Code is 100% Python; compiled wheels under the hood are fine** (Kùzu C++, LanceDB Rust, tree-sitter C) — we never write/compile native code.
- **Kùzu pinned `0.11.3`** (archived upstream) **behind a `GraphStore` Protocol** → the graph is a rebuildable cache, so swapping the backend later is a one-file change.
- **Embeddings local by default** (`fastembed`, optional extra; `NullEmbedder` fallback) — offline, no API key, keeps the core light.
- **FastMCP = PrefectHQ `fastmcp`** (not an "Anthropic SDK").
- **Deterministic build, zero tokens** — the graph is built by mechanical AST + embeddings, not LLM extraction; the LLM is only used at *query* time by the consuming agent.

## Backlog (post-3-phase)
- Time-Travel Architecture Diffing (snapshot the graph across git commits / PRs).
- Multi-Repo / cross-service mapping.
- Additional language grammars (trivial via `tree-sitter-language-pack`).

## Contributing
Dev setup: `uv sync` → `uv run ruff check` · `uv run mypy --strict src` · `uv run pytest`. See `CONTRIBUTING.md` (added in Phase 1). Issues and PRs welcome once the repo is public.
