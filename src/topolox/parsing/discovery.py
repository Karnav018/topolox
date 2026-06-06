"""Discover source files in a repository."""

from __future__ import annotations

import os
from collections.abc import Sequence
from fnmatch import fnmatch
from pathlib import Path

from topolox.parsing.languages import EXTENSION_TO_LANGUAGE

DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        ".topolox",
        "dist",
        "build",
        ".eggs",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".idea",
        ".vscode",
        ".tox",
        "site-packages",
    }
)


def discover_files(
    root: Path,
    *,
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
    respect_gitignore: bool = True,
) -> list[Path]:
    """Return parseable source files under ``root``.

    Walks the tree, pruning common build/VCS directories (and, when
    ``respect_gitignore`` is set, hidden directories), and keeps only files
    whose extension maps to a known tree-sitter language. ``include`` and
    ``exclude`` are fnmatch globs tested against the repo-relative POSIX path.
    """
    root = root.resolve()
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in DEFAULT_IGNORE_DIRS and not (respect_gitignore and d.startswith("."))
        ]
        base = Path(dirpath)
        for filename in filenames:
            file_path = base / filename
            if file_path.suffix.lower() not in EXTENSION_TO_LANGUAGE:
                continue
            rel = file_path.relative_to(root).as_posix()
            if include and not any(fnmatch(rel, pattern) for pattern in include):
                continue
            if exclude and any(fnmatch(rel, pattern) for pattern in exclude):
                continue
            results.append(file_path)
    results.sort()
    return results
