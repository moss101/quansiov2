"""Migration runner for the authoritative relational schema.

Applies ``migrations/up/<id>.sql`` and reverses ``migrations/down/<id>.sql``
in lexicographic order, recording each step in ``schema_migrations`` with the
file's sha256. Applied out of band from request handling; each migration is
one transaction.

Usage::

    python -m quansio.platform.migrate up     [--database quansio_platform]
    python -m quansio.platform.migrate down   [--steps N]
    python -m quansio.platform.migrate status
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import psycopg

from quansio.platform.db import database_config

ROOT = Path(__file__).resolve().parents[2]
UP_DIR = ROOT / "migrations/up"
DOWN_DIR = ROOT / "migrations/down"
MIGRATION_ID = re.compile(r"^(\d+_.+)\.sql$")


def _ensure_history(connection: psycopg.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id TEXT PRIMARY KEY,
            direction    TEXT NOT NULL CHECK (direction IN ('up','down')),
            checksum     TEXT NOT NULL,
            applied_at   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def _applied(connection: psycopg.Connection) -> dict[str, str]:
    _ensure_history(connection)
    cursor = connection.execute(
        "SELECT migration_id, checksum FROM schema_migrations WHERE direction = 'up'"
    )
    return {migration_id: checksum for migration_id, checksum in cursor.fetchall()}


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def up(connection: psycopg.Connection, steps: int | None = None) -> list[str]:
    applied = _applied(connection)
    pending = []
    for path in sorted(UP_DIR.glob("*.sql")):
        migration_id = MIGRATION_ID.match(path.name)
        if not migration_id:
            raise RuntimeError(f"migration file does not match <id>.sql: {path.name}")
        migration_id = migration_id.group(1)
        if migration_id not in applied:
            pending.append((migration_id, path))
    pending = pending[:steps] if steps is not None else pending
    applied_now = []
    for migration_id, path in pending:
        with connection.transaction():
            connection.execute(path.read_text())
            connection.execute(
                "INSERT INTO schema_migrations (migration_id, direction, checksum) VALUES (%s, 'up', %s)",
                (migration_id, _checksum(path)),
            )
        applied_now.append(migration_id)
    return applied_now


def down(connection: psycopg.Connection, steps: int = 1) -> list[str]:
    applied = _applied(connection)
    reversed_ids = sorted(applied, reverse=True)[:steps]
    undone = []
    for migration_id in reversed_ids:
        path = DOWN_DIR / f"{migration_id}.sql"
        if not path.is_file():
            raise RuntimeError(f"migration {migration_id} has no down script; refusing irreversible rollback")
        with connection.transaction():
            connection.execute(path.read_text())
            connection.execute(
                "INSERT INTO schema_migrations (migration_id, direction, checksum) VALUES (%s, 'down', %s)",
                (migration_id, _checksum(path)),
            )
            connection.execute("DELETE FROM schema_migrations WHERE migration_id = %s AND direction = 'up'", (migration_id,))
        undone.append(migration_id)
    return undone


def status(connection: psycopg.Connection) -> dict[str, bool]:
    applied = _applied(connection)
    known = {MIGRATION_ID.match(p.name).group(1) for p in UP_DIR.glob("*.sql") if MIGRATION_ID.match(p.name)}
    return {migration_id: migration_id in applied for migration_id in sorted(known)}


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    database = "quansio_platform"
    if "--database" in sys.argv:
        database = sys.argv[sys.argv.index("--database") + 1]
    steps = int(sys.argv[sys.argv.index("--steps") + 1]) if "--steps" in sys.argv else None

    config = database_config(database)
    with psycopg.connect(config.conninfo(), autocommit=True) as connection:
        _ensure_history(connection)
        if command == "up":
            done = up(connection, steps)
            print(f"MIGRATE UP: {len(done)} applied {done}")
        elif command == "down":
            done = down(connection, steps or 1)
            print(f"MIGRATE DOWN: {len(done)} reverted {done}")
        elif command == "status":
            for migration_id, is_applied in status(connection).items():
                print(f"{'applied ' if is_applied else 'pending '}{migration_id}")
        else:
            raise SystemExit(f"unknown command {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
