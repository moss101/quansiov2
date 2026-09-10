"""DAT-003/DAT-004 acceptance tests: RuntimeEvent append/replay + outbox.

Positive: events append with stable identity, canonical per-run sequence,
causal parents, producer, generation and commit timestamp; replay reproduces
canonical order. Negative: duplicate event_id or non-monotonic sequence fails
without corrupting replay. Recovery: a committed event not yet delivered is
delivered exactly once to a resuming consumer cursor without re-execution.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.runtime.events import EventAppendError, EventLog  # noqa: E402


@pytest.fixture()
def context(workspace_setup) -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup["workspace_a"],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )


@pytest.fixture()
def log(migrated_db) -> EventLog:
    return EventLog(migrated_db)


def _run(context: IdentityContext) -> str:
    return str(uuid.uuid4())


def test_dat003_p01_append_and_canonical_replay(log, context):
    run_id = _run(context)
    parent = None
    appended = []
    for i in range(5):
        event = log.append(
            context,
            run_id,
            f"stage.{i}",
            {"step": i, "of": "dat003"},
            causal_parents=(parent,) if parent else (),
            generation=1,
        )
        appended.append(event)
        parent = event.event_id

    assert [e.sequence for e in appended] == [1, 2, 3, 4, 5]
    assert len({e.event_id for e in appended}) == 5
    assert appended[3].causal_parents == (appended[2].event_id,)
    assert all(e.producer == "quansio-runtime" for e in appended)
    assert all(e.generation == 1 for e in appended)
    assert all(e.committed_at is not None for e in appended)
    assert all(e.tenant_id == context.tenant_id and e.workspace_id == context.workspace_id for e in appended)

    replayed = log.replay(context.tenant_id, run_id)
    assert [e.sequence for e in replayed] == [1, 2, 3, 4, 5]
    assert [e.event_id for e in replayed] == [e.event_id for e in appended]


def test_dat003_n01_duplicate_event_id_fails_without_corrupting_replay(log, context):
    run_id = _run(context)
    first = log.append(context, run_id, "a.first", {"n": 1})
    with pytest.raises(EventAppendError, match="duplicate event identity"):
        log.append(context, run_id, "a.dupe", {"n": 2}, event_id=first.event_id)
    replayed = log.replay(context.tenant_id, run_id)
    assert [e.sequence for e in replayed] == [1]
    assert replayed[0].payload == {"n": 1}


def test_dat003_n01_non_monotonic_sequence_fails(log, context):
    run_id = _run(context)
    log.append(context, run_id, "b.first", {"n": 1})
    with pytest.raises(EventAppendError, match="non-monotonic"):
        log.append(context, run_id, "b.gap", {"n": 9}, sequence=7)
    # next valid explicit sequence is accepted, a repeat is rejected
    log.append(context, run_id, "b.second", {"n": 2}, sequence=2)
    with pytest.raises(EventAppendError):
        log.append(context, run_id, "b.repeat", {"n": 3}, sequence=2)
    replayed = log.replay(context.tenant_id, run_id)
    assert [(e.sequence, e.event_type) for e in replayed] == [(1, "b.first"), (2, "b.second")]


def test_dat004_r01_committed_event_delivered_exactly_once_after_reconnect(log, context):
    run_id = _run(context)
    committed = log.append(context, run_id, "c.work", {"action": "committed"})
    # Simulate crash before delivery: no outbox publication, no cursor movement.
    cursor = log.cursor(context.tenant_id, "qual-projection", run_id)
    assert cursor == 0
    # Reconnect from prior cursor: the committed event is projected exactly once.
    delivered = [e for e in log.replay(context.tenant_id, run_id, after_sequence=cursor)]
    assert len(delivered) == 1
    assert delivered[0].event_id == committed.event_id
    log.advance_cursor(context.tenant_id, "qual-projection", run_id, delivered[-1].sequence)
    # Second delivery round after cursor advance delivers nothing (no re-execution).
    assert log.replay(context.tenant_id, run_id, after_sequence=log.cursor(context.tenant_id, "qual-projection", run_id)) == []


def test_dat004_p01_outbox_marks_exactly_the_committed_delivery(log, context):
    run_id = _run(context)
    event = log.append(context, run_id, "d.outbox", {"n": 1})
    pending = log.publish_pending_outbox()
    assert event.event_id in pending, "committed event must be announced by the outbox"
    state = migrated_outbox_state(log, context, event.event_id)
    assert state is not None and state["attempts"] == 1 and state["published_at"] is not None
    assert event.event_id not in log.publish_pending_outbox(), "published outbox rows must not redeliver"


def migrated_outbox_state(log: EventLog, context: IdentityContext, event_id: str):
    row = log._db.query_one(
        "SELECT attempts, published_at FROM event_outbox WHERE event_id = %s",
        (event_id,),
    )
    return {"attempts": row[0], "published_at": row[1]} if row else None


def test_dat004_n01_rollback_after_outbox_preparation_leaves_no_transport_trace(log, context):
    run_id = _run(context)
    committed = log.append(context, run_id, "e.first", {"n": 1})
    # Duplicate event identity fails at the event insert, after the outbox
    # announcement row was already prepared inside the same transaction.
    with pytest.raises(EventAppendError):
        log.append(context, run_id, "e.dupe", {"n": 2}, event_id=committed.event_id)
    # The rolled-back mutation has no outbox row and no transport delivery.
    outbox_rows = log._db.query_one(
        "SELECT count(*) FROM event_outbox WHERE event_id = %s", (committed.event_id,)
    )[0]
    assert outbox_rows == 1, "only the committed append may keep its announcement"
    transport = log._db.query_one(
        "SELECT count(*) FROM delivered_events WHERE event_id = %s",
        (committed.event_id,),
    )[0]
    assert transport == 0, "nothing may be published before delivery is performed"
    replayed = log.replay(context.tenant_id, run_id)
    assert [e.sequence for e in replayed] == [1]


def test_dat004_r01_crash_between_publish_and_ack_redelivers_deduplicated(log, context):
    run_id = _run(context)
    event = log.append(context, run_id, "f.crash", {"n": 1})
    # Publisher crash after transport publish, before outbox acknowledgement.
    published = log.publish_pending_outbox(crash_after_publish=True)
    assert event.event_id in published
    # Restart: redelivery of the still-unacknowledged row is deduplicated by
    # event identity on the durable transport.
    republished = log.publish_pending_outbox()
    assert republished.count(event.event_id) == 1, "redelivery must not duplicate the event"
    deliveries = log._db.query_one(
        "SELECT count(*) FROM delivered_events WHERE tenant_id = %s AND event_id = %s",
        (context.tenant_id, event.event_id),
    )[0]
    assert deliveries == 1
    assert log._db.query_one(
        "SELECT published_at IS NOT NULL FROM event_outbox WHERE event_id = %s",
        (event.event_id,),
    )[0] is True
