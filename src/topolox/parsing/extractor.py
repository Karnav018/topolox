"""Extract symbols and edges from a parsed file using tree-sitter.

Extraction is driven by per-language :class:`~topolox.parsing.languages.LangSpec`
configs, so the same generic traversal works across languages.
"""

from __future__ import annotations

import hashlib
from collections import deque
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from topolox.models.edges import Edge, EdgeKind
from topolox.models.graph import ParseResult
from topolox.models.nodes import NodeKind, Span, SymbolNode
from topolox.parsing.languages import get_parser_for, spec_for

if TYPE_CHECKING:
    from tree_sitter import Node

_NAME_NODE_TYPES = frozenset(
    {
        "identifier",
        "type_identifier",
        "field_identifier",
        "constant",
        "scoped_identifier",
        "simple_identifier",
        "name",
    }
)

_IMPORT_FIELDS = ("module_name", "name", "source", "path", "argument")

_IMPORT_NODE_TYPES = frozenset(
    {
        "string",
        "string_literal",
        "interpreted_string_literal",
        "raw_string_literal",
        "string_fragment",
        "dotted_name",
        "scoped_identifier",
        "namespace_name",
        "qualified_name",
        "package_identifier",
        "identifier",
        "type_identifier",
    }
)


def _text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", "replace")


def _span(node: Node) -> Span:
    return Span(
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
    )


def _module_qualname(path: str) -> str:
    parts = list(PurePosixPath(path.replace("\\", "/")).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _clean_import(text: str) -> str:
    return text.strip().strip("\"'`;<>").strip()


def _node_name(node: Node, source: bytes) -> str:
    direct = node.child_by_field_name("name")
    if direct is not None:
        return _text(direct, source)
    # C/C++ bury the name inside a declarator chain.
    declarator = node.child_by_field_name("declarator")
    while declarator is not None:
        if declarator.type in ("identifier", "field_identifier", "type_identifier"):
            return _text(declarator, source)
        declarator = declarator.child_by_field_name("declarator")
    # Fall back to the first name-like descendant.
    queue: deque[Node] = deque(node.named_children)
    while queue:
        current = queue.popleft()
        if current.type in _NAME_NODE_TYPES:
            return _text(current, source)
        queue.extend(current.named_children)
    return ""


def _import_target(node: Node, source: bytes) -> str | None:
    for field_name in _IMPORT_FIELDS:
        child = node.child_by_field_name(field_name)
        if child is not None:
            return _clean_import(_text(child, source))
    queue: deque[Node] = deque(node.named_children)
    while queue:
        current = queue.popleft()
        if current.type in _IMPORT_NODE_TYPES:
            return _clean_import(_text(current, source))
        queue.extend(current.named_children)
    return None


class SymbolExtractor:
    """Run tree-sitter over a file to produce nodes and edges."""

    def __init__(self, language: str) -> None:
        self._language = language

    def extract(self, path: str, source: bytes) -> ParseResult:
        """Extract a :class:`ParseResult` from ``source``."""
        spec = spec_for(self._language)
        root = get_parser_for(self._language).parse(source).root_node
        module_qual = _module_qualname(path)
        language = self._language

        nodes: list[SymbolNode] = [
            SymbolNode(
                id=path,
                kind=NodeKind.FILE,
                name=PurePosixPath(path).name,
                qualified_name=module_qual,
                path=path,
                language=language,
                span=_span(root),
            )
        ]
        edges: list[Edge] = []

        def visit(node: Node, parent_id: str, parent_qual: str, container: NodeKind) -> None:
            if spec is None:
                return
            for child in node.named_children:
                ctype = child.type
                if ctype in spec.classes:
                    name = _node_name(child, source)
                    if not name:
                        visit(child, parent_id, parent_qual, container)
                        continue
                    qual = f"{parent_qual}.{name}" if parent_qual else name
                    sid = f"{path}::{qual}"
                    nodes.append(
                        SymbolNode(
                            id=sid,
                            kind=NodeKind.CLASS,
                            name=name,
                            qualified_name=qual,
                            path=path,
                            language=language,
                            span=_span(child),
                        )
                    )
                    edges.append(Edge(src_id=parent_id, dst_id=sid, kind=EdgeKind.DEFINES))
                    visit(child, sid, qual, NodeKind.CLASS)
                elif ctype in spec.functions:
                    name = _node_name(child, source)
                    if not name:
                        visit(child, parent_id, parent_qual, container)
                        continue
                    qual = f"{parent_qual}.{name}" if parent_qual else name
                    sid = f"{path}::{qual}"
                    kind = NodeKind.METHOD if container == NodeKind.CLASS else NodeKind.FUNCTION
                    nodes.append(
                        SymbolNode(
                            id=sid,
                            kind=kind,
                            name=name,
                            qualified_name=qual,
                            path=path,
                            language=language,
                            span=_span(child),
                            signature=_signature(child, name, source),
                        )
                    )
                    edges.append(Edge(src_id=parent_id, dst_id=sid, kind=EdgeKind.DEFINES))
                    visit(child, sid, qual, NodeKind.FUNCTION)
                elif ctype in spec.imports:
                    target = _import_target(child, source)
                    if target:
                        edges.append(Edge(src_id=path, dst_id=target, kind=EdgeKind.IMPORTS))
                elif ctype in spec.containers:
                    visit(child, parent_id, parent_qual, NodeKind.CLASS)
                else:
                    visit(child, parent_id, parent_qual, container)

        if spec is not None:
            visit(root, path, module_qual, NodeKind.MODULE)

        return ParseResult(
            path=path,
            language=language,
            nodes=tuple(nodes),
            edges=tuple(edges),
            content_hash=hashlib.sha256(source).hexdigest(),
        )


def _signature(node: Node, name: str, source: bytes) -> str:
    params = node.child_by_field_name("parameters")
    return f"{name}{_text(params, source)}" if params is not None else f"{name}()"
