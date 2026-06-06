"""Tests for repository file discovery."""

from __future__ import annotations

from pathlib import Path

from topolox.parsing.discovery import discover_files


def test_discovers_python_files(sample_repo: Path) -> None:
    names = {p.name for p in discover_files(sample_repo)}
    assert {"main.py", "auth.py", "db.py"} <= names


def test_exclude_glob(sample_repo: Path) -> None:
    names = {p.name for p in discover_files(sample_repo, exclude=["*/db.py"])}
    assert "db.py" not in names
    assert "auth.py" in names


def test_include_glob(sample_repo: Path) -> None:
    names = {p.name for p in discover_files(sample_repo, include=["*/auth.py"])}
    assert names == {"auth.py"}
