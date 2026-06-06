"""Tests for incremental indexing and daemon event partitioning."""

from __future__ import annotations

from pathlib import Path

from topolox.config import load_settings
from topolox.daemon.service import partition_events
from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.index.indexer import Indexer
from topolox.vectors.embedder import NullEmbedder
from topolox.vectors.lancedb_store import LanceDBVectorStore


def _names(graph: KuzuGraphStore, rel: str) -> set[str]:
    rows = graph.query("MATCH (s:Symbol {path: $p}) RETURN s.name AS name", {"p": rel})
    return {str(row["name"]) for row in rows}


def test_incremental_update(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    module = tmp_path / "pkg" / "mod.py"
    module.write_text("def alpha():\n    pass\n")

    graph = KuzuGraphStore(tmp_path / ".topolox" / "graph.kuzu")
    graph.init_schema()
    vectors = LanceDBVectorStore(tmp_path / ".topolox" / "vectors.lance")
    vectors.init_schema(NullEmbedder().dim)
    indexer = Indexer(load_settings(), graph, vectors, NullEmbedder())
    indexer._root = tmp_path  # set root without running a full (pool-based) build

    indexer.update([module], [])
    assert "alpha" in _names(graph, "pkg/mod.py")

    module.write_text("def beta():\n    pass\n")
    indexer.update([module], [])
    names = _names(graph, "pkg/mod.py")
    assert "beta" in names
    assert "alpha" not in names  # stale symbol pruned on re-index

    indexer.update([], [module])
    assert _names(graph, "pkg/mod.py") == set()

    graph.close()
    vectors.close()


def test_partition_events() -> None:
    changed, removed = partition_events(
        [
            ("a.py", False),
            ("b.py", True),
            ("a.py", False),
            ("c.py", False),
            ("c.py", True),
        ]
    )
    assert {p.name for p in changed} == {"a.py"}
    assert {p.name for p in removed} == {"b.py", "c.py"}
