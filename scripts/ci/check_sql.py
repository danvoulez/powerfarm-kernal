#!/usr/bin/env python3
"""Static migration invariants that do not require a database."""

from __future__ import annotations

import re
from pathlib import Path

from pglast import parse_sql


def main() -> int:
    migrations = sorted(Path("supabase/migrations").glob("*.sql"))
    if not migrations:
        raise RuntimeError("no migrations found")
    forbidden_storage_write = re.compile(
        r"\b(?:insert|update|delete|alter|create)\s+(?:into\s+)?storage\.", re.IGNORECASE
    )
    versions: set[str] = set()
    for migration in migrations:
        content = migration.read_text()
        parse_sql(content)
        version = migration.name.split("_", 1)[0]
        if version in versions:
            raise RuntimeError(f"duplicate migration version: {version}")
        versions.add(version)
        if content.count("begin;") != 1 or content.count("commit;") != 1:
            raise RuntimeError(f"migration must have exactly one transaction: {migration}")
        if forbidden_storage_write.search(content):
            raise RuntimeError(f"direct storage schema write is forbidden: {migration}")
    print(f"validated {len(migrations)} SQL migrations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
