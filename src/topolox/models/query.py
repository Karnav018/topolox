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
