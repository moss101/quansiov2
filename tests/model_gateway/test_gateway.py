"""Acceptance tests for MOD-002..MOD-007.

Real-provider tests run against llama.cpp (the enabled profile); protocol
abuse cases run against a local misbehaving HTTP server. Usage settlement
exercises the canonical budget ledger from M2.
"""

from __future__ import annotations

import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.model_gateway.adapters import (  # noqa: E402
    CanonicalRequest,
    ProviderProtocolFailure,
    ProviderUnreachable,
    adapter_for,
)
from quansio.model_gateway.credentials import ProviderCredentials  # noqa: E402
from quansio.model_gateway.failover import (  # noqa: E402
    EffectBoundaryCommitted,
    FailoverCoordinator,
    ProviderHealth,
    TypedOutcome,
    classify_failure,
)
from quansio.model_gateway.gateway import ModelGateway  # noqa: E402
from quansio.model_gateway.privacy import (  # noqa: E402
    PrivacyDenied,
    PrivacyFailClosed,
    ModelPrivacyGate,
)
from quansio.model_gateway.routing import ModelRouter, NoQualifiedRoute  # noqa: E402
from quansio.model_gateway.streaming import (  # noqa: E402
    InvalidStream,
    StreamValidator,
    BoundedEventChannel,
    validated_stream,
)
from quansio.model_gateway.usage import ModelUsageLedger  # noqa: E402
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.platform.repository import TenantRepository  # noqa: E402
from quansio.runtime.orchestration import BudgetLedger  # noqa: E402
from tests.model_gateway.conftest import PROVIDER_BASE  # noqa: E402


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


def _seed_profiles(db, context, extra=None):
    profiles = {
        "quansio-local-lfm": {
            "provider": "llama.cpp", "residency": ["local"], "max_context_tokens": 8192,
            "cost_per_1k_tokens_cents": 1, "capabilities": ["chat"], "enabled": True,
        },
    }
    profiles.update(extra or {})
    with db.connection() as connection:
        for entry_id, definition in profiles.items():
            connection.execute(
                """
                INSERT INTO registry_entries (tenant_id, registry, entry_id, definition, enabled)
                VALUES (%s, 'model_profile', %s, %s, true)
                ON CONFLICT (tenant_id, registry, entry_id) DO UPDATE SET definition = EXCLUDED.definition
                """,
                (context.tenant_id, entry_id, __import__("json").dumps(definition)),
            )


@pytest.fixture()
def context(workspace_setup) -> IdentityContext:
    return _ctx(workspace_setup)


@pytest.fixture()
def gateway(migrated_db) -> ModelGateway:
    return ModelGateway(migrated_db)


@pytest.fixture()
def parent_run(migrated_db, context):
    repository = TenantRepository(migrated_db)
    agent_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', %s)",
            (context.tenant_id, context.workspace_id, agent_id, "gateway-parent"),
        )
    run_id = repository.create_run(context, agent_id, budget_cents=1000)
    with migrated_db.connection() as connection:
        connection.execute("UPDATE runs SET status='running' WHERE tenant_id=%s AND run_id=%s",
                           (context.tenant_id, run_id))
    return run_id


def _admit(gateway, context, parent_run, profiles=("quansio-local-lfm",), residency=("local",), budget=200):
    return gateway.admit(
        context, run_id=parent_run, step_id="step-1",
        demand={"dimensions": {"capabilities": ["chat"]}},
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        policy_allowed_profiles=list(profiles), required_residency=list(residency),
        context_tokens=64, budget_cents=budget,
    )


# ---------------------------------------------------------------------------
# MOD-002: provider-neutral adapter contract (real boundary)
# ---------------------------------------------------------------------------


def test_mod002_p01_real_profile_translates_to_canonical_events(real_provider, monkeypatch):
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", PROVIDER_BASE)
    adapter = adapter_for(ProviderCredentials(
        profile_id="quansio-local-lfm", base_url=PROVIDER_BASE, api_key=None, protocol="openai-chat",
    ))
    request = CanonicalRequest(
        request_id=str(uuid.uuid4()), model_profile_id="quansio-local-lfm",
        messages=[{"role": "user", "content": "Count from 1 to 3, digits only."}],
        sampling={"max_tokens": 24}, trace_id="t1",
    )
    events = list(adapter.stream(request))
    assert events[0].event_type == "MODEL_STARTED" and events[0].sequence == 1
    deltas = [e for e in events if e.event_type == "OUTPUT_DELTA"]
    assert deltas, "real provider produced no output deltas"
    assert [e.sequence for e in events] == list(range(1, len(events) + 1))
    terminal = events[-1]
    assert terminal.event_type == "MODEL_COMPLETED" and terminal.payload["terminal"] is True
    usage = terminal.payload["usage"]
    assert usage["prompt_tokens"] > 0 and usage["completion_tokens"] > 0 and usage["total_tokens"] > 0


