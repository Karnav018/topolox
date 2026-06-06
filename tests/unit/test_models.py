"""Tests for the core data contracts."""

from __future__ import annotations

from topolox.models import (
    Edge,
    EdgeKind,
    NodeKind,
    ParseResult,
    Span,
    SymbolNode,
)
from topolox.vectors.embedder import NullEmbedder


def test_symbol_node_fields() -> None:
    node = SymbolNode(
        id="pkg_auth_login",
        kind=NodeKind.FUNCTION,
        name="login",
        qualified_name="pkg.auth.login",
        path="pkg/auth.py",
        language="python",
        span=Span(0, 10, 1, 2),
    )
    assert node.name == "login"
    assert node.kind == "function"
    assert node.signature is None


def test_parse_result_defaults() -> None:
    result = ParseResult(path="pkg/auth.py", language="python")
    assert result.nodes == ()
    assert result.edges == ()
    assert result.error is None


def test_edge_defaults() -> None:
    edge = Edge(src_id="a", dst_id="b", kind=EdgeKind.CALLS)
    assert edge.weight == 1.0
    assert edge.kind == "calls"


def test_null_embedder() -> None:
    embedder = NullEmbedder(dim=8)
    vectors = embedder.embed(["a", "b"])
    assert embedder.dim == 8
    assert len(vectors) == 2
    assert len(vectors[0]) == 8
