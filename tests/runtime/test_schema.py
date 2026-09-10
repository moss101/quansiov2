"""DAT-002 acceptance tests: authoritative relational schema and migrations.

Runs against the real qualification PostgreSQL. Positive: migrations build
the tenant-scoped schema across all governed areas. Negative: cross-tenant
key/reference insertion is rejected by composite foreign keys. Recovery: the
latest reversible migration rolls back and re-applies with consistent
schema, invariants and migration history.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from quansio.platform import migrate as migrate_module  # noqa: E402
from quansio.platform.db import database_config  # noqa: E402


@pytest.fixture()
def db(migrated_db):
    return migrated_db


def _table_names(db) -> set[str]:
    rows = db.query_all(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    )
    return {r[0] for r in rows}


def test_dat002_p01_all_governed_schema_areas_exist(db):
    tables = _table_names(db)
    required = {
        "tenants",          # identities
        "workspaces",
        "users",
        "sessions",
        "role_bindings",
        "agents",           # agents
        "runs",             # runs
        "graphs",           # graphs
        "graph_nodes",
        "protocol_state",   # protocol state
        "approvals",        # approvals
        "effects",          # effects
        "schedules",        # schedules
        "registry_entries", # registries
        "runtime_events",   # durable event transport
        "event_outbox",
        "event_cursors",
    }
    missing = required - tables
    assert missing == set(), f"missing schema areas: {missing}"
    # every tenant-scoped table carries tenant_id in its primary key scope
    for table in ("runs", "graphs", "effects", "approvals", "schedules"):
        pk = db.query_all(
            """
            SELECT a.attname FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
            """,
            (table,),
        )
        assert any(column[0] == "tenant_id" for column in pk), f"{table} primary key is not tenant-scoped: {pk}"


def test_dat002_n01_cross_tenant_reference_is_rejected(db, control, workspace_setup):
    suffix = uuid.uuid4().hex[:10]
    other_tenant = control.create_tenant(f"other-{suffix}")
    other_workspace = control.create_workspace(other_tenant, f"ws-{suffix}")

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with db.connection() as connection:
            connection.execute(
                """
                INSERT INTO runs (tenant_id, workspace_id, run_id, agent_id, status)
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (
                    workspace_setup["tenant_id"],          # run claims tenant A
                    workspace_setup["workspace_a"],
                    str(uuid.uuid4()),
                    workspace_setup["admin"],              # but the agent id is a user id of tenant A scope, invalid shape
                ),
            )

    # A run in tenant A referencing an agent owned by tenant B must fail.
    with db.connection() as connection:
        connection.execute(
            """
            INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)
            VALUES (%s, %s, %s, 'persistent_teammate', %s)
            """,
            (other_tenant, other_workspace, str(uuid.uuid4()), "rogue"),
        )
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with db.connection() as connection:
            connection.execute(
                """
                INSERT INTO runs (tenant_id, workspace_id, run_id, agent_id, status)
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (
                    workspace_setup["tenant_id"],
                    workspace_setup["workspace_a"],
                    str(uuid.uuid4()),
                    _last_agent_id(db, other_tenant),  # cross-tenant agent identity
                ),
            )


def _last_agent_id(db, tenant_id: str) -> str:
    return db.query_one(
        "SELECT agent_id FROM agents WHERE tenant_id = %s ORDER BY created_at DESC LIMIT 1",
        (tenant_id,),
    )[0]


def test_dat002_r01_latest_reversible_migration_round_trip(db):
    config = database_config()
    with psycopg.connect(config.conninfo(), autocommit=True) as connection:
        # Up: ensure fully applied.
        assert "0003_events_outbox" in _migration_state(connection)
        # Rollback the latest reversible migration.
        undone = migrate_module.down(connection, steps=1)
        assert undone == ["0003_events_outbox"]
        tables = {r[0] for r in connection.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()}
        assert "runtime_events" not in tables
        assert "approvals" in tables, "rollback must not touch unrelated schema areas"
        # Re-apply: history and invariants consistent.
        applied = migrate_module.up(connection)
        assert applied == ["0003_events_outbox"]
        state = _migration_state(connection)
        assert state == {"0001_identities", "0002_work_runtime", "0003_events_outbox"}


def _migration_state(connection) -> set[str]:
    connection.execute("SELECT 1")  # keep transaction context explicit
    rows = connection.execute(
        "SELECT migration_id FROM schema_migrations WHERE direction = 'up'"
    ).fetchall()
    return {r[0] for r in rows}
