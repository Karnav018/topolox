"""Integration tests for the call-graph and class-hierarchy query services."""

from __future__ import annotations

from pathlib import Path

from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.graph.resolve import resolve_calls, resolve_imports, resolve_inheritance
from topolox.parsing.extractor import SymbolExtractor
from topolox.query.calls import CallGraphService
from topolox.query.hierarchy import HierarchyService

SOURCE = """\
class Animal:
    def speak(self):
        return self.noise()

    def noise(self):
        return "..."


class Dog(Animal):
    def bark(self):
        return woof()


def woof():
    return "woof"


def main():
    Dog()
    woof()
"""


def _graph(tmp_path: Path) -> KuzuGraphStore:
    store = KuzuGraphStore(tmp_path / "g.kuzu")
    store.init_schema()
    store.upsert(SymbolExtractor("python").extract("zoo.py", SOURCE.encode()))
    resolve_inheritance(store)
    resolve_calls(store)
    return store


def test_callees(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    report = CallGraphService(store).callees("main")
    assert report.direction == "callees"
    assert report.matched == ["zoo.main"]
    names = {n.name for n in report.neighbors}
    assert {"Dog", "woof"} <= names  # constructor call + function call
    store.close()


def test_callers(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    report = CallGraphService(store).callers("woof")
    assert report.direction == "callers"
    assert {n.qualified_name for n in report.neighbors} == {"zoo.Dog.bark", "zoo.main"}
    store.close()


def test_class_hierarchy(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    hierarchy = HierarchyService(store)

    dog = hierarchy.of_class("Dog")
    assert [s.qualified_name for s in dog.supertypes] == ["zoo.Animal"]
    assert dog.subtypes == []

    animal = hierarchy.of_class("Animal")
    assert [s.qualified_name for s in animal.subtypes] == ["zoo.Dog"]
    assert animal.supertypes == []
    store.close()


def test_resolves_class_method_form(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    calls = CallGraphService(store)
    # "Class.method" is a dotted suffix of the qualified name, not an exact match.
    report = calls.callees("Dog.bark")
    assert report.matched == ["zoo.Dog.bark"]
    assert "woof" in {n.name for n in report.neighbors}
    # Boundary-safe: a partial path component does not resolve.
    assert calls.callees("og.bark").matched == []
    store.close()


def test_unknown_symbol_is_empty(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    report = CallGraphService(store).callees("does_not_exist")
    assert report.matched == []
    assert report.neighbors == []
    store.close()


# `connect` is defined in two files; service.py imports the one in db.py.
IMPORT_AWARE = {
    "db.py": "def connect():\n    return 1\n",
    "cache.py": "def connect():\n    return 2\n",
    "service.py": "from db import connect\n\n\ndef use():\n    return connect()\n",
}


def test_import_aware_resolution_picks_the_imported_definition(tmp_path: Path) -> None:
    store = KuzuGraphStore(tmp_path / "g.kuzu")
    store.init_schema()
    for rel, src in IMPORT_AWARE.items():
        store.upsert(SymbolExtractor("python").extract(rel, src.encode()))
    resolve_imports(store)
    resolve_calls(store)

    callees = CallGraphService(store).callees("use", path="service.py")
    # Globally ambiguous (db.connect vs cache.connect) — resolved via the import.
    assert [n.qualified_name for n in callees.neighbors] == ["db.connect"]

    # And db.connect's caller is service.use, not anything in cache.py.
    callers = CallGraphService(store).callers("connect", path="db.py")
    assert {n.qualified_name for n in callers.neighbors} == {"service.use"}
    store.close()
