# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3] - 2026-06-06

### Fixed
- Cross-file **dependents and blast radius** now work on `src/`- and monorepo layouts. An import-resolution pass links bare import names (e.g. `app.db`) to the file they actually name (e.g. `apps/api/app/db.py`) when the match is unique, so `analyze_blast_radius` and `get_file_dependencies` traverse the real file graph instead of returning empty.

### Changed
- The MCP server now ships usage **instructions** and sharper, directive tool descriptions so agents reach for the tools proactively (instead of grepping/reading files).

### Docs
- Clarify that a separate `topolox daemon` and an agent's MCP server cannot run at the same time (Kùzu allows a single writer); the README quickstart no longer starts the daemon alongside the agent, and notes the read-only multi-agent model + the planned combined live server.

## [0.1.2] - 2026-06-06

### Fixed
- MCP server and the `deps` / `prune` / `blast` CLIs now open the Kùzu graph **read-only**, so they coexist with a running `topolox daemon` (Kùzu allows one writer + many readers) and with multiple agents. Previously, connecting an agent while the daemon held the write lock crashed the server with `Could not set lock` ("MCP error -32000: Connection closed"). The server also seeds an empty graph if none exists yet and suppresses the FastMCP stdout banner.

## [0.1.1] - 2026-06-06

### Changed
- Set the package author email and the security / code-of-conduct contact address.

## [0.1.0] - 2026-06-06

### Added
- Multi-language extraction: a config-driven (per-language `LangSpec`) generalized extractor now pulls functions/classes/methods/imports from Python, JavaScript/JSX, TypeScript/TSX, Go, Rust, Java, C, C++, C#, Ruby, PHP, Kotlin, Swift, and Scala; any other tree-sitter-language-pack grammar is parsed and indexed at the file level.
- Multi-agent `topolox mcp install`: registers the MCP server with Claude Code, Cursor, OpenAI Codex CLI (TOML), Gemini CLI, VS Code (`servers` key), Windsurf, and Claude Desktop, merging existing config.
- Daemon (Phase 2): incremental `Indexer.update()` (re-parse changed files in-process, content-hash skip, prune stale symbols, handle deletions) and a `watchdog` watcher → debounced async service that patches the graph + vectors in milliseconds. Wired as `topolox daemon` (initial index, then live watch).
- MCP server (Phase 2): a FastMCP server exposing `get_file_dependencies`, `analyze_blast_radius`, `prune_context`, and `search_architecture_graph` (async, thread-offloaded) to Claude Code / Cursor. `topolox mcp serve` runs it over stdio; `topolox mcp install` writes the client config (`.mcp.json` / `.cursor/mcp.json`). Tested via an in-memory FastMCP client.
- Query engine (Phase 2): blast-radius simulation (transitive downstream importers), LanceDB vector search, a `FastEmbedEmbedder` (local ONNX embeddings via the `[embeddings]` extra), and a hybrid `ContextPruner` (vector seeds → graph expansion → token-budget cap). Wired as `topolox blast` and `topolox prune`; `topolox index` now uses real embeddings when `fastembed` is installed.
- Storage & indexing (Phase 1): embedded Kùzu graph store (`Symbol` nodes + `Rel` edges, idempotent MERGE upserts) and LanceDB vector store behind their ports; `Indexer.build()` wiring the parser pool into both stores. `topolox index` now persists to `.topolox/`, and `topolox deps <file>` reports module-level dependencies/dependents.
- Core parser (Phase 1): gitignore-aware file discovery, tree-sitter symbol/edge extraction (functions, classes, methods, imports), a picklable worker, and a `ProcessPoolExecutor` pool. `topolox index --dry-run` parses a repo and prints node/edge counts.
- Project scaffold: `src/` layout, packaging (`pyproject.toml`), and tooling (uv, ruff, mypy, pytest).
- Core data contracts (`SymbolNode`, `Edge`, `ParseResult`, query DTOs) and store ports (`GraphStore`, `VectorStore`, `Embedder`).
- CLI skeleton (`topolox`) and module stubs for parser, stores, indexer, query, daemon, MCP, and TUI.
- Open-source project files: README, license, contributing guide, code of conduct, security policy, CI, and issue/PR templates.

[Unreleased]: https://github.com/Karnav018/topolox/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/Karnav018/topolox/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/Karnav018/topolox/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Karnav018/topolox/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Karnav018/topolox/releases/tag/v0.1.0
