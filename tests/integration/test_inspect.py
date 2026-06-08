"""Integration tests for read_symbol / file_outline / repo_overview services."""

from __future__ import annotations

from pathlib import Path

from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.graph.resolve import resolve_imports
from topolox.parsing.extractor import SymbolExtractor
from topolox.query.outline import OutlineService
from topolox.query.overview import OverviewService
from topolox.query.source import SymbolReader

SVC_SOURCE = '''\
"""The service module."""
from pkg.db import Connection


class Service:
    """A service."""

    def start(self) -> None:
        """Start the service."""
        return None


def main() -> None:
    """Entry point."""
    return None
'''

DB_SOURCE = '''\
"""Database access."""


class Connection:
    """A DB connection."""
'''


def _index(tmp_path: Path) -> KuzuGraphStore:
    store = KuzuGraphStore(tmp_path / ".topolox" / "graph.kuzu")
    store.init_schema()
    for rel, src in (("pkg/svc.py", SVC_SOURCE), ("pkg/db.py", DB_SOURCE)):
        file_path = tmp_path / rel
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(src, encoding="utf-8")
        store.upsert(SymbolExtractor("python").extract(rel, src.encode()))
    resolve_imports(store)
    return store


def test_read_symbol_returns_exact_source(tmp_path: Path) -> None:
    store = _index(tmp_path)
    result = SymbolReader(store, tmp_path).read("main")
    assert len(result.matches) == 1
    match = result.matches[0]
    assert match.kind == "function"
    assert match.path == "pkg/svc.py"
    assert match.source.startswith("def main()")
    assert "Entry point." in match.source
    store.close()


def test_read_symbol_disambiguates_by_path(tmp_path: Path) -> None:
    store = _index(tmp_path)
    result = SymbolReader(store, tmp_path).read("start", path="pkg/svc.py")
    assert [m.qualified_name for m in result.matches] == ["pkg.svc.Service.start"]
    assert SymbolReader(store, tmp_path).read("nope").matches == []
    store.close()


def test_read_symbol_resolves_class_method_form(tmp_path: Path) -> None:
    store = _index(tmp_path)
    reader = SymbolReader(store, tmp_path)
    # The "Class.method" form is a dotted suffix of the qualified name.
    result = reader.read("Service.start")
    assert [m.qualified_name for m in result.matches] == ["pkg.svc.Service.start"]
    assert "def start(self)" in result.matches[0].source
    # Boundary-safe: a partial component is not a match.
    assert reader.read("ce.start").matches == []
    store.close()


def test_file_outline_lists_shape_with_docstrings(tmp_path: Path) -> None:
    store = _index(tmp_path)
    outline = OutlineService(store).of_file("pkg/svc.py")
    assert outline.language == "python"
    by_name = {s.name: s for s in outline.symbols}
    assert by_name["Service"].kind == "class"
    assert by_name["Service"].docstring == "A service."
    assert by_name["start"].kind == "method"
    assert by_name["main"].docstring == "Entry point."
    # Ordered by source position.
    assert [s.start_line for s in outline.symbols] == sorted(s.start_line for s in outline.symbols)
    store.close()


def test_repo_overview_counts_and_hubs(tmp_path: Path) -> None:
    store = _index(tmp_path)
    report = OverviewService(store).summary()
    assert report.files == 2
    assert report.symbols >= 4
    assert report.languages == {"python": 2}
    # svc.py imports db.py, so db.py is a hub.
    assert report.hubs[0].path == "pkg/db.py"
    assert report.hubs[0].dependents == 1
    store.close()
