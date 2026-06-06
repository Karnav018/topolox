"""Tests for tree-sitter symbol extraction."""

from __future__ import annotations

from pathlib import Path

from topolox.models.edges import EdgeKind
from topolox.models.nodes import NodeKind
from topolox.parsing.extractor import SymbolExtractor
from topolox.parsing.worker import parse_file

SOURCE = b"""import os
from pkg.db import Connection


class Service:
    def start(self) -> None:
        pass


def main() -> None:
    pass
"""


def test_extracts_symbols_and_edges() -> None:
    result = SymbolExtractor("python").extract("pkg/svc.py", SOURCE)
    assert result.error is None

    by_kind: dict[NodeKind, list[str]] = {}
    for node in result.nodes:
        by_kind.setdefault(node.kind, []).append(node.name)

    assert by_kind[NodeKind.FILE] == ["svc.py"]
    assert "Service" in by_kind[NodeKind.CLASS]
    assert "main" in by_kind[NodeKind.FUNCTION]
    assert "start" in by_kind[NodeKind.METHOD]

    imports = {e.dst_id for e in result.edges if e.kind == EdgeKind.IMPORTS}
    assert "os" in imports
    assert "pkg.db" in imports
    assert result.content_hash


def test_worker_parses_real_file(sample_repo: Path) -> None:
    path = sample_repo / "pkg" / "auth.py"
    result = parse_file((str(path), "pkg/auth.py"))
    assert result.error is None
    names = {n.name for n in result.nodes}
    assert {"login", "verify"} <= names
