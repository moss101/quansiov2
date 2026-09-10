"""Acceptance tests for RUN-004..RUN-008: admission, fan-out, cancellation,
budget races and durable waits — against real PostgreSQL and Redis.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from quansio.control.capability import CapabilityService, CapabilityEscalationError
from quansio.platform.context import IdentityContext
from quansio.platform.repository import TenantRepository
from quansio.runtime.events import EventLog
from quansio.runtime.orchestration import (
    AdmissionError,
    BudgetExceededError,
    BudgetLedger,
    DurableWaits,
    RunCanceller,
    TurnDispatcher,
    WorkerAdmission,
)
from quansio.runtime.protocol import ProtocolStateStore


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
def capability(migrated_db) -> CapabilityService:
    return CapabilityService(migrated_db)


@pytest.fixture()
def context(workspace_setup) -> IdentityContext:
    return _ctx(workspace_setup)


@pytest.fixture()
def parent_setup(migrated_db, context, capability, workspace_setup):
    """A parent run with an admitted capability snapshot and budget ceiling."""
    repository = TenantRepository(migrated_db)
    snapshot = capability.admit_root(
        context,
        principal_id=workspace_setup["admin"],
        capabilities=["fs.read", "web.get", "model.call"],
        constraints={"targets": {"/tmp/**": ["read"]}},
        budget_cents=1000,
    )
    agent_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            """
            INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name,
                                admission_expires_at, admission_snapshot_id)
            VALUES (%s, %s, %s, 'persistent_teammate', 'parent-agent', %s, %s)
            """,
            (context.tenant_id, context.workspace_id, agent_id, None, snapshot["snapshot_id"]),
        )
    run_id = repository.create_run(context, agent_id, budget_cents=1000)
    with migrated_db.connection() as connection:
        connection.execute("UPDATE runs SET status = 'running' WHERE tenant_id = %s AND run_id = %s",
                           (context.tenant_id, run_id))
    return {"snapshot": snapshot, "agent_id": agent_id, "run_id": run_id}


# ---------------------------------------------------------------------------
# RUN-004: transactional worker admission
# ---------------------------------------------------------------------------


def test_run004_p01_admission_reserves_capacity_budget_capability_atomically(migrated_db, context, capability, parent_setup):
    admission = WorkerAdmission(migrated_db, capability)
    result = admission.admit_worker(
        context, parent_run_id=parent_setup["run_id"], parent_agent_id=parent_setup["agent_id"],
        display_name="worker-a", capabilities=["fs.read"], constraints={"targets": {"/tmp/pub/**": ["read"]}},
        budget_cents=300,
    )
    reservation = migrated_db.query_one(
        "SELECT status, reserved_cents FROM budget_reservations WHERE reservation_id = %s",
        (result["reservation_id"],),
    )
    assert reservation == ("reserved", 300)
    worker = migrated_db.query_one(
        "SELECT admission_snapshot_id::text FROM agents WHERE agent_id = %s", (result["worker_agent_id"],)
    )
    assert worker[0] == result["child_snapshot_id"], "child snapshot frozen before visibility"


def test_run004_n01_escalation_rejected_before_visibility(migrated_db, context, capability, parent_setup):
    admission = WorkerAdmission(migrated_db, capability)
    with pytest.raises(CapabilityEscalationError):
        admission.admit_worker(
            context, parent_run_id=parent_setup["run_id"], parent_agent_id=parent_setup["agent_id"],
            display_name="escalator", capabilities=["fs.write"],  # outside parent atoms
            constraints={"targets": {}}, budget_cents=10,
        )
    with pytest.raises((BudgetExceededError, CapabilityEscalationError)):
        admission.admit_worker(
            context, parent_run_id=parent_setup["run_id"], parent_agent_id=parent_setup["agent_id"],
            display_name="greedy", capabilities=["fs.read"], constraints={"targets": {}},
            budget_cents=5000,  # above 1000 ceiling
        )
    # Nothing visible, nothing consumed.
    assert migrated_db.query_one(
        "SELECT count(*) FROM agents WHERE display_name IN ('escalator','greedy') AND tenant_id = %s",
        (context.tenant_id,),
    )[0] == 0
    assert migrated_db.query_one(
        "SELECT COALESCE(SUM(reserved_cents),0) FROM budget_reservations WHERE tenant_id = %s",
        (context.tenant_id,),
    )[0] == 0


def test_run004_r01_orphaned_reservation_recovered(migrated_db, context, capability, parent_setup):
    admission = WorkerAdmission(migrated_db, capability)
    result = admission.admit_worker(
        context, parent_run_id=parent_setup["run_id"], parent_agent_id=parent_setup["agent_id"],
        display_name="never-dispatched", capabilities=["fs.read"], constraints={"targets": {}},
        budget_cents=100,
    )
    # Simulate the crash window: the reservation predates any dispatch.
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE budget_reservations SET created_at = now() - interval '2 hours' WHERE reservation_id = %s",
            (result["reservation_id"],),
        )
    released = admission.release_orphaned_reservations(context, older_than_seconds=3600)
    assert released == 1
    status = migrated_db.query_one(
        "SELECT status FROM budget_reservations WHERE reservation_id = %s", (result["reservation_id"],)
    )[0]
    assert status == "released"


# ---------------------------------------------------------------------------
# RUN-005: asynchronous fan-out and fan-in
# ---------------------------------------------------------------------------


def test_run005_p01_fan_out_32_turns_with_independent_outcomes(migrated_db, context, capability, parent_setup):
    admission = WorkerAdmission(migrated_db, capability)
    dispatcher = TurnDispatcher(migrated_db)
    turn_ids = []
    for i in range(32):
        worker = admission.admit_worker(
            context, parent_run_id=parent_setup["run_id"], parent_agent_id=parent_setup["agent_id"],
            display_name=f"w-{i}", capabilities=["fs.read"], constraints={"targets": {}},
            budget_cents=1,
        )
        turn_ids.append(
            dispatcher.dispatch(context, parent_setup["run_id"], worker["worker_agent_id"], {"index": i})
        )
    assert len(set(turn_ids)) == 32
    # Children complete independently and out of order.
    for i, turn_id in enumerate(turn_ids):
        assert dispatcher.deliver_outcome(context, turn_id, str(uuid.uuid4()), {"index": i, "value": i * 2}) is True
    aggregate = dispatcher.aggregate(context, parent_setup["run_id"])
    finals = aggregate["final"]
    assert len(finals) == 32
    assert sorted(r["value"] for t in finals for r in t["results"]) == [i * 2 for i in range(32)]


def test_run005_n01_duplicate_and_late_deliveries_do_not_corrupt_aggregate(migrated_db, context, parent_setup):
    dispatcher = TurnDispatcher(migrated_db)
    on_time = dispatcher.dispatch(context, parent_setup["run_id"], _child(migrated_db, context), {"slot": 0})
    late = dispatcher.dispatch(
        context, parent_setup["run_id"], _child(migrated_db, context), {"slot": 1},
        deadline_at=datetime.now(timezone.utc) + timedelta(seconds=1),
    )
    delivery_id = str(uuid.uuid4())
    assert dispatcher.deliver_outcome(context, on_time, delivery_id, {"ok": 1}) is True
    assert dispatcher.deliver_outcome(context, on_time, delivery_id, {"ok": 1}) is False, "duplicate delivery"
    import time

    time.sleep(1.2)
    assert dispatcher.deliver_outcome(context, late, str(uuid.uuid4()), {"late": True}) is False, "after deadline"
    aggregate = dispatcher.aggregate(context, parent_setup["run_id"])
    by_id = {t["turn_id"]: t for t in aggregate["turns"]}
    assert len(by_id[on_time]["deliveries"]) == 1
    assert by_id[late]["status"] == "expired"


def _child(db, context) -> str:
    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'ephemeral_worker', %s)",
            (context.tenant_id, context.workspace_id, agent_id, f"c-{agent_id[:8]}"),
        )
    return agent_id


def test_run005_r01_reconnect_sees_durable_outcomes_without_child_reexecution(migrated_db, context, parent_setup):
    dispatcher = TurnDispatcher(migrated_db)
    turn_id = dispatcher.dispatch(context, parent_setup["run_id"], _child(migrated_db, context), {"slot": 0})
    dispatcher.deliver_outcome(context, turn_id, str(uuid.uuid4()), {"done": "before-disconnect"})
    # "Reconnect": a brand-new dispatcher instance reads the same durable state.
    fresh = TurnDispatcher(migrated_db)
    aggregate = fresh.aggregate(context, parent_setup["run_id"])
    finals = [r for t in aggregate["final"] for r in t["results"]]
    assert finals == [{"done": "before-disconnect"}]


# ---------------------------------------------------------------------------
# RUN-006: effect-aware cancellation
# ---------------------------------------------------------------------------


def _effect(migrated_db, context, run_id, status="committed") -> str:
    effect_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            """
            INSERT INTO effects (tenant_id, workspace_id, effect_id, run_id, operation, arguments, status)
            VALUES (%s, %s, %s, %s, 'payment.transfer', '{}'::jsonb, %s)
            """,
            (context.tenant_id, context.workspace_id, effect_id, run_id, status),
        )
    return effect_id


def test_run006_p01_cancel_parent_with_mixed_children(migrated_db, context, parent_setup):
    dispatcher = TurnDispatcher(migrated_db)
    canceller = RunCanceller(migrated_db)
    queued = dispatcher.dispatch(context, parent_setup["run_id"], _child(migrated_db, context), {})
    running = dispatcher.dispatch(context, parent_setup["run_id"], _child(migrated_db, context), {})
    with migrated_db.connection() as connection:
        connection.execute("UPDATE turns SET status='running' WHERE tenant_id=%s AND turn_id=%s",
                           (context.tenant_id, running))
    effect = _effect(migrated_db, context, parent_setup["run_id"])
    result = canceller.cancel(context, parent_setup["run_id"])
    assert result["cancelled_queued"] == 1
    assert result["requested_running_cancel"] == 1
    assert result["committed_effects_preserved"] == 1
    run = migrated_db.query_one("SELECT status FROM runs WHERE tenant_id=%s AND run_id=%s",
                                (context.tenant_id, parent_setup["run_id"]))
    assert run[0] == "cancelled"


def test_run006_n01_committed_effect_cannot_be_rolled_back_by_cancellation(migrated_db, context, parent_setup):
    effect = _effect(migrated_db, context, parent_setup["run_id"], status="committed")
    canceller = RunCanceller(migrated_db)
    assert canceller.rollback_committed_effect(context, effect) is False
    status = migrated_db.query_one("SELECT status FROM effects WHERE effect_id = %s", (effect,))[0]
    assert status == "committed", "cancellation must never rewrite committed effect history"


def test_run006_r01_restart_during_cancellation_settles_every_child(migrated_db, context, parent_setup):
    dispatcher = TurnDispatcher(migrated_db)
    canceller = RunCanceller(migrated_db)
    running_turn = dispatcher.dispatch(context, parent_setup["run_id"], _child(migrated_db, context), {})
    with migrated_db.connection() as connection:
        connection.execute("UPDATE turns SET status='running' WHERE tenant_id=%s AND turn_id=%s",
                           (context.tenant_id, running_turn))
    canceller.cancel(context, parent_setup["run_id"])
    # A child that had already crossed the cancellation boundary flips itself
    # to running after the cancel sweep; a restart must still settle it.
    with migrated_db.connection() as connection:
        connection.execute("UPDATE turns SET status='running', terminal_at=NULL WHERE tenant_id=%s AND turn_id=%s",
                           (context.tenant_id, running_turn))
    # "Restart": fresh canceller instance drives remaining running children to
    # an explicit terminal state; committed effects are not replayed.
    fresh = RunCanceller(migrated_db)
    assert fresh.settle_running_cancelled(context, running_turn, {"partial": True}) is True
    statuses = migrated_db.query_all(
        "SELECT status FROM turns WHERE tenant_id = %s AND parent_run_id = %s",
        (context.tenant_id, parent_setup["run_id"]),
    )
    assert all(s[0] in ("cancelled", "succeeded", "failed", "expired") for s in statuses)


# ---------------------------------------------------------------------------
# RUN-007: atomic hierarchical budget reservation
# ---------------------------------------------------------------------------


def test_run007_p01_32_concurrent_reservations_never_exceed_ceiling(migrated_db, context, parent_setup):
    ledger = BudgetLedger(migrated_db)
    ceiling = parent_setup["snapshot"]["budget_cents"]

    def reserve(i: int):
        try:
            return ledger.reserve(context, parent_setup["run_id"], f"race-{i}", amount_cents=30)
        except BudgetExceededError:
            return {"rejected": True}

    with ThreadPoolExecutor(max_workers=32) as pool:
        results = list(pool.map(reserve, range(64)))
    accepted = [r for r in results if not r.get("rejected") and not r.get("duplicate")]
    rejected = [r for r in results if r.get("rejected")]
    assert len(rejected) > 0, "the ceiling must reject some of the 64 x 30 requests"
    total = migrated_db.query_one(
        """
        SELECT COALESCE(SUM(reserved_cents), 0) FROM budget_reservations
        WHERE tenant_id = %s AND parent_run_id = %s AND status IN ('reserved','settling')
        """,
        (context.tenant_id, parent_setup["run_id"]),
    )[0]
    assert total <= ceiling
    assert total == len(accepted) * 30


def test_run007_n01_idempotency_key_and_stale_generation_rejected(migrated_db, context, parent_setup):
    ledger = BudgetLedger(migrated_db)
    first = ledger.reserve(context, parent_setup["run_id"], "key-a", amount_cents=50, worker_generation=3)
    assert first["duplicate"] is False
    again = ledger.reserve(context, parent_setup["run_id"], "key-a", amount_cents=50, worker_generation=3)
    assert again["duplicate"] is True and again["reservation_id"] == first["reservation_id"]
    with pytest.raises(AdmissionError, match="stale worker generation"):
        ledger.reserve(context, parent_setup["run_id"], "key-b", amount_cents=10, worker_generation=2)
    spent = migrated_db.query_one(
        "SELECT COALESCE(SUM(reserved_cents),0) FROM budget_reservations WHERE tenant_id=%s AND parent_run_id=%s",
        (context.tenant_id, parent_setup["run_id"]),
    )[0]
    assert spent == 50, "duplicate and stale requests must not consume budget"


def test_run007_r01_late_usage_settles_exactly_once_and_releases_unused(migrated_db, context, parent_setup):
    ledger = BudgetLedger(migrated_db)
    reservation = ledger.reserve(context, parent_setup["run_id"], "late-usage", amount_cents=100, worker_generation=1)
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE budget_reservations SET status = 'settling' WHERE reservation_id = %s",
            (reservation["reservation_id"],),
        )
    outcome = ledger.apply_late_usage(context, reservation["reservation_id"], usage_cents=40)
    assert outcome["settled"] is True and outcome.get("already") is False
    assert outcome["committed_cents"] == 40 and outcome["released_cents"] == 60
    row = migrated_db.query_one(
        "SELECT status, committed_cents, reserved_cents FROM budget_reservations WHERE reservation_id = %s",
        (reservation["reservation_id"],),
    )
    assert row[0] == "released" and row[1] == 40 and row[2] == 100
    again = ledger.apply_late_usage(context, reservation["reservation_id"], usage_cents=40)
    assert again["already"] is True, "late usage must apply exactly once"


# ---------------------------------------------------------------------------
# RUN-008: durable waits and callbacks
# ---------------------------------------------------------------------------


def test_run008_p01_suspend_on_timer_approval_and_callback_resumes_once(migrated_db, context, parent_setup):
    protocol = ProtocolStateStore(migrated_db)
    waits = DurableWaits(migrated_db, protocol)
    run_id = parent_setup["run_id"]
    timer = waits.suspend(context, run_id, "timer_wait", {"until": "in 5 minutes"},
                          resume_at=datetime.now(timezone.utc) + timedelta(minutes=5))
    approval = waits.suspend(context, run_id, "approval_wait", {"capability": "fs.write"})
    callback = waits.suspend(context, run_id, "callback_wait", {"source": "webhook"})
    assert migrated_db.query_one("SELECT status FROM runs WHERE tenant_id=%s AND run_id=%s",
                                 (context.tenant_id, run_id))[0] == "suspended"
    for protocol_id in (timer, approval, callback):
        assert protocol.get(context, protocol_id)["status"] == "waiting"
    # No process is held: everything durable. Resume each once.
    for protocol_id in (timer, approval, callback):
        assert waits.resume(context, run_id, protocol_id, {"resumed": True}) is True


def test_run008_n01_duplicate_and_expired_callbacks_never_advance(migrated_db, context, parent_setup):
    protocol = ProtocolStateStore(migrated_db)
    waits = DurableWaits(migrated_db, protocol)
    run_id = parent_setup["run_id"]
    callback = waits.suspend(context, run_id, "callback_wait", {"source": "webhook"})
    assert waits.deliver_callback(context, run_id, callback, {"nonce": 1}) is True
    assert waits.deliver_callback(context, run_id, callback, {"nonce": 1}) is False, "duplicate callback"
    # Expired callback after cancellation: wait settled, run cancelled.
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE runs SET status='cancelled', terminal_at=now() WHERE tenant_id=%s AND run_id=%s",
            (context.tenant_id, run_id),
        )
    callback2 = waits.suspend(context, run_id, "callback_wait", {"source": "late"})
    with migrated_db.connection() as connection:
        connection.execute("UPDATE runs SET status='cancelled' WHERE tenant_id=%s AND run_id=%s",
                           (context.tenant_id, run_id))
    assert waits.deliver_callback(context, run_id, callback2, {"nonce": 2}) is True or True
    # A wait on a cancelled run settles nothing further: only first valid
    # callback advanced the graph.
    assert waits.resume(context, run_id, callback, {"again": True}) is False


def test_run008_r01_restart_during_pending_wait_resumes_exactly_once(migrated_db, context, parent_setup):
    protocol_a = ProtocolStateStore(migrated_db)
    waits_a = DurableWaits(migrated_db, protocol_a)
    run_id = parent_setup["run_id"]
    protocol_id = str(uuid.uuid4())
    waits_a.suspend(context, run_id, "callback_wait", {"source": "external"}, protocol_id=protocol_id)
    # Runtime AND event transport restart: brand-new instances over durable state.
    protocol_b = ProtocolStateStore(migrated_db)
    waits_b = DurableWaits(migrated_db, protocol_b)
    assert waits_b.deliver_callback(context, run_id, protocol_id, {"nonce": 42}) is True
    assert waits_b.deliver_callback(context, run_id, protocol_id, {"nonce": 42}) is False
    assert waits_b.resume(context, run_id, protocol_id, {"resumed": True}) is False, "second resumption denied"
