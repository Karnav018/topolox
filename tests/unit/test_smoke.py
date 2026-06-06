"""Smoke tests: the package imports and the CLI runs."""

from __future__ import annotations

import subprocess
import sys

import topolox


def test_version_is_set() -> None:
    assert isinstance(topolox.__version__, str)
    assert topolox.__version__


def test_cli_help_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "topolox", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "topolox" in result.stdout.lower()


def test_cli_version_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "topolox", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert topolox.__version__ in result.stdout