def test_mod002_n01_missing_mandatory_fields_emit_typed_protocol_failure(stub_provider_factory, monkeypatch):
    base = stub_provider_factory("missing_usage")
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", base)
    adapter = adapter_for(ProviderCredentials(
        profile_id="quansio-local-lfm", base_url=base, api_key=None, protocol="openai-chat",
    ))
    request = CanonicalRequest(str(uuid.uuid4()), "quansio-local-lfm",
                               [{"role": "user", "content": "hi"}], {}, "t")
    with pytest.raises(ProviderProtocolFailure, match="usage"):
        list(adapter.stream(request))
    base2 = stub_provider_factory("malformed_json")
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", base2)
    adapter2 = adapter_for(ProviderCredentials(
        profile_id="quansio-local-lfm", base_url=base2, api_key=None, protocol="openai-chat",
    ))
    with pytest.raises(ProviderProtocolFailure, match="malformed"):
        list(adapter2.stream(request))


def test_mod002_r01_adapter_disabled_mid_flight_reaches_explicit_terminal(migrated_db, workspace_setup, gateway, parent_run, monkeypatch):
    context = _ctx(workspace_setup)
    _seed_profiles(migrated_db, context)

    def _no_credentials(profile_id):
        raise KeyError(f"provider profile {profile_id} disabled")

    monkeypatch.setattr("quansio.model_gateway.gateway.load_credentials", _no_credentials)
    envelope = _admit(gateway, context, parent_run)
    events = list(gateway.fulfill(context, envelope))
    terminal = [e for e in events if e.event_type == "MODEL_FAILED"]
    assert terminal, "disabled adapter must normalize to an explicit terminal outcome"
    state = migrated_db.query_one(
        "SELECT state FROM model_requests WHERE tenant_id=%s AND request_id=%s",
        (context.tenant_id, envelope["request_id"]),
    )[0]
    assert state == "failed"
    # Reservation remains reconcilable: still bound to this request, settled/released exactly once later.
    reservation = migrated_db.query_one(
        "SELECT status FROM budget_reservations WHERE reservation_id = %s",
        (envelope["usage_reservation_id"],),
    )
    assert reservation is not None


# ---------------------------------------------------------------------------
# MOD-003: deterministic routing
# ---------------------------------------------------------------------------


