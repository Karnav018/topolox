"""Resolve import edges (bare module names) to the files they name.

Code imports a module by its *import name* (e.g. ``app.db``), but a file's node id is
its repo-relative path and its qualified name is path-derived (``apps.api.app.db``).
Without linking the two, dependents and blast radius can't traverse the file graph on
``src/``- or monorepo layouts.

This pass links an import target to a file when the file's dotted path *ends with* the
imported module and that match is unique, adding an ``imports`` edge from the importer to
the resolved file node.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topolox.graph.store import GraphStore

_FILES = "MATCH (s:Symbol {kind: 'file'}) RETURN s.id AS id, s.qualified_name AS qn"

_IMPORT_EDGES = (
    "MATCH (a:Symbol)-[r:Rel {kind: 'imports'}]->(t) "
    "RETURN DISTINCT a.id AS importer, t.id AS target"
)

_LINK = (
    "MATCH (a:Symbol {id: $src}), (b:Symbol {id: $dst}) MERGE (a)-[r:Rel {kind: 'imports'}]->(b)"
)


def resolve_imports(store: GraphStore) -> int:
    """Add ``imports`` edges from importers to resolved file nodes; return the count."""
    qn_to_id: dict[str, str] = {}
    suffix_to_ids: dict[str, set[str]] = {}
    for row in store.query(_FILES):
        file_id = str(row["id"])
        qualified = str(row["qn"] or "")
        if not qualified:
            continue
        qn_to_id[qualified] = file_id
        parts = qualified.split(".")
        for index in range(len(parts)):
            suffix_to_ids.setdefault(".".join(parts[index:]), set()).add(file_id)

    file_ids = set(qn_to_id.values())
    resolved = 0
    for row in store.query(_IMPORT_EDGES):
        importer = str(row["importer"])
        target = str(row["target"])
        if target in file_ids:
            continue  # already points at a file
        dest = qn_to_id.get(target)
        if dest is None:
            candidates = suffix_to_ids.get(target)
            if candidates and len(candidates) == 1:
                dest = next(iter(candidates))
        if dest is not None and dest != importer:
            store.query(_LINK, {"src": importer, "dst": dest})
            resolved += 1
    return resolved
