"""Real promotion of an exact release candidate (REL-001..008).

The candidate's identity is bound to the actual current commit, real
artifact digests, the real compose configuration and the real migration
list. Every blocking decision input is a MEASURED outcome of a real
operation executed here: a backup/restore drill (dr), a measured-load
phase against live API+runtime instances (slo), real cross-tenant
adversarial probes (security), and a real canary deploy/rollback over
live instances (canary/rollback). The promotion through GATE-M14's state
machine then carries those measured inputs — and the promoted identity is
independently re-verified.
"""

from __future__ import annotations

import hashlib
import socket
import statistics
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.control.capability import CapabilityService  # noqa: E402
from quansio.control.identity import ControlService  # noqa: E402
from quansio.control.release import ReleaseService  # noqa: E402
from quansio.observability.backup import BackupRestoreDrill  # noqa: E402
from quansio.observability.sre import AdversarialProber  # noqa: E402
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.platform.repository import TenantRepository  # noqa: E402
from quansio.runtime.agents import AgentRegistry  # noqa: E402

READERS = 6
READ_REQUESTS_PER_READER = 10
SLO_P95_MS = 1500.0


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _launch(service_dir: str, port: int, name: str, runtime_url=None):
    import os

    log = open(f"/tmp/quansio-promo-{name}-{port}.log", "wb")  # noqa: SIM115
    env = dict(os.environ)
    if runtime_url:
        env["QUANSIO_RUNTIME_URL"] = runtime_url
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--app-dir", f"services/{service_dir}",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT, env=env,
    )


def _wait_healthy(url: str) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{url}/healthz", timeout=2).status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.4)
    raise AssertionError(f"{url} did not become healthy")


