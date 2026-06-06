"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_repo() -> Path:
    """Path to the bundled sample repository fixture."""
    return Path(__file__).parent / "fixtures" / "sample_repo"
