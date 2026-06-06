# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Core parser (Phase 1): gitignore-aware file discovery, tree-sitter symbol/edge extraction (functions, classes, methods, imports), a picklable worker, and a `ProcessPoolExecutor` pool. `topolox index --dry-run` parses a repo and prints node/edge counts.
- Project scaffold: `src/` layout, packaging (`pyproject.toml`), and tooling (uv, ruff, mypy, pytest).
- Core data contracts (`SymbolNode`, `Edge`, `ParseResult`, query DTOs) and store ports (`GraphStore`, `VectorStore`, `Embedder`).
- CLI skeleton (`topolox`) and module stubs for parser, stores, indexer, query, daemon, MCP, and TUI.
- Open-source project files: README, license, contributing guide, code of conduct, security policy, CI, and issue/PR templates.

[Unreleased]: https://github.com/Karnav018/topolox/commits/main
