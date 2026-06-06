"""Sample application entry point (test fixture)."""

from pkg.auth import login
from pkg.db import connect


def run() -> bool:
    conn = connect()
    return login(conn, "user", "pass")
