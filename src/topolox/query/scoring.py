"""Graph scoring helpers (centrality, downstream traversal). Phase 2.

Traversal/ranking is done in Kùzu Cypher by default; ``networkx`` is added only
if personalized-PageRank-style scoring is needed.
"""

from __future__ import annotations
