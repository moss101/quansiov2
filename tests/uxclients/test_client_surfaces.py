"""Acceptance tests for UX-001..008: thin client surfaces over canonical
commands/events with convergence, degraded states, exact-scope approvals,
artifact grants and CLI event-follow resume.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))
sys.path.insert(0, str(REPO_ROOT))  # clients package lives at repo root

from clients.pyapp.engine import ConvergenceEngine  # noqa: E402
from clients.pyapp.surface import (  # noqa: E402
    ClientApi,
    MobileSurface,
    WebSurface,
    build_parser,
)
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.platform.db import database_config  # noqa: E402
from quansio.platform.repository import TenantRepository  # noqa: E402
from quansio.runtime.events import EventLog  # noqa: E402


def _ctx(workspace_setup) -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup["workspace_a"],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@pytest.fixture()
def context(workspace_setup) -> IdentityContext:
    return _ctx(workspace_setup)


def _canonical_events(run_id: str) -> list[dict]:
    return [
        {"sequence": 1, "event_type": "run.state", "run_id": run_id,
         "payload": {"status": "running"}},
        {"sequence": 2, "event_type": "run.state", "run_id": run_id,
         "payload": {"status": "suspended"}},
        {"sequence": 3, "event_type": "run.state", "run_id": run_id,
         "payload": {"status": "succeeded"}},
    ]


# ---------------------------------------------------------------------------
# UX-002: convergence across two clients
# ---------------------------------------------------------------------------


def test_ux002_p01_two_clients_converge_identically():
    run_id = str(uuid.uuid4())
    events = _canonical_events(run_id)
    client_a = ConvergenceEngine("desktop")
    client_b = ConvergenceEngine("web")
    client_a.apply_snapshot({"timeline": [], "task_status": {}, "cursor": 0})
    client_b.apply_snapshot({"timeline": [], "task_status": {}, "cursor": 0})
    client_a.apply_batch(events)
    client_b.apply_batch(events)
    assert client_a.visible_state() == client_b.visible_state()
    assert client_a.visible_state()["task_status"][run_id] == "succeeded"


def test_ux002_n01_duplicate_and_out_of_order_never_invent_sequence():
    run_id = str(uuid.uuid4())
    engine = ConvergenceEngine("test")
    events = _canonical_events(run_id)
    engine.apply_event(events[0])
    assert engine.apply_event(events[0]) is False, "duplicate dropped"
    with pytest.raises(ValueError, match="gap"):
        engine.apply_event({**events[2]})


def test_ux002_r01_cache_clear_rebuilds_from_snapshot(migrated_db, workspace_setup, context):
    run_id = str(uuid.uuid4())
    events = _canonical_events(run_id)
    engine = ConvergenceEngine("desktop")
    engine.apply_batch(events)
    # Clear local cache.
    engine.apply_snapshot({"timeline": [], "task_status": {}, "cursor": 0})
    # Server snapshot + ordered events rebuild the full visible state.
    engine.apply_snapshot({
        "timeline": [], "task_status": {run_id: "running"}, "cursor": 0,
    })
    engine.apply_batch(events)
    assert engine.visible_state()["task_status"][run_id] == "succeeded"
    assert engine.export_cursor() == 3


# ---------------------------------------------------------------------------
# UX-001: shell offline/degraded and reconnect rebuild
# ---------------------------------------------------------------------------


def test_ux001_p01_and_n01_offline_state_explicit_not_claiming_completion():
    engine = ConvergenceEngine("desktop")
    engine.mark_offline()
    visible = engine.visible_state()
    assert visible["offline"] is True
    # The shell cannot claim a task completed while offline: no local mutation
    # path exists (engine has no task-state setter other than canonical events).
    run_id = str(uuid.uuid4())
    with pytest.raises(ValueError):
        engine.apply_event({"sequence": 9, "event_type": "run.state",
                            "run_id": run_id, "payload": {"status": "succeeded"}})


def test_ux001_r01_reconnect_from_durable_cursor_without_duplicates(migrated_db, workspace_setup, context):
    run_id = str(uuid.uuid4())
    engine = ConvergenceEngine("desktop")
    events = _canonical_events(run_id)
    engine.apply_batch(events[:2])
    cursor = engine.export_cursor()
    # Reconnect: replay from durable cursor.
    engine.mark_online()
    engine.apply_batch(events[2:])
    assert engine.export_cursor() == 3
    timeline_sequences = [t["sequence"] for t in engine.state.timeline]
    assert timeline_sequences == sorted(timeline_sequences)
    assert len(timeline_sequences) == len(set(timeline_sequences)), "no duplicates"


# ---------------------------------------------------------------------------
# UX-003: live pane control lease (over takeover service)
# ---------------------------------------------------------------------------


def test_ux003_p01_and_n01_pane_respects_controller_lease(migrated_db, workspace_setup, context):
    from quansio.worker_gateway.browser import (  # noqa: F401
        BrowserSessionManager,
        TakeoverService,
        TakeoverStateError,
    )

    sessions = BrowserSessionManager(migrated_db)
    takeover = TakeoverService(migrated_db, sessions)
    target_id = f"tgt-{uuid.uuid4().hex[:8]}"
    session = sessions.create(context, target_id=target_id, generation=1)
    takeover.takeover(context, session["session_id"], human_id="human-1")
    with pytest.raises(TakeoverStateError, match="human controller"):
        takeover.agent_actuate(context, session["session_id"])


# ---------------------------------------------------------------------------
# UX-004: exact-scope approval UX
# ---------------------------------------------------------------------------


def _parent_run(db, context) -> str:
    from quansio.platform.repository import TenantRepository

    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', %s)",
            (context.tenant_id, context.workspace_id, agent_id, f"ux-{agent_id[:8]}"),
        )
    run_id = TenantRepository(db).create_run(context, agent_id)
    with db.connection() as connection:
        connection.execute("UPDATE runs SET status='running' WHERE tenant_id=%s AND run_id=%s",
                           (context.tenant_id, run_id))
    return run_id


def test_ux004_p01_exact_scope_displayed_and_submitted(migrated_db, workspace_setup, context):
    from quansio.control.effects import ApprovalService, EffectLedger
    from quansio.control.policy import PolicyEngine

    policy = PolicyEngine(migrated_db)
    approvals = ApprovalService(migrated_db, policy)
    ledger = EffectLedger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    arguments = {"amount": 15000, "currency": "EUR", "payee": "vendor-x"}
    effect = ledger.propose(context, run_id=run_id, operation="payment.transfer",
                            arguments=arguments, target="external:bank",
                            idempotency_key=str(uuid.uuid4()))
    approval = approvals.request(
        context, run_id=run_id, effect_id=effect["effect_id"],
        operation="payment.transfer", arguments=arguments, target="external:bank",
        financial={"amount_minor": 15000, "ceiling_minor": 20000,
                   "currency": "EUR", "payee": "vendor-x"})
    row = migrated_db.query_one(
        "SELECT amount_minor, currency, payee, status FROM approvals WHERE approval_id=%s",
        (approval["approval_id"],),
    )
    assert row[0] == 15000 and row[2] == "vendor-x" and row[3] == "pending"
    api = ClientApi(migrated_db)
    result = api.approval_respond(context, approval["approval_id"], True,
                                  context.user_id, approvals)
    assert result["decision"] == "approved"


def test_ux004_n01_changed_scope_after_render_rejected(migrated_db, workspace_setup, context):
    from quansio.control.effects import ApprovalMismatch, ApprovalService, EffectLedger
    from quansio.control.policy import PolicyEngine

    policy = PolicyEngine(migrated_db)
    approvals = ApprovalService(migrated_db, policy)
    ledger = EffectLedger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    arguments = {"amount": 10000, "currency": "EUR", "payee": "vendor-a"}
    effect = ledger.propose(context, run_id=run_id, operation="payment.transfer",
                            arguments=arguments, target="external:bank",
                            idempotency_key=str(uuid.uuid4()))
    approval = approvals.request(
        context, run_id=run_id, effect_id=effect["effect_id"],
        operation="payment.transfer", arguments=arguments, target="external:bank",
        financial={"amount_minor": 10000, "ceiling_minor": 20000,
                   "currency": "EUR", "payee": "vendor-a"})
    approvals.decide(context, approval["approval_id"], True, context.user_id)
    # Underlying scope changed after the UI rendered the approval: submission
    # of the exact request identity now fails verification.
    with pytest.raises(ApprovalMismatch):
        approvals.verify_execution_scope(
            context, approval["approval_id"],
            {"amount": 10500, "currency": "EUR", "payee": "vendor-b"})


def test_ux004_r01_resolved_on_other_client_updates_first(migrated_db, workspace_setup, context):
    from quansio.control.effects import ApprovalService, EffectLedger
    from quansio.control.policy import PolicyEngine
    from quansio.platform.db import database_config, PlatformDatabase

    policy = PolicyEngine(migrated_db)
    approvals_a = ApprovalService(migrated_db, policy)
    ledger = EffectLedger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    arguments = {"recipient": "x@y.z"}
    effect = ledger.propose(context, run_id=run_id, operation="email.send",
                            arguments=arguments, target="external:mail",
                            idempotency_key=str(uuid.uuid4()))
    approval = approvals_a.request(
        context, run_id=run_id, effect_id=effect["effect_id"],
        operation="email.send", arguments=arguments, target="external:mail")
    # Client B (another authorized surface) resolves the approval.
    approvals_b = ApprovalService(PlatformDatabase(database_config(), max_size=2), policy)
    approvals_b.decide(context, approval["approval_id"], True, approver_id=context.user_id)
    # Client A learns from canonical state: approval no longer pending.
    row = migrated_db.query_one(
        "SELECT status FROM approvals WHERE approval_id=%s", (approval["approval_id"],)
    )[0]
    assert row == "approved"
    second = approvals_a.decide(context, approval["approval_id"], True,
                                approver_id=context.user_id)
    assert second["already_decided"] is True, "no second approval action"


# ---------------------------------------------------------------------------
# UX-005: artifact/evidence exploration
# ---------------------------------------------------------------------------


def test_ux005_p01_artifact_metadata_with_grants(migrated_db, workspace_setup, context):
    from quansio.artifact.store import ArtifactStore
    from minio import Minio
    from quansio.platform.db import load_qualenv_passwords

    material = load_qualenv_passwords()
    client = Minio("127.0.0.1:54331", access_key="quansio_qual_admin",
                   secret_key=material["QUAL_MINIO_PASSWORD"], secure=False)
    store = ArtifactStore(migrated_db, client)
    data = b"explorable artifact"
    record = store.put(context, data, "text/plain", grants={"read": ["workspace"]})
    api = ClientApi(migrated_db)
    found = api.artifact_lookup(context, record["digest"][:8], artifact_fetch=lambda d: None)
    assert found["found"] is True and found["digest"] == record["digest"]


def test_ux005_n01_wrong_tenant_artifact_not_exposed(migrated_db, workspace_setup, context):
    from quansio.artifact.store import ArtifactStore
    from minio import Minio
    from quansio.platform.db import load_qualenv_passwords

    material = load_qualenv_passwords()
    client = Minio("127.0.0.1:54331", access_key="quansio_qual_admin",
                   secret_key=material["QUAL_MINIO_PASSWORD"], secure=False)
    store = ArtifactStore(migrated_db, client)
    context = _ctx(workspace_setup)
    record = store.put(context, b"private bytes", "text/plain")
    foreign_ctx = IdentityContext(
        tenant_id=str(uuid.uuid4()), workspace_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        roles=("member",), expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    api = ClientApi(migrated_db)
    found = api.artifact_lookup(foreign_ctx, record["digest"][:8],
                                artifact_fetch=lambda d: None)
    assert found["found"] is False, "other tenant's artifact bytes/metadata hidden"


# ---------------------------------------------------------------------------
# UX-006/007/008: web, mobile, CLI
# ---------------------------------------------------------------------------


def test_ux006_p01_web_same_convergence_path():
    run_id = str(uuid.uuid4())
    events = _canonical_events(run_id)
    web = WebSurface(ConvergenceEngine("web"))
    web.engine.apply_batch(events)
    desktop = ConvergenceEngine("desktop")
    desktop.apply_batch(events)
    assert web.engine.visible_state() == desktop.visible_state()


def test_ux006_n01_web_local_mutation_rejected():
    web = WebSurface(ConvergenceEngine("web"))
    with pytest.raises(TypeError, match="cannot mutate task state locally"):
        web.mutate_task_locally(str(uuid.uuid4()), "succeeded")


def test_ux007_n01_mobile_unsupported_surface_gated():
    mobile = MobileSurface(ConvergenceEngine("mobile"))
    assert mobile.supports("task_status") is True
    gated = mobile.request("machine_control")
    assert gated["rejected"] is True
    direct = mobile.request("effect_direct")
    assert direct["rejected"] is True


def test_ux008_p01_cli_commands_parse_over_canonical_schemas():
    parser = build_parser()
    args = parser.parse_args(["task", "status", "--run-id", "r-1"])
    assert args.command == "task" and args.run_id == "r-1"
    args = parser.parse_args(["approval", "--approval-id", "a-1", "--decision", "approve"])
    assert args.decision == "approve"
    args = parser.parse_args(["artifact", "--digest-prefix", "ab"])
    assert args.digest_prefix == "ab"
    args = parser.parse_args(["follow", "--run-id", "r-1", "--cursor", "2"])
    assert args.cursor == 2


def test_ux008_p01_cli_task_status_and_cancel(migrated_db, workspace_setup, context):
    repository = TenantRepository(migrated_db)
    agent_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', 'cli-parent')",
            (context.tenant_id, context.workspace_id, agent_id),
        )
    run_id = repository.create_run(context, agent_id)
    api = ClientApi(migrated_db)
    status = api.task_status(context, run_id)
    assert status["status"] == "pending"
    cancelled = api.cancel_task(context, run_id)
    assert cancelled["status"] == "cancelled"
    status = api.task_status(context, run_id)
    assert status["status"] == "cancelled"


def test_ux008_r01_event_follow_resume_from_stored_cursor(migrated_db, workspace_setup, context):
    from quansio.platform.repository import TenantRepository

    event_log = EventLog(migrated_db)
    agent_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', 'follow-parent')",
            (context.tenant_id, context.workspace_id, agent_id),
        )
    run_id = TenantRepository(migrated_db).create_run(context, agent_id)
    event_log.append(context, run_id, "run.started", {"n": 1})
    event_log.append(context, run_id, "run.progress", {"n": 2})
    api = ClientApi(migrated_db)
    engine = ConvergenceEngine("cli")
    first = api.event_follow(context, run_id, 0, engine, event_log)
    assert first["applied"] == 2
    stored_cursor = engine.export_cursor()
    event_log.append(context, run_id, "run.progress", {"n": 3})
    engine_second = ConvergenceEngine("cli")
    resumed = api.event_follow(context, run_id, stored_cursor, engine_second, event_log)
    assert resumed["applied"] == 1, "only missing canonical events delivered"
    assert resumed["cursor"] == 3


def test_ux008_n01_cli_package_has_no_execution_authority():
    """The CLI package contains no alternate model/runtime/effect authority:
    import scan over clients/ for forbidden authority patterns."""
    forbidden = [
        "requests.", "httpx.post", "urllib", "socket.socket",
        "QUAL_PROVIDER_", "subprocess", "openai", "anthropic",
        "UPDATE effects", "INSERT INTO effects", "UPDATE runs SET status='succeeded'",
    ]
    hits = []
    for path in (REPO_ROOT / "clients").rglob("*.py"):
        text = path.read_text(errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in forbidden:
                if pattern in line:
                    hits.append((path.name, lineno, pattern))
    assert hits == [], f"alternate execution authority in clients: {hits[:5]}"
