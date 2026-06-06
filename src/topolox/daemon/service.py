"""The background daemon: bridges watchdog events to incremental indexing."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.config import Settings
    from topolox.index.indexer import Indexer


class DaemonService:
    """Watch the repo and patch the index on file changes."""

    def __init__(self, settings: Settings, indexer: Indexer) -> None:
        self._settings = settings
        self._indexer = indexer

    async def run(self) -> None:
        """Run the watch → debounce → ``Indexer.update`` loop. Phase 2."""
        raise NotImplementedError("Phase 2: daemon loop")
