"""Kùzu graph schema (Cypher DDL)."""

from __future__ import annotations

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """CREATE NODE TABLE IF NOT EXISTS Symbol(
        id STRING,
        kind STRING,
        name STRING,
        qualified_name STRING,
        path STRING,
        language STRING,
        signature STRING,
        docstring STRING,
        start_line INT64,
        end_line INT64,
        PRIMARY KEY (id)
    )""",
    "CREATE REL TABLE IF NOT EXISTS Rel(FROM Symbol TO Symbol, kind STRING, weight DOUBLE)",
)
