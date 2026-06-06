"""Subprocess entry point for parsing a single file.

This must stay a top-level function so it is picklable by ``ProcessPoolExecutor``.
"""

from __future__ import annotations

from pathlib import Path

from topolox.models.graph import ParseResult
from topolox.parsing.extractor import SymbolExtractor
from topolox.parsing.languages import language_for


def parse_file(item: tuple[str, str]) -> ParseResult:
    """Parse one file into a :class:`ParseResult`.

    ``item`` is ``(absolute_path, repo_relative_path)``. The parser is built and
    cached per worker process (parsers are not picklable). This never raises —
    failures are returned via :attr:`ParseResult.error` so one bad file cannot
    crash the pool.
    """
    abs_path, rel_path = item
    language = language_for(Path(abs_path))
    if language is None:
        return ParseResult(path=rel_path, language="", error="unsupported file type")
    try:
        source = Path(abs_path).read_bytes()
    except OSError as exc:
        return ParseResult(path=rel_path, language=language, error=f"read error: {exc}")
    try:
        return SymbolExtractor(language).extract(rel_path, source)
    except Exception as exc:
        return ParseResult(path=rel_path, language=language, error=f"parse error: {exc}")
