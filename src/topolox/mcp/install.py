"""Register the Topolox MCP server with AI coding agents.

Writes/merges each client's MCP config. Most use the JSON ``{"mcpServers": ...}``
shape; VS Code uses ``{"servers": ...}`` and Codex CLI uses TOML.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_SERVER_NAME = "topolox"

# Project-scoped clients (config lives in the repo) — written by `install all`.
PROJECT_CLIENTS: tuple[str, ...] = ("claude-code", "cursor", "gemini", "vscode", "codex")
# Global-only clients (config lives in the home dir) — opt-in by name.
GLOBAL_CLIENTS: tuple[str, ...] = ("windsurf", "claude-desktop")
ALL_CLIENTS: tuple[str, ...] = (*PROJECT_CLIENTS, *GLOBAL_CLIENTS)

# client -> config format: "mcpServers" (json), "servers" (json, VS Code), "toml" (Codex)
_FORMAT = {
    "claude-code": "mcpServers",
    "cursor": "mcpServers",
    "gemini": "mcpServers",
    "windsurf": "mcpServers",
    "claude-desktop": "mcpServers",
    "vscode": "servers",
    "codex": "toml",
}


def _command() -> list[str]:
    return [sys.executable, "-m", "topolox.mcp.server"]


def _claude_desktop_path() -> Path:
    home = Path.home()
    platform = sys.platform  # local var avoids mypy's platform-specific unreachable warning
    if platform == "darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if platform == "win32":
        return Path(os.environ.get("APPDATA", str(home))) / "Claude" / "claude_desktop_config.json"
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def _config_path(client: str, root: Path) -> Path | None:
    home = Path.home()
    paths: dict[str, Path] = {
        "claude-code": root / ".mcp.json",
        "cursor": root / ".cursor" / "mcp.json",
        "gemini": root / ".gemini" / "settings.json",
        "vscode": root / ".vscode" / "mcp.json",
        "codex": root / ".codex" / "config.toml",
        "windsurf": home / ".codeium" / "windsurf" / "mcp_config.json",
        "claude-desktop": _claude_desktop_path(),
    }
    return paths.get(client)


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _write_json(path: Path, top_key: str, entry: dict[str, object]) -> None:
    data = _load_json(path)
    raw = data.get(top_key)
    servers: dict[str, object] = raw if isinstance(raw, dict) else {}
    servers[_SERVER_NAME] = entry
    data[top_key] = servers
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_toml(path: Path) -> None:
    command, *args = _command()
    args_toml = ", ".join(json.dumps(arg) for arg in args)
    block = f"[mcp_servers.{_SERVER_NAME}]\ncommand = {json.dumps(command)}\nargs = [{args_toml}]\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if f"[mcp_servers.{_SERVER_NAME}]" in existing:
            return
        path.write_text(existing.rstrip() + "\n\n" + block, encoding="utf-8")
    else:
        path.write_text(block, encoding="utf-8")


def _install_one(client: str, root: Path) -> Path | None:
    path = _config_path(client, root)
    if path is None:
        return None
    fmt = _FORMAT[client]
    command, *args = _command()
    if fmt == "toml":
        _write_toml(path)
    elif fmt == "servers":
        _write_json(path, "servers", {"type": "stdio", "command": command, "args": args})
    else:
        _write_json(path, "mcpServers", {"command": command, "args": args})
    return path


def install_mcp(root: Path, *, client: str = "all") -> list[Path]:
    """Register Topolox with the requested client(s).

    ``client="all"`` writes every project-scoped client config under ``root``.
    A specific client name writes just that one (global clients write to the home
    dir). Returns the config files written (empty if ``client`` is unknown).
    """
    if client == "all":
        targets = PROJECT_CLIENTS
    elif client in ALL_CLIENTS:
        targets = (client,)
    else:
        return []
    written: list[Path] = []
    for name in targets:
        path = _install_one(name, root)
        if path is not None:
            written.append(path)
    return written
