"""Auth module (test fixture)."""

from pkg.db import Connection


def login(conn: Connection, user: str, password: str) -> bool:
    return verify(conn, user, password)


def verify(conn: Connection, user: str, password: str) -> bool:
    return bool(user and password)
