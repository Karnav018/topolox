"""Extract symbols and edges from a parsed file using tree-sitter."""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from topolox.models.edges import Edge, EdgeKind
from topolox.models.graph import ParseResult
from topolox.models.nodes import NodeKind, Span, SymbolNode
from topolox.parsing.languages import get_parser_for

if TYPE_CHECKING:
    from tree_sitter import Node


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


class SymbolExtractor:
    """Run tree-sitter over a file to produce nodes and edges."""

    def __init__(self, language: str) -> None:
        self._language = language

    def extract(self, path: str, source: bytes) -> ParseResult:
        """Extract a :class:`ParseResult` from ``source``."""
        parser = get_parser_for(self._language)
        root = parser.parse(source).root_node

        nodes: list[SymbolNode] = []
        edges: list[Edge] = []
        module_qual = _module_qualname(path)

        nodes.append(
            SymbolNode(
                id=path,
                kind=NodeKind.FILE,
                name=PurePosixPath(path).name,
                qualified_name=module_qual,
                path=path,
                language=self._language,
                span=_span(root),
            )
        )

        def visit(node: Node, parent_id: str, parent_qual: str, container: NodeKind) -> None:
            for child in node.named_children:
                ctype = child.type
                if ctype == "function_definition":
                    name = self._field_text(child, "name", source)
                    if not name:
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
                            language=self._language,
                            span=_span(child),
                            signature=self._signature(child, name, source),
                        )
                    )
                    edges.append(Edge(src_id=parent_id, dst_id=sid, kind=EdgeKind.DEFINES))
                    body = child.child_by_field_name("body")
                    if body is not None:
                        visit(body, sid, qual, NodeKind.FUNCTION)
                elif ctype == "class_definition":
                    name = self._field_text(child, "name", source)
                    if not name:
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
                            language=self._language,
                            span=_span(child),
                        )
                    )
                    edges.append(Edge(src_id=parent_id, dst_id=sid, kind=EdgeKind.DEFINES))
                    body = child.child_by_field_name("body")
                    if body is not None:
                        visit(body, sid, qual, NodeKind.CLASS)
                elif ctype in ("import_statement", "import_from_statement"):
                    module = self._import_module(child, source)
                    if module:
                        edges.append(Edge(src_id=path, dst_id=module, kind=EdgeKind.IMPORTS))
                else:
                    visit(child, parent_id, parent_qual, container)

        visit(root, path, module_qual, NodeKind.MODULE)

        return ParseResult(
            path=path,
            language=self._language,
            nodes=tuple(nodes),
            edges=tuple(edges),
            content_hash=hashlib.sha256(source).hexdigest(),
        )

    @staticmethod
    def _field_text(node: Node, field: str, source: bytes) -> str:
        child = node.child_by_field_name(field)
        return _text(child, source) if child is not None else ""

    @staticmethod
    def _signature(func: Node, name: str, source: bytes) -> str:
        params = func.child_by_field_name("parameters")
        return f"{name}{_text(params, source)}" if params is not None else f"{name}()"

    @staticmethod
    def _import_module(node: Node, source: bytes) -> str | None:
        if node.type == "import_from_statement":
            module = node.child_by_field_name("module_name")
            return _text(module, source) if module is not None else None
        queue: list[Node] = list(node.named_children)
        while queue:
            current = queue.pop(0)
            if current.type == "dotted_name":
                return _text(current, source)
            queue.extend(current.named_children)
        return None
