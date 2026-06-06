"""Graph node types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class NodeKind(StrEnum):
    """The kind of a symbol node in the graph."""

    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"


@dataclass(slots=True, frozen=True)
class Span:
    """A byte/line range within a source file."""

    start_byte: int
    end_byte: int
    start_line: int
    end_line: int


@dataclass(slots=True, frozen=True)
class SymbolNode:
    """A code symbol (file, class, function, ...) extracted from source."""

    id: str
    kind: NodeKind
    name: str
    qualified_name: str
    path: str
    language: str
    span: Span
    signature: str | None = None
    docstring: str | None = None
