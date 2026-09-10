"""Acceptance tests for SEC-002..005 and EFF-001..003 against the real
environment, with a real HTTP actuation target for effect semantics.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))
sys.path.insert(0, str(REPO_ROOT / "tests/control"))

import httpx  # noqa: E402
from effect_target import start_effect_target  # noqa: E402
from quansio.control.broker import CredentialBroker, HandleRefused  # noqa: E402
from quansio.control.effects import (  # noqa: E402
    ApprovalMismatch,
    ApprovalService,
    BlindRetryBlocked,
    EffectLedger,
    EffectRequired,
    EffectStateError,
    UnknownEffectReconciler,
)
from quansio.control.guard import BehaviorSequenceGuard, SequenceBlocked  # noqa: E402
from quansio.control.policy import (  # noqa: E402
    PolicyDenied,
    PolicyEngine,
    PolicyUnavailable,
    ScopeDigestMismatch,
)
from quansio.control.privacy_gate import (  # noqa: E402
    ClassifierUnavailable,
    DestinationPrivacyGate,
    EgressDenied,
    Route,
)
from quansio.platform.context import IdentityContext  # noqa: E402


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
def policy(migrated_db) -> PolicyEngine:
    return PolicyEngine(migrated_db)


@pytest.fixture(scope="module")
def effect_target_factory():
    servers = []

    def factory(delay_seconds: float = 0.0):
        server, port, recorded = start_effect_target(delay_seconds=delay_seconds)
        servers.append(server)
        return {"base": f"http://127.0.0.1:{port}", "recorded": recorded}

    yield factory
    for server in servers:
        server.shutdown()




# ---------------------------------------------------------------------------
# SEC-002: argument-bound policy decisions
# ---------------------------------------------------------------------------


def test_sec002_p01_decision_binds_all_inputs(policy, migrated_db, workspace_setup, context):
    decision = policy.decide(
        context, actor_id=context.user_id, operation="file.publish",
        arguments={"path": "/srv/reports/q3.pdf"}, target="external:storage",
        data_classification=[], capability_snapshot_id=str(uuid.uuid4()),
    )
    assert decision["decision"] == "REQUIRE_APPROVAL"
    stored = migrated_db.query_one(
        """
        SELECT actor_id::text, operation, argument_scope_digest, target, decision, policy_revision
        FROM policy_decisions WHERE policy_decision_id = %s
        """,
        (decision["policy_decision_id"],),
    )
    assert stored[1] == "file.publish" and stored[4] == "REQUIRE_APPROVAL"
    # Deterministic digest: identical arguments produce the same scope digest.
    again = policy.decide(
        context, actor_id=context.user_id, operation="file.publish",
        arguments={"path": "/srv/reports/q3.pdf"}, target="external:storage",
        data_classification=[],
    )
    assert again["argument_scope_digest"] == decision["argument_scope_digest"]


def test_sec002_n01_changed_argument_breaks_scope_binding(policy, migrated_db):
    decision = policy.decide(
        _fake_ctx(migrated_db), actor_id=str(uuid.uuid4()), operation="payment.transfer",
        arguments={"amount": 1000, "payee": "vendor-a"}, target="external:bank",
        data_classification=[],
    )
    # A one-unit argument change must fail the scope check.
    with pytest.raises(ScopeDigestMismatch):
        policy.check_scope(decision, {"amount": 1001, "payee": "vendor-a"})


def _fake_ctx(db) -> IdentityContext:
    tenant_id, workspace_id = str(uuid.uuid4()), str(uuid.uuid4())
    db.execute("INSERT INTO tenants (tenant_id, name) VALUES (%s, 'fake') ON CONFLICT DO NOTHING",
               (tenant_id,))
    db.execute("INSERT INTO workspaces (tenant_id, workspace_id, name) VALUES (%s, %s, 'fw')",
               (tenant_id, workspace_id))
    return IdentityContext(
        tenant_id=tenant_id, workspace_id=workspace_id,
        user_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def test_sec002_r01_policy_outage_requires_fresh_decision(policy, migrated_db):
    policy.set_dependency_available(False)
    with pytest.raises(PolicyUnavailable):
        policy.decide(_fake_ctx(migrated_db), actor_id=str(uuid.uuid4()), operation="file.publish",
                      arguments={"path": "/x"}, target="external:storage",
                      data_classification=[])
    # Recovery: fresh decision produced under the same engine; stale state
    # (an expired decision) is rejected by require_fresh.
    policy.set_dependency_available(True)
    decision = policy.decide(_fake_ctx(migrated_db), actor_id=str(uuid.uuid4()), operation="file.publish",
                             arguments={"path": "/x"}, target="external:storage",
                             data_classification=[])
    expired = {**decision, "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)}
    with pytest.raises(PolicyUnavailable, match="fresh decision required"):
        policy.require_fresh(expired)
    assert policy.require_fresh(decision)["decision"] == decision["decision"]


# ---------------------------------------------------------------------------
# SEC-003: destination-aware privacy gate
# ---------------------------------------------------------------------------


SECRET_UPLOAD = b"transfer instructions: key sk-abcdefghijklmnop123456"


def test_sec003_p01_gate_classifies_and_redacts_all_routes(migrated_db, workspace_setup, context):
    gate = DestinationPrivacyGate(migrated_db)
    benign = b"quarterly report body text"
    for route in (Route.MODEL, Route.CONNECTOR, Route.UPLOAD, Route.REMOTE_WORKER):
        decision = gate.evaluate(context, route, "partner", benign)
        assert decision["decision"] == "ALLOW", route
    # Internal destination with secret bytes: redacted allow.
    decision = gate.evaluate(context, Route.MODEL, "partner", SECRET_UPLOAD)
    assert decision["decision"] == "ALLOW_REDACTED"
    assert b"sk-abcdefghijklmnop123456" not in decision["outbound"]


def test_sec003_n01_denied_secret_blocked_on_alternate_routes(migrated_db, workspace_setup, context):
    gate = DestinationPrivacyGate(migrated_db)
    ssn_payload = "employee record: 123-45-6789"
    for route in (Route.CONNECTOR, Route.UPLOAD):
        with pytest.raises(EgressDenied):
            gate.evaluate(context, route, "external:partner", ssn_payload)
    # No egress decision for denied transfers was ever ALLOWed.
    count = migrated_db.query_one(
        "SELECT count(*) FROM policy_decisions WHERE tenant_id=%s AND decision='ALLOW'",
        (context.tenant_id,),
    )[0]
    assert count == 0


def test_sec003_r01_classifier_recovery_reevaluates_pending(migrated_db, workspace_setup, context):
    gate = DestinationPrivacyGate(migrated_db)
    benign = b"pending quarterly report"
    gate.set_classifier_available(False)
    with pytest.raises(ClassifierUnavailable):
        gate.evaluate(context, Route.UPLOAD, "partner", benign)
    assert len(gate._pending) == 1, "egress must wait while classification is unavailable"
    # Classifier dependency recovers: pending egress is re-evaluated under
    # the CURRENT policy revision, not replayed as a stale allow.
    gate.set_classifier_available(True)
    assert gate._pending == [], "re-evaluated benign egress must be sent"
    # Fresh secret egress to an internal destination is redacted; to an
    # external destination it is denied outright.
    decision = gate.evaluate(context, Route.MODEL, "internal:archive", SECRET_UPLOAD)
    assert decision["decision"] == "ALLOW_REDACTED"
    with pytest.raises(EgressDenied):
        gate.evaluate(context, Route.UPLOAD, "partner", SECRET_UPLOAD)


# ---------------------------------------------------------------------------
# SEC-004: scoped credential broker
# ---------------------------------------------------------------------------


def test_sec004_p01_handle_bound_without_secret_disclosure(migrated_db, workspace_setup, context):
    broker = CredentialBroker(migrated_db)
    broker.register_secret(context, "bank-api", "bank", "super-secret-material")
    handle = broker.issue(context, "bank-api", "payment.transfer", "external:bank", "payments")
    assert "super-secret-material" not in str(handle)
    material = broker.exchange(context, handle["handle_id"], "payment.transfer", "external:bank")
    assert material == "super-secret-material"


def test_sec004_n01_expired_or_misbound_handle_refused(migrated_db, workspace_setup, context):
    broker = CredentialBroker(migrated_db)
    broker.register_secret(context, "api-2", "partner", "partner-secret")
    handle = broker.issue(context, "api-2", "payment.transfer", "external:bank", capability="payments")
    # Expire it.
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE credential_handles SET expires_at = now() - interval '1 second' WHERE handle_id = %s",
            (handle["handle_id"],),
        )
    with pytest.raises(HandleRefused, match="expired"):
        broker.exchange(context, handle["handle_id"], "payment.transfer", "external:bank")
    # Wrong target / wrong operation, still within expiry.
    fresh = broker.issue(context, "api-2", "email.send", "external:mail", capability="mail")
    with pytest.raises(HandleRefused, match="bound to"):
        broker.exchange(context, fresh["handle_id"], "payment.transfer", "external:mail")


def test_sec004_r01_rotation_invalidates_outstanding_handles(migrated_db, workspace_setup, context):
    broker = CredentialBroker(migrated_db)
    broker.register_secret(context, "rotating", "saas", "generation-1-secret")
    handle = broker.issue(context, "rotating", "connector.call", "external:saas", capability="connector")
    broker.rotate(context, "rotating", "generation-2-secret")
    with pytest.raises(HandleRefused, match="rotated|superseded|invalidated"):
        broker.exchange(context, handle["handle_id"], "connector.call", "external:saas")
    new_handle = broker.issue(context, "rotating", "connector.call", "external:saas", capability="connector")
    assert broker.exchange(context, new_handle["handle_id"], "connector.call", "external:saas") == \
        "generation-2-secret"


# ---------------------------------------------------------------------------
# SEC-005: behavior-sequence guard
# ---------------------------------------------------------------------------


def test_sec005_p01_and_n01_dangerous_sequence_blocked(migrated_db, workspace_setup, context):
    guard = BehaviorSequenceGuard(migrated_db)
    guard.add_rule(context, "no-secret-exfil",
                   ["secret.read", "upload.outbound"], action="block")
    ledger = EffectLedger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    # Independently valid secret read: allowed.
    read_effect = ledger.propose(context, run_id=run_id,
                                 operation="secret.read", arguments={"path": "/vault/key"},
                                 target="internal:vault")
    assert guard.check(context, "secret.read")["action"] == "allow"
    ledger.start_execution = ledger.start_execution  # noqa: B018 - no-op clarity
    ledger.authorize = ledger.authorize  # noqa: B018
    with migrated_db.connection() as connection:
        connection.execute(
            """
            INSERT INTO effects (tenant_id, workspace_id, effect_id, run_id, operation,
                                 arguments, status)
            VALUES (%s, %s, %s, %s, 'secret.read', '{}'::jsonb, 'committed')
            """,
            (context.tenant_id, context.workspace_id, str(uuid.uuid4()), run_id),
        )
    # The following outbound upload is blocked despite uploads being
    # individually valid: the SEQUENCE matches the rule.
    with pytest.raises(SequenceBlocked, match="no-secret-exfil"):
        guard.check(context, "upload.outbound")


def test_sec005_r01_rule_update_reevaluates_without_deleting_history(migrated_db, workspace_setup, context):
    guard = BehaviorSequenceGuard(migrated_db)
    guard.add_rule(context, "rule-1", ["connector.call", "connector.call"], action="escalate")
    run_id = _parent_run(migrated_db, context)
    with migrated_db.connection() as connection:
        for _ in range(2):
            connection.execute(
                """
                INSERT INTO effects (tenant_id, workspace_id, effect_id, run_id, operation,
                                     arguments, status)
                VALUES (%s, %s, %s, %s, 'connector.call', '{}'::jsonb, 'committed')
                """,
                (context.tenant_id, context.workspace_id, str(uuid.uuid4()), run_id),
            )
    guard.check(context, "connector.call")  # matches rule-1 -> escalate
    # Policy/rule update: the rule is tightened to a different sequence.
    guard.add_rule(context, "rule-1", ["upload.outbound", "upload.outbound"], action="block")
    decision = guard.check(context, "connector.call")
    assert decision["action"] == "allow", "re-evaluation must be deterministic under current rules"
    # History preserved.
    assert migrated_db.query_one(
        "SELECT count(*) FROM effects WHERE tenant_id=%s AND operation='connector.call'",
        (context.tenant_id,),
    )[0] == 2
    evaluations = migrated_db.query_one(
        "SELECT count(*) FROM behavior_evaluations WHERE tenant_id=%s", (context.tenant_id,)
    )[0]
    assert evaluations >= 2, "evaluation trail must be append-only"


# ---------------------------------------------------------------------------
# EFF-001: universal Effect Ledger
# ---------------------------------------------------------------------------


def _ledger(db) -> EffectLedger:
    return EffectLedger(db)


def _parent_run(db, context) -> str:
    from quansio.platform.repository import TenantRepository

    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', 'fx-parent')",
            (context.tenant_id, context.workspace_id, agent_id),
        )
    run_id = TenantRepository(db).create_run(context, agent_id)
    with db.connection() as connection:
        connection.execute("UPDATE runs SET status='running' WHERE tenant_id=%s AND run_id=%s",
                           (context.tenant_id, run_id))
    return run_id


def test_eff001_p01_effect_record_precedes_actuation_with_correlation(migrated_db, workspace_setup, context, effect_target_factory):
    target = effect_target_factory()
    ledger = _ledger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    effect = ledger.propose(
        context, run_id=run_id, operation="connector.submit",
        arguments={"payload": "transfer"}, target=target["base"],
        policy_decision_id=str(uuid.uuid4()), idempotency_key=str(uuid.uuid4()),
    )
    ledger.authorize(context, effect["effect_id"], str(uuid.uuid4()))
    ledger.start_execution(context, effect["effect_id"])
    response = httpx.post(target["base"] + "/submit",
                          data={"idempotency_key": effect["idempotency_key"]}, timeout=10)
    ledger.complete(context, effect["effect_id"], {"http_status": response.status_code},
                    receipt=response.json())
    row = migrated_db.query_one(
        "SELECT status, policy_decision_id, receipt, approval_id FROM effects WHERE effect_id=%s",
        (effect["effect_id"],),
    )
    assert row[0] == "committed" and row[1] is not None and row[2]["accepted"] is True


def test_eff001_n01_actuation_without_effect_id_rejected(migrated_db, workspace_setup, context, effect_target_factory):
    target = effect_target_factory()
    ledger = _ledger(migrated_db)
    with pytest.raises(EffectRequired):
        ledger.require_effect(context, str(uuid.uuid4()), expected_status="authorized")
    # An actuator-shaped flow must reject the missing effect before any call.
    with pytest.raises(EffectStateError):
        ledger.start_execution(context, str(uuid.uuid4()))


def test_eff001_r01_restart_during_executing_reconciles_same_identity(migrated_db, workspace_setup, context, effect_target_factory):
    target = effect_target_factory()
    ledger = _ledger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    idem = str(uuid.uuid4())
    effect = ledger.propose(context, run_id=run_id, operation="connector.submit",
                            arguments={}, target=target["base"],
                            idempotency_key=idem)
    ledger.authorize(context, effect["effect_id"], str(uuid.uuid4()))
    ledger.start_execution(context, effect["effect_id"])
    # Crash: the POST reached the target but no terminal was recorded.
    httpx.post(target["base"] + "/submit", data={"idempotency_key": idem}, timeout=10)
    recovered = ledger.recover_actuating(context)
    match = [r for r in recovered if r["effect_id"] == effect["effect_id"]]
    assert match and match[0]["idempotency_key"] == idem, "recovery binds the same identity"
    reconciler = UnknownEffectReconciler(migrated_db, ledger)
    ledger.mark_unknown(context, effect["effect_id"], {"crash": True})
    outcome = reconciler.probe(
        context, effect["effect_id"],
        target_query=lambda key: "committed" if target["recorded"].get(key) else "not_found",
    )
    assert outcome["final"] == "reconciled"
    row = migrated_db.query_one("SELECT status FROM effects WHERE effect_id=%s", (effect["effect_id"],))
    assert row[0] == "committed", "same effect reconciled, never a new effect"


# ---------------------------------------------------------------------------
# EFF-002: durable scoped approvals
# ---------------------------------------------------------------------------


def test_eff002_p01_financial_approval_binds_payee_amount_currency_ceiling(migrated_db, workspace_setup, context, effect_target_factory):
    target = effect_target_factory()
    policy = PolicyEngine(migrated_db)
    approvals = ApprovalService(migrated_db, policy)
    ledger = _ledger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    arguments = {"amount": 25000, "currency": "EUR", "payee": "vendor-gmbh"}
    effect = ledger.propose(context, run_id=run_id, operation="payment.transfer",
                            arguments=arguments, target="external:bank",
                            idempotency_key=str(uuid.uuid4()))
    decision = policy.decide(context, actor_id=context.user_id, operation="payment.transfer",
                             arguments=arguments, target="external:bank", data_classification=[])
    approval = approvals.request(
        context, run_id=run_id, effect_id=effect["effect_id"],
        operation="payment.transfer", arguments=arguments, target="external:bank",
        financial={"amount_minor": 25000, "ceiling_minor": 30000, "currency": "EUR",
                   "payee": "vendor-gmbh"},
    )
    approvals.decide(context, approval["approval_id"], approved=True,
                     approver_id=context.user_id)
    ledger.authorize(context, effect["effect_id"], decision["policy_decision_id"],
                     approval_id=approval["approval_id"])
    stored = migrated_db.query_one(
        "SELECT amount_minor, ceiling_minor, currency, payee, status FROM approvals WHERE approval_id=%s",
        (approval["approval_id"],),
    )
    assert stored == (25000, 30000, "EUR", "vendor-gmbh", "approved")


def test_eff002_n01_amount_or_payee_change_denied_before_invocation(migrated_db, workspace_setup, context, effect_target_factory):
    target = effect_target_factory()
    policy = PolicyEngine(migrated_db)
    approvals = ApprovalService(migrated_db, policy)
    ledger = _ledger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    arguments = {"amount": 10000, "currency": "EUR", "payee": "vendor-a"}
    effect = ledger.propose(context, run_id=run_id, operation="payment.transfer",
                            arguments=arguments, target="external:bank",
                            idempotency_key=str(uuid.uuid4()))
    approval = approvals.request(
        context, run_id=run_id, effect_id=effect["effect_id"],
        operation="payment.transfer", arguments=arguments, target="external:bank",
        financial={"amount_minor": 10000, "ceiling_minor": 20000, "currency": "EUR",
                   "payee": "vendor-a"},
    )
    approvals.decide(context, approval["approval_id"], approved=True, approver_id=context.user_id)
    # One minor currency unit more: denied before provider invocation.
    with pytest.raises(ApprovalMismatch, match="amount"):
        approvals.verify_execution_scope(
            context, approval["approval_id"],
            {"amount": 10001, "currency": "EUR", "payee": "vendor-a"})
    # Substituted payee: denied.
    with pytest.raises(ApprovalMismatch, match="payee"):
        approvals.verify_execution_scope(
            context, approval["approval_id"],
            {"amount": 10000, "currency": "EUR", "payee": "vendor-b"})
    # The provider was never invoked.
    assert target["recorded"] == {}


def test_eff002_r01_other_surface_approves_waiting_effect_without_duplicates(migrated_db, workspace_setup, context):
    policy = PolicyEngine(migrated_db)
    approvals = ApprovalService(migrated_db, policy)
    ledger = _ledger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    effect = ledger.propose(context, run_id=run_id, operation="email.send",
                            arguments={"recipient": "x@y.z"}, target="external:mail",
                            idempotency_key=str(uuid.uuid4()))
    approval = approvals.request(context, run_id=run_id, effect_id=effect["effect_id"],
                                 operation="email.send",
                                 arguments={"recipient": "x@y.z"}, target="external:mail")
    other_surface_ctx = _ctx(workspace_setup)  # disconnected client, new session
    first = approvals.decide(other_surface_ctx, approval["approval_id"], True,
                             approver_id=context.user_id)
    second = approvals.decide(context, approval["approval_id"], True, approver_id=context.user_id)
    assert first["already_decided"] is False and second["already_decided"] is True
    count = migrated_db.query_one(
        "SELECT count(*) FROM approvals WHERE tenant_id=%s AND capability='email.send'",
        (context.tenant_id,),
    )[0]
    assert count == 1, "no duplicate approval creation"


# ---------------------------------------------------------------------------
# EFF-003: UNKNOWN effect reconciliation
# ---------------------------------------------------------------------------


def test_eff003_p01_unknown_timeout_reconciles_via_probe(migrated_db, workspace_setup, context, effect_target_factory):
    target = effect_target_factory(delay_seconds=2.0)
    ledger = _ledger(migrated_db)
    reconciler = UnknownEffectReconciler(migrated_db, ledger)
    run_id = _parent_run(migrated_db, context)
    idem = str(uuid.uuid4())
    effect = ledger.propose(context, run_id=run_id, operation="connector.submit",
                            arguments={}, target=target["base"], idempotency_key=idem)
    ledger.authorize(context, effect["effect_id"], str(uuid.uuid4()))
    ledger.start_execution(context, effect["effect_id"])
    # Ambiguous timeout: the target processed but never answered.
    with pytest.raises(httpx.ReadTimeout):
        httpx.post(target["base"] + "/submit",
                   data={"idempotency_key": idem}, timeout=1.0)
    reconciler.mark_unknown_on_timeout(context, effect["effect_id"], {"transport": "read timeout"})
    assert migrated_db.query_one("SELECT status FROM effects WHERE effect_id=%s",
                                 (effect["effect_id"],))[0] == "unknown"
    outcome = reconciler.probe(
        context, effect["effect_id"],
        target_query=lambda key: "committed" if target["recorded"].get(key) else "not_found",
    )
    assert outcome["probe_result"] == "committed" and outcome["final"] == "reconciled"
    row = migrated_db.query_one("SELECT status FROM effects WHERE effect_id=%s", (effect["effect_id"],))
    assert row[0] == "committed"


def test_eff003_n01_blind_retry_of_unknown_blocked(migrated_db, workspace_setup, context, effect_target_factory):
    target = effect_target_factory(delay_seconds=2.0)
    ledger = _ledger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    idem = str(uuid.uuid4())
    effect = ledger.propose(context, run_id=run_id, operation="connector.submit",
                            arguments={}, target=target["base"], idempotency_key=idem)
    ledger.authorize(context, effect["effect_id"], str(uuid.uuid4()))
    ledger.start_execution(context, effect["effect_id"])
    with pytest.raises(httpx.ReadTimeout):
        httpx.post(target["base"] + "/submit", data={"idempotency_key": idem}, timeout=1.0)
    ledger.mark_unknown(context, effect["effect_id"], {"timeout": True})
    # A blind retry (authorized -> executing) is blocked by the ledger.
    with pytest.raises(EffectStateError):
        ledger.start_execution(context, effect["effect_id"])
    # Probe says not_found: only then is a safe retry re-authorized.
    reconciler = UnknownEffectReconciler(migrated_db, ledger)
    outcome = reconciler.probe(context, effect["effect_id"], target_query=lambda key: "not_found")
    assert outcome["final"] == "authorized_for_safe_retry"


def test_eff003_r01_reconciliation_worker_restart_continues_same_identity(migrated_db, workspace_setup, context, effect_target_factory):
    target = effect_target_factory(delay_seconds=2.0)
    ledger = _ledger(migrated_db)
    reconciler_a = UnknownEffectReconciler(migrated_db, ledger)
    run_id = _parent_run(migrated_db, context)
    idem = str(uuid.uuid4())
    effect = ledger.propose(context, run_id=run_id, operation="connector.submit",
                            arguments={}, target=target["base"], idempotency_key=idem)
    ledger.authorize(context, effect["effect_id"], str(uuid.uuid4()))
    ledger.start_execution(context, effect["effect_id"])
    with pytest.raises(httpx.ReadTimeout):
        httpx.post(target["base"] + "/submit", data={"idempotency_key": idem}, timeout=1.0)
    reconciler_a.mark_unknown_on_timeout(context, effect["effect_id"], {"timeout": True})
    # Worker 'a' probed once and recorded 'unknown' (target still processing).
    outcome_a = reconciler_a.probe(context, effect["effect_id"], target_query=lambda key: "unknown")
    assert outcome_a["final"] == "unknown"
    # Restart: worker 'b' continues with the SAME effect/idempotency identity.
    reconciler_b = UnknownEffectReconciler(migrated_db, ledger)
    outcome_b = reconciler_b.probe(
        context, effect["effect_id"],
        target_query=lambda key: "committed" if target["recorded"].get(key) else "not_found",
    )
    assert outcome_b["final"] == "reconciled"
    assert outcome_b["attempt"] == outcome_a["attempt"] + 1
    row = migrated_db.query_one("SELECT status, idempotency_key FROM effects WHERE effect_id=%s",
                                (effect["effect_id"],))
    assert row == ("committed", idem), "explicit reconciled terminal with the original identity"


def json_dumps(value) -> str:
    import json

    return json.dumps(value, default=str)
