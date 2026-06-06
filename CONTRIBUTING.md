# Contributing to Topolox

Thanks for your interest! Topolox is in early development — see [ROADMAP.md](ROADMAP.md) for the phase plan.

## Development setup

Topolox uses [uv](https://docs.astral.sh/uv/) for environment and dependency management.

```bash
git clone https://github.com/Karnav018/topolox.git
cd topolox
uv sync                       # creates .venv, installs deps + dev tools
uv run pre-commit install     # optional: enable git hooks
```

The project targets Python 3.11–3.13. `uv` will fetch the pinned interpreter automatically (see `.python-version`).

## Before you push

All of these run in CI and must pass:

```bash
uv run ruff check .           # lint
uv run ruff format --check .  # formatting
uv run mypy src               # static types (strict)
uv run pytest                 # tests
```

`uv run ruff check --fix .` and `uv run ruff format .` fix most issues automatically.

## Guidelines

- **Match the surrounding code** — typing is strict; annotate everything in `src/`.
- **Keep the engine deterministic.** Graph construction must not call an LLM; the LLM is only used at query time by the consuming agent.
- **New ports go behind a Protocol.** Storage backends implement `GraphStore` / `VectorStore` (see `src/topolox/graph/store.py`, `src/topolox/vectors/store.py`).
- **Conventional commits** are appreciated (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

## Pull request flow

`main` is a **protected branch** — every change lands through a pull request that
the maintainer ([@Karnav018](https://github.com/Karnav018), the code owner) reviews
and approves. Direct pushes to `main` are disabled.

1. **Fork** the repository, then create a feature branch off `main`:
   ```bash
   git checkout -b feat/short-description
   ```
2. Make your change **with tests**, and add a note under *Unreleased* in `CHANGELOG.md`.
3. Run the checks above (`ruff`, `mypy`, `pytest`) and make sure they pass.
4. **Push to your fork** and **open a pull request** against `Karnav018/topolox:main`,
   describing the change and linking any related issue (e.g. `Closes #123`).
5. CI runs automatically and the maintainer is auto-requested for review (via
   [`CODEOWNERS`](.github/CODEOWNERS)). Address any feedback; a maintainer merges
   once the PR is **approved** and **green**.

By contributing you agree your work is licensed under the project's
[MIT License](LICENSE) and that you follow the [Code of Conduct](CODE_OF_CONDUCT.md).
