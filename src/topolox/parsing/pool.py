"""Parallel parsing across CPU cores via ``ProcessPoolExecutor``."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from topolox.models.graph import ParseResult


def parse_repo(
    paths: Sequence[Path],
    *,
    max_workers: int | None = None,
) -> Iterator[ParseResult]:
    """Parse all ``paths`` in parallel, yielding results as they complete.

    Phase 1: ``ProcessPoolExecutor`` + ``as_completed``.
    """
    raise NotImplementedError("Phase 1: process pool")