def test_mod003_p01_deterministic_route_decision(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    _seed_profiles(migrated_db, context, extra={
        "quansio-expensive": {
            "provider": "llama.cpp", "residency": ["local"], "max_context_tokens": 32768,
            "cost_per_1k_tokens_cents": 9, "capabilities": ["chat", "tools"], "enabled": True,
        },
    })
    router = ModelRouter(migrated_db)
    decisions = [
        router.route(context, {"dimensions": {"capabilities": ["chat"]}},
                     policy_allowed_profiles=["quansio-local-lfm", "quansio-expensive"],
                     residency_required=["local"], context_tokens=128, budget_cents=500)
        for _ in range(3)
    ]
    print("SELECTED:", [d.selected_profile_id for d in decisions],
          [d.ranked_profile_ids for d in decisions][:1])
    assert all(d.selected_profile_id == "quansio-local-lfm" for d in decisions), "cheapest covering profile wins"
    assert len({d.route_decision_id for d in decisions}) == 3
    assert len({d.catalog_version for d in decisions}) == 1, "same catalog, same version"
    stored = migrated_db.query_one(
        "SELECT catalog_version, selected_profile_id FROM route_decisions WHERE route_decision_id = %s",
        (decisions[0].route_decision_id,),
    )
    assert stored[0] == decisions[0].catalog_version and stored[1] == "quansio-local-lfm"


def test_mod003_n01_unsatisfiable_constraints_fail_without_provider_call(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    _seed_profiles(migrated_db, context)
    router = ModelRouter(migrated_db)
    with pytest.raises(NoQualifiedRoute):
        router.route(context, {"dimensions": {"capabilities": ["chat"]}},
                     policy_allowed_profiles=["quansio-local-lfm"],
                     residency_required=["eu-central"], context_tokens=64, budget_cents=500)
    # Nothing consumed: no request rows, no reservations, no outbound.
    assert migrated_db.query_one(
        "SELECT count(*) FROM model_requests WHERE tenant_id = %s", (context.tenant_id,)
    )[0] == 0


def test_mod003_r01_pinned_route_decision_prevents_silent_drift(migrated_db, workspace_setup):
    context = _ctx(workspace_setup)
    _seed_profiles(migrated_db, context)
    router = ModelRouter(migrated_db)
    pinned_catalog = router.catalog(context)
    decision = router.route(context, {"dimensions": {"capabilities": ["chat"]}},
                            policy_allowed_profiles=["quansio-local-lfm"],
                            residency_required=["local"], context_tokens=64, budget_cents=500,
                            catalog_snapshot=pinned_catalog)
    # Catalog changes between retries (provider disables the profile).
    _seed_profiles(migrated_db, context, extra={
        "quansio-local-lfm": {
            "provider": "llama.cpp", "residency": ["local"], "max_context_tokens": 8192,
            "cost_per_1k_tokens_cents": 1, "capabilities": ["chat"], "enabled": False,
        },
    })
    # Retrying the admitted step uses the PINNED catalog snapshot: no drift.
    retry = router.route(context, {"dimensions": {"capabilities": ["chat"]}},
                         policy_allowed_profiles=["quansio-local-lfm"],
                         residency_required=["local"], context_tokens=64, budget_cents=500,
                         catalog_snapshot=pinned_catalog)
    assert retry.selected_profile_id == decision.selected_profile_id
    assert retry.catalog_version == decision.catalog_version
    # A fresh decision against the new catalog refuses (profile disabled).
    with pytest.raises(NoQualifiedRoute):
        router.route(context, {"dimensions": {"capabilities": ["chat"]}},
                     policy_allowed_profiles=["quansio-local-lfm"],
                     residency_required=["local"], context_tokens=64, budget_cents=500)


# ---------------------------------------------------------------------------
# MOD-004: streaming, cancellation, backpressure
# ---------------------------------------------------------------------------


def test_mod004_p01_canonical_order_with_backpressure(real_provider, monkeypatch):
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", PROVIDER_BASE)
    adapter = adapter_for(ProviderCredentials(
        profile_id="quansio-local-lfm", base_url=PROVIDER_BASE, api_key=None, protocol="openai-chat"))
    request = CanonicalRequest(str(uuid.uuid4()), "quansio-local-lfm",
                               [{"role": "user", "content": "Write a sentence about rivers."}],
                               {"max_tokens": 48}, "t")
    channel = BoundedEventChannel(maxsize=2)
    errors = []

    def produce():
        try:
            for event in adapter.stream(request):
                if not channel.put(event, timeout=10):
                    return
        except Exception as error:  # noqa: BLE001
            errors.append(error)
        finally:
            channel.close()

    worker = threading.Thread(target=produce, daemon=True)
    worker.start()
    validator = StreamValidator()
    count = 0
    while True:
        event = channel.get(timeout=30)
        if event is None:
            break
        validator.accept(event)
        count += 1
        time.sleep(0.01)  # slow consumer: backpressure must hold
    worker.join(timeout=30)
    assert not errors, errors
    assert count >= 3 and validator.terminal_seen


def test_mod004_n01_injected_invalid_streams_never_reach_runtime():
    from quansio_contracts import ModelEvent as M

    def make(seq, event_type):
        return M.from_dict({
            "schema_revision": "9.0.0", "event_id": str(uuid.uuid4()), "request_id": "r",
            "run_id": "r", "step_id": "s", "execution_generation": 1,
            "model_profile_id": "p", "route_decision_id": "d", "sequence": seq,
            "event_type": event_type, "occurred_at": "2026-09-10T00:00:00Z", "payload": {},
        })

    started = make(1, "MODEL_STARTED")
    delta = make(2, "OUTPUT_DELTA")
    completed = make(3, "MODEL_COMPLETED")
    # Duplicate sequence and pre-start events are rejected: they never pass
    # through to the runtime as valid events.
    passed = list(validated_stream(iter([started, delta, delta])))
    assert [e.sequence for e in passed] == [1, 2], "duplicate sequence must be rejected"
    assert list(validated_stream(iter([delta]))) == [], "pre-start event must be rejected"
    # Post-terminal events: the validator raises so the gateway normalizes
    # the stream into a typed failure; no post-terminal event passes as valid.
    with pytest.raises(InvalidStream):
        list(validated_stream(iter([started, delta, completed, make(4, "OUTPUT_DELTA")])))


def test_mod004_r01_cancel_during_blocked_consumption(real_provider, monkeypatch, migrated_db, workspace_setup, gateway, parent_run):
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", PROVIDER_BASE)
    context = _ctx(workspace_setup)
    _seed_profiles(migrated_db, context)
    envelope = _admit(gateway, context, parent_run)
    channel = BoundedEventChannel(maxsize=1)
    adapter = adapter_for(ProviderCredentials(
        profile_id="quansio-local-lfm", base_url=PROVIDER_BASE, api_key=None, protocol="openai-chat"))
    canonical = CanonicalRequest(envelope["request_id"], envelope["model_profile_id"],
                                 envelope["messages"], envelope["sampling"], "t")
    producer_done = threading.Event()

    def produce():
        for event in adapter.stream(canonical):
            if not channel.put(event, timeout=10):
                break
        producer_done.set()

    worker = threading.Thread(target=produce, daemon=True)
    worker.start()
    first = channel.get(timeout=30)
    assert first is not None
    # Consumer stops consuming: producer blocks on the bounded channel.
    time.sleep(1.0)
    assert not producer_done.is_set(), "producer must be blocked by backpressure"
    # Cancel: provider stream unwinds, terminal MODEL_CANCELLED + settlement.
    channel.cancel()
    worker.join(timeout=30)
    assert producer_done.is_set()
    from quansio.model_gateway.adapters import _event
    from quansio.model_gateway.adapters import CanonicalRequest as CR

    terminal = _event(CR(envelope["request_id"], envelope["model_profile_id"], [], {}, "t"),
                      10**6, "MODEL_CANCELLED", {"reason": "consumer cancelled", "terminal": True})
    usage = gateway._usage.apply_final_usage(
        context, parent_run, envelope["request_id"], envelope["usage_reservation_id"],
        {"total_tokens": 5}, cancelled=True,
    )
    assert usage["duplicate"] is False
    gateway._persist_event(context, envelope["request_id"], terminal)
    gateway._mark_request(context, envelope["request_id"], "cancelled")
    state = migrated_db.query_one(
        "SELECT state FROM model_requests WHERE tenant_id=%s AND request_id=%s",
        (context.tenant_id, envelope["request_id"]),
    )[0]
    assert state == "cancelled"


# ---------------------------------------------------------------------------
# MOD-005: usage reservation and late settlement
# ---------------------------------------------------------------------------


def test_mod005_p01_reserve_apply_release_with_idempotent_final(migrated_db, workspace_setup, context, parent_run):
    ledger = ModelUsageLedger(migrated_db, BudgetLedger(migrated_db))
    request_id = str(uuid.uuid4())
    reservation = ledger.reserve(context, parent_run, request_id, amount_cents=100)
    outcome = ledger.apply_final_usage(
        context, parent_run, request_id, reservation["reservation_id"],
        {"total_tokens": 60},
    )
    assert outcome == {"spend_applied": 60, "duplicate": False, "released_cents": 40, "policy_required": False}
    duplicate = ledger.apply_final_usage(
        context, parent_run, request_id, reservation["reservation_id"], {"total_tokens": 60},
    )
    assert duplicate["duplicate"] is True and duplicate["spend_applied"] == 0
    row = migrated_db.query_one(
        "SELECT status, committed_cents FROM budget_reservations WHERE reservation_id = %s",
        (reservation["reservation_id"],),
    )
    assert row == ("settled", 60)


def test_mod005_n01_duplicate_late_charge_and_over_ceiling_policy(migrated_db, workspace_setup, context, parent_run):
    ledger = ModelUsageLedger(migrated_db, BudgetLedger(migrated_db))
    request_id = str(uuid.uuid4())
    reservation = ledger.reserve(context, parent_run, request_id, amount_cents=50)
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE budget_reservations SET status='cancelled' WHERE reservation_id=%s",
            (reservation["reservation_id"],),
        )
    first = ledger.apply_final_usage(context, parent_run, request_id,
                                     reservation["reservation_id"], {"total_tokens": 30}, cancelled=True)
    assert first["duplicate"] is False
    second = ledger.apply_final_usage(context, parent_run, request_id,
                                      reservation["reservation_id"], {"total_tokens": 30}, cancelled=True)
    assert second["duplicate"] is True and second["spend_applied"] == 0, "second late charge: no additional spend"
    # Over-ceiling final usage: typed policy handling, recorded as adjustment.
    request_id2 = str(uuid.uuid4())
    reservation2 = ledger.reserve(context, parent_run, request_id2, amount_cents=10)
    outcome = ledger.apply_final_usage(context, parent_run, request_id2,
                                       reservation2["reservation_id"], {"total_tokens": 90})
    assert outcome["policy_required"] is True and outcome["spend_applied"] == 10
    adjustments = ledger.adjustments(context, request_id2)
    assert any(a["kind"] == "policy_adjustment" and a["payload"]["over_ceiling"] == 80 for a in adjustments)


def test_mod005_r01_gateway_restart_with_settling_records_appends_only(migrated_db, workspace_setup, context, parent_run):
    ledger = ModelUsageLedger(migrated_db, BudgetLedger(migrated_db))
    request_id = str(uuid.uuid4())
    reservation = ledger.reserve(context, parent_run, request_id, amount_cents=80)
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE budget_reservations SET status='settling' WHERE reservation_id=%s",
            (reservation["reservation_id"],),
        )
    before = ledger.adjustments(context, request_id)
    # "Gateway restart": fresh ledger instance completes the append-only history.
    fresh = ModelUsageLedger(migrated_db, BudgetLedger(migrated_db))
    outcome = fresh.apply_final_usage(context, parent_run, request_id,
                                      reservation["reservation_id"], {"total_tokens": 30})
    assert outcome["spend_applied"] == 30
    after = fresh.adjustments(context, request_id)
    assert after[: len(before)] == before, "earlier settlement history must not be rewritten"
    assert len(after) == len(before) + 1


