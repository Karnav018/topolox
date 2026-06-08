"""API DTOs returned by the query layer and MCP tools."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScoredSymbol(BaseModel):
    """A symbol with a relevance score."""

    id: str
    path: str
    name: str
    score: float
    signature: str | None = None


class PrunedContext(BaseModel):
    """The top-percentile of relevant context for an agent prompt."""

    query: str
    symbols: list[ScoredSymbol] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    token_estimate: int = 0


class DependencyMap(BaseModel):
    """Dependencies and dependents of a file or symbol."""

    root: str
    dependencies: list[ScoredSymbol] = Field(default_factory=list)
    dependents: list[ScoredSymbol] = Field(default_factory=list)


class BlastRadiusReport(BaseModel):
    """The downstream impact of changing one or more files."""

    changed: list[str] = Field(default_factory=list)
    impacted_files: list[str] = Field(default_factory=list)
    impacted_tests: list[str] = Field(default_factory=list)
    impacted_symbols: list[str] = Field(default_factory=list)
    max_depth: int = 0


class SymbolDetail(BaseModel):
    """A single symbol located precisely, with its exact source slice."""

    id: str
    name: str
    qualified_name: str
    kind: str
    path: str
    language: str = ""
    signature: str | None = None
    start_line: int = 0
    end_line: int = 0
    source: str = ""


class SymbolSource(BaseModel):
    """The result of ``read_symbol`` — one match, or several on a name collision."""

    query: str
    matches: list[SymbolDetail] = Field(default_factory=list)


class OutlineSymbol(BaseModel):
    """One symbol in a file outline (no body — just shape)."""

    name: str
    qualified_name: str
    kind: str
    signature: str | None = None
    docstring: str | None = None
    start_line: int = 0
    end_line: int = 0


class FileOutline(BaseModel):
    """The symbol outline of a single file — its shape without reading it."""

    path: str
    language: str = ""
    symbols: list[OutlineSymbol] = Field(default_factory=list)


class HubFile(BaseModel):
    """A file ranked by how many other indexed files import it."""

    path: str
    dependents: int


class RepoOverview(BaseModel):
    """A top-level architectural summary of the indexed repository."""

    files: int = 0
    symbols: int = 0
    languages: dict[str, int] = Field(default_factory=dict)
    hubs: list[HubFile] = Field(default_factory=list)


class SymbolRef(BaseModel):
    """A lightweight reference to a symbol on the other end of an edge."""

    id: str
    name: str
    qualified_name: str
    kind: str
    path: str
    start_line: int = 0


class CallReport(BaseModel):
    """The callers or callees of a symbol (resolved call graph)."""

    symbol: str
    direction: str  # "callers" | "callees"
    matched: list[str] = Field(default_factory=list)  # qualified names the query resolved to
    neighbors: list[SymbolRef] = Field(default_factory=list)


class ClassHierarchy(BaseModel):
    """The direct supertypes and subtypes of a class."""

    symbol: str
    matched: list[str] = Field(default_factory=list)
    supertypes: list[SymbolRef] = Field(default_factory=list)
    subtypes: list[SymbolRef] = Field(default_factory=list)
