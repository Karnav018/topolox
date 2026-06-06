"""Watchdog file watcher feeding the indexer. Phase 2.

A debounced ``watchdog`` event handler pushes changed paths onto an asyncio
queue consumed by :class:`~topolox.daemon.service.DaemonService`.
"""

from __future__ import annotations
