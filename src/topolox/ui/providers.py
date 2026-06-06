"""Data-provider ports for the TUI, decoupled from the engine. Phase 3.

Concrete implementations (real Anthropic chat, live graph queries, the daemon
event stream) and offline stubs both satisfy these protocols.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from topolox.models.query import BlastRadiusReport, DependencyMap


@runtime_checkable
class ChatBackend(Protocol):
    """Streams assistant tokens for the chat pane."""

    def stream(self, prompt: str) -> AsyncIterator[str]: ...


@runtime_checkable
class GraphProvider(Protocol):
    """Supplies graph and blast-radius data for the graph pane."""

    async def dependencies(self, path: str) -> DependencyMap: ...

    async def blast_radius(self, files: Sequence[str]) -> BlastRadiusReport: ...


@runtime_checkable
class DaemonEvents(Protocol):
    """Yields daemon log lines for the log pane."""

    def stream(self) -> AsyncIterator[str]: ...
