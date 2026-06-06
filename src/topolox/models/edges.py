"""Graph edge types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EdgeKind(StrEnum):
    """The kind of a relationship between two symbol nodes."""

    DEFINES = "defines"
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    REFERENCES = "references"


@dataclass(slots=True, frozen=True)
class Edge:
    """A directed relationship from ``src_id`` to ``dst_id``."""

    src_id: str
    dst_id: str
    kind: EdgeKind
    weight: float = 1.0
