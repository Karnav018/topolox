"""The background daemon: bridges watchdog events to incremental indexing."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from topolox.daemon.watcher import RepoEventHandler
from topolox.logging import get_logger

if TYPE_CHECKING:
    from topolox.config import Settings
    from topolox.index.indexer import Indexer

_log = get_logger("daemon")


def partition_events(batch: list[tuple[str, bool]]) -> tuple[list[Path], list[Path]]:
    """Collapse a batch of ``(path, removed)`` events into changed/removed lists.

    The last event for a path wins, so a save-then-delete ends up removed and a
    delete-then-recreate ends up changed.
    """
    changed: dict[str, Path] = {}
    removed: dict[str, Path] = {}
    for raw_path, is_removed in batch:
        path = Path(raw_path)
        key = str(path)
        if is_removed:
            removed[key] = path
            changed.pop(key, None)
        else:
            changed[key] = path
            removed.pop(key, None)
    return list(changed.values()), list(removed.values())


class DaemonService:
    """Watch the repo and patch the index on file changes."""

    def __init__(
        self,
        settings: Settings,
        indexer: Indexer,
        root: Path,
        *,
        debounce: float = 0.5,
    ) -> None:
        self._settings = settings
        self._indexer = indexer
        self._root = root.resolve()
        self._debounce = debounce

    async def run(self) -> None:
        """Run the watch → debounce → ``Indexer.update`` loop until cancelled."""
        from watchdog.observers import Observer

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[tuple[str, bool]] = asyncio.Queue()

        def on_change(path: str, removed: bool) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, (path, removed))

        observer = Observer()
        observer.schedule(RepoEventHandler(on_change), str(self._root), recursive=True)
        observer.start()
        try:
            while True:
                batch = [await queue.get()]
                await asyncio.sleep(self._debounce)
                while not queue.empty():
                    batch.append(queue.get_nowait())
                changed, removed = partition_events(batch)
                stats = await asyncio.to_thread(self._indexer.update, changed, removed)
                _log.info(
                    "patched %d changed / %d removed in %.0fms",
                    len(changed),
                    len(removed),
                    stats.seconds * 1000,
                )
        finally:
            observer.stop()
            observer.join()
