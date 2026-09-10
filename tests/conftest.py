"""Shared fixtures: real qualification PostgreSQL with migrated schema."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.control.identity import ControlService  # noqa: E402
from quansio.platform.db import PlatformDatabase, database_config  # noqa: E402
from quansio.platform import migrate as migrate_module  # noqa: E402


import subprocess


def _env_healthy() -> bool:
    result = subprocess.run(
        [sys.executable, "tools/environment/qualenv.py", "health", "--no-write"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    return result.returncode == 0


@pytest.fixture(scope="session")
def events_db():
    database = PlatformDatabase(database_config("quansio_events"))
    yield database
    database.close()


@pytest.fixture(scope="session")
def minio_client():
    from minio import Minio
    from quansio.platform.db import load_qualenv_passwords

    material = load_qualenv_passwords()
    return Minio(
        "127.0.0.1:54331",
        access_key="quansio_qual_admin",
        secret_key=material["QUAL_MINIO_PASSWORD"],
        secure=False,
    )


@pytest.fixture(scope="session")
def redis_url():
    from quansio.platform.db import load_qualenv_passwords

    material = load_qualenv_passwords()
    return f"redis://:{material['QUAL_REDIS_PASSWORD']}@127.0.0.1:54330/0"


@pytest.fixture(scope="session")
def platform_db():
    # Ensure the real qualification environment is up before any suite that
    # touches authoritative state; if it is down, provision it fresh.
    if not _env_healthy():
        result = subprocess.run(
            [sys.executable, "tools/environment/qualenv.py", "provision"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stdout + result.stderr
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


def pytest_collection_modifyitems(items):
    """Environment lifecycle tests run last: they provision and tear down
    the shared qualification stack, which other suites must not depend on
    during teardown."""
    environment = [item for item in items if "tests/environment" in str(item.fspath)]
    if environment:
        rest = [item for item in items if "tests/environment" not in str(item.fspath)]
        items[:] = rest + environment
