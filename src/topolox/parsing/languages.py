"""File-extension → tree-sitter language map, cached parsers, and per-language
symbol-extraction specs.

Parsers come from ``tree-sitter-language-pack`` (300+ grammars). Languages with a
:class:`LangSpec` get full symbol extraction; any other mapped extension is still
parsed and recorded as a file node.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Parser

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
    ".rb": "ruby",
    ".cs": "csharp",
    ".php": "php",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".scala": "scala",
    ".sc": "scala",
    ".lua": "lua",
    ".sh": "bash",
    ".bash": "bash",
    ".r": "r",
}


@dataclass(frozen=True, slots=True)
class LangSpec:
    """Which tree-sitter node types denote functions, classes, imports, and calls."""

    functions: frozenset[str]
    classes: frozenset[str]
    imports: frozenset[str]
    containers: frozenset[str] = field(default_factory=frozenset)
    calls: frozenset[str] = field(default_factory=frozenset)
    func_bindings: frozenset[str] = field(default_factory=frozenset)


def _spec(
    functions: Iterable[str],
    classes: Iterable[str],
    imports: Iterable[str],
    containers: Iterable[str] = (),
    calls: Iterable[str] = (),
    func_bindings: Iterable[str] = (),
) -> LangSpec:
    return LangSpec(
        frozenset(functions),
        frozenset(classes),
        frozenset(imports),
        frozenset(containers),
        frozenset(calls),
        frozenset(func_bindings),
    )


LANGUAGE_SPECS: dict[str, LangSpec] = {
    "python": _spec(
        ["function_definition"],
        ["class_definition"],
        ["import_statement", "import_from_statement"],
        calls=["call"],
    ),
    "javascript": _spec(
        ["function_declaration", "method_definition", "generator_function_declaration"],
        ["class_declaration"],
        ["import_statement"],
        calls=["call_expression", "new_expression"],
        func_bindings=["variable_declarator", "public_field_definition", "field_definition"],
    ),
    "typescript": _spec(
        ["function_declaration", "method_definition", "function_signature"],
        ["class_declaration", "interface_declaration", "enum_declaration"],
        ["import_statement"],
        calls=["call_expression", "new_expression"],
        func_bindings=["variable_declarator", "public_field_definition", "field_definition"],
    ),
    "tsx": _spec(
        ["function_declaration", "method_definition"],
        ["class_declaration", "interface_declaration", "enum_declaration"],
        ["import_statement"],
        calls=["call_expression", "new_expression"],
        func_bindings=["variable_declarator", "public_field_definition", "field_definition"],
    ),
    "go": _spec(
        ["function_declaration", "method_declaration"],
        ["type_declaration"],
        ["import_declaration"],
    ),
    "rust": _spec(
        ["function_item"],
        ["struct_item", "enum_item", "trait_item"],
        ["use_declaration"],
        containers=["impl_item", "mod_item"],
    ),
    "java": _spec(
        ["method_declaration", "constructor_declaration"],
        ["class_declaration", "interface_declaration", "enum_declaration", "record_declaration"],
        ["import_declaration"],
    ),
    "c": _spec(
        ["function_definition"],
        ["struct_specifier", "enum_specifier", "union_specifier"],
        ["preproc_include"],
    ),
    "cpp": _spec(
        ["function_definition"],
        ["class_specifier", "struct_specifier", "enum_specifier"],
        ["preproc_include"],
    ),
    "ruby": _spec(["method", "singleton_method"], ["class", "module"], []),
    "csharp": _spec(
        ["method_declaration", "constructor_declaration"],
        ["class_declaration", "interface_declaration", "struct_declaration", "record_declaration"],
        ["using_directive"],
    ),
    "php": _spec(
        ["function_definition", "method_declaration"],
        ["class_declaration", "interface_declaration", "trait_declaration", "enum_declaration"],
        ["namespace_use_declaration"],
    ),
    "kotlin": _spec(
        ["function_declaration"],
        ["class_declaration", "object_declaration"],
        ["import_header"],
    ),
    "swift": _spec(
        ["function_declaration"],
        ["class_declaration", "protocol_declaration"],
        ["import_declaration"],
    ),
    "scala": _spec(
        ["function_definition"],
        ["class_definition", "object_definition", "trait_definition"],
        ["import_declaration"],
    ),
}


def language_for(path: Path) -> str | None:
    """Return the tree-sitter language name for ``path``, or ``None``."""
    return EXTENSION_TO_LANGUAGE.get(path.suffix.lower())


def spec_for(language: str) -> LangSpec | None:
    """Return the extraction spec for ``language``, or ``None`` if unsupported."""
    return LANGUAGE_SPECS.get(language)


@cache
def get_parser_for(language: str) -> Parser:
    """Return a cached tree-sitter ``Parser`` for ``language``.

    Built per-process (parsers are not picklable). Uses the standard
    ``tree_sitter.Parser`` with a grammar from ``tree_sitter_language_pack``.
    """
    from tree_sitter import Parser
    from tree_sitter_language_pack import get_language

    return Parser(get_language(language))
