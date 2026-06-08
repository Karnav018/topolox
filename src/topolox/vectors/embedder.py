"""Embedding providers.

The default :class:`HashingEmbedder` is deterministic, offline, and dependency
free — it gives real lexical relevance via subword feature hashing. Higher-quality
neural embeddings (``fastembed``) ship behind the optional ``[embeddings]`` extra.
:class:`NullEmbedder` (zero vectors) remains for tests and explicit no-search mode.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """Turns text into dense vectors for semantic search."""

    @property
    def dim(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class NullEmbedder:
    """A deterministic zero-vector embedder for tests and no-embeddings mode."""

    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.0] * self._dim for _ in texts]


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")


def _split_identifier(token: str) -> list[str]:
    """Split a camelCase / PascalCase identifier into lowercase subwords."""
    return [part.lower() for part in _CAMEL_RE.findall(token)]


def _features(text: str) -> list[str]:
    """Word + character-trigram features for ``text``.

    Identifiers are split on case and underscore boundaries so ``BlastRadiusService``
    contributes ``blast``/``radius``/``service``; character trigrams bridge
    morphological variants (``embed`` / ``embedder`` / ``embeddings``).
    """
    feats: list[str] = []
    for raw in _TOKEN_RE.findall(text):
        words = {raw.lower(), *_split_identifier(raw)}
        for word in words:
            feats.append(f"w:{word}")
            padded = f"#{word}#"
            for i in range(len(padded) - 2):
                feats.append(f"3:{padded[i : i + 3]}")
    return feats


class HashingEmbedder:
    """Deterministic, dependency-free embedder using the hashing trick.

    Tokenizes text (splitting ``snake_case`` / ``camelCase`` identifiers and adding
    character trigrams) and feature-hashes the result into a fixed-width,
    L2-normalized vector. L2 nearest-neighbor over unit vectors ranks by cosine
    similarity, so this gives genuine lexical "find by meaning" search offline,
    without the heavyweight ``fastembed`` dependency.
    """

    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for feature in _features(text):
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            bucket = value % self._dim
            sign = 1.0 if (value >> 63) & 1 else -1.0
            vec[bucket] += sign
        norm = math.sqrt(sum(component * component for component in vec))
        if norm == 0.0:
            return vec
        return [component / norm for component in vec]


class FastEmbedEmbedder:
    """Local ONNX embeddings via ``fastembed`` (the optional ``[embeddings]`` extra)."""

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5") -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model)
        self._dim = len(next(iter(self._model.embed(["topolox"]))))

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[float(x) for x in vector] for vector in self._model.embed(list(texts))]


def default_embedder() -> Embedder:
    """Return a real neural embedder if ``fastembed`` is installed, else the
    deterministic offline :class:`HashingEmbedder`."""
    try:
        return FastEmbedEmbedder()
    except ImportError:
        return HashingEmbedder()