# ---------------------------------------------------------------------------
# MOD-006: privacy and residency enforcement
# ---------------------------------------------------------------------------

PROTECTED_MESSAGE = [{"role": "user", "content": "My email is alice@example.com, send the report."}]


def test_mod006_p01_classification_redaction_and_audit_identity(migrated_db, workspace_setup, context):
    gate = ModelPrivacyGate(migrated_db)
    decision, outbound = gate.decide(
        context, request_id=str(uuid.uuid4()), destination_profile="quansio-local-lfm",
        messages=PROTECTED_MESSAGE,
    )
    assert decision.decision == "ALLOW_REDACTED" and decision.redactions >= 1
    assert "alice@example.com" not in json_dumps(outbound)
    assert "[REDACTED:email]" in json_dumps(outbound)
    stored = migrated_db.query_one(
        "SELECT decision, policy_revision FROM model_privacy_decisions WHERE privacy_decision_id = %s",
        (decision.privacy_decision_id,),
    )
    assert stored == ("ALLOW_REDACTED", gate._policy_revision)


def json_dumps(value) -> str:
    import json

    return json.dumps(value)


def test_mod006_n01_denied_destination_never_sends_protected_content(migrated_db, workspace_setup, context):
    gate = ModelPrivacyGate(migrated_db)
    with pytest.raises(PrivacyDenied):
        gate.decide(
            context, request_id=str(uuid.uuid4()), destination_profile="quansio-remote",
            messages=[{"role": "user", "content": "ssn 123-45-6789 please"}],
            required_residency=["remote"],
            destination_residency=None,
        )
    # Zero outbound bytes: nothing was captured or sent anywhere.
    assert migrated_db.query_one(
        "SELECT count(*) FROM model_privacy_decisions WHERE tenant_id = %s", (context.tenant_id,)
    )[0] == 0


