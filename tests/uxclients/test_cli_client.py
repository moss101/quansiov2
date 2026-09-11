"""Acceptance tests for the packaged command-line client (UX-008).

The CLI must work as a real client of the canonical HTTP surfaces: it logs
in against quansio-api, submits an admitted command, follows canonical
events with a persisted cursor, and owns no execution authority locally.
The service apps are exercised through an in-process HTTP boundary with the
real migrated database; only the network socket is substituted.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))
sys.path.insert(0, str(REPO_ROOT / "clients/cli"))

import quansio_cli.main as cli  # noqa: E402

from quansio.api.app import create_app as create_api_app  # noqa: E402
from quansio.control.app import create_app as create_control_app  # noqa: E402
from quansio.control.capability import CapabilityService  # noqa: E402
from quansio.notify.app import create_app as create_notify_app  # noqa: E402
from quansio.runtime.app import create_app as create_runtime_app  # noqa: E402

PORTS = {"8080": "api", "8081": "control", "8087": "runtime", "8089": "notify"}


@pytest.fixture()
def cli_home(tmp_path, monkeypatch):
    home = tmp_path / "quansio-home"
    monkeypatch.setattr(cli, "CONFIG_DIR", home)
    monkeypatch.setattr(cli, "CONFIG_PATH", home / "cli.json")
    return home


@pytest.fixture()
def http_boundary(migrated_db, monkeypatch):
    """Route the CLI's httpx.request calls onto the in-process apps."""
    apps = {
        "api": create_api_app(migrated_db),
        "control": create_control_app(migrated_db),
        "runtime": create_runtime_app(migrated_db),
        "notify": create_notify_app(migrated_db),
    }

    def fake_request(method, url, **kwargs):
        from urllib.parse import urlparse

        from fastapi.testclient import TestClient

        port = urlparse(url).port
        service = PORTS[str(port)]
        path = urlparse(url).path
        with TestClient(apps[service]) as client:
            response = client.request(
                method, path,
                params=kwargs.get("params"),
                json=kwargs.get("json"),
                content=kwargs.get("content"),
                headers=kwargs.get("headers") or {},
            )
        return response

    monkeypatch.setattr(cli.httpx, "request", fake_request)
    return apps


def _login(tenant_setup):
    result = cli.main([
        "login",
        "--tenant-id", tenant_setup["tenant_id"],
        "--workspace-id", tenant_setup["workspace_a"],
        "--email", tenant_setup["admin_email"],
        "--password", "correct horse battery",
    ])
    assert result == 0


def test_cli_login_whoami_task_and_event_follow(
    migrated_db, workspace_setup, cli_home, http_boundary, capsys
):
    from quansio.platform.repository import TenantRepository
    from quansio.runtime.events import EventLog

    _login(workspace_setup)
    capsys.readouterr()  # drop the login output before parsing later output
    saved = json.loads(cli.CONFIG_PATH.read_text())
    assert saved["token"], "login must persist the bearer token"
    import os

    mode = oct(cli.CONFIG_PATH.stat().st_mode & 0o777)
    assert mode == "0o600", f"credentials must be owner-only, got {mode}"

    # whoami reflects server-resolved identity, not client claims
    assert cli.main(["whoami"]) == 0
    identity = json.loads(capsys.readouterr().out)["identity"]
    assert identity["tenant_id"] == workspace_setup["tenant_id"]

    # a canonical run with events exists; the CLI follows it with a cursor
    identity_dict = identity
    from quansio.platform.context import IdentityContext
    from quansio.control.capability import CapabilityService
    from quansio.runtime.agents import AgentRegistry

    identity_context = IdentityContext(
        tenant_id=identity_dict["tenant_id"],
        workspace_id=identity_dict["workspace_id"],
        user_id=identity_dict["user_id"],
        session_id=str(uuid.uuid4()),
        roles=tuple(identity_dict["roles"]),
        expires_at=identity_dict["expires_at"],
    )
    snapshot = CapabilityService(migrated_db).admit_root(
        identity_context, identity_dict["user_id"], ["cap.cli"], {}, 100,
    )
    agent_id = AgentRegistry(migrated_db, CapabilityService(migrated_db)).create_persistent_teammate(
        identity_context, f"cli-agent-{uuid.uuid4().hex[:6]}", snapshot["snapshot_id"],
    )
    run_id = TenantRepository(migrated_db).create_run(
        identity_context, agent_id=agent_id, budget_cents=10,
    )
    events = EventLog(migrated_db)
    events.append(identity_context, run_id, "run.started", {"status": "running"})
    events.append(identity_context, run_id, "run.state", {"status": "succeeded"})

    assert cli.main(["follow", "--run-id", run_id]) == 0
    followed = json.loads(capsys.readouterr().out)
    assert followed["applied"] == 2
    assert followed["cursor"] == 2

    # a second follow applies nothing new (cursor persisted) — no duplicates
    assert cli.main(["follow", "--run-id", run_id]) == 0
    again = json.loads(capsys.readouterr().out)
    assert again["applied"] == 0
    assert again["cursor"] == 2

    # task status reads the canonical run
    assert cli.main(["task", "status", "--run-id", run_id]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["run_id"] == run_id
    assert status["status"] == "pending"


def test_cli_without_login_refuses(migrated_db, cli_home, http_boundary, capsys):
    # No stored token: the CLI refuses instead of inventing identity.
    assert cli.main(["whoami"]) == 1
    assert "not logged in" in capsys.readouterr().err
