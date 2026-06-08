"""Integration tests for the call-graph and class-hierarchy query services."""

from __future__ import annotations

from pathlib import Path

from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.graph.resolve import resolve_calls, resolve_inheritance
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


def test_unknown_symbol_is_empty(tmp_path: Path) -> None:
    store = _graph(tmp_path)
    report = CallGraphService(store).callees("does_not_exist")
    assert report.matched == []
    assert report.neighbors == []
    store.close()
