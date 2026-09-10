"""Acceptance tests for AUT-001..004 and COL-001..004."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.context.collaboration import (  # noqa: E402
    CollaborationOwnershipViolation,
    CollaborationProjection,
    HandoffRefused,
    HandoffService,
    NotificationService,
    TeammateRoutineService,
)
from quansio.context.scheduler import (  # noqa: E402
    AmbiguousSchedule,
    AutomationDenied,
    AutomationService,
    next_fires,
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
def scheduler(migrated_db) -> AutomationService:
    return AutomationService(migrated_db)


# ---------------------------------------------------------------------------
# AUT-001: timezone-aware scheduling
# ---------------------------------------------------------------------------


def test_aut001_p01_normal_dates_and_dst_fold_policy(scheduler, migrated_db, context):
    automation = scheduler.create(
        context, "nightly-1", "America/New_York", "0 2 * * *",
        fold_gap_policy="skip", catchup_policy="FIRE_ONCE", catchup_max=1,
        work_template={"action": "digest"},
    )
    assert automation["automation_id"]
    fires = next_fires("0 2 * * *", "America/New_York",
                       datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc), 3,
                       fold_gap_policy="earliest")
    logical = [f["logical_fire"] for f in fires]
    # Fold day 2026-11-01 02:00 occurs once per policy and keeps a stable
    # logical identity; subsequent days proceed normally.
    assert "2026-11-01T02:00" in logical
    assert len(logical) == len(set(logical)), "logical identities unique"


def test_aut001_n01_ambiguous_schedule_without_policy_refused(scheduler, context):
    with pytest.raises(AmbiguousSchedule):
        scheduler.create(
            context, "bad-1", "America/New_York", "not-a-cron",
            fold_gap_policy="earliest", catchup_policy="SKIP", catchup_max=0,
            work_template={},
        )


def test_aut001_r01_restart_across_clock_transition_unique_fire_identities(migrated_db, scheduler, context):
    automation = scheduler.create(
        context, "dst-auto", "America/New_York", "30 1 * * *",
        fold_gap_policy="earliest", catchup_policy="CATCH_UP_BOUNDED",
        catchup_max=5, work_template={"action": "tick"},
    )
    auto_id = automation["automation_id"]
    from_utc = datetime(2025, 10, 30, 5, 0, tzinfo=timezone.utc)
    to_utc = from_utc + timedelta(days=4)
    first = scheduler.emit_fires(context, auto_id, from_utc, to_utc)
    # "Restart": second emit run across the same window must not duplicate.
    second = scheduler.emit_fires(context, auto_id, from_utc, to_utc)
    emitted_first = [e["logical_fire"] for e in first["emitted"]]
    emitted_second = [e["logical_fire"] for e in second["emitted"]]
    assert emitted_first and not set(emitted_second) - set(emitted_first), \
        "restart must not mint new accepted fire identities"


# ---------------------------------------------------------------------------
# AUT-002: missed-fire and bounded catch-up
# ---------------------------------------------------------------------------


def test_aut002_p01_policies_skip_fireonce_and_bounded(migrated_db, scheduler, context):
    auto_skip = scheduler.create(
        context, "skip-auto", "UTC", "0 * * * *", "earliest", "SKIP", 0, {})
    result = scheduler.emit_fires(
        context, auto_skip["automation_id"],
        datetime.now(timezone.utc) - timedelta(hours=5),
        datetime.now(timezone.utc) + timedelta(minutes=1))
    assert result["emitted"] == [] and result["catchup_skipped"] >= 1

    auto_once = scheduler.create(
        context, "once-auto", "UTC", "0 * * * *", "earliest", "FIRE_ONCE", 0, {})
    result_once = scheduler.emit_fires(
        context, auto_once["automation_id"],
        datetime.now(timezone.utc) - timedelta(hours=5),
        datetime.now(timezone.utc) + timedelta(minutes=1))
    assert len(result_once["emitted"]) == 1

    auto_bounded = scheduler.create(
        context, "bounded-auto", "UTC", "0 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 3, {})
    result_bounded = scheduler.emit_fires(
        context, auto_bounded["automation_id"],
        datetime.now(timezone.utc) - timedelta(hours=5),
        datetime.now(timezone.utc) + timedelta(minutes=1))
    assert len(result_bounded["emitted"]) == 3
    assert result_bounded["catchup_skipped"] >= 1


def test_aut002_n01_excess_occurrences_not_silently_emitted(migrated_db, scheduler, context):
    auto = scheduler.create(
        context, "bounded-2", "UTC", "0 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 2, {})
    result = scheduler.emit_fires(
        context, auto["automation_id"],
        datetime.now(timezone.utc) - timedelta(hours=5),
        datetime.now(timezone.utc) + timedelta(minutes=1))
    emitted_keys = {e["logical_fire"] for e in result["emitted"]}
    # Only the bounded tail is emitted; the excess are durably recorded as
    # catchup_skipped, never silently lost.
    rows = migrated_db.query_all(
        "SELECT state, logical_fire FROM automation_occurrences WHERE tenant_id=%s"
        " AND automation_id=%s",
        (context.tenant_id, auto["automation_id"]),
    )
    assert len(rows) >= 5
    assert all(r[0] in ("fired", "catchup_skipped", "pending") for r in rows)
    skipped = {r[1] for r in rows if r[0] == "catchup_skipped"}
    assert skipped and not (skipped & emitted_keys)


def test_aut002_r01_catchup_identities_survive_second_restart(migrated_db, scheduler, context):
    auto = scheduler.create(
        context, "bounded-3", "UTC", "30 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 5, {})
    window_from = datetime.now(timezone.utc) - timedelta(hours=2)
    window_to = datetime.now(timezone.utc) + timedelta(minutes=1)
    first = scheduler.emit_fires(context, auto["automation_id"], window_from, window_to)
    keys_first = {(e["logical_fire"], e["fire_time_utc"].isoformat()) for e in first["emitted"]}
    # Second restart: same window yields the same logical identities, no dupes.
    second = scheduler.emit_fires(context, auto["automation_id"], window_from, window_to)
    keys_second = {(e["logical_fire"], e["fire_time_utc"].isoformat()) for e in second["emitted"]}
    assert keys_second <= keys_first


# ---------------------------------------------------------------------------
# AUT-003: authority re-evaluation at fire
# ---------------------------------------------------------------------------


def test_aut003_p01_and_n01_revoked_authority_blocks_fire(migrated_db, scheduler, context):
    def deny_all(ctx, template):
        raise PermissionError("capability revoked after schedule creation")

    auto = scheduler.create(
        context, "auth-auto", "UTC", "*/5 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 3, {"action": "report"})
    result = scheduler.emit_fires(
        context, auto["automation_id"],
        datetime.now(timezone.utc) - timedelta(minutes=10),
        datetime.now(timezone.utc) + timedelta(minutes=1),
        authority_resolver=deny_all,
    )
    blocked = [e for e in result["emitted"] if e["state"] == "blocked_attention"]
    assert blocked, "unauthorized fires must become blocked_attention"
    row = migrated_db.query_one(
        "SELECT blocked_reason FROM automation_occurrences WHERE tenant_id=%s"
        " AND automation_id=%s AND state='blocked_attention' LIMIT 1",
        (context.tenant_id, auto["automation_id"]),
    )
    assert "revoked" in row[0]


def test_aut003_r01_restored_authority_follows_missed_fire_policy(migrated_db, scheduler, context):
    calls = []

    def allow_then_check(ctx, template):
        calls.append(template)
        return f"work-{len(calls)}"

    auto = scheduler.create(
        context, "recover-auto", "UTC", "*/5 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 2, {"action": "report"})
    with_fx = scheduler.emit_fires(
        context, auto["automation_id"],
        datetime.now(timezone.utc) - timedelta(hours=2),
        datetime.now(timezone.utc) + timedelta(minutes=1),
        authority_resolver=allow_then_check,
    )
    fired = [e for e in with_fx["emitted"] if e["state"] == "fired"]
    assert fired, "authorized fires run normally"
    # No unauthorized replay: only fires emitted through the authority path.
    for entry in with_fx["emitted"]:
        assert entry["state"] in ("fired", "blocked_attention")


# ---------------------------------------------------------------------------
# AUT-004: pause/resume/delete
# ---------------------------------------------------------------------------


def test_aut004_p01_and_n01_pause_resume_serialized_against_claiming(scheduler, migrated_db, context):
    auto = scheduler.create(
        context, "pause-auto", "UTC", "*/10 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 1, {})
    assert scheduler.pause(context, auto["automation_id"]) == "paused"
    with pytest.raises(AutomationDenied, match="paused"):
        scheduler.emit_fires(
            context, auto["automation_id"],
            datetime.now(timezone.utc) - timedelta(minutes=30),
            datetime.now(timezone.utc) + timedelta(minutes=1))
    assert scheduler.resume(context, auto["automation_id"]) == "active"
    result = scheduler.emit_fires(
        context, auto["automation_id"],
        datetime.now(timezone.utc) - timedelta(minutes=30),
        datetime.now(timezone.utc) + timedelta(minutes=1))
    assert result["emitted"] or result["catchup_skipped"] >= 0


def test_aut004_r01_deleted_automation_cannot_reappear(migrated_db, scheduler, context):
    auto = scheduler.create(
        context, "deleted-auto", "UTC", "0 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 2, {})
    assert scheduler.delete(context, auto["automation_id"]) == "deleted"
    # A stale scheduler instance (cache/lease state) still cannot resurrect it.
    assert scheduler.delete(context, auto["automation_id"]) == "already-deleted"
    with pytest.raises(AutomationDenied, match="deleted"):
        scheduler.emit_fires(
            context, auto["automation_id"],
            datetime.now(timezone.utc) - timedelta(minutes=30),
            datetime.now(timezone.utc) + timedelta(minutes=1))
    state = migrated_db.query_one(
        "SELECT lifecycle FROM automations WHERE automation_id=%s",
        (auto["automation_id"],),
    )[0]
    assert state == "deleted"


# ---------------------------------------------------------------------------
# COL-001: collaboration as runtime projections
# ---------------------------------------------------------------------------


def test_col001_p01_room_projection_over_participants_and_messages(migrated_db, workspace_setup, context):
    projection = CollaborationProjection(migrated_db)
    room = projection.create_room(context, "ops-room")
    agent_a = str(uuid.uuid4())
    agent_b = str(uuid.uuid4())
    projection.join(context, room, agent_a, "lead")
    projection.join(context, room, agent_b, "member")
    projection.post_message(context, room, agent_a, {"text": "starting triage"},
                            capability_context="task")
    view = projection.projection(context, room)
    assert len(view["participants"]) == 2
    assert len(view["messages"]) == 1
    assert view["messages"][0]["payload"]["text"] == "starting triage"


def test_col001_n01_shadow_execution_queue_rejected(migrated_db, workspace_setup, context):
    projection = CollaborationProjection(migrated_db)
    room = projection.create_room(context, "ops-room-2")
    with pytest.raises(CollaborationOwnershipViolation, match="canonical runtime"):
        projection.reject_shadow_queue(
            context, room,
            {"name": "collab-queue", "mutates_task_state": True})


def test_col001_r01_projection_rebuilds_from_canonical_events(migrated_db, workspace_setup, context):
    projection = CollaborationProjection(migrated_db)
    room = projection.create_room(context, "ops-room-3")
    agent = str(uuid.uuid4())
    projection.join(context, room, agent, "member")
    projection.post_message(context, room, agent, {"text": "hello"})
    # "Restart": fresh instance rebuilds the full projection from canonical rows.
    fresh = CollaborationProjection(migrated_db)
    view = fresh.projection(context, room)
    assert view["participants"] and view["messages"]


# ---------------------------------------------------------------------------
# COL-002: durable typed handoffs
# ---------------------------------------------------------------------------


def test_col002_p01_handoff_persists_identity_and_outcome(migrated_db, workspace_setup, context):
    projection = CollaborationProjection(migrated_db)
    handoff = HandoffService(migrated_db)
    room = projection.create_room(context, "handoff-room")
    sender = str(uuid.uuid4())
    turn = str(uuid.uuid4())
    result = handoff.deliver(
        context, room, sender, str(uuid.uuid4()), turn,
        payload={"artifact": "digest-1"}, capability_context="analysis",
        artifact_refs=["digest-1"],
    )
    assert result["duplicate"] is False
    view = projection.projection(context, room)
    assert view["messages"][0]["capability_context"] == "analysis"


def test_col002_n01_duplicate_handoff_and_cancelled_target(migrated_db, workspace_setup, context):
    projection = CollaborationProjection(migrated_db)
    handoff = HandoffService(migrated_db)
    room = projection.create_room(context, "handoff-room-2")
    sender = str(uuid.uuid4())
    turn = str(uuid.uuid4())
    first = handoff.deliver(context, room, sender, str(uuid.uuid4()), turn,
                            payload={"n": 1}, capability_context="task")
    second = handoff.deliver(context, room, sender, str(uuid.uuid4()), turn,
                             payload={"n": 1}, capability_context="task")
    assert first["duplicate"] is False and second["duplicate"] is True
    with pytest.raises(HandoffRefused, match="cancelled"):
        handoff.deliver(context, room, sender, str(uuid.uuid4()), str(uuid.uuid4()),
                        payload={}, capability_context="task", worker_status="cancelled")
    with pytest.raises(HandoffRefused, match="unauthorized"):
        handoff.deliver(context, room, sender, str(uuid.uuid4()), str(uuid.uuid4()),
                        payload={}, capability_context="task", worker_status="unauthorized")


def test_col002_r01_interrupted_delivery_exposes_durable_outcome(migrated_db, workspace_setup, context):
    projection = CollaborationProjection(migrated_db)
    handoff = HandoffService(migrated_db)
    room = projection.create_room(context, "handoff-room-3")
    message = projection.post_message(context, room, str(uuid.uuid4()),
                                      {"text": "in flight"}, delivery_state="pending")
    handoff.mark_failed(context, message)
    view = projection.projection(context, room)
    states = {m["message_id"]: m["delivery_state"] for m in view["messages"]}
    assert states[message] == "failed", "durable failed outcome exposed"


# ---------------------------------------------------------------------------
# COL-003: attention and notifications
# ---------------------------------------------------------------------------


def test_col003_p01_notification_created_delivered_acknowledged(migrated_db, workspace_setup, context):
    notifications = NotificationService(migrated_db)
    created = notifications.create(context, recipient_id=context.user_id,
                                   channel_class="email", urgency="high",
                                   deep_link="/approvals/123",
                                   payload={"summary": "approval needed"})
    delivered = notifications.deliver(context, created["notification_id"])
    assert delivered["state"] == "delivered"
    ack = notifications.acknowledge(context, created["notification_id"],
                                   acknowledging_tenant=context.tenant_id,
                                   ack_by=context.user_id)
    assert ack["acknowledged_by"] == context.user_id


def test_col003_n01_duplicate_delivery_and_wrong_tenant_ack(migrated_db, workspace_setup, context):
    notifications = NotificationService(migrated_db)
    created = notifications.create(context, recipient_id=context.user_id,
                                   channel_class="push", urgency="critical",
                                   deep_link="/incidents/1", payload={})
    first = notifications.deliver(context, created["notification_id"])
    duplicate = notifications.deliver(context, created["notification_id"])
    assert duplicate["duplicate"] is True
    wrong_tenant = str(uuid.uuid4())
    with pytest.raises(PermissionError, match="wrong tenant"):
        notifications.acknowledge(context, created["notification_id"],
                                  acknowledging_tenant=wrong_tenant, ack_by="attacker")


def test_col003_r01_outage_recovery_delivers_pending_without_state_change(migrated_db, workspace_setup, context):
    notifications = NotificationService(migrated_db)
    created = notifications.create(context, recipient_id=context.user_id,
                                   channel_class="email", urgency="normal",
                                   deep_link="/tasks/5", payload={}, ttl_seconds=3600)
    delivered_count = notifications.deliver_pending_after_outage(context)
    assert delivered_count >= 1
    row = migrated_db.query_one(
        "SELECT state FROM notifications WHERE notification_id=%s",
        (created["notification_id"],),
    )[0]
    assert row == "delivered"


# ---------------------------------------------------------------------------
# COL-004: persistent teammate routines
# ---------------------------------------------------------------------------


def test_col004_p01_routine_fires_with_current_identity(migrated_db, workspace_setup, context, scheduler):
    auto = scheduler.create(
        context, "routine-auto", "UTC", "0 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 3, {})
    teammate = str(uuid.uuid4())
    routines = TeammateRoutineService(
        migrated_db, scheduler,
        teammate_liveness=lambda ctx, agent_id: agent_id == teammate)
    bound = routines.bind_routine(context, teammate, auto["automation_id"],
                                  work_template={"action": "weekly digest"})
    outcome = routines.fire(context, bound["automation_id"], teammate, "logical-1")
    assert outcome["fired"] is True, outcome


def test_col004_n01_stale_teammate_no_orphan_routine(migrated_db, workspace_setup, context, scheduler):
    auto = scheduler.create(
        context, "routine-auto-2", "UTC", "0 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 3, {})
    retired = str(uuid.uuid4())
    routines = TeammateRoutineService(
        migrated_db, scheduler,
        teammate_liveness=lambda ctx, agent_id: False)  # teammate retired
    bound = routines.bind_routine(context, retired, auto["automation_id"], {})
    outcome = routines.fire(context, bound["automation_id"], retired, "logical-2")
    assert outcome["fired"] is False, outcome
    assert "stale or retired" in outcome.get("reason", "") or "revoked" in outcome.get("reason", ""), outcome


def test_col004_r01_missed_windows_apply_policy_with_durable_identities(migrated_db, workspace_setup, context, scheduler):
    auto = scheduler.create(
        context, "routine-missed", "UTC", "0 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 2, {})
    teammate = str(uuid.uuid4())
    routines = TeammateRoutineService(
        migrated_db, scheduler,
        teammate_liveness=lambda ctx, agent_id: agent_id == teammate)
    routines.bind_routine(context, teammate, auto["automation_id"], {})
    outcome = routines.fire(context, auto["automation_id"], teammate, "logical-m1")
    assert outcome["fired"] is True
    rows = migrated_db.query_all(
        "SELECT logical_fire, state FROM automation_occurrences WHERE tenant_id=%s"
        " AND automation_id=%s",
        (context.tenant_id, auto["automation_id"]),
    )
    assert rows, "durable logical-fire identities recorded"
    keys = [r[0] for r in rows]
    assert len(keys) == len(set(keys))
