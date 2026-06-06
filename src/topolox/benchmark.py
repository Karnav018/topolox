"""Benchmark Topolox on a repository: index speed, query latency, token reduction.

Indexes ``root`` into a throwaway database (so it never touches the repo's
``.topolox/``), then samples files and compares the tokens an agent would spend
reading a file + its blast radius against the tokens Topolox returns.
"""

from __future__ import annotations

import json
import shutil
import statistics
import tempfile
import time
from pathlib import Path

from pydantic import BaseModel

from topolox.config import load_settings
from topolox.graph.kuzu_store import KuzuGraphStore
from topolox.index.indexer import Indexer
from topolox.query.blast_radius import BlastRadiusService
from topolox.query.dependencies import DependencyService
from topolox.query.scoring import estimate_tokens
from topolox.vectors.embedder import NullEmbedder
from topolox.vectors.lancedb_store import LanceDBVectorStore


class BenchmarkReport(BaseModel):
    """Measured metrics for a single benchmark run."""

    files: int = 0
    nodes: int = 0
    edges: int = 0
    index_seconds: float = 0.0
    files_per_second: float = 0.0
    sampled_files: int = 0
    query_p50_ms: float = 0.0
    query_p95_ms: float = 0.0
    token_reduction_median: float = 0.0
    token_reduction_mean: float = 0.0
    baseline_tokens: int = 0
    topolox_tokens: int = 0


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct
    low = int(rank)
    if low + 1 < len(ordered):
        return ordered[low] + (rank - low) * (ordered[low + 1] - ordered[low])
    return ordered[low]


def _sample(items: list[str], count: int) -> list[str]:
    if count <= 0 or len(items) <= count:
        return items
    step = len(items) / count
    return [items[int(i * step)] for i in range(count)]


def run_benchmark(root: Path, *, sample: int = 50) -> BenchmarkReport:
    """Index ``root`` in a temp database and measure speed, latency, token reduction."""
    root = root.resolve()
    data_dir = Path(tempfile.mkdtemp(prefix="topolox-bench-"))
    graph = KuzuGraphStore(data_dir / "graph.kuzu")
    vectors = LanceDBVectorStore(data_dir / "vectors.lance")
    indexer = Indexer(load_settings(), graph, vectors, NullEmbedder())
    try:
        stats = indexer.build(root)
        files = sorted(
            str(row["id"])
            for row in graph.query("MATCH (s:Symbol {kind: 'file'}) RETURN s.id AS id")
        )
        sampled = _sample(files, sample)

        deps = DependencyService(graph)
        blast = BlastRadiusService(graph)
        latencies: list[float] = []
        ratios: list[float] = []
        baseline_total = 0
        topolox_total = 0

        for file_id in sampled:
            start = time.perf_counter()
            report = blast.simulate([file_id])
            latencies.append((time.perf_counter() - start) * 1000)
            start = time.perf_counter()
            dependency_map = deps.of_file(file_id)
            latencies.append((time.perf_counter() - start) * 1000)

            baseline = 0
            for rel in (file_id, *report.impacted_files):
                source = root / rel
                if source.is_file():
                    baseline += estimate_tokens(
                        source.read_text(encoding="utf-8", errors="replace")
                    )
            topolox = estimate_tokens(json.dumps(report.model_dump())) + estimate_tokens(
                json.dumps(dependency_map.model_dump())
            )
            if baseline > 0 and topolox > 0:
                baseline_total += baseline
                topolox_total += topolox
                ratios.append(baseline / topolox)

        return BenchmarkReport(
            files=stats.files,
            nodes=stats.nodes,
            edges=stats.edges,
            index_seconds=round(stats.seconds, 2),
            files_per_second=round(stats.files / stats.seconds, 1) if stats.seconds else 0.0,
            sampled_files=len(sampled),
            query_p50_ms=round(_percentile(latencies, 0.5), 2),
            query_p95_ms=round(_percentile(latencies, 0.95), 2),
            token_reduction_median=round(statistics.median(ratios), 1) if ratios else 0.0,
            token_reduction_mean=round(statistics.mean(ratios), 1) if ratios else 0.0,
            baseline_tokens=baseline_total,
            topolox_tokens=topolox_total,
        )
    finally:
        graph.close()
        vectors.close()
        shutil.rmtree(data_dir, ignore_errors=True)