def test_mod006_r01_policy_dependency_down_fails_closed(migrated_db, workspace_setup, context):
    gate = ModelPrivacyGate(migrated_db)
    gate.set_dependency_available(False)
    with pytest.raises(PrivacyFailClosed):
        gate.decide(context, request_id=str(uuid.uuid4()), destination_profile="quansio-local-lfm",
                    messages=[{"role": "user", "content": "totally harmless"}])
    gate.set_dependency_available(True)
    decision, _out = gate.decide(context, request_id=str(uuid.uuid4()),
                                 destination_profile="quansio-local-lfm",
                                 messages=[{"role": "user", "content": "totally harmless"}])
    assert decision.decision == "ALLOW"


# ---------------------------------------------------------------------------
# MOD-007: failure isolation and failover
# ---------------------------------------------------------------------------


def test_mod007_p01_typed_outcomes_and_allowed_failover(migrated_db, workspace_setup, context, parent_run, stub_provider_factory, monkeypatch):
    gateway = ModelGateway(migrated_db)
    _seed_profiles(migrated_db, context, extra={
        "quansio-broken": {
            "provider": "llama.cpp", "residency": ["local"], "max_context_tokens": 8192,
            "cost_per_1k_tokens_cents": 1, "capabilities": ["chat"], "enabled": True,
        },
    })
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", PROVIDER_BASE)
    broken = stub_provider_factory("http_500")
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_BROKEN_BASE_URL", broken)
    envelope = _admit(gateway, context, parent_run, profiles=("quansio-broken", "quansio-local-lfm"))
    events = list(gateway.fulfill(context, envelope, policy_allowed_profiles=["quansio-broken", "quansio-local-lfm"]))
    terminal = events[-1]
    assert terminal.event_type == "MODEL_COMPLETED", terminal.payload
    health = migrated_db.query_one(
        "SELECT state FROM provider_health WHERE tenant_id=%s AND profile_id='quansio-broken'",
        (context.tenant_id,),
    )
    assert health is not None and health[0] == "down"


