"""Discover source files in a repository (gitignore-aware)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


def discover_files(
    root: Path,
    *,
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
    respect_gitignore: bool = True,
) -> list[Path]:
    """Return the list of source files under ``root``.

    Phase 1: gitignore-aware walk with include/exclude globs.
    """
    raise NotImplementedError("Phase 1: file discovery")
