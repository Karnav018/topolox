"""Database module (test fixture)."""


class Connection:
    """A fake database connection."""


def connect() -> Connection:
    return Connection()
