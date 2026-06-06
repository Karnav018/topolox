"""Tests for `topolox mcp install` across AI coding agents."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from topolox.mcp.install import PROJECT_CLIENTS, install_mcp


def test_install_all_writes_every_project_client(tmp_path: Path) -> None:
    targets = install_mcp(tmp_path, client="all")
    assert len(targets) == len(PROJECT_CLIENTS)
    assert (tmp_path / ".mcp.json") in targets
    assert (tmp_path / ".cursor" / "mcp.json") in targets
    assert (tmp_path / ".vscode" / "mcp.json") in targets
    assert (tmp_path / ".codex" / "config.toml") in targets


def test_json_clients(tmp_path: Path) -> None:
    install_mcp(tmp_path, client="claude-code")
    install_mcp(tmp_path, client="gemini")
    claude = json.loads((tmp_path / ".mcp.json").read_text())
    assert claude["mcpServers"]["topolox"]["args"] == ["-m", "topolox.mcp.server"]
    gemini = json.loads((tmp_path / ".gemini" / "settings.json").read_text())
    assert "topolox" in gemini["mcpServers"]


def test_vscode_uses_servers_key(tmp_path: Path) -> None:
    install_mcp(tmp_path, client="vscode")
    config = json.loads((tmp_path / ".vscode" / "mcp.json").read_text())
    assert "mcpServers" not in config
    assert config["servers"]["topolox"]["type"] == "stdio"


def test_codex_uses_toml(tmp_path: Path) -> None:
    install_mcp(tmp_path, client="codex")
    config = tomllib.loads((tmp_path / ".codex" / "config.toml").read_text())
    assert config["mcp_servers"]["topolox"]["args"] == ["-m", "topolox.mcp.server"]


def test_merge_preserves_existing_servers(tmp_path: Path) -> None:
    path = tmp_path / ".mcp.json"
    path.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}))
    install_mcp(tmp_path, client="claude-code")
    config = json.loads(path.read_text())
    assert "other" in config["mcpServers"]
    assert "topolox" in config["mcpServers"]


def test_unknown_client_returns_empty(tmp_path: Path) -> None:
    assert install_mcp(tmp_path, client="nope") == []
