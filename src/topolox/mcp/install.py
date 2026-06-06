"""Write MCP client configuration so Claude Code / Cursor can find Topolox."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SERVER_KEY = "topolox"


def _server_entry() -> dict[str, object]:
    """The MCP server command — run via the current interpreter (no PATH dependency)."""
    return {"command": sys.executable, "args": ["-m", "topolox.mcp.server"]}


def _merge_config(path: Path, entry: dict[str, object]) -> None:
    data: dict[str, object] = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except json.JSONDecodeError:
            data = {}
    raw_servers = data.get("mcpServers")
    servers: dict[str, object] = raw_servers if isinstance(raw_servers, dict) else {}
    servers[_SERVER_KEY] = entry
    data["mcpServers"] = servers
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def install_mcp(root: Path, *, client: str = "all") -> list[Path]:
    """Write/merge the Topolox MCP entry into the requested client configs.

    Returns the list of config files written (empty if ``client`` is unknown).
    """
    entry = _server_entry()
    targets: list[Path] = []
    if client in ("all", "claude-code"):
        targets.append(root / ".mcp.json")
    if client in ("all", "cursor"):
        targets.append(root / ".cursor" / "mcp.json")
    for target in targets:
        _merge_config(target, entry)
    return targets
