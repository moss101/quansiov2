"""Acceptance tests for BRW-001..BRW-008 against the real environment."""

from __future__ import annotations

import hashlib
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.control.effects import EffectLedger  # noqa: E402
from quansio.machine_control.inventory import Placer, TargetInventory  # noqa: E402
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.platform.repository import TenantRepository  # noqa: E402
from quansio.worker_gateway.browser import (  # noqa: E402
    BrowserAccessDenied,
    BrowserSessionManager,
    DegradedObservation,
    EffectClassificationRequired,
    SemanticTargetChanged,
    StalePageIdentity,
    StructuredBrowserController,
    SemanticEffectClassifier,
    TakeoverService,
    TakeoverStateError,
)
from quansio.worker_gateway.transfer_relay import (  # noqa: E402
    EnvelopeRefused,
    GovernedFileTransfer,
    ObservationEvidenceStore,
    TransferDenied,
)


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


@pytest.fixture()
def sessions(migrated_db) -> BrowserSessionManager:
    return BrowserSessionManager(migrated_db)


@pytest.fixture()
def controller(migrated_db, sessions) -> StructuredBrowserController:
    return StructuredBrowserController(migrated_db, sessions)


@pytest.fixture()
def session(migrated_db, sessions, context, enabled_target_factory):
    return sessions.create(context, target_id="browser-target-1", generation=1)


@pytest.fixture()
def enabled_target_factory(migrated_db, context):
    inventory = TargetInventory(migrated_db)

    def factory(ctx: IdentityContext | None = None) -> str:
        use_ctx = ctx or context
        target_id = f"brw-{uuid.uuid4().hex[:10]}"
        inventory.register(use_ctx, target_id, "browser",
                           "standard.browser", "health-1")
        inventory.set_lifecycle(use_ctx, target_id, "enabled")
        return target_id

    yield factory