def test_rel008_real_promotion_of_current_commit(migrated_db):
    control = ControlService(migrated_db)
    prober = AdversarialProber(migrated_db)

    # -- 1. candidate identity bound to the REAL current tree ----------------
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                            capture_output=True, text=True).stdout.strip()
    bindings_digest = _sha(REPO_ROOT / "MANIFEST.json")
    artifacts = {
        "platform_repository": _sha(REPO_ROOT / "quansio/platform/repository.py"),
        "runtime_orchestration": _sha(REPO_ROOT / "quansio/runtime/orchestration.py"),
        "api_app": _sha(REPO_ROOT / "quansio/api/app.py"),
    }
    config_digest = _sha(REPO_ROOT / "deploy/compose/docker-compose.yml")
    migrations = sorted(p.name for p in (REPO_ROOT / "migrations/up").glob("*.sql"))

    suffix = uuid.uuid4().hex[:10]
    tenant_id = control.create_tenant(f"promo-{suffix}")
    workspace_id = control.create_workspace(tenant_id, f"promo-ws-{suffix}")
    admin_email = f"promo-{suffix}@qual.invalid"
    control.create_user(tenant_id, admin_email, "Promotion", "correct horse battery",
                        role="tenant_admin", workspace_id=workspace_id)
    context = IdentityContext(
        tenant_id=tenant_id, workspace_id=workspace_id,
        user_id=control.create_user(
            tenant_id, f"bot-{suffix}@qual.invalid", "Bot", "correct horse battery",
            role="tenant_admin", workspace_id=workspace_id),
        session_id=str(uuid.uuid4()), roles=("tenant_admin",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    release = ReleaseService(migrated_db)
    created = release.create_candidate(
        context, commit=commit, bindings_digest=bindings_digest,
        artifacts=artifacts, config_digest=config_digest,
        migrations=migrations, support_selection={})

    # -- 2. real backup/restore drill (dr_ok from measured outcome) ----------
    drill = BackupRestoreDrill(migrated_db).run()
    assert drill.get("error") is None, drill
    assert drill["all_components_restored"] is True and drill["rpo_seconds"] == 0
    dr_ok = True

    # -- 3. measured load against live API+runtime instances (slo_ok) --------
    snapshot = CapabilityService(migrated_db).admit_root(
        context, context.user_id, ["cap.promo"], {}, 200)
    agent_id = AgentRegistry(migrated_db, CapabilityService(migrated_db)).create_persistent_teammate(
        context, f"promo-agent-{suffix}", snapshot["snapshot_id"])
    run_id = TenantRepository(migrated_db).create_run(context, agent_id=agent_id,
                                                      budget_cents=100)

    runtime_port, api_port = _free_port(), _free_port()
    runtime_proc = _launch("quansio_runtime", runtime_port, "rt")
    api_proc = _launch("quansio_api", api_port, "api",
                       runtime_url=f"http://127.0.0.1:{runtime_port}")
    try:
        _wait_healthy(f"http://127.0.0.1:{runtime_port}")
        api_base = f"http://127.0.0.1:{api_port}"
        _wait_healthy(api_base)
        token, _ = control.authenticate(tenant_id, admin_email,
                                        "correct horse battery", workspace_id)
        headers = {"Authorization": f"Bearer {token}"}

        latencies: list[float] = []
        read_errors: list[str] = []

        def reader(_: int) -> None:
            with httpx.Client(timeout=10.0) as client:
                for _ in range(READ_REQUESTS_PER_READER):
                    started = time.monotonic()
                    try:
                        response = client.get(f"{api_base}/v9/identity", headers=headers)
                        if response.status_code == 200:
                            latencies.append((time.monotonic() - started) * 1000)
                        else:
                            read_errors.append(str(response.status_code))
                    except httpx.HTTPError as error:
                        read_errors.append(str(error))

        with ThreadPoolExecutor(max_workers=READERS) as pool:
            list(pool.map(reader, range(READERS)))
        assert len(latencies) == READERS * READ_REQUESTS_PER_READER, read_errors[:5]
        p95 = statistics.quantiles(latencies, n=20)[18]
        slo_ok = p95 <= SLO_P95_MS
        assert slo_ok, f"p95 {p95:.0f}ms exceeds SLO"

        # real admission through the candidate build (command -> durable run)
        admitted = httpx.post(f"{api_base}/v9/commands", headers=headers, json={
            "command_type": "task.start",
            "arguments": {"objective": "promotion exercise", "agent_id": agent_id,
                          "budget_cents": 100},
            "idempotency_key": f"promo-{uuid.uuid4().hex[:10]}",
        })
        assert admitted.status_code == 200, admitted.text
        promo_run_id = admitted.json()["run_id"]

        # -- 4. real cross-tenant adversarial probes (security_ok) ------------
        foreign_context = IdentityContext(
            tenant_id=str(uuid.uuid4()), workspace_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
            roles=("member",),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        probe_results = {
            "foreign_run_read": TenantRepository(migrated_db).get_run(
                foreign_context, run_id) is None,
        }
        for kind, denied in probe_results.items():
            prober.record(context, kind, denied, {"expected": "denied"})
        security_ok = prober.all_denied(context) and all(probe_results.values())
        assert security_ok

        # -- 5. real canary deploy/rollback of the same candidate -------------
        for suite in ("backup-restore-drill", "measured-load", "cross-tenant-probes"):
            release.record_suite_run(context, created["candidate_id"], suite, True,
                                     f"measured:{suite}")
        release.qualify(context, created["candidate_id"],
                        required_suites=["backup-restore-drill", "measured-load",
                                         "cross-tenant-probes"])
        canary_port = _free_port()
        canary = _launch("quansio_api", canary_port, "canary",
                         runtime_url=f"http://127.0.0.1:{runtime_port}")
        try:
            _wait_healthy(f"http://127.0.0.1:{canary_port}")
            health_ok = httpx.get(f"http://127.0.0.1:{canary_port}/healthz",
                                  timeout=3).json()["status"] == "live"
            release.canary_deploy(context, created["candidate_id"],
                                  cohort="promo-1", health_ok=health_ok)
            canary_login = httpx.post(
                f"http://127.0.0.1:{canary_port}/v9/sessions", headers=headers, json={
                    "tenant_id": tenant_id, "workspace_id": workspace_id,
                    "email": admin_email, "password": "correct horse battery"})
            canary_ok = canary_login.status_code == 200
        finally:
            canary.terminate()
            try:
                canary.wait(timeout=10)
            except subprocess.TimeoutExpired:
                canary.kill()
        stable_ok = httpx.get(f"{api_base}/healthz", timeout=3).status_code == 200
        rollback_ok = canary_ok and stable_ok
        release.canary_rollback(context, created["candidate_id"], rollback_ok=rollback_ok)
        assert rollback_ok and stable_ok

        # -- 6. go decision, readiness seal, promotion -------------------------
        release.go_decision(context, created["candidate_id"],
                            blocking_reports={"backup-restore-drill": drill["all_components_restored"],
                                              "measured-load": slo_ok,
                                              "cross-tenant-probes": security_ok},
                            slo_ok=slo_ok, security_ok=security_ok, dr_ok=dr_ok,
                            canary_ok=canary_ok, rollback_ok=rollback_ok)
        bundle = release.seal_readiness(
            context, created["candidate_id"],
            blocking_reports={"backup-restore-drill": drill["all_components_restored"],
                              "measured-load": slo_ok,
                              "cross-tenant-probes": security_ok},
            canary={"ok": canary_ok}, rollback={"ok": rollback_ok},
            slo={"ok": slo_ok, "p95_ms": round(p95, 1)},
            security={"ok": security_ok},
            dr={"ok": dr_ok, "rpo_seconds": drill["rpo_seconds"],
                "rto_seconds": drill["rto_seconds"]},
            go={"decision": "GO_APPROVED"})
        promoted = release.gate_m14_promote(context, created["candidate_id"],
                                            bundle["bundle_digest"])
        assert promoted["state"] == "production_ready"

        # -- 7. independent identity re-verification ---------------------------
        release.verify_promoted_identity(
            context, created["candidate_id"], commit=commit,
            bindings_digest=bindings_digest, artifacts=artifacts,
            config_digest=config_digest, migrations=migrations)
        changed = dict(commit=commit, bindings_digest=bindings_digest,
                       artifacts=artifacts, config_digest=config_digest,
                       migrations=migrations[:-1])
        from quansio.control.release import PromotionRejected

        with pytest.raises(PromotionRejected):
            release.verify_promoted_identity(context, created["candidate_id"],
                                             **changed)
    finally:
        for process in (api_proc, runtime_proc):
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
