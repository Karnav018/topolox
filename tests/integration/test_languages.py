"""Multi-language symbol-extraction smoke tests."""

from __future__ import annotations

import pytest

from topolox.models.nodes import NodeKind
from topolox.parsing.extractor import SymbolExtractor

CASES = [
    (
        "javascript",
        "app.js",
        b"import x from 'y';\nclass A { m(){} }\nfunction f(){}\n",
        {"A", "f", "m"},
    ),
    ("go", "app.go", b'package main\nimport "fmt"\ntype A struct{}\nfunc f(){}\n', {"A", "f"}),
    (
        "rust",
        "app.rs",
        b"use std::io;\nstruct A;\nimpl A { fn m(&self){} }\nfn f(){}\n",
        {"A", "f", "m"},
    ),
    ("java", "App.java", b"import java.util.List;\nclass A { void m(){} }\n", {"A", "m"}),
    ("c", "app.c", b"#include <stdio.h>\nint f(){ return 0; }\n", {"f"}),
    ("ruby", "app.rb", b"class A\n  def m; end\nend\ndef f; end\n", {"A", "f", "m"}),
]


@pytest.mark.parametrize(("language", "path", "source", "expected"), CASES)
def test_extracts_across_languages(
    language: str, path: str, source: bytes, expected: set[str]
) -> None:
    result = SymbolExtractor(language).extract(path, source)
    assert result.error is None
    names = {node.name for node in result.nodes}
    assert expected <= names


def test_unsupported_language_yields_only_file_node() -> None:
    result = SymbolExtractor("json").extract("data.json", b'{"a": 1}\n')
    assert result.error is None
    assert {node.kind for node in result.nodes} == {NodeKind.FILE}
