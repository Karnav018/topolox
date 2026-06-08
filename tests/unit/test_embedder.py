"""Unit tests for the offline HashingEmbedder and the default selection."""

from __future__ import annotations

from collections.abc import Sequence

from topolox.vectors.embedder import HashingEmbedder, default_embedder


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_hashing_embedder_is_deterministic_and_normalized() -> None:
    embedder = HashingEmbedder(dim=256)
    first = embedder.embed(["BlastRadiusService.simulate"])[0]
    second = embedder.embed(["BlastRadiusService.simulate"])[0]
    assert embedder.dim == 256
    assert first == second  # deterministic
    norm = sum(x * x for x in first) ** 0.5
    assert abs(norm - 1.0) < 1e-6  # L2-normalized


def test_empty_text_is_zero_vector_without_crashing() -> None:
    embedder = HashingEmbedder(dim=64)
    assert embedder.embed(["   "])[0] == [0.0] * 64


def test_ranks_related_text_above_unrelated() -> None:
    embedder = HashingEmbedder()
    query = embedder.embed(["user authentication and login session"])[0]
    relevant = embedder.embed(["app.auth.login: validate a user login session"])[0]
    unrelated = embedder.embed(["app.db.pool: open a database connection"])[0]
    assert _cosine(query, relevant) > _cosine(query, unrelated)


def test_results_are_query_dependent() -> None:
    # The NullEmbedder bug made every query identical (all-zero vectors); a real
    # embedder must rank a doc differently depending on the query.
    embedder = HashingEmbedder()
    auth_doc = embedder.embed(["authentication login session token"])[0]
    db_doc = embedder.embed(["database connection pool query"])[0]
    auth_query = embedder.embed(["how does login authentication work"])[0]
    assert _cosine(auth_query, auth_doc) > _cosine(auth_query, db_doc)


def test_subword_split_bridges_identifier_to_words() -> None:
    # "BlastRadiusService" should look like the words "blast radius service".
    embedder = HashingEmbedder()
    identifier = embedder.embed(["BlastRadiusService"])[0]
    words = embedder.embed(["blast radius service"])[0]
    noise = embedder.embed(["watcher filesystem observer"])[0]
    assert _cosine(identifier, words) > _cosine(identifier, noise)


def test_default_embedder_is_not_a_zero_vector() -> None:
    vector = default_embedder().embed(["topolox"])[0]
    assert any(abs(x) > 0.0 for x in vector)
