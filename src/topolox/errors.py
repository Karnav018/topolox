"""Exception hierarchy for Topolox."""

from __future__ import annotations


class TopoloxError(Exception):
    """Base class for all Topolox errors."""


class ConfigError(TopoloxError):
    """Raised when configuration is invalid."""


class ParseError(TopoloxError):
    """Raised when a file cannot be parsed."""


class StoreError(TopoloxError):
    """Raised when the graph or vector store fails."""
