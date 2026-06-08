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


_DOCSTRING_CAP = 500


def _string_value(node: Node, source: bytes) -> str:
    parts = [_text(c, source) for c in node.named_children if c.type == "string_content"]
    if parts:
        return "".join(parts).strip()
    text = _text(node, source).strip().lstrip("rRbBuUfF")
    for quote in ('"""', "'''", '"', "'"):
        if text.startswith(quote) and text.endswith(quote) and len(text) >= 2 * len(quote):
            return text[len(quote) : -len(quote)].strip()
    return text.strip()


def _docstring(node: Node, source: bytes, language: str) -> str | None:
    """Return the leading docstring of a Python def/class/module, if any.

    The grammar exposes a docstring as the first ``string`` in the body (or, on
    older versions, an ``expression_statement`` wrapping it).
    """
    if language != "python":
        return None
    body = node.child_by_field_name("body")
    block = body if body is not None else node
    first = next(iter(block.named_children), None)
    if first is not None and first.type == "expression_statement":
        first = next(iter(first.named_children), None)
    if first is None or first.type != "string":
        return None
    text = _string_value(first, source)
    if not text:
        return None
    return text[: _DOCSTRING_CAP - 1] + "…" if len(text) > _DOCSTRING_CAP else text


# Builtins are never internal symbols — skip them so the call graph stays meaningful
# and the graph isn't flooded with placeholder nodes.
_PY_BUILTINS = frozenset(
    {
        "print",
        "len",
        "range",
        "str",
        "int",
        "float",
        "bool",
        "list",
        "dict",
        "set",
        "tuple",
        "isinstance",
        "issubclass",
        "getattr",
        "setattr",
        "hasattr",
        "delattr",
        "super",
        "type",
        "enumerate",
        "zip",
        "sorted",
        "reversed",
        "map",
        "filter",
        "open",
        "repr",
        "format",
        "next",
        "iter",
        "abs",
        "min",
        "max",
        "sum",
        "any",
        "all",
        "id",
        "hash",
        "vars",
        "dir",
        "callable",
        "bytes",
        "bytearray",
        "frozenset",
        "object",
        "property",
        "staticmethod",
        "classmethod",
        "round",
        "pow",
        "divmod",
        "ord",
        "chr",
        "hex",
        "oct",
        "bin",
        "input",
    }
)


_LEAF_NAME_TYPES = frozenset(
    {"identifier", "type_identifier", "property_identifier", "field_identifier"}
)

# JS/TS function values bound to a name (const f = () => …, handler = function(){}).
_FUNCTION_EXPRS = frozenset({"arrow_function", "function_expression"})

# Class-heritage containers across languages (Python uses the `superclasses` field instead).
_HERITAGE_TYPES = frozenset(
    {"class_heritage", "extends_clause", "implements_clause", "extends_type_clause"}
)
_HERITAGE_SKIP = frozenset({"type_arguments", "type_parameters"})


def _field_text(node: Node, field: str, source: bytes) -> str | None:
    child = node.child_by_field_name(field)
    return _text(child, source) if child is not None else None


def _callee_name(callee: Node, source: bytes) -> str | None:
    """The rightmost name of a callee expression, across language grammars."""
    t = callee.type
    if t in _LEAF_NAME_TYPES:
        return _text(callee, source)
    if t == "attribute":  # Python: obj.method
        return _field_text(callee, "attribute", source)
    if t == "member_expression":  # JS/TS: obj.method
        return _field_text(callee, "property", source)
    if t in ("selector_expression", "field_expression"):  # Go / Rust: obj.method
        return _field_text(callee, "field", source)
    if t in ("scoped_identifier", "scoped_type_identifier"):  # Rust: mod::func
        name = callee.child_by_field_name("name")
        return _text(name, source) if name is not None else None
    return None


def _new_type_name(node: Node, source: bytes) -> str | None:
    """The class name of a Java ``new X()`` type (handles generics/scoped types)."""
    if node.type == "type_identifier":
        return _text(node, source)
    for child in node.named_children:
        if child.type == "type_identifier":
            return _text(child, source)
    for child in node.named_children:
        if child.type in ("generic_type", "scoped_type_identifier"):
            return _new_type_name(child, source)
    return None


