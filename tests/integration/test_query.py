"""Integration tests for the Phase 2 query engine."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.graph.resolve import resolve_imports
from topolox.models.edges import Edge, EdgeKind
from topolox.models.graph import ParseResult
from topolox.models.nodes import NodeKind, Span, SymbolNode
from topolox.query.blast_radius import BlastRadiusService
from topolox.query.pruner import ContextPruner
from topolox.query.scoring import estimate_tokens
from topolox.vectors.lancedb_store import LanceDBVectorStore


class _ToyEmbedder:
    """Deterministic 3-axis embedder (auth / db / main) for testing."""

    dim = 3

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            lower = text.lower()
            out.append(
                [
                    1.0 if "auth" in lower else 0.0,
                    1.0 if "db" in lower else 0.0,
                    1.0 if "main" in lower else 0.0,
                ]
            )
        return out


def _fragment(path: str, qualified: str, imports: list[str]) -> ParseResult:
    node = SymbolNode(
        id=path,
        kind=NodeKind.FILE,
        name=Path(path).name,
        qualified_name=qualified,
        path=path,
        language="python",
        span=Span(0, 0, 1, 1),
    )
    edges = tuple(Edge(src_id=path, dst_id=module, kind=EdgeKind.IMPORTS) for module in imports)
    return ParseResult(path=path, language="python", nodes=(node,), edges=edges)


def _build_graph(tmp: Path) -> KuzuGraphStore:
    store = KuzuGraphStore(tmp / "graph.kuzu")
    store.init_schema()
    store.upsert(_fragment("app/main.py", "app.main", ["app.auth", "app.db"]))
    store.upsert(_fragment("app/auth.py", "app.auth", ["app.db"]))
    store.upsert(_fragment("app/db.py", "app.db", []))
    resolve_imports(store)
    return store


def test_estimate_tokens() -> None:
    assert estimate_tokens("") == 1
    assert estimate_tokens("a" * 40) == 10


def test_blast_radius(tmp_path: Path) -> None:
    store = _build_graph(tmp_path)
    report = BlastRadiusService(store).simulate(["app/db.py"])
    assert set(report.impacted_files) == {"app/main.py", "app/auth.py"}
    assert report.max_depth >= 1
    store.close()


def test_blast_radius_resolves_package_root(tmp_path: Path) -> None:
    # src/monorepo layout: file at apps/api/app/db.py is imported as "app.db".
    store = KuzuGraphStore(tmp_path / "graph.kuzu")
    store.init_schema()
    store.upsert(_fragment("apps/api/app/db.py", "apps.api.app.db", []))
    store.upsert(_fragment("apps/api/app/main.py", "apps.api.app.main", ["app.db"]))
    store.upsert(
        _fragment("apps/api/app/routers/forms.py", "apps.api.app.routers.forms", ["app.db"])
    )
    resolve_imports(store)
    report = BlastRadiusService(store).simulate(["apps/api/app/db.py"])
    assert set(report.impacted_files) == {
        "apps/api/app/main.py",
        "apps/api/app/routers/forms.py",
    }
    store.close()


def test_context_pruner(tmp_path: Path) -> None:
    store = _build_graph(tmp_path)
    embedder = _ToyEmbedder()
    vectors = LanceDBVectorStore(tmp_path / "vectors.lance")
    vectors.init_schema(embedder.dim)
    vectors.upsert(
        [
            {"id": fid, "path": fid, "text": qual, "vector": embedder.embed([qual])[0]}
            for fid, qual in [
                ("app/main.py", "app.main"),
                ("app/auth.py", "app.auth"),
                ("app/db.py", "app.db"),
            ]
        ]
    )

    context = ContextPruner(store, vectors, embedder).prune("authentication flow")
    top_ids = [symbol.id for symbol in context.symbols]
    assert "app/auth.py" in top_ids
    assert context.symbols[0].id == "app/auth.py"
    assert context.token_estimate > 0
    store.close()
    vectors.close()


def test_fastembed_embedder_optional() -> None:
    pytest.importorskip("fastembed")
    from topolox.vectors.embedder import FastEmbedEmbedder

    embedder = FastEmbedEmbedder()
    vectors = embedder.embed(["hello world"])
    assert embedder.dim > 0
    assert len(vectors[0]) == embedder.dim
