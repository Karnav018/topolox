"""Watchdog file watcher feeding the indexer.

Forwards source-file change/delete events to a callback; the callback is invoked
from watchdog's background thread, so it must be thread-safe.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.events import FileSystemEventHandler

from topolox.parsing.languages import language_for

if TYPE_CHECKING:
    from watchdog.events import FileSystemEvent

OnChange = Callable[[str, bool], None]


class RepoEventHandler(FileSystemEventHandler):
    """Emit ``(path, removed)`` for source files that change or disappear."""

    def __init__(self, on_change: OnChange) -> None:
        self._on_change = on_change

    def on_created(self, event: FileSystemEvent) -> None:
        self._emit(event, removed=False)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._emit(event, removed=False)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._emit(event, removed=True)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._emit_path(str(event.src_path), removed=True)
        dest = getattr(event, "dest_path", "")
        if dest:
            self._emit_path(str(dest), removed=False)

    def _emit(self, event: FileSystemEvent, *, removed: bool) -> None:
        if event.is_directory:
            return
        self._emit_path(str(event.src_path), removed=removed)

    def _emit_path(self, path: str, *, removed: bool) -> None:
        if language_for(Path(path)) is not None:
            self._on_change(path, removed)
