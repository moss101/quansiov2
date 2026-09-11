"""DAT-001 acceptance tests: tenant and authenticated session authority.

Positive: authenticating into one tenant/workspace makes every admitted
command carry server-resolved tenant, user, session and workspace identity.
Negative: a modified client-supplied tenant or user identifier is rejected
before any authoritative read or write. Recovery: restarting the API process
preserves durable sessions; a valid session resumes without recreating
authority from client state.

These tests run against the real qualification PostgreSQL provisioned by
ENV-001 (never in-memory substitutes).
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from quansio.api.app import create_app  # noqa: E402
from quansio.platform.context import IdentityContextError  # noqa: E402
from quansio.platform.db import database_config  # noqa: E402


def _recording_transport(envelope, authorization):
    """Stand-in for the runtime admission authority: records the forwarded
    envelope so tests can assert exactly what the API forwarded."""
    _recording_transport.forwarded.append(dict(envelope))
    return {
        "command_id": envelope["command_id"],
        "run_id": str(uuid.uuid4()),
        "status": "dispatched",
        "replayed": False,
    }


_recording_transport.forwarded = []


@pytest.fixture()
def app(migrated_db):
    from quansio.platform.db import PlatformDatabase

    _recording_transport.forwarded.clear()
    return create_app(
        PlatformDatabase(database_config(), max_size=4),
        runtime_transport=_recording_transport,
    )


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient

    with TestClient(app) as http:
        yield http


def _login(client, setup, workspace=None, email_key="admin_email") -> tuple[str, dict]:
    response = client.post(
        "/v9/sessions",
        json={
            "tenant_id": setup["tenant_id"],
            "workspace_id": workspace or setup["workspace_a"],
            "email": setup[email_key],
            "password": "correct horse battery" if email_key == "admin_email" else "member pass phrase",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return body["token"], body["identity"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_dat001_p01_commands_carry_server_resolved_identity(client, workspace_setup):
    token, identity = _login(client, workspace_setup)
    response = client.post(
        "/v9/commands",
        json={
            "command_type": "run.create",
            "arguments": {"objective": "qualify identity propagation"},
            "idempotency_key": uuid.uuid4().hex,
        },
        headers=_auth(token),
    )
    assert response.status_code == 200, response.text
    command = response.json()["command"]
    # Every authoritative identity field comes from the server-resolved session.
    assert command["tenant_id"] == workspace_setup["tenant_id"] == identity["tenant_id"]
    assert command["workspace_id"] == workspace_setup["workspace_a"] == identity["workspace_id"]
    assert command["actor_id"] == workspace_setup["admin"] == identity["user_id"]
    assert command["session_id"] == identity["session_id"]
    assert command["idempotency_key"], "idempotency key must be present"


def test_dat001_p01_session_resolves_from_server_state(client, workspace_setup, control):
    token, identity = _login(client, workspace_setup)
    response = client.get("/v9/identity", headers=_auth(token))
    assert response.status_code == 200
    resolved = response.json()["identity"]
    assert resolved == identity
    # The durable session row exists server-side; the raw token is not stored.
    row = control._db.query_one(
        "SELECT token_hash FROM sessions WHERE session_id = %s",
        (identity["session_id"],),
    )
    assert row is not None
    assert "bearer" not in row[0].lower()[:10] and token.encode() not in row[0].encode()


def test_dat001_n01_client_supplied_identity_is_rejected_before_authority(client, workspace_setup, control):
    token, _identity = _login(client, workspace_setup)
    foreign_tenant = str(uuid.uuid4())
    for smuggled in (
        {"tenant_id": foreign_tenant},
        {"user_id": workspace_setup["member"]},
        {"workspace_id": workspace_setup["workspace_b"]},
        {"session_id": str(uuid.uuid4())},
    ):
        response = client.post(
            "/v9/commands",
            json={
                "command_type": "run.create",
                "arguments": {"objective": "escalate", **smuggled},
                "idempotency_key": uuid.uuid4().hex,
            },
            headers=_auth(token),
        )
        assert response.status_code == 403, (smuggled, response.text)
        assert "not accepted" in response.json()["detail"]
    # No authoritative identity state was created or modified by the attempts.
    sessions = control._db.query_all(
        "SELECT session_id FROM sessions WHERE tenant_id = %s",
        (workspace_setup["tenant_id"],),
    )
    assert len(sessions) == 1, "rejected requests must not create authoritative state"


def test_dat001_n01_wrong_tenant_credentials_do_not_authenticate(client, workspace_setup):
    response = client.post(
        "/v9/sessions",
        json={
            "tenant_id": str(uuid.uuid4()),
            "workspace_id": workspace_setup["workspace_a"],
            "email": workspace_setup["admin_email"],
            "password": "correct horse battery",
        },
    )
    assert response.status_code == 401


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _spawn_api(port: int) -> subprocess.Popen:
    env = dict(os.environ)
    env["QUANSIO_API_PORT"] = str(port)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "quansio.api.app:create_app", "--factory", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=REPO_ROOT,
        env=env,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return process
        except OSError:
            if process.poll() is not None:
                raise AssertionError(f"api process exited: {process.communicate()}")
            time.sleep(0.3)
    raise AssertionError("api process did not become reachable")


def test_dat001_r01_session_survives_api_process_restart(migrated_db):
    port = _free_port()
    process = _spawn_api(port)
    client = httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=10)
    try:
        suffix = uuid.uuid4().hex[:10]
        from quansio.control.identity import ControlService

        control = ControlService(migrated_db)
        tenant_id = control.create_tenant(f"restart-{suffix}")
        workspace_id = control.create_workspace(tenant_id, f"ws-{suffix}")
        control.create_user(tenant_id, f"u-{suffix}@qual.invalid", "U", "restart proof pw", role="tenant_admin")
        login = client.post(
            "/v9/sessions",
            json={
                "tenant_id": tenant_id,
                "workspace_id": workspace_id,
                "email": f"u-{suffix}@qual.invalid",
                "password": "restart proof pw",
            },
        )
        assert login.status_code == 200, login.text
        token = login.json()["token"]

        before = client.get("/v9/identity", headers=_auth(token))
        assert before.status_code == 200

        # Kill the API process hard (SIGKILL) and restart it.
        process.send_signal(signal.SIGKILL)
        process.wait(timeout=10)
        restarted = _spawn_api(port)
        try:
            after = client.get("/v9/identity", headers=_auth(token))
            assert after.status_code == 200, after.text
            assert after.json()["identity"]["session_id"] == before.json()["identity"]["session_id"]
        finally:
            restarted.send_signal(signal.SIGTERM)
            restarted.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
        client.close()
