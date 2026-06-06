"""Tests for the benchmark harness."""

from __future__ import annotations

from pathlib import Path

from topolox.benchmark import _percentile, _sample, run_benchmark


def test_percentile() -> None:
    assert _percentile([], 0.5) == 0.0
    assert _percentile([10.0], 0.95) == 10.0
    assert _percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5


def test_sample() -> None:
    assert _sample(["a", "b"], 5) == ["a", "b"]
    assert len(_sample([str(i) for i in range(100)], 10)) == 10


def test_run_benchmark(sample_repo: Path) -> None:
    report = run_benchmark(sample_repo, sample=10)
    assert report.files >= 1
    assert report.nodes >= 1
    assert report.sampled_files >= 1
    assert report.token_reduction_median >= 0.0
    assert report.baseline_tokens >= 0
    assert report.query_p50_ms >= 0.0
