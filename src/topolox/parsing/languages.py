"""Map file extensions to tree-sitter languages and cache parsers."""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Parser

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
}


def language_for(path: Path) -> str | None:
    """Return the tree-sitter language name for ``path``, or ``None``."""
    return EXTENSION_TO_LANGUAGE.get(path.suffix.lower())


@cache
def get_parser_for(language: str) -> Parser:
    """Return a cached tree-sitter ``Parser`` for ``language``.

    Built per-process (parsers are not picklable). Uses the standard
    ``tree_sitter.Parser`` with a grammar from ``tree_sitter_language_pack``
    (the pack's own ``get_parser`` returns a non-standard, str-only parser).
    """
    from tree_sitter import Parser
    from tree_sitter_language_pack import get_language

    return Parser(get_language(language))
