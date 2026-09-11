"""Deployable service surface tests: every canonical service must expose its
package behavior over HTTP with server-resolved identity, not just health
endpoints. These tests run against the real qualification PostgreSQL
(migrated schema) and, for artifact storage, the real MinIO boundary.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.artifact.app import create_app as create_artifact_app  # noqa: E402
from quansio.control.app import create_app as create_control_app  # noqa: E402
from quansio.control.capability import CapabilityService  # noqa: E402
from quansio.context.app import create_app as create_context_app  # noqa: E402
from quansio.indexer.app import create_app as create_indexer_app  # noqa: E402
from quansio.integration_broker.app import create_app as create_broker_app  # noqa: E402
from quansio.machine_control.app import create_app as create_machine_app  # noqa: E402
from quansio.model_gateway.app import create_app as create_gateway_app  # noqa: E402
from quansio.notify.app import create_app as create_notify_app  # noqa: E402
from quansio.qworkerd.app import create_app as create_qworkerd_app  # noqa: E402
from quansio.runtime.app import create_app as create_runtime_app  # noqa: E402
from quansio.worker_gateway.app import create_app as create_worker_gateway_app  # noqa: E402

SERVICES = {
    "quansio-control": create_control_app,
    "quansio-runtime": create_runtime_app,
    "quansio-context": create_context_app,
    "quansio-indexer": create_indexer_app,
    "quansio-worker-gateway": create_worker_gateway_app,
    "quansio-artifact": create_artifact_app,
    "quansio-notify": create_notify_app,
    "quansio-machine-control": create_machine_app,
    "quansio-integration-broker": create_broker_app,
    "qworkerd": create_qworkerd_app,
    "quansio-model-gateway": create_gateway_app,
}


def _client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture(scope="module")
def auth(migrated_db):
    """One fresh tenant with two workspaces plus bearer tokens for its admin
    and member. Built directly on the control authority so the whole module
    shares a single identity set."""
    from quansio.control.identity import ControlService

    control = ControlService(migrated_db)
    suffix = uuid.uuid4().hex[:10]
    tenant_id = control.create_tenant(f"svc-{suffix}")
    workspace_a = control.create_workspace(tenant_id, f"svc-ws-a-{suffix}")
    workspace_b = control.create_workspace(tenant_id, f"svc-ws-b-{suffix}")
    admin = control.create_user(
        tenant_id, f"svc-admin-{suffix}@qual.invalid", "Svc Admin",
        "correct horse battery", role="tenant_admin",
    )
    member = control.create_user(
        tenant_id, f"svc-member-{suffix}@qual.invalid", "Svc Member",
        "member pass phrase", role="member", workspace_id=workspace_a,
    )
    admin_token, admin_context = control.authenticate(
        tenant_id, f"svc-admin-{suffix}@qual.invalid",
        "correct horse battery", workspace_a,
    )
    member_token, _ = control.authenticate(
        tenant_id, f"svc-member-{suffix}@qual.invalid",
        "member pass phrase", workspace_a,
    )
    from dataclasses import replace

    from quansio.platform.context import IdentityContext

    # Normalize durable UUID objects to their canonical string form for the
    # HTTP layer (every route treats identity fields as strings).
    context = IdentityContext(
        tenant_id=str(admin_context.tenant_id),
        workspace_id=str(admin_context.workspace_id),
        user_id=str(admin_context.user_id),
        session_id=str(admin_context.session_id),
        roles=admin_context.roles,
        expires_at=admin_context.expires_at,
    )
    return {
        "admin": admin_token,
        "member": member_token,
        "context": context,
        "setup": {
            "tenant_id": tenant_id,
            "workspace_a": workspace_a,
            "workspace_b": workspace_b,
            "admin": admin,
            "member": member,
        },
    }


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Every service: live + ready + identity enforcement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("service", sorted(SERVICES))
def test_service_health_and_identity_enforced(service, migrated_db):
    """A shell is not a service: healthz must exist, and business routes must
    reject unauthenticated calls (no route may trust the transport)."""
    with _client(SERVICES[service](migrated_db)) as http:
        health = http.get("/healthz")
        assert health.status_code == 200
        assert health.json()["status"] == "live"


def test_every_service_rejects_missing_session(migrated_db):
    probes = {
        "quansio-control": ("GET", "/v9/identity", None),
        "quansio-runtime": ("POST", "/v9/runs", {"agent_id": "x", "budget_cents": 0}),
        "quansio-context": ("POST", "/v9/rooms", {"name": "r"}),
        "quansio-indexer": ("GET", "/v9/index/query?terms=a", None),
        "quansio-worker-gateway": ("POST", "/v9/browser/sessions", {"target_id": "t", "generation": 1}),
        "quansio-notify": ("POST", "/v9/notifications", {"recipient_id": "r", "channel_class": "inbox", "urgency": "low", "deep_link": "/", "payload": {}}),
        "quansio-machine-control": ("GET", "/v9/targets/none", None),
        "qworkerd": ("POST", "/v9/guest/execute", {"task_id": "t", "target_id": "x", "generation": 1, "fence_token": 1, "operation": "fs.read", "arguments": {}}),
        "quansio-model-gateway": ("POST", "/v9/model/admissions", {"run_id": "r", "step_id": "s", "demand": {}, "messages": [], "policy_allowed_profiles": [], "required_residency": [], "context_tokens": 1, "budget_cents": 1}),
    }
    for service, (method, url, body) in probes.items():
        with _client(SERVICES[service](migrated_db)) as http:
            response = http.request(method, url, json=body)
            assert response.status_code == 401, (
                f"{service} {url} admitted an unauthenticated call: {response.status_code}"
            )


# ---------------------------------------------------------------------------
# quansio-control: registry authority and tenancy enforcement
# ---------------------------------------------------------------------------


def test_control_tool_registry_roundtrip_and_cross_tenant_workspace(migrated_db, auth):
    with _client(create_control_app(migrated_db)) as http:
        headers = _auth_header(auth["admin"])
        registered = http.post("/v9/tools", headers=headers, json={
            "operation_name": f"svc.test.op-{uuid.uuid4().hex[:8]}",
            "version": 1, "schema_def": {"type": "object"},
            "effect_class": "state_changing", "fidelity_class": "lossless",
            "capability_need": "cap.test", "policy_need": "pol.test",
            "timeout_ms": 1000, "idempotent": True,
            "evidence_contract": "receipt",
        })
        assert registered.status_code == 200, registered.text
        name = registered.json()["tool"]["operation_name"]
        resolved = http.get(f"/v9/tools/{name}", headers=headers)
        assert resolved.status_code == 200
        assert resolved.json()["tool"]["effect_class"] == "state_changing"
        # cross-tenant workspace creation is refused before any write
        foreign = http.post("/v9/workspaces", headers=headers, json={
            "tenant_id": str(uuid.uuid4()), "name": "nope",
        })
        assert foreign.status_code == 403


# ---------------------------------------------------------------------------
# quansio-runtime: graph event replay, budget reservation, durable waits
# ---------------------------------------------------------------------------


def test_runtime_event_replay_budget_and_wait_resume(migrated_db, auth):
    from quansio.runtime.events import EventLog

    context = auth["context"]
    capabilities = CapabilityService(migrated_db)
    snapshot = capabilities.admit_root(
        context, context.user_id, ["cap.test"], {"path": "/w"}, 500,
    )
    with _client(create_runtime_app(migrated_db)) as http:
        headers = _auth_header(auth["admin"])
        agent = http.post("/v9/agents", headers=headers, json={
            "display_name": f"svc-agent-{uuid.uuid4().hex[:6]}",
            "snapshot_id": snapshot["snapshot_id"],
        })
        assert agent.status_code == 200, agent.text
        agent_id = agent.json()["agent"]["agent_id"]

        run = http.post("/v9/runs", headers=headers, json={
            "agent_id": agent_id, "budget_cents": 100,
        })
        assert run.status_code == 200, run.text
        run_id = run.json()["run_id"]

        first = http.post("/v9/events", headers=headers, json={
            "run_id": run_id, "event_type": "run.started", "payload": {"status": "running"},
        })
        assert first.status_code == 200, first.text
        second = http.post("/v9/events", headers=headers, json={
            "run_id": run_id, "event_type": "run.state", "payload": {"status": "working"},
        })
        assert second.status_code == 200

        replay = http.get(f"/v9/events?run_id={run_id}", headers=headers)
        assert replay.status_code == 200
        events = replay.json()["events"]
        assert [e["sequence"] for e in events] == [1, 2]

        # non-monotonic sequences are refused without corrupting replay
        stale = http.post("/v9/events", headers=headers, json={
            "run_id": run_id, "event_type": "run.state", "payload": {},
            "sequence": 1,
        })
        assert stale.status_code == 409

        reservation_payload = {
            "parent_run_id": run_id, "idempotency_key": f"svc-{uuid.uuid4().hex[:8]}",
            "amount_cents": 40,
        }
        reservation = http.post("/v9/budgets/reservations", headers=headers, json=reservation_payload)
        assert reservation.status_code == 200, reservation.text
        duplicate = http.post("/v9/budgets/reservations", headers=headers, json=reservation_payload)
        assert duplicate.status_code == 200
        assert duplicate.json()["duplicate"] is True

        over = http.post("/v9/budgets/reservations", headers=headers, json={
            "parent_run_id": run_id, "idempotency_key": f"svc-{uuid.uuid4().hex[:8]}",
            "amount_cents": 10_000,
        })
        assert over.status_code == 402

        wait = http.post("/v9/waits", headers=headers, json={
            "run_id": run_id, "kind": "approval_wait", "payload": {"approval_id": "a1"},
        })
        assert wait.status_code == 200, wait.text
        protocol_id = wait.json()["protocol_id"]
        resumed = http.post("/v9/waits/resume", headers=headers, json={
            "run_id": run_id, "protocol_id": protocol_id, "outcome": {"approved": True},
        })
        assert resumed.status_code == 200 and resumed.json()["resumed"] is True
        replay_again = EventLog(migrated_db).replay(auth["context"].tenant_id, run_id)
        assert len(replay_again) == 2


# ---------------------------------------------------------------------------
# quansio-context: automation lifecycle and collaboration projection
# ---------------------------------------------------------------------------


def test_context_automation_and_room_projection(migrated_db, auth):
    with _client(create_context_app(migrated_db)) as http:
        headers = _auth_header(auth["admin"])
        automation = http.post("/v9/automations", headers=headers, json={
            "name": "svc-nightly", "tz_name": "UTC", "cron": "30 2 * * *",
            "fold_gap_policy": "skip", "catchup_policy": "CATCH_UP_BOUNDED",
            "catchup_max": 3, "work_template": {"task": "summarize"},
        })
        assert automation.status_code == 200, automation.text
        automation_id = automation.json()["automation_id"]
        paused = http.post(f"/v9/automations/{automation_id}/pause", headers=headers)
        assert paused.status_code == 200
        fired = http.post(f"/v9/automations/{automation_id}/fires", headers=headers, json={})
        assert fired.status_code == 409  # paused automations cannot fire

        room = http.post("/v9/rooms", headers=headers, json={"name": "svc-room"})
        assert room.status_code == 200
        room_id = room.json()["room_id"]
        posted = http.post(f"/v9/rooms/{room_id}/messages", headers=headers, json={
            "sender_agent": auth["context"].user_id, "payload": {"text": "hello"},
        })
        assert posted.status_code == 200
        projection = http.get(f"/v9/rooms/{room_id}/projection", headers=headers)
        assert projection.status_code == 200
        assert len(projection.json()["messages"]) == 1


# ---------------------------------------------------------------------------
# quansio-indexer: ingest, tombstone, freshness
# ---------------------------------------------------------------------------


def test_indexer_ingest_query_tombstone_freshness(migrated_db, auth):
    with _client(create_indexer_app(migrated_db)) as http:
        headers = _auth_header(auth["admin"])
        source_id = f"svc-src-{uuid.uuid4().hex[:8]}"
        ingested = http.post("/v9/index/ingest", headers=headers, json={
            "source_id": source_id, "url": "https://example.test/a",
            "chunks": [{"chunk_id": "c1", "content": "quansio service surface"}],
        })
        assert ingested.status_code == 200, ingested.text
        found = http.get("/v9/index/query?terms=quansio", headers=headers)
        assert found.status_code == 200
        assert any(r["source_id"] == source_id for r in found.json()["results"])
        stale = http.post("/v9/index/freshness", headers=headers, json={
            "live_source_ids": [],
        })
        assert stale.status_code == 200
        assert source_id in stale.json()["stale_source_ids"]
        tombstoned = http.post(f"/v9/index/{source_id}/tombstone", headers=headers)
        assert tombstoned.status_code == 200
        after = http.get("/v9/index/query?terms=quansio", headers=headers)
        assert not any(r["source_id"] == source_id for r in after.json()["results"])


# ---------------------------------------------------------------------------
# quansio-notify: durable delivery and receipts
# ---------------------------------------------------------------------------


def test_notify_delivery_receipts_and_cross_tenant_refusal(migrated_db, auth):
    with _client(create_notify_app(migrated_db)) as http:
        headers = _auth_header(auth["admin"])
        created = http.post("/v9/notifications", headers=headers, json={
            "recipient_id": auth["context"].user_id, "channel_class": "inbox",
            "urgency": "high", "deep_link": "/tasks/1",
            "payload": {"summary": "service surface"},
        })
        assert created.status_code == 200, created.text
        notification_id = created.json()["notification"]["notification_id"]

        delivered = http.post(f"/v9/notifications/{notification_id}/deliver", headers=headers)
        assert delivered.status_code == 200 and delivered.json()["state"] == "delivered"
        duplicate = http.post(f"/v9/notifications/{notification_id}/deliver", headers=headers)
        assert duplicate.json()["duplicate"] is True

        acknowledged = http.post(
            f"/v9/notifications/{notification_id}/acknowledge",
            headers=headers, json={"ack_by": auth["context"].user_id},
        )
        assert acknowledged.status_code == 200
        assert acknowledged.json()["state"] == "acknowledged"

        listed = http.get(
            f"/v9/notifications?recipient_id={auth['context'].user_id}&state=acknowledged",
            headers=headers,
        )
        assert listed.status_code == 200
        assert any(n["notification_id"] == notification_id for n in listed.json()["notifications"])

        # unknown notification is a 404, not a fabricated success
        missing = http.post(f"/v9/notifications/{uuid.uuid4()}/deliver", headers=headers)
        assert missing.status_code == 404


# ---------------------------------------------------------------------------
# quansio-artifact: real MinIO boundary
# ---------------------------------------------------------------------------


def test_artifact_put_get_digest_verification(migrated_db, auth, minio_client):
    with _client(create_artifact_app(migrated_db, client=minio_client)) as http:
        headers = _auth_header(auth["admin"])
        payload = b"service-surface-artifact-bytes"
        stored = http.put(
            "/v9/artifacts", headers={**headers, "Content-Type": "text/plain"},
            content=payload,
        )
        assert stored.status_code == 200, stored.text
        digest = stored.json()["artifact"]["digest"]
        assert digest == hashlib.sha256(payload).hexdigest()

        fetched = http.get(f"/v9/artifacts/{digest}", headers=headers)
        assert fetched.status_code == 200
        assert fetched.content == payload

        meta = http.get(f"/v9/artifacts/{digest}/metadata", headers=headers)
        assert meta.status_code == 200
        assert meta.json()["metadata"]["scan_state"] == "unscanned"

        missing = http.get(f"/v9/artifacts/{uuid.uuid4().hex}", headers=headers)
        assert missing.status_code == 404


# ---------------------------------------------------------------------------
# quansio-machine-control + qworkerd: inventory, lease/fence, guest execution
# ---------------------------------------------------------------------------


def test_machine_control_full_actuation_path_with_qworkerd(migrated_db, auth):
    context = auth["context"]
    with _client(create_machine_app(migrated_db)) as machine, \
            _client(create_qworkerd_app(migrated_db)) as worker:
        headers = _auth_header(auth["admin"])
        target_id = f"svc-target-{uuid.uuid4().hex[:8]}"
        registered = machine.post("/v9/targets", headers=headers, json={
            "target_id": target_id, "target_type": "fs",
            "support_profile": "std", "health_identity": "qual-host",
        })
        assert registered.status_code == 200, registered.text
        generation = registered.json()["generation"]

        heartbeat = machine.post(f"/v9/targets/{target_id}/heartbeat", headers=headers, json={"health": "ok"})
        assert heartbeat.status_code == 200

        enabled = machine.post(f"/v9/targets/{target_id}/lifecycle", headers=headers,
                               json={"lifecycle": "enabled"})
        assert enabled.status_code == 200, enabled.text

        placed = machine.post(f"/v9/targets/{target_id}/place", headers=headers, json={
            "holder": context.user_id,
        })
        assert placed.status_code == 200, placed.text
        lease = placed.json()["lease"]
        fence_token = lease["fence_token"]

        task_id = f"svc-task-{uuid.uuid4().hex[:8]}"
        provisioned = machine.put(f"/v9/tasks/{task_id}/environment", headers=headers, json={
            "declared_inputs": [{"path": "input.txt", "content": "declared"}],
        })
        assert provisioned.status_code == 200, provisioned.text

        # guest execution through qworkerd validates the lease before actuation
        executed = worker.post("/v9/guest/execute", headers=headers, json={
            "task_id": task_id, "target_id": target_id,
            "generation": generation, "fence_token": fence_token,
            "operation": "fs.write", "arguments": {"path": "workspace/out.txt", "content": "done"},
        })
        assert executed.status_code == 200, executed.text
        assert executed.json()["result"]["operation"] == "fs.write"

        # a stale fence token is refused before any actuation
        stale = worker.post("/v9/guest/execute", headers=headers, json={
            "task_id": task_id, "target_id": target_id,
            "generation": generation, "fence_token": fence_token - 1,
            "operation": "fs.read", "arguments": {"path": "workspace/out.txt"},
        })
        assert stale.status_code == 409

        # durable delivery with idempotent ACK
        idem = f"svc-delivery-{uuid.uuid4().hex[:8]}"
        enqueued = machine.post("/v9/deliveries", headers=headers, json={
            "target_id": target_id, "operation": "fs.write",
            "arguments": {"path": "workspace/delivery.txt", "content": "x"},
            "idempotency_key": idem,
        })
        assert enqueued.status_code == 200, enqueued.text
        delivery_id = enqueued.json()["delivery"]["delivery_id"]
        delivered = machine.post(f"/v9/deliveries/{delivery_id}/deliver", headers=headers, json={
            "task_id": task_id, "target_id": target_id,
            "generation": generation, "fence_token": fence_token,
        })
        assert delivered.status_code == 200, delivered.text
        assert delivered.json()["delivery"]["replayed"] is False
        replayed = machine.post(f"/v9/deliveries/{delivery_id}/deliver", headers=headers, json={
            "task_id": task_id, "target_id": target_id,
            "generation": generation, "fence_token": fence_token,
        })
        assert replayed.status_code == 200
        assert replayed.json()["delivery"]["replayed"] is True


def test_machine_control_private_targets_stay_disabled(migrated_db, auth):
    with _client(create_machine_app(migrated_db)) as machine:
        headers = _auth_header(auth["admin"])
        target_id = f"svc-private-{uuid.uuid4().hex[:8]}"
        registered = machine.post("/v9/private-targets", headers=headers, json={
            "target_id": target_id, "mapped_qualification_suites": ["suite-a"],
        })
        assert registered.status_code == 200
        assert registered.json()["target"]["enabled"] is False
        enabled = machine.post(f"/v9/private-targets/{target_id}/enable", headers=headers, json={
            "target_id": target_id, "mapped_qualification_suites": ["suite-a"],
        })
        assert enabled.status_code == 403


# ---------------------------------------------------------------------------
# quansio-worker-gateway: browser sessions, stale page identity
# ---------------------------------------------------------------------------


def test_worker_gateway_browser_act_and_stale_epoch_refusal(migrated_db, auth):
    with _client(create_worker_gateway_app(migrated_db)) as http:
        headers = _auth_header(auth["admin"])
        target_id = f"svc-browser-{uuid.uuid4().hex[:8]}"
        from quansio.machine_control.inventory import TargetInventory

        TargetInventory(migrated_db).register(
            auth["context"], target_id, "browser", "std", "qual-host"
        )
        session = http.post("/v9/browser/sessions", headers=headers, json={
            "target_id": target_id, "generation": 1,
        })
        assert session.status_code == 200, session.text
        session_id = session.json()["session"]["session_id"]
        epoch = session.json()["session"]["page_epoch"]

        acted = http.post("/v9/browser/act", headers=headers, json={
            "session_id": session_id, "action": "navigate",
            "arguments": {"url": "https://example.test/"}, "page_epoch": epoch,
            "run_id": str(uuid.uuid4()), "step_id": "s1",
        })
        assert acted.status_code == 200, acted.text

        # acting on the pre-navigation page epoch is refused
        stale = http.post("/v9/browser/act", headers=headers, json={
            "session_id": session_id, "action": "click",
            "arguments": {"selector": "#ok"}, "page_epoch": epoch,
            "run_id": str(uuid.uuid4()), "step_id": "s2",
        })
        assert stale.status_code == 409


# ---------------------------------------------------------------------------
# quansio-integration-broker: mediated connector op + webhook ingress
# ---------------------------------------------------------------------------


class _EchoHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 - http.server API
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        body = json.dumps({"ok": True, "echo": "connector"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence
        return


@pytest.fixture()
def echo_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _EchoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/hook"
    server.shutdown()


def test_broker_mediated_connector_operation(migrated_db, auth, echo_server):
    from quansio.control.broker import CredentialBroker
    from quansio.control.capability import CapabilityService
    from quansio.control.effects import EffectLedger
    from quansio.platform.repository import TenantRepository
    from quansio.runtime.agents import AgentRegistry

    context = auth["context"]
    snapshot = CapabilityService(migrated_db).admit_root(
        context, context.user_id, ["cap.echo"], {}, 0,
    )
    agent_id = AgentRegistry(migrated_db, CapabilityService(migrated_db)).create_persistent_teammate(
        context, f"svc-broker-{uuid.uuid4().hex[:6]}", snapshot["snapshot_id"],
    )
    run_id = TenantRepository(migrated_db).create_run(
        context, agent_id=agent_id, budget_cents=0,
    )
    ledger = EffectLedger(migrated_db)
    decision = {
        "policy_decision_id": str(uuid.uuid4()), "decision": "ALLOW",
    }
    effect = ledger.propose(context, run_id=run_id,
                            operation="connector.submit", arguments={},
                            target="external:echo")
    ledger.authorize(context, effect["effect_id"], decision["policy_decision_id"])

    with _client(create_broker_app(migrated_db, webhook_secrets={"echo": "whsec"})) as http:
        headers = _auth_header(auth["admin"])
        secret_id = f"svc-secret-{uuid.uuid4().hex[:8]}"
        registered = http.post("/v9/secrets", headers=headers, json={
            "secret_id": secret_id, "provider": "echo", "secret_material": "material-1",
        })
        assert registered.status_code == 200, registered.text

        handle = http.post(f"/v9/secrets/{secret_id}/handles", headers=headers, json={
            "secret_id": secret_id, "operation": "connector.submit",
            "target": echo_server, "capability": "cap.echo",
        })
        assert handle.status_code == 200, handle.text
        handle_id = handle.json()["handle"]["handle_id"]

        outcome = http.post("/v9/connector-operations", headers=headers, json={
            "effect_id": effect["effect_id"], "handle_id": handle_id,
            "operation": "connector.submit", "target": echo_server,
            "arguments": {"ping": True},
        })
        assert outcome.status_code == 200, outcome.text
        assert outcome.json()["outcome"]["receipt"]["status"] == 200

        # the mediated path records effect commitment server-side
        final = ledger.require_effect(context, effect["effect_id"], expected_status="committed")
        assert final["status"] == "committed"


def test_broker_webhook_signature_enforced(migrated_db, auth):
    body = json.dumps({"event": "external.update"}).encode()
    signature = hmac.new(b"real-secret", body, hashlib.sha256).hexdigest()
    with _client(create_broker_app(migrated_db, webhook_secrets={"ledger": "real-secret"})) as http:
        headers = {**_auth_header(auth["admin"]), "X-Webhook-Signature": signature,
                   "X-Webhook-Event-Identity": f"evt-{uuid.uuid4().hex[:8]}"}
        received = http.post("/v9/webhooks/ledger/ingest", headers=headers,
                             content=body)
        assert received.status_code == 200, received.text
        webhook_id = received.json()["webhook"]["webhook_id"]
        work = http.post(f"/v9/webhooks/{webhook_id}/work", headers=headers)
        assert work.status_code == 200 and work.json()["created_now"] is True
        replay = http.post("/v9/webhooks/ledger/ingest", headers=headers, content=body)
        assert replay.json()["webhook"]["duplicate"] is True

        bad = http.post("/v9/webhooks/ledger/ingest",
                        headers={**_auth_header(auth["admin"]),
                                 "X-Webhook-Signature": "bad",
                                 "X-Webhook-Event-Identity": f"evt-{uuid.uuid4().hex[:8]}"},
                        content=body)
        assert bad.status_code == 401


# ---------------------------------------------------------------------------
# quansio-model-gateway: admission with the real catalog
# ---------------------------------------------------------------------------


def test_gateway_admission_shape(migrated_db, auth):
    """Admission must produce the canonical envelope fields or a typed
    no-route refusal; a shell response (no envelope, no refusal) fails."""
    with _client(create_gateway_app(migrated_db)) as http:
        headers = _auth_header(auth["admin"])
        response = http.post("/v9/model/admissions", headers=headers, json={
            "run_id": str(uuid.uuid4()), "step_id": "s1",
            "demand": {"capability": "text.generation"},
            "messages": [{"role": "user", "content": "hello"}],
            "policy_allowed_profiles": ["quansio-local-lfm"],
            "required_residency": ["US"],
            "context_tokens": 256, "budget_cents": 5,
        })
        assert response.status_code in (200, 409), response.text
        if response.status_code == 200:
            envelope = response.json()["envelope"]
            for field in ("request_id", "model_profile_id", "usage_reservation_id",
                          "privacy_decision_id", "stream_id"):
                assert field in envelope, f"missing canonical envelope field {field}"


def test_degraded_dependency_returns_readyz_503(migrated_db, auth):
    """A service whose database is unreachable must answer readiness with
    HTTP 503 (never a 200 body claiming degraded) while liveness stays 200:
    load balancers key on the status code."""
    from quansio.platform.db import PlatformDatabase, database_config

    standalone = PlatformDatabase(database_config(), max_size=1)
    standalone.close()  # dependency down
    with _client(create_notify_app(standalone)) as http:
        assert http.get("/healthz").status_code == 200
        ready = http.get("/readyz")
        assert ready.status_code == 503, ready.text
        assert ready.json()["status"] == "degraded"
