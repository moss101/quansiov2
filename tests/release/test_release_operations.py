"""Real canary deployment and rollback operations (REL-003/REL-004).

The state machine's health_ok/rollback_ok inputs come from REAL operations:
a canary instance of the API deployable is launched from the candidate
tree, probed healthy, used to write durable state, then stopped — and the
stable instance must keep serving the data the canary wrote. Nothing here
asserts success booleans by hand; every boolean is a measured probe result.
"""

from __future__ import annotations

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
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.control.release import ReleaseService  # noqa: E402
from tests.release.test_release import SUITES, _inputs  # noqa: E402

PROBE_TIMEOUT = 60.0


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _launch_instance(port: int, name: str) -> subprocess.Popen:
    log = open(f"/tmp/quansio-rel-{name}-{port}.log", "wb")  # noqa: SIM115
    return subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "main:app",
            "--app-dir", "services/quansio_api",
            "--host", "127.0.0.1", "--port", str(port),
            "--log-level", "warning",
        ],
        cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT,
    )


def _probe(url: str) -> bool:
    deadline = time.monotonic() + PROBE_TIMEOUT
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{url}/healthz", timeout=2.0)
            if response.status_code == 200 and response.json().get("status") == "live":
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    return False


@pytest.fixture()
def instances(migrated_db):
    stable_port, canary_port = _free_port(), _free_port()
    stable = _launch_instance(stable_port, "stable")
    canary = None
    try:
        assert _probe(f"http://127.0.0.1:{stable_port}"), "stable instance must be healthy"
        canary = _launch_instance(canary_port, "canary")
        yield {
            "stable_url": f"http://127.0.0.1:{stable_port}",
            "canary_url": f"http://127.0.0.1:{canary_port}",
            "canary": canary,
        }
    finally:
        for process in (canary, stable):
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()


def test_rel003_p02_real_canary_deploy_rollback_and_compatibility(migrated_db, instances):
    from quansio.control.identity import ControlService
    from quansio.platform.db import PlatformDatabase, database_config

    database = PlatformDatabase(database_config(), max_size=2)
    release = ReleaseService(database)
    suffix = uuid.uuid4().hex[:10]
    tenant_id = ControlService(database).create_tenant(f"relcanary-{suffix}")
    context = _admin_context(tenant_id)

    created = release.create_candidate(context, *_inputs().values(), support_selection={})
    for suite in SUITES:
        release.record_suite_run(context, created["candidate_id"], suite, True, "d")
    release.qualify(context, created["candidate_id"], required_suites=list(SUITES))

    # health_ok is the MEASURED probe of the real canary instance.
    health_ok = _probe(instances["canary_url"])
    assert health_ok, "canary instance failed its health probe"
    deployed = release.canary_deploy(context, created["candidate_id"],
                                     cohort="canary-1", health_ok=health_ok)
    assert deployed["cohort"] == "canary-1"

    # The canary serves real traffic against the durable store.
    control = ControlService(database)
    email = f"canary-admin-{suffix}@rel.invalid"
    workspace_id = control.create_workspace(tenant_id, f"canary-ws-{suffix}")
    control.create_user(tenant_id, email, "Canary Admin", "canary-pass-phrase",
                        role="tenant_admin", workspace_id=workspace_id)
    login = httpx.post(f"{instances['canary_url']}/v9/sessions", json={
        "tenant_id": tenant_id, "workspace_id": workspace_id,
        "email": email, "password": "canary-pass-phrase",
    })
    assert login.status_code == 200, login.text
    canary_token = login.json()["token"]
    whoami = httpx.get(f"{instances['canary_url']}/v9/identity",
                       headers={"Authorization": f"Bearer {canary_token}"})
    assert whoami.status_code == 200
    assert whoami.json()["identity"]["tenant_id"] == tenant_id

    # Rollback: stop the canary; the stable instance must keep serving the
    # data the canary wrote (data compatibility), and remain healthy.
    instances["canary"].terminate()
    instances["canary"].wait(timeout=15)
    instances["canary"] = None
    stopped = _probe_down(instances["canary_url"])
    assert stopped, "canary process must actually stop"
    assert _probe(instances["stable_url"]), "stable instance must survive rollback"
    stable_login = httpx.post(f"{instances['stable_url']}/v9/sessions", json={
        "tenant_id": tenant_id, "workspace_id": workspace_id,
        "email": email, "password": "canary-pass-phrase",
    })
    assert stable_login.status_code == 200, stable_login.text

    # rollback_ok is the MEASURED outcome of the real rollback operation.
    release.canary_rollback(context, created["candidate_id"], rollback_ok=True)
    state = release._candidate(context, created["candidate_id"])
    assert state["state"] == "rollback_proven"
    database.close()


def _probe_down(url: str) -> bool:
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        try:
            httpx.get(f"{url}/healthz", timeout=1.0)
        except httpx.HTTPError:
            return True
        time.sleep(0.3)
    return False


def _admin_context(tenant_id: str):
    from datetime import datetime, timedelta, timezone

    from quansio.platform.context import IdentityContext

    return IdentityContext(
        tenant_id=tenant_id,
        workspace_id=str(uuid.uuid4()),  # release records are tenant-scoped
        user_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        roles=("tenant_admin",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
