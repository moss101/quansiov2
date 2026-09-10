"""Canonical RuntimeEvent append, replay and transactional outbox (DAT-003/DAT-004).

The event log is the durable event transport: per-run canonical sequences,
stable event ids, causal parents, producer identity, execution generation
and committed timestamps. Appends are idempotent by event_id and strictly
monotonic per run; replay reproduces the canonical order. The outbox row is
written inside the same transaction as the event, so a committed state
mutation is always accompanied by its announcement.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

import psycopg
from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


def _s(value) -> str:
    """Normalize database UUID objects to canonical strings."""
    return str(value) if isinstance(value, uuid.UUID) else value


@dataclass(frozen=True)
class RuntimeEvent:
    tenant_id: str
    workspace_id: str
    run_id: str
    sequence: int
    event_id: str
    event_type: str
    producer: str
    generation: int
    causal_parents: tuple[str, ...]
    payload: dict
    committed_at: datetime


class EventAppendError(Exception):
    """Raised when an append would violate event-log invariants."""


class EventLog:
    """Owner: quansio-runtime. Table: runtime_events."""

    def __init__(self, database: PlatformDatabase, producer: str = "quansio-runtime"):
        self._db = database
        self._producer = producer

    def append(
        self,
        context: IdentityContext,
        run_id: str,
        event_type: str,
        payload: dict,
        sequence: int | None = None,
        event_id: str | None = None,
        generation: int = 0,
        causal_parents: tuple[str, ...] = (),
        outbox: bool = True,
    ) -> RuntimeEvent:
        """Append one event inside a single transaction.

        ``sequence=None`` allocates max+1 under a per-run advisory lock;
        an explicit ``sequence`` must be exactly next, otherwise the append
        fails without corrupting replay.
        """
        event_id = event_id or str(uuid.uuid4())
        with self._db.connection() as connection:
            try:
                with connection.transaction():
                    connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (run_id,))
                    if sequence is None:
                        row = connection.execute(
                            "SELECT COALESCE(MAX(sequence), 0) FROM runtime_events WHERE run_id = %s",
                            (run_id,),
                        ).fetchone()
                        sequence = row[0] + 1
                    else:
                        current_max = connection.execute(
                            "SELECT COALESCE(MAX(sequence), 0) FROM runtime_events WHERE run_id = %s",
                            (run_id,),
                        ).fetchone()[0]
                        if sequence <= 0 or sequence > current_max + 1:
                            raise EventAppendError(
                                f"non-monotonic sequence {sequence} for run {run_id} (next is {current_max + 1})"
                            )
                    if outbox:
                        # The announcement is prepared before the mutation it
                        # announces; a deferred FK keeps the pair atomic, so a
                        # rollback after this point leaves no transport trace.
                        connection.execute(
                            "INSERT INTO event_outbox (tenant_id, event_id) VALUES (%s, %s)",
                            (context.tenant_id, event_id),
                        )
                    row = connection.execute(
                        """
                        INSERT INTO runtime_events
                            (tenant_id, workspace_id, run_id, sequence, event_id, event_type,
                             producer, generation, causal_parents, payload)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING committed_at
                        """,
                        (
                            context.tenant_id,
                            context.workspace_id,
                            run_id,
                            sequence,
                            event_id,
                            event_type,
                            self._producer,
                            generation,
                            list(causal_parents),
                            Json(payload),
                        ),
                    ).fetchone()
            except psycopg.errors.UniqueViolation as error:
                raise EventAppendError(f"duplicate event identity: {error.diag.constraint_name}") from error
        return RuntimeEvent(
            tenant_id=context.tenant_id,
            workspace_id=context.workspace_id,
            run_id=run_id,
            sequence=sequence,
            event_id=event_id,
            event_type=event_type,
            producer=self._producer,
            generation=generation,
            causal_parents=tuple(causal_parents),
            payload=payload,
            committed_at=row[0],
        )

    def replay(self, tenant_id: str, run_id: str, after_sequence: int = 0) -> list[RuntimeEvent]:
        """Replay canonical order strictly after a consumer cursor."""
        rows = self._db.query_all(
            """
            SELECT tenant_id, workspace_id, run_id, sequence, event_id, event_type,
                   producer, generation, causal_parents, payload, committed_at
            FROM runtime_events
            WHERE tenant_id = %s AND run_id = %s AND sequence > %s
            ORDER BY sequence ASC
            """,
            (tenant_id, run_id, after_sequence),
        )
        return [
            RuntimeEvent(
                tenant_id=_s(r[0]),
                workspace_id=_s(r[1]),
                run_id=_s(r[2]),
                sequence=r[3],
                event_id=_s(r[4]),
                event_type=r[5],
                producer=r[6],
                generation=r[7],
                causal_parents=tuple(_s(p) for p in (r[8] or ())),
                payload=r[9],
                committed_at=r[10],
            )
            for r in rows
        ]

    def publish_pending_outbox(self, limit: int = 100, crash_after_publish: bool = False) -> list[str]:
        """Two-phase outbox delivery.

        Phase 1 marks the delivery attempt and publishes onto the durable
        transport (``delivered_events``), deduplicated by event identity.
        Phase 2 acknowledges the outbox row. A crash between the phases is
        safe: restart redelivery inserts conflict on event identity and the
        consumer sees the event exactly once.

        ``crash_after_publish`` simulates the crash window for recovery
        qualification: phase 2 is skipped for the batch.
        """
        published = []
        with self._db.connection() as connection:
            with connection.transaction():
                rows = connection.execute(
                    """
                    SELECT o.outbox_id, o.tenant_id, o.event_id FROM event_outbox o
                    WHERE o.published_at IS NULL
                    ORDER BY o.outbox_id
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (limit,),
                ).fetchall()
                for outbox_id, tenant_id, event_id in rows:
                    connection.execute(
                        "UPDATE event_outbox SET attempts = attempts + 1 WHERE outbox_id = %s",
                        (outbox_id,),
                    )
                    # Transport publish: deduplicated by event identity.
                    connection.execute(
                        """
                        INSERT INTO delivered_events (tenant_id, event_id)
                        VALUES (%s, %s)
                        ON CONFLICT (tenant_id, event_id) DO NOTHING
                        """,
                        (tenant_id, event_id),
                    )
                    published.append(_s(event_id))
        if crash_after_publish:
            return published  # phase 2 never ran
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute(
                    """
                    UPDATE event_outbox o SET published_at = now()
                    WHERE o.published_at IS NULL
                      AND (o.tenant_id, o.event_id) IN (
                        SELECT tenant_id, event_id FROM delivered_events
                      )
                    """
                )
        return published

    def advance_cursor(self, tenant_id: str, consumer: str, run_id: str, last_sequence: int) -> None:
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO event_cursors (tenant_id, consumer, run_id, last_sequence, updated_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (tenant_id, consumer, run_id)
                DO UPDATE SET last_sequence = EXCLUDED.last_sequence, updated_at = now()
                """,
                (tenant_id, consumer, run_id, last_sequence),
            )

    def cursor(self, tenant_id: str, consumer: str, run_id: str) -> int:
        row = self._db.query_one(
            "SELECT last_sequence FROM event_cursors WHERE tenant_id = %s AND consumer = %s AND run_id = %s",
            (tenant_id, consumer, run_id),
        )
        return row[0] if row else 0
