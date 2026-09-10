"""Shared fixtures: real qualification PostgreSQL with migrated schema."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.control.identity import ControlService  # noqa: E402
from quansio.platform.db import PlatformDatabase, database_config  # noqa: E402
from quansio.platform import migrate as migrate_module  # noqa: E402


@pytest.fixture(scope="session")
def platform_db():
    database = PlatformDatabase(database_config())
    yield database
    database.close()


@pytest.fixture(scope="session")
def migrated_db(platform_db):
    config = database_config()
    import psycopg

    with psycopg.connect(config.conninfo(), autocommit=True) as connection:
        migrate_module.up(connection)
    return platform_db


@pytest.fixture()
def control(migrated_db) -> ControlService:
    return ControlService(migrated_db)


@pytest.fixture()
def workspace_setup(control):
    """One tenant with two workspaces and two users (isolation per test)."""
    suffix = uuid.uuid4().hex[:10]
    tenant_id = control.create_tenant(f"qual-{suffix}")
    workspace_a = control.create_workspace(tenant_id, f"ws-a-{suffix}")
    workspace_b = control.create_workspace(tenant_id, f"ws-b-{suffix}")
    admin = control.create_user(
        tenant_id, f"admin-{suffix}@qual.invalid", "Qual Admin", "correct horse battery", role="tenant_admin"
    )
    member = control.create_user(
        tenant_id,
        f"member-{suffix}@qual.invalid",
        "Qual Member",
        "member pass phrase",
        role="member",
        workspace_id=workspace_a,
    )
    return {
        "tenant_id": tenant_id,
        "workspace_a": workspace_a,
        "workspace_b": workspace_b,
        "admin": admin,
        "member": member,
        "admin_email": f"admin-{suffix}@qual.invalid",
        "member_email": f"member-{suffix}@qual.invalid",
    }
