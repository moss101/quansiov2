"""Canonical RuntimeEvent append, replay and transactional outbox (DAT-003/DAT-004).

Events are represented by the generated canonical binding
``quansio_contracts.RuntimeEvent``; there is no competing DTO. Appends are
idempotent by event_id and strictly monotonic per run; replay reproduces
canonical order. The outbox row is prepared inside the same transaction as
the event, so a committed mutation is always announced.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio_contracts import RuntimeEvent as RuntimeEventContract


class EventAppendError(Exception):
    """Raised when an append would violate event-log invariants."""


def _s(value):
    return str(value) if isinstance(value, uuid.UUID) else value


class EventLog:
    """Owner: quansio-runtime. Table: runtime_events."""

    def __init__(self, database: PlatformDatabase, producer_id: str = "quansio-runtime"):
        self._db = database
        self._producer_id = producer_id

    def append(
        self,
        context: IdentityContext,
        run_id: str,
        event_type: str,
        payload: dict,
        sequence: int | None = None,
        event_id: str | None = None,
        execution_generation: int = 1,
        causal_parent_ids: tuple[str, ...] = (),
        outbox: bool = True,
        occurred_at: datetime | None = None,
    ) -> RuntimeEventContract:
        """Append one canonical event inside a single transaction.

        ``sequence=None`` allocates max+1 under a per-run advisory lock; an
        explicit ``sequence`` must be exactly next, otherwise the append
        fails without corrupting replay.
        """
        event_id = event_id or str(uuid.uuid4())
        with self._db.connection() as connection:
            try:
                with connection.transaction():
                    connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (run_id,))
                    if sequence is None:
                        current_max = connection.execute(
                            "SELECT COALESCE(MAX(sequence), 0) FROM runtime_events WHERE run_id = %s",
                            (run_id,),
                        ).fetchone()[0]
                        sequence = current_max + 1
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
                        # Announcement prepared before the mutation it
                        # announces; the deferred FK keeps the pair atomic.
                        connection.execute(
                            "INSERT INTO event_outbox (tenant_id, event_id) VALUES (%s, %s)",
                            (context.tenant_id, event_id),
                        )
                    committed_at = connection.execute(
                        """
                        INSERT INTO runtime_events
                            (tenant_id, workspace_id, run_id, sequence, event_id, schema_revision,
                             event_type, producer_id, execution_generation, causal_parent_ids,
                             payload, occurred_at)
                        VALUES (%s, %s, %s, %s, %s, '9.0.0', %s, %s, %s, %s, %s,
                                COALESCE(%s, now()))
                        RETURNING committed_at
                        """,
                        (
                            context.tenant_id,
                            context.workspace_id,
                            run_id,
                            sequence,
                            event_id,
                            event_type,
                            self._producer_id,
                            execution_generation,
                            list(causal_parent_ids),
                            Json(payload),
                            occurred_at,
                        ),
                    ).fetchone()[0]
            except psycopg.errors.UniqueViolation as error:
                raise EventAppendError(f"duplicate event identity: {error.diag.constraint_name}") from error
        return self._bind(
            tenant_id=context.tenant_id,
            workspace_id=context.workspace_id,
            run_id=run_id,
            sequence=sequence,
            event_id=event_id,
            event_type=event_type,
            producer_id=self._producer_id,
            execution_generation=execution_generation,
            causal_parent_ids=tuple(causal_parent_ids),
            payload=payload,
            occurred_at=occurred_at or committed_at,
            committed_at=committed_at,
        )

    @staticmethod
    def _bind(**fields) -> RuntimeEventContract:
        canonical = {
            "schema_revision": "9.0.0",
            "event_id": fields["event_id"],
            "tenant_id": fields["tenant_id"],
            "workspace_id": fields["workspace_id"],
            "run_id": fields["run_id"],
            "sequence": fields["sequence"],
            "producer_id": fields["producer_id"],
            "execution_generation": fields["execution_generation"],
            "event_type": fields["event_type"],
            "occurred_at": fields["occurred_at"],
            "committed_at": fields["committed_at"],
            "payload": fields["payload"],
            "causal_parent_ids": list(fields["causal_parent_ids"]),
        }
        canonical = EventLog._serialize(canonical)
        return RuntimeEventContract.from_dict(canonical)

    @staticmethod
    def _serialize(canonical: dict) -> dict:
        return {
            key: (value.isoformat() if isinstance(value, datetime) else value)
            for key, value in canonical.items()
        }

    def replay(self, tenant_id: str, run_id: str, after_sequence: int = 0) -> list[RuntimeEventContract]:
        """Replay canonical order strictly after a consumer cursor."""
        rows = self._db.query_all(
            """
            SELECT tenant_id, workspace_id, run_id, sequence, event_id, schema_revision,
                   event_type, producer_id, execution_generation, causal_parent_ids,
                   payload, occurred_at, committed_at
            FROM runtime_events
            WHERE tenant_id = %s AND run_id = %s AND sequence > %s
            ORDER BY sequence ASC
            """,
            (tenant_id, run_id, after_sequence),
        )
        events = []
        for r in rows:
            events.append(
                self._bind(
                    tenant_id=_s(r[0]),
                    workspace_id=_s(r[1]),
                    run_id=_s(r[2]),
                    sequence=r[3],
                    event_id=_s(r[4]),
                    event_type=r[6],
                    producer_id=r[7],
                    execution_generation=r[8],
                    causal_parent_ids=tuple(_s(p) for p in (r[9] or ())),
                    payload=r[10],
                    occurred_at=r[11],
                    committed_at=r[12],
                )
            )
        return events

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
