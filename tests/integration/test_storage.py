"""Integration tests for the Kùzu graph store, LanceDB store, and dependency query."""

from __future__ import annotations

from pathlib import Path

from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.graph.resolve import resolve_imports
from topolox.models.edges import Edge, EdgeKind
from topolox.models.graph import ParseResult
from topolox.models.nodes import NodeKind, Span, SymbolNode
from topolox.query.dependencies import DependencyService
from topolox.vectors.embedder import NullEmbedder
from topolox.vectors.lancedb_store import LanceDBVectorStore


def _file_fragment(path: str, qualified: str, imports: list[str]) -> ParseResult:
    file_node = SymbolNode(
        id=path,
        kind=NodeKind.FILE,
        name=Path(path).name,
        qualified_name=qualified,
        path=path,
        language="python",
        span=Span(0, 0, 1, 1),
    )
    edges = tuple(Edge(src_id=path, dst_id=module, kind=EdgeKind.IMPORTS) for module in imports)
    return ParseResult(path=path, language="python", nodes=(file_node,), edges=edges)


def test_graph_store_persists_and_queries(tmp_path: Path) -> None:
    store = KuzuGraphStore(tmp_path / "graph.kuzu")
    store.init_schema()
    store.upsert(_file_fragment("app/main.py", "app.main", ["app.db"]))
    store.upsert(_file_fragment("app/db.py", "app.db", []))

    rows = store.query("MATCH (s:Symbol {id: $id}) RETURN s.kind AS kind", {"id": "app/main.py"})
    assert rows and rows[0]["kind"] == "file"
    store.close()


def test_init_schema_migrates_pre_docstring_db(tmp_path: Path) -> None:
    """An index built before the docstring column existed must migrate, not crash."""
    import kuzu

    db_path = tmp_path / "graph.kuzu"
    # Simulate an old Symbol table that predates the docstring column.
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    conn.execute(
        "CREATE NODE TABLE Symbol(id STRING, kind STRING, name STRING, qualified_name STRING, "
        "path STRING, language STRING, signature STRING, start_line INT64, end_line INT64, "
        "PRIMARY KEY (id))"
    )
    conn.execute("CREATE REL TABLE Rel(FROM Symbol TO Symbol, kind STRING, weight DOUBLE)")
    conn.close()
    db.close()

    store = KuzuGraphStore(db_path)
    store.init_schema()  # adds the missing docstring column
    store.upsert(_file_fragment("app/db.py", "app.db", []))  # SET s.docstring must not crash
    rows = store.query("MATCH (s:Symbol {id: $id}) RETURN s.docstring AS d", {"id": "app/db.py"})
    assert rows  # column exists and is queryable
    store.close()


def test_dependency_service(tmp_path: Path) -> None:
    store = KuzuGraphStore(tmp_path / "graph.kuzu")
    store.init_schema()
    store.upsert(_file_fragment("app/main.py", "app.main", ["app.db"]))
    store.upsert(_file_fragment("app/db.py", "app.db", []))
    resolve_imports(store)

    deps = DependencyService(store)
    main_map = deps.of_file("app/main.py")
    assert "app.db" in {d.id for d in main_map.dependencies}

    db_map = deps.of_file("app/db.py")
    assert "app/main.py" in {d.id for d in db_map.dependents}
    store.close()


def test_vector_store_upsert(tmp_path: Path) -> None:
    store = LanceDBVectorStore(tmp_path / "vectors.lance")
    embedder = NullEmbedder(dim=8)
    store.init_schema(embedder.dim)
    store.upsert([{"id": "a", "path": "x.py", "text": "foo", "vector": embedder.embed(["foo"])[0]}])
    store.close()