def _call_target(node: Node, source: bytes) -> str | None:
    """Return the simple name of a call's callee.

    Covers ``foo()`` / ``obj.foo()`` (Python ``call``, JS/TS/Go/Rust ``call_expression``),
    ``new Foo()`` (JS/TS ``new_expression``, Java ``object_creation_expression``), and
    Java ``method_invocation`` — the rightmost name is what we link on.
    """
    if node.type == "method_invocation":  # Java
        return _field_text(node, "name", source)
    if node.type == "object_creation_expression":  # Java: new X()
        typ = node.child_by_field_name("type")
        return _new_type_name(typ, source) if typ is not None else None
    callee = node.child_by_field_name("function") or node.child_by_field_name("constructor")
    return _callee_name(callee, source) if callee is not None else None


def _heritage_names(node: Node, source: bytes) -> list[str]:
    """Collect type names in a JS/TS class-heritage subtree, recursing only through the
    ``extends``/``implements`` wrappers (never into generics or arbitrary nodes)."""
    names: list[str] = []
    for child in node.named_children:
        if child.type in ("identifier", "type_identifier"):
            names.append(_text(child, source))
        elif child.type == "member_expression":
            prop = child.child_by_field_name("property")
            if prop is not None:
                names.append(_text(prop, source))
        elif child.type in _HERITAGE_TYPES and child.type not in _HERITAGE_SKIP:
            names.extend(_heritage_names(child, source))
    return names


def _python_bases(node: Node, source: bytes) -> list[str]:
    supers = node.child_by_field_name("superclasses")
    if supers is None:
        return []
    bases: list[str] = []
    for child in supers.named_children:
        if child.type in ("identifier", "type_identifier"):
            bases.append(_text(child, source))
        elif child.type == "attribute":  # dotted base, e.g. abc.ABC
            attr = child.child_by_field_name("attribute")
            if attr is not None:
                bases.append(_text(attr, source))
    return bases


def _type_idents(node: Node, source: bytes) -> list[str]:
    """All ``type_identifier`` names in a subtree, skipping generic argument lists."""
    names: list[str] = []
    queue: deque[Node] = deque([node])
    while queue:
        current = queue.popleft()
        if current.type == "type_identifier":
            names.append(_text(current, source))
        elif current.type not in _HERITAGE_SKIP:
            queue.extend(current.named_children)
    return names


def _base_classes(node: Node, source: bytes, language: str) -> list[str]:
    """Return the names of a class's base classes / implemented interfaces, if any."""
    if language == "python":
        return _python_bases(node, source)
    if language in ("javascript", "typescript", "tsx"):
        bases: list[str] = []
        for child in node.named_children:
            if child.type in _HERITAGE_TYPES:
                bases.extend(_heritage_names(child, source))
        return bases
    if language == "java":  # extends <superclass> + implements <interfaces>
        bases = []
        for field_name in ("superclass", "interfaces"):
            clause = node.child_by_field_name(field_name)
            if clause is not None:
                bases.extend(_type_idents(clause, source))
        return bases
    return []


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
                docstring=_docstring(root, source, language),
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
                            docstring=_docstring(child, source, language),
                        )
                    )
                    edges.append(Edge(src_id=parent_id, dst_id=sid, kind=EdgeKind.DEFINES))
                    for base in _base_classes(child, source, language):
                        edges.append(Edge(src_id=sid, dst_id=base, kind=EdgeKind.INHERITS))
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
                            docstring=_docstring(child, source, language),
                        )
                    )
                    edges.append(Edge(src_id=parent_id, dst_id=sid, kind=EdgeKind.DEFINES))
                    visit(child, sid, qual, NodeKind.FUNCTION)
                elif ctype in spec.func_bindings:
                    value = child.child_by_field_name("value")
                    name_node = child.child_by_field_name("name")
                    if (
                        value is not None
                        and value.type in _FUNCTION_EXPRS
                        and name_node is not None
                        and name_node.type in ("identifier", "property_identifier")
                    ):
                        name = _text(name_node, source)
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
                                signature=_signature(value, name, source),
                            )
                        )
                        edges.append(Edge(src_id=parent_id, dst_id=sid, kind=EdgeKind.DEFINES))
                        visit(value, sid, qual, NodeKind.FUNCTION)
                    else:
                        visit(child, parent_id, parent_qual, container)
                elif ctype in spec.imports:
                    target = _import_target(child, source)
                    if target:
                        edges.append(Edge(src_id=path, dst_id=target, kind=EdgeKind.IMPORTS))
                elif ctype in spec.calls:
                    if container == NodeKind.FUNCTION:
                        callee = _call_target(child, source)
                        if callee and callee not in _PY_BUILTINS:
                            edges.append(Edge(src_id=parent_id, dst_id=callee, kind=EdgeKind.CALLS))
                    visit(child, parent_id, parent_qual, container)  # nested calls in args
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