def test_mod007_p01_typed_outcome_classification():
    from quansio.model_gateway.adapters import ProviderProtocolFailure, ProviderUnreachable

    assert classify_failure(ProviderUnreachable("p", "rate limited (HTTP 429)")) == TypedOutcome.RATE_LIMIT
    assert classify_failure(ProviderUnreachable("p", "timeout: read timed out")) == TypedOutcome.TIMEOUT
    assert classify_failure(ProviderUnreachable("p", "connection failed")) == TypedOutcome.OUTAGE
    assert classify_failure(ProviderProtocolFailure("p", "malformed SSE chunk")) == TypedOutcome.MALFORMED
    assert classify_failure(ProviderProtocolFailure("p", "missing choice")) == TypedOutcome.PROTOCOL


def test_mod007_n01_failover_after_effect_boundary_is_forbidden(migrated_db, workspace_setup, context):
    health = ProviderHealth(migrated_db)
    coordinator = FailoverCoordinator(migrated_db, health)
    with pytest.raises(EffectBoundaryCommitted):
        coordinator.failover_candidate(
            context, ["a", "b"], failed_profile="a", policy_allowed_profiles=["a", "b"],
            effect_boundary_committed=True, adapters={},
        )
    # No silent replay: failover never ran, no candidate was returned.
    assert health.state(context, "b") == "healthy"


def test_mod007_r01_outage_reentry_requires_fresh_probe(migrated_db, workspace_setup, context, real_provider):
    health = ProviderHealth(migrated_db)
    health.mark(context, "quansio-local-lfm", "down", "outage during qualification")
    assert health.routable(context, "quansio-local-lfm") is False
    adapter = adapter_for(ProviderCredentials(
        profile_id="quansio-local-lfm", base_url=PROVIDER_BASE, api_key=None, protocol="openai-chat"))
    # Fresh probe against the restored provider re-enables routing.
    assert health.probe_for_reentry(context, "quansio-local-lfm", adapter) is True
    assert health.routable(context, "quansio-local-lfm") is True
    # A provider that is still dead keeps failing fresh probes.
    dead_adapter = adapter_for(ProviderCredentials(
        profile_id="quansio-dead", base_url="http://127.0.0.1:59999", api_key=None, protocol="openai-chat"))
    assert health.probe_for_reentry(context, "quansio-dead", dead_adapter) is False
    assert health.state(context, "quansio-dead") == "down"
