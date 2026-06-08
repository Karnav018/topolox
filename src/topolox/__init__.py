"""Topolox — the topological memory and architecture layer for AI coding agents."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("topolox")
except PackageNotFoundError:  # running from a source tree without an installed dist
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
