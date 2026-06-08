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

# Name-based CALLS / INHERITS edges point at bare-name placeholders (path = '');
# these passes link them to the real symbol they name, in order of confidence:
# a same-file definition, then a definition in a file the caller imports, then a
# unique repo-wide match. Ambiguous names are left unresolved rather than mislinked.
_CLASSES = (
    "MATCH (s:Symbol {kind: 'class'}) WHERE s.path <> '' "
    "RETURN s.id AS id, s.name AS name, s.path AS path"
)

# Resolved file-to-file import edges (built by resolve_imports), used to prefer an
# imported definition when a bare name is defined in several files.
_FILE_IMPORTS = (
    "MATCH (a:Symbol {kind: 'file'})-[r:Rel {kind: 'imports'}]->(b:Symbol {kind: 'file'}) "
    "RETURN a.path AS importer, b.path AS imported"
)

_CALL_TARGETS = (
    "MATCH (s:Symbol) WHERE s.path <> '' AND s.kind IN ['function', 'method', 'class'] "
    "RETURN s.id AS id, s.name AS name, s.path AS path"
)

_INHERIT_EDGES = (
    "MATCH (a:Symbol)-[r:Rel {kind: 'inherits'}]->(t) WHERE t.path IS NULL OR t.path = '' "
    "RETURN DISTINCT a.id AS src, a.path AS src_path, t.id AS name"
)

_CALL_EDGES = (
    "MATCH (a:Symbol)-[r:Rel {kind: 'calls'}]->(t) WHERE t.path IS NULL OR t.path = '' "
    "RETURN DISTINCT a.id AS src, a.path AS src_path, t.id AS name"
)

_LINK_INHERITS = (
    "MATCH (a:Symbol {id: $src}), (b:Symbol {id: $dst}) MERGE (a)-[r:Rel {kind: 'inherits'}]->(b)"
)

_LINK_CALLS = (
    "MATCH (a:Symbol {id: $src}), (b:Symbol {id: $dst}) MERGE (a)-[r:Rel {kind: 'calls'}]->(b)"
)


def _index_by_name(rows: list[dict[str, object]]) -> dict[str, list[tuple[str, str]]]:
    by_name: dict[str, list[tuple[str, str]]] = {}
    for row in rows:
        by_name.setdefault(str(row["name"]), []).append((str(row["id"]), str(row["path"])))
    return by_name


def _imports_by_file(store: GraphStore) -> dict[str, set[str]]:
    """Map each file path to the set of file paths it imports (resolved edges)."""
    out: dict[str, set[str]] = {}
    for row in store.query(_FILE_IMPORTS):
        out.setdefault(str(row["importer"]), set()).add(str(row["imported"]))
    return out


def _pick(
    candidates: list[tuple[str, str]],
    src_path: str,
    src_id: str,
    imported_paths: set[str],
    *,
    exclude_self: bool,
) -> str | None:
    """Choose the best symbol id for a name: same-file, then imported-file, then unique global."""
    cands = [(cid, cpath) for cid, cpath in candidates if not (exclude_self and cid == src_id)]
    if not cands:
        return None
    same = [cid for cid, cpath in cands if cpath == src_path]
    if len(same) == 1:
        return same[0]
    if same:
        return None  # ambiguous within the file
    imported = [cid for cid, cpath in cands if cpath in imported_paths]
    if len(imported) == 1:
        return imported[0]
    if imported:
        return None  # ambiguous among imported files
    return cands[0][0] if len(cands) == 1 else None


def resolve_inheritance(store: GraphStore) -> int:
    """Link ``inherits`` edges from a class to the base class it names; return the count."""
    by_name = _index_by_name(store.query(_CLASSES))
    imports = _imports_by_file(store)
    resolved = 0
    for row in store.query(_INHERIT_EDGES):
        src, src_path, name = str(row["src"]), str(row["src_path"]), str(row["name"])
        dest = _pick(
            by_name.get(name, []), src_path, src, imports.get(src_path, set()), exclude_self=True
        )
        if dest is not None:
            store.query(_LINK_INHERITS, {"src": src, "dst": dest})
            resolved += 1
    return resolved


def resolve_calls(store: GraphStore) -> int:
    """Link ``calls`` edges to the function/method/class they name; return the count."""
    by_name = _index_by_name(store.query(_CALL_TARGETS))
    imports = _imports_by_file(store)
    resolved = 0
    for row in store.query(_CALL_EDGES):
        src, src_path, name = str(row["src"]), str(row["src_path"]), str(row["name"])
        dest = _pick(
            by_name.get(name, []), src_path, src, imports.get(src_path, set()), exclude_self=False
        )
        if dest is not None:
            store.query(_LINK_CALLS, {"src": src, "dst": dest})
            resolved += 1
    return resolved


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
