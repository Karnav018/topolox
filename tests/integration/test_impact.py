"""Integration tests for symbol-level blast radius (call-graph traversal)."""

from __future__ import annotations

from pathlib import Path

from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.graph.resolve import resolve_calls, resolve_inheritance
from topolox.parsing.extractor import SymbolExtractor
from topolox.query.impact import SymbolImpactService

DB = """\
def connect():
    return 1
"""

SERVICE = """\
from db import connect


def load_user():
    return connect()


def handler():
    return load_user()
"""

TEST = """\
from service import handler


def test_handler():
    assert handler()
"""


def _graph(tmp_path: Path) -> KuzuGraphStore:
    store = KuzuGraphStore(tmp_path / "g.kuzu")
    store.init_schema()
    for rel, src in (("db.py", DB), ("service.py", SERVICE), ("tests/test_app.py", TEST)):
        store.upsert(SymbolExtractor("python").extract(rel, src.encode()))
    resolve_calls(store)
    resolve_inheritance(store)
    return store


def test_transitive_impact_reaches_tests(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    report = SymbolImpactService(store).analyze("connect", path="db.py")

    impacted = {s.qualified_name for s in report.impacted_symbols}
    assert {"service.load_user", "service.handler", "tests.test_app.test_handler"} <= impacted
    assert "tests/test_app.py" in report.impacted_files
    assert report.impacted_tests == ["tests/test_app.py"]
    assert report.max_depth >= 3
    store.close()


def test_depth_limit_truncates(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    report = SymbolImpactService(store).analyze("connect", path="db.py", max_depth=1)
    # Only direct callers of connect() at depth 1.
    assert {s.qualified_name for s in report.impacted_symbols} == {"service.load_user"}
    store.close()


def test_unknown_symbol_is_empty(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    report = SymbolImpactService(store).analyze("nope")
    assert report.matched == []
    assert report.impacted_symbols == []
    store.close()
