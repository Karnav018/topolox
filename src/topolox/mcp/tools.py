"""MCP tool definitions exposed to agents. Phase 2.

Registers the agent-facing tools (async, offloading the sync stores to threads):
``get_file_dependencies``, ``prune_context``, ``analyze_blast_radius``,
``search_architecture_graph``.
"""

from __future__ import annotations
