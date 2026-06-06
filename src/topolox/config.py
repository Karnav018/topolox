"""Runtime configuration, loaded from the environment (prefix ``TOPOLOX_``)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Topolox settings. Override via ``TOPOLOX_*`` env vars or a ``.env`` file."""

    model_config = SettingsConfigDict(
        env_prefix="TOPOLOX_",
        env_file=".env",
        extra="ignore",
    )

    repo_root: Path = Field(default_factory=Path.cwd)
    data_dir: Path = Path(".topolox")
    graph_path: Path = Path(".topolox/graph.kuzu")
    vector_uri: Path = Path(".topolox/vectors.lance")
    max_workers: int | None = None
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    log_level: str = "INFO"


def load_settings() -> Settings:
    """Load settings from the environment."""
    return Settings()