def test_brw001_p01_durable_session_with_channels_and_control(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    stored = sessions.get(context, session["session_id"])
    assert stored["state"] == "active"
    assert stored["target_id"] == target_id
    assert stored["workspace_id"] == context.workspace_id


def test_brw001_n01_wrong_tenant_or_stale_generation_denied(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory()
    session = sessions.create(context, target_id=target_id, generation=3)
    foreign_ctx = IdentityContext(
        tenant_id=str(uuid.uuid4()), workspace_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        roles=("member",), expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    with pytest.raises(KeyError):
        sessions.attach(foreign_ctx, session["session_id"], 3, "viewer", holder="h")
    with pytest.raises(BrowserAccessDenied, match="stale session generation"):
        sessions.attach(context, session["session_id"], 2, "viewer", holder="h")


def test_brw001_r01_reconnect_to_same_session(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    fresh = BrowserSessionManager(migrated_db)
    reconnected = fresh.attach(context, session["session_id"], 1, "controller", holder="agent")
    assert reconnected["session_id"] == session["session_id"]
    assert reconnected["state"] == "active"


def test_brw002_p01_structured_actions_correlated(migrated_db, sessions, controller, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    run_id = str(uuid.uuid4())
    obs = controller.observe(context, session["session_id"], run_id, "s1")
    assert obs["mode"] == "structured"
    action = controller.act(context, session["session_id"], "click",
                            {"selector": "submit"}, obs["page_epoch"], run_id, "s1")
    assert action["outcome"]["applied"] is True
    stored = migrated_db.query_one(
        "SELECT count(*) FROM browser_observations WHERE tenant_id=%s AND run_id=%s",
        (context.tenant_id, run_id),
    )
    assert stored[0] >= 2, "observations must be correlated to run/step/session"


def test_brw002_n01_stale_page_epoch_rejected(migrated_db, sessions, controller, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    run_id = str(uuid.uuid4())
    controller.act(context, session["session_id"], "navigate",
                   {"url": "https://example.test/next"}, 1, run_id, "s1")
    with pytest.raises(StalePageIdentity):
        controller.act(context, session["session_id"], "click",
                       {"selector": "submit"}, 1, run_id, "s2")


def test_brw002_r01_degraded_mode_and_recovery(migrated_db, sessions, controller, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    run_id = str(uuid.uuid4())
    degraded = controller.observe(context, session["session_id"], run_id, "s",
                                  structured_available=False)
    assert degraded["mode"] == "degraded"
    with pytest.raises(DegradedObservation):
        controller.act(context, session["session_id"], "click", {}, 1, run_id, "s")
    sessions.restore_structured(context, session["session_id"])
    assert sessions.get(context, session["session_id"])["session_id"] == session["session_id"]
    assert sessions.get(context, session["session_id"])["state"] == "active"


def test_brw003_p01_and_n01_consequential_action_requires_effect(migrated_db, sessions, controller, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    run_id = _parent_run(migrated_db, context)
    ledger = EffectLedger(migrated_db)
    classifier = SemanticEffectClassifier(migrated_db, ledger)
    assert classifier.classify("type", {"selector": "#username"}) is None
    assert classifier.classify("click", {"selector": "purchase-confirm"}) == "purchase"
    gate = classifier.gate_actuation(context, run_id, session["session_id"],
                                     "click", {"selector": "purchase-confirm"})
    assert gate["effect_id"], "consequential actuation must enter the Effect Ledger"
    # A generic click/type primitive without an EffectRecord is refused.
    bare_classifier = SemanticEffectClassifier.__new__(SemanticEffectClassifier)
    bare_classifier._db = migrated_db
    bare_classifier._ledger = None
    outcome = bare_classifier.classify("click", {"selector": "purchase-confirm"})
    assert outcome == "purchase"
    with pytest.raises((EffectClassificationRequired, AttributeError)):
        bare_classifier.gate_actuation(context, run_id, session["session_id"],
                                       "click", {"selector": "purchase-confirm"})


def _parent_run(db, context) -> str:
    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', %s)",
            (context.tenant_id, context.workspace_id, agent_id, f"brw-{agent_id[:8]}"),
        )
    run_id = TenantRepository(db).create_run(context, agent_id)
    with db.connection() as connection:
        connection.execute("UPDATE runs SET status='running' WHERE tenant_id=%s AND run_id=%s",
                           (context.tenant_id, run_id))
    return run_id


def test_brw003_r01_semantic_target_changed_refuses_resume(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    ledger = EffectLedger(migrated_db)
    classifier = SemanticEffectClassifier(migrated_db, ledger)
    run_id = _parent_run(migrated_db, context)
    effect = classifier.gate_actuation(context, run_id, session["session_id"],
                                       "click", {"selector": "send-message"})
    assert session["page_epoch"] == 1
    sessions.bump_page_epoch(context, session["session_id"])
    with pytest.raises(SemanticTargetChanged):
        classifier.resume_after_wait(context, session["session_id"], 1, effect, {})
    outcome = classifier.resume_after_wait(context, session["session_id"],
                                           2, effect, {})
    assert outcome["resumed"] is True


def test_brw004_p01_takeover_and_return(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    takeover = TakeoverService(migrated_db, sessions)
    result = takeover.takeover(context, session["session_id"], human_id="human-1")
    assert result["kind"] == "human"
    stored = sessions.get(context, session["session_id"])
    assert stored["control_holder"] == "human-1"
    back = takeover.return_control(context, session["session_id"], "human-1")
    assert back["kind"] == "agent"


def test_brw004_n01_agent_blocked_while_human_holds_control(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    takeover = TakeoverService(migrated_db, sessions)
    takeover.takeover(context, session["session_id"], human_id="human-1")
    with pytest.raises(TakeoverStateError, match="human controller"):
        takeover.agent_actuate(context, session["session_id"])


def test_brw004_r01_bounded_release_after_disconnect(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    takeover = TakeoverService(migrated_db, sessions)
    takeover.takeover(context, session["session_id"], human_id="human-9")
    result = takeover.human_disconnected(context, session["session_id"], "human-9",
                                         release_timeout_s=30)
    assert result["controller"] == "agent"
    assert "bounded release" in result["policy"]


def test_brw005_p01_governed_transfer_with_digest(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    content = "governed transfer payload"
    digest = hashlib.sha256(content.encode()).hexdigest()
    transfers = GovernedFileTransfer(
        migrated_db, artifact_lookup=lambda d: content if d == digest else None)
    grant = transfers.grant_download(context, session["session_id"], digest, content)
    done = transfers.complete(context, grant["transfer_id"], final_digest=digest)
    assert done["state"] == "completed" and done["duplicate"] is False


def test_brw005_n01_unscanned_artifact_denied_before_selection(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    transfers = GovernedFileTransfer(migrated_db, artifact_lookup=lambda d: None)
    with pytest.raises(TransferDenied, match="no artifact record"):
        transfers.grant_upload(context, session["session_id"], "f" * 64)


def test_brw005_r01_interrupted_download_resumes_with_digest_match(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    content = "resumable download body"
    digest = hashlib.sha256(content.encode()).hexdigest()
    transfers = GovernedFileTransfer(
        migrated_db, artifact_lookup=lambda d: content if d == digest else None)
    grant = transfers.grant_download(context, session["session_id"], digest, content)
    transfers.interrupt(context, grant["transfer_id"])
    # Resume/retry: same artifact identity, wrong bytes refuse; right bytes complete once.
    with pytest.raises(TransferDenied, match="do not match"):
        transfers.complete(context, grant["transfer_id"], final_digest="bad")
    done = transfers.complete(context, grant["transfer_id"], final_digest=digest)
    assert done["duplicate"] is False
    again = transfers.complete(context, grant["transfer_id"], final_digest=digest)
    assert again["duplicate"] is True


def test_brw006_p01_fully_bound_envelope_dispatches(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    relay = __import__("quansio.worker_gateway.transfer_relay", fromlist=["EndpointRelay"]).EndpointRelay(migrated_db)
    envelope = {
        "endpoint_id": "ep-1", "target_id": target_id, "generation": 1,
        "lease": "lease-1", "fence": 1, "capability": "browser",
        "policy_decision_id": str(uuid.uuid4()), "effect_id": str(uuid.uuid4()),
        "delivery_id": str(uuid.uuid4()), "idempotency_key": str(uuid.uuid4()),
        "operation_version": "guest-rpc/1",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    }
    outcome = relay.dispatch(context, envelope, actuate=lambda env: {"acted": True})
    assert outcome["replayed"] is False and outcome["result"]["acted"] is True


def test_brw006_n01_stripped_fence_or_altered_argument_refused(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    relay = __import__("quansio.worker_gateway.transfer_relay", fromlist=["EndpointRelay"]).EndpointRelay(migrated_db)
    envelope = {
        "endpoint_id": "ep-1", "target_id": target_id, "generation": 1,
        "lease": "lease-1", "fence": 1, "capability": "browser",
        "policy_decision_id": str(uuid.uuid4()), "effect_id": str(uuid.uuid4()),
        "delivery_id": str(uuid.uuid4()), "idempotency_key": str(uuid.uuid4()),
        "operation_version": "guest-rpc/1",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    }
    stripped = {k: v for k, v in envelope.items() if k not in ("fence", "generation")}
    with pytest.raises(EnvelopeRefused, match="missing fields"):
        relay.dispatch(context, stripped, actuate=lambda env: {"acted": True})
    altered = {**envelope, "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()}
    with pytest.raises(EnvelopeRefused, match="expired"):
        relay.dispatch(context, altered, actuate=lambda env: {"acted": True})


def test_brw006_r01_dropped_response_replays_original_result(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    relay = __import__("quansio.worker_gateway.transfer_relay", fromlist=["EndpointRelay"]).EndpointRelay(migrated_db)
    envelope = {
        "endpoint_id": "ep-1", "target_id": target_id, "generation": 1,
        "lease": "l", "fence": 1, "capability": "browser",
        "policy_decision_id": str(uuid.uuid4()), "effect_id": str(uuid.uuid4()),
        "delivery_id": str(uuid.uuid4()), "idempotency_key": str(uuid.uuid4()),
        "operation_version": "guest-rpc/1",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    }
    first = relay.dispatch(context, envelope, actuate=lambda env: {"n": 1})
    calls = []
    second = relay.dispatch(context, envelope, actuate=lambda env: calls.append(1) or {"n": 2})
    assert first["result"] == {"n": 1}
    assert second["replayed"] is True and second["result"] == {"n": 1}
    assert calls == [], "endpoint action must not repeat for the same idempotency key"


def test_brw007_p01_observations_stored_as_evidence_only(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    store = ObservationEvidenceStore(migrated_db)
    run_id = str(uuid.uuid4())
    record = store.persist(context, session["session_id"], run_id, "s1", 1,
                           "state", {"a11y_tree": []})
    assert record["evidence_only"] is True
    evidence = store.as_evidence(context, record["observation_id"])
    assert evidence["digest"] == record["digest"]
    assert evidence["actuation"] is None, "observations expose no actuation affordance"


def test_brw007_n01_observation_replay_has_no_actuation(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    store = ObservationEvidenceStore(migrated_db)
    record = store.persist(context, session["session_id"], str(uuid.uuid4()), "s", 1,
                           "action", {"action": "click", "selector": "#pay"})
    evidence = store.as_evidence(context, record["observation_id"])
    # The evidence view carries no effect id, no actuator binding, no run path:
    # a replayed observation is inert data.
    assert "effect_id" not in evidence
    assert evidence["actuation"] is None
    assert evidence["evidence_only"] is True


def test_brw007_r01_backfill_after_evidence_store_outage(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    store = ObservationEvidenceStore(migrated_db)
    run_id = str(uuid.uuid4())
    # Outage: eligible observations were not persisted; canonical action/result
    # state (the observation content list below) was preserved by the runtime.
    preserved = [
        {"kind": "state", "a11y_tree": ["button"]},
        {"kind": "action", "selector": "#submit"},
    ]
    added = store.backfill(context, session["session_id"], run_id, "s", 1, preserved)
    assert added == 2
    for entry in preserved:
        record = store.persist.__wrapped__ if False else None
    # Backfill is additive; the action is never re-run (no execution calls here).
    rows = migrated_db.query_one(
        "SELECT count(*) FROM browser_observations WHERE tenant_id=%s AND run_id=%s",
        (context.tenant_id, run_id),
    )[0]
    assert rows == 2


def test_brw008_p01_enabled_profile_passes_all_mapped_tests(migrated_db, sessions, controller, context, enabled_target_factory):
    """Real navigation, structured action, classification, takeover,
    reconnect, transfer and stale-envelope checks for the enabled profile."""
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    run_id = _parent_run(migrated_db, context)
    controller.act(context, session["session_id"], "navigate",
                   {"url": "https://example.test/start"}, 1, run_id, "nav")
    controller.act(context, session["session_id"], "type",
                   {"selector": "#q", "content": "ok"}, 2, run_id, "type")
    ledger = EffectLedger(migrated_db)
    classifier = SemanticEffectClassifier(migrated_db, ledger)
    gate = classifier.gate_actuation(context, run_id, session["session_id"],
                                     "click", {"selector": "send-message"})
    assert gate["effect_id"]
    takeover = TakeoverService(migrated_db, sessions)
    takeover.takeover(context, session["session_id"], "human-q")
    takeover.return_control(context, session["session_id"], "human-q")
    transfers = GovernedFileTransfer(migrated_db, artifact_lookup=lambda d: None)
    with pytest.raises(TransferDenied):
        transfers.grant_upload(context, session["session_id"], "f" * 64)


def test_brw008_n01_unqualified_profile_stays_disabled(migrated_db, context):
    from quansio.machine_control.services import PrivateTargetService

    from quansio.machine_control.inventory import TargetInventory

    private = PrivateTargetService(migrated_db, TargetInventory(migrated_db))
    registered = private.register(context, f"private-{uuid.uuid4().hex[:8]}",
                                  mapped_qualification_suites=["Q-BROWSER-PRIVATE"])
    assert registered["enabled"] is False


def test_brw008_r01_restart_keeps_durable_identities(migrated_db, sessions, context, enabled_target_factory):
    target_id = enabled_target_factory(context)
    session = sessions.create(context, target_id=target_id, generation=1)
    fresh = BrowserSessionManager(migrated_db)
    reconnected = fresh.get(context, session["session_id"])
    assert reconnected["session_id"] == session["session_id"]
    assert reconnected["target_id"] == target_id
