"""Parallel parsing across CPU cores via ``ProcessPoolExecutor``."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from topolox.models.graph import ParseResult
from topolox.parsing.worker import parse_file


def parse_repo(
    paths: Sequence[Path],
    *,
    root: Path,
    max_workers: int | None = None,
) -> Iterator[ParseResult]:
    """Parse all ``paths`` in parallel, yielding results as they complete.

    Files are dispatched to a process pool (bypassing the GIL). ``root`` is used
    to compute stable, repo-relative ids.
    """
    root = root.resolve()
    items: list[tuple[str, str]] = []
    for path in paths:
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(root).as_posix()
        except ValueError:
            rel = resolved.name
        items.append((str(resolved), rel))

    if not items:
        return

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(parse_file, item) for item in items]
        for future in as_completed(futures):
            yield future.result()
