"""Logging setup.

Note: the MCP stdio transport uses *stdout* for the protocol, so Topolox always
logs to *stderr* to avoid corrupting it.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    """Configure ``topolox.*`` logging to stderr. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s"))
    root = logging.getLogger("topolox")
    root.setLevel(level.upper())
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced ``topolox.*`` logger."""
    return logging.getLogger(f"topolox.{name}")
