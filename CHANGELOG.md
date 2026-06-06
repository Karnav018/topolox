# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Daemon (Phase 2): incremental `Indexer.update()` (re-parse changed files in-process, content-hash skip, prune stale symbols, handle deletions) and a `watchdog` watcher → debounced async service that patches the graph + vectors in milliseconds. Wired as `topolox daemon` (initial index, then live watch).
- MCP server (Phase 2): a FastMCP server exposing `get_file_dependencies`, `analyze_blast_radius`, `prune_context`, and `search_architecture_graph` (async, thread-offloaded) to Claude Code / Cursor. `topolox mcp serve` runs it over stdio; `topolox mcp install` writes the client config (`.mcp.json` / `.cursor/mcp.json`). Tested via an in-memory FastMCP client.
- Query engine (Phase 2): blast-radius simulation (transitive downstream importers), LanceDB vector search, a `FastEmbedEmbedder` (local ONNX embeddings via the `[embeddings]` extra), and a hybrid `ContextPruner` (vector seeds → graph expansion → token-budget cap). Wired as `topolox blast` and `topolox prune`; `topolox index` now uses real embeddings when `fastembed` is installed.
- Storage & indexing (Phase 1): embedded Kùzu graph store (`Symbol` nodes + `Rel` edges, idempotent MERGE upserts) and LanceDB vector store behind their ports; `Indexer.build()` wiring the parser pool into both stores. `topolox index` now persists to `.topolox/`, and `topolox deps <file>` reports module-level dependencies/dependents.
- Core parser (Phase 1): gitignore-aware file discovery, tree-sitter symbol/edge extraction (functions, classes, methods, imports), a picklable worker, and a `ProcessPoolExecutor` pool. `topolox index --dry-run` parses a repo and prints node/edge counts.
- Project scaffold: `src/` layout, packaging (`pyproject.toml`), and tooling (uv, ruff, mypy, pytest).
- Core data contracts (`SymbolNode`, `Edge`, `ParseResult`, query DTOs) and store ports (`GraphStore`, `VectorStore`, `Embedder`).
- CLI skeleton (`topolox`) and module stubs for parser, stores, indexer, query, daemon, MCP, and TUI.
- Open-source project files: README, license, contributing guide, code of conduct, security policy, CI, and issue/PR templates.

[Unreleased]: https://github.com/Karnav018/topolox/commits/main
