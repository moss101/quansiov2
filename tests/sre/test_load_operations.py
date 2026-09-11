"""Measured load and degradation qualification (SRE-005).

Load is driven over real HTTP against a live instance of the API deployable:
concurrent authenticated readers with measured latency percentiles compared
against SLO objectives, and a concurrent admission burst against a bounded
budget where the expected degradation is a bounded, typed refusal (HTTP 402)
— never a crash, hang, or unbounded acceptance. The measured numbers, not
asserted booleans, are the evidence.
"""

from __future__ import annotations

import socket
import statistics
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

READERS = 8
READ_REQUESTS_PER_READER = 15
ADMITTERS = 6
ADMISSIONS_PER_ADMITTER = 5
SLO_P95_MS = 1500.0


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def live_api(migrated_db):
    """One live API instance plus a prepared tenant with an admitted agent."""
    from quansio.control.capability import CapabilityService
    from quansio.control.identity import ControlService
    from quansio.platform.context import IdentityContext
    from quansio.runtime.agents import AgentRegistry
    from datetime import datetime, timedelta, timezone

    port = _free_port()
    log = open(f"/tmp/quansio-load-{port}.log", "wb")  # noqa: SIM115
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--app-dir", "services/quansio_api",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{base}/healthz", timeout=2).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.4)
    else:
        process.terminate()
        raise AssertionError("api instance did not become healthy")

    database = migrated_db
    control = ControlService(database)
    suffix = uuid.uuid4().hex[:10]
    tenant_id = control.create_tenant(f"load-{suffix}")
    workspace_id = control.create_workspace(tenant_id, f"load-ws-{suffix}")
    control.create_user(tenant_id, f"load-{suffix}@qual.invalid", "Load",
                        "correct horse battery", role="tenant_admin",
                        workspace_id=workspace_id)
    token, context = control.authenticate(tenant_id, f"load-{suffix}@qual.invalid",
                                          "correct horse battery", workspace_id)
    snapshot = CapabilityService(database).admit_root(
        context, context.user_id, ["cap.load"], {}, 500)
    agent_id = AgentRegistry(database, CapabilityService(database)).create_persistent_teammate(
        context, f"load-agent-{suffix}", snapshot["snapshot_id"])
    try:
        yield {"base": base, "token": token, "tenant_id": tenant_id,
               "workspace_id": workspace_id, "agent_id": agent_id}
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def test_sre005_p02_measured_load_meets_slo_and_overload_degrades_bounded(live_api):
    base, headers = live_api["base"], {"Authorization": f"Bearer {live_api['token']}"}

    # -- phase 1: sustained concurrent authenticated reads -------------------
    latencies: list[float] = []
    errors: list[str] = []

    def reader(_: int) -> None:
        with httpx.Client(timeout=10.0) as client:
            for _ in range(READ_REQUESTS_PER_READER):
                started = time.monotonic()
                try:
                    response = client.get(f"{base}/v9/identity", headers=headers)
                    elapsed_ms = (time.monotonic() - started) * 1000
                    if response.status_code != 200:
                        errors.append(f"identity -> {response.status_code}")
                    else:
                        latencies.append(elapsed_ms)
                except httpx.HTTPError as error:
                    errors.append(f"identity -> {error}")

    with ThreadPoolExecutor(max_workers=READERS) as pool:
        list(pool.map(reader, range(READERS)))

    total_reads = READERS * READ_REQUESTS_PER_READER
    assert len(latencies) == total_reads, f"read errors: {errors[:5]}"
    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18]
    assert p95 <= SLO_P95_MS, f"p95 latency {p95:.0f}ms exceeds SLO {SLO_P95_MS}ms"
    assert p50 <= SLO_P95_MS

    # -- phase 2: admission burst over a bounded budget -----------------------
    runtime_base = base.replace(":8080", ":8087")  # not used; runtime is reached via API
    # Budgeted run: create one through admission, then reserve concurrently.
    admitted = httpx.post(f"{base}/v9/commands", headers=headers, json={
        "command_type": "task.start",
        "arguments": {"objective": "load burst", "agent_id": live_api["agent_id"],
                      "budget_cents": 100},
        "idempotency_key": f"load-{uuid.uuid4().hex[:10]}",
    })
    assert admitted.status_code == 200, admitted.text
    # The runtime service lives on its own port in a real deployment; here the
    # burst goes against the live runtime instance launched separately.
    runtime_port = _free_port()
    log = open(f"/tmp/quansio-load-rt-{runtime_port}.log", "wb")  # noqa: SIM115
    runtime = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--app-dir", "services/quansio_runtime",
         "--host", "127.0.0.1", "--port", str(runtime_port), "--log-level", "warning"],
        cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT,
    )
    runtime_base = f"http://127.0.0.1:{runtime_port}"
    try:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                if httpx.get(f"{runtime_base}/healthz", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.4)
        else:
            raise AssertionError("runtime instance did not become healthy")

        outcomes: list[int] = []

        def reserver(index: int) -> None:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(f"{runtime_base}/v9/budgets/reservations",
                                       headers=headers, json={
                    "parent_run_id": admitted.json()["run_id"],
                    "idempotency_key": f"burst-{index}",
                    "amount_cents": 30,
                })
                outcomes.append(response.status_code)

        with ThreadPoolExecutor(max_workers=ADMITTERS) as pool:
            list(pool.map(reserver, range(ADMITTERS * ADMISSIONS_PER_ADMITTER)))

        accepted = outcomes.count(200)
        bounded_denials = outcomes.count(402)
        assert accepted == 3, f"ceiling 100 admits exactly 3x30: {outcomes}"
        assert bounded_denials == 27, "overload must be bounded typed refusals"
        assert outcomes.count(500) == 0, "no crashes under overload"
    finally:
        runtime.terminate()
        try:
            runtime.wait(timeout=10)
        except subprocess.TimeoutExpired:
            runtime.kill()
