"""Transaction worker admission, fan-out/fan-in, cancellation and budgets
(RUN-004..RUN-008). Owner: quansio-runtime.

- ``admit_worker`` atomically reserves capacity, budget and a strict-subset
  child capability snapshot before the worker dispatch becomes visible.
- ``TurnDispatcher`` persists child turn dispatches and incremental outcomes
  independently; aggregation reads durable state, deduplicates deliveries and
  enforces deadlines.
- ``cancel_run`` drives every child to an explicit terminal/cancellation
  state while committed external effects are never rolled back by
  cancellation alone.
- ``BudgetLedger`` serializes reservations against the parent ceiling under
  a per-run advisory lock; idempotency keys and parent generations prevent
  duplicate spend and stale admission.
- Durable waits resume exactly once from protocol state identity.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.types.json import Json

from quansio.control.capability import CapabilityEscalationError, CapabilityService
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio.runtime.protocol import ProtocolStateStore


class AdmissionError(Exception):
    """Admission refused before the worker becomes visible."""


class BudgetExceededError(AdmissionError):
    """The parent run's budget ceiling refused the reservation."""


class WorkerAdmission:
    """RUN-004: capacity + budget + capability reserved atomically."""

    def __init__(self, database: PlatformDatabase, capabilities: CapabilityService):
        self._db = database
        self._capabilities = capabilities

    def admit_worker(
        self,
        context: IdentityContext,
        parent_run_id: str,
        parent_agent_id: str,
        display_name: str,
        capabilities: list[str],
        constraints: dict,
        budget_cents: int,
        worker_generation: int = 1,
    ) -> dict:
        """Atomically admit one ephemeral worker for a parent run.

        The child snapshot is admitted (strict subset of the parent's active
        snapshot), the budget reservation is taken, and the agent row becomes
        visible in one transaction. Any failure rolls all of it back.
        """
        with self._db.connection() as connection:
            try:
                with connection.transaction():
                    connection.execute(
                        "SELECT pg_advisory_xact_lock(hashtext(%s))",
                        (f"budget:{context.tenant_id}:{parent_run_id}",),
                    )
                    parent_run = connection.execute(
                        """
                        SELECT r.agent_id, r.budget_cents, a.admission_snapshot_id
                        FROM runs r JOIN agents a ON a.tenant_id = r.tenant_id AND a.agent_id = r.agent_id
                        WHERE r.tenant_id = %s AND r.run_id = %s FOR UPDATE
                        """,
                        (context.tenant_id, parent_run_id),
                    ).fetchone()
                    if parent_run is None:
                        raise AdmissionError("parent run unknown")
                    parent_snapshot_id = parent_run[2]
                    if parent_snapshot_id is None:
                        raise AdmissionError("parent run has no admitted capability snapshot")
                    # Strict-subset child snapshot before anything is visible.
                    try:
                        child = self._capabilities.admit_child(
                            context,
                            parent_snapshot_id=parent_snapshot_id,
                            principal_id=parent_agent_id,
                            capabilities=capabilities,
                            constraints=constraints,
                            budget_cents=budget_cents,
                        )
                    except CapabilityEscalationError:
                        raise
                    spent = connection.execute(
                        """
                        SELECT COALESCE(SUM(reserved_cents), 0) FROM budget_reservations
                        WHERE tenant_id = %s AND parent_run_id = %s AND status IN ('reserved','settling')
                        """,
                        (context.tenant_id, parent_run_id),
                    ).fetchone()[0]
                    if spent + budget_cents > parent_run[1]:
                        raise BudgetExceededError(
                            f"budget ceiling exceeded: spent {spent} + requested {budget_cents} > {parent_run[1]}"
                        )
                    worker_generation = max(worker_generation, 1)
                    connection.execute("SELECT set_config('app.mutation_context', 'graph_transaction', true)")
                    agent_id = str(uuid.uuid4())
                    connection.execute(
                        """
                        INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name,
                                            parent_agent_id, admission_expires_at, admission_snapshot_id)
                        VALUES (%s, %s, %s, 'ephemeral_worker', %s, %s,
                                now() + interval '1 hour', %s)
                        """,
                        (context.tenant_id, context.workspace_id, agent_id, display_name,
                         parent_agent_id, child["snapshot_id"]),
                    )
                    reservation_id = str(uuid.uuid4())
                    connection.execute(
                        """
                        INSERT INTO budget_reservations
                            (tenant_id, reservation_id, parent_run_id, idempotency_key,
                             amount_cents, status, reserved_cents, worker_generation, worker_agent_id)
                        VALUES (%s, %s, %s, %s, %s, 'reserved', %s, %s, %s)
                        """,
                        (context.tenant_id, reservation_id, parent_run_id,
                         f"admission:{agent_id}", budget_cents, budget_cents, worker_generation, agent_id),
                    )
            except CapabilityEscalationError:
                raise
        return {
            "worker_agent_id": agent_id,
            "child_snapshot_id": child["snapshot_id"],
            "reservation_id": reservation_id,
            "budget_cents": budget_cents,
            "worker_generation": worker_generation,
        }

    def release_orphaned_reservations(self, context: IdentityContext, older_than_seconds: int = 3600) -> int:
        """RUN-004-R01 recovery: crash after reservation but before dispatch
        leaves an orphaned reservation (its worker never received a turn);
        recovery releases it so the budget returns to the parent."""
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE budget_reservations r SET status = 'released', updated_at = now()
                WHERE r.tenant_id = %s AND r.status = 'reserved'
                  AND r.created_at < now() - (%s || ' seconds')::interval
                  AND NOT EXISTS (
                    SELECT 1 FROM turns t
                    WHERE t.tenant_id = r.tenant_id AND t.child_agent_id = r.worker_agent_id
                  )
                """,
                (context.tenant_id, str(older_than_seconds)),
            )
            return cursor.rowcount


class TurnDispatcher:
    """RUN-005: asynchronous fan-out with independent durable outcomes."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def dispatch(self, context: IdentityContext, parent_run_id: str, child_agent_id: str, payload: dict, deadline_at: datetime | None = None) -> str:
        turn_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO turns (tenant_id, workspace_id, turn_id, parent_run_id, child_agent_id,
                                   status, payload, deadline_at)
                VALUES (%s, %s, %s, %s, %s, 'queued', %s, %s)
                """,
                (context.tenant_id, context.workspace_id, turn_id, parent_run_id, child_agent_id,
                 Json(payload), deadline_at),
            )
        return turn_id

    def deliver_outcome(self, context: IdentityContext, turn_id: str, delivery_id: str, result: dict, partial: bool = False) -> bool:
        """Record one child outcome delivery. Returns False for duplicates
        and turns whose deadline has passed."""
        row = self._db.query_one(
            """
            SELECT deadline_at, status FROM turns
            WHERE tenant_id = %s AND turn_id = %s
            """,
            (context.tenant_id, turn_id),
        )
        if row is None:
            return False
        deadline_at, status = row
        if status in ("cancelled", "expired"):
            return False
        if deadline_at is not None and deadline_at < datetime.now(timezone.utc):
            with self._db.connection() as connection:
                connection.execute(
                    "UPDATE turns SET status = 'expired', terminal_at = now() WHERE tenant_id = %s AND turn_id = %s",
                    (context.tenant_id, turn_id),
                )
            return False
        try:
            with self._db.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO turn_outcomes (tenant_id, turn_id, delivery_id, partial, result)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (context.tenant_id, turn_id, delivery_id, partial, Json(result)),
                )
        except psycopg.errors.UniqueViolation:
            return False  # duplicate delivery: durable identity deduplicates
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE turns SET status = CASE WHEN %s THEN status ELSE 'succeeded' END,
                                  terminal_at = CASE WHEN %s THEN terminal_at ELSE now() END
                WHERE tenant_id = %s AND turn_id = %s
                """,
                (partial, partial, context.tenant_id, turn_id),
            )
        return True

    def aggregate(self, context: IdentityContext, parent_run_id: str) -> dict:
        """Fan-in: aggregate durable state without blocking the parent."""
        turns = self._db.query_all(
            """
            SELECT turn_id::text, status, deadline_at FROM turns
            WHERE tenant_id = %s AND parent_run_id = %s ORDER BY dispatched_at
            """,
            (context.tenant_id, parent_run_id),
        )
        outcomes = self._db.query_all(
            """
            SELECT o.turn_id::text, o.partial, o.result FROM turn_outcomes o
            JOIN turns t ON t.tenant_id = o.tenant_id AND t.turn_id = o.turn_id
            WHERE o.tenant_id = %s AND t.parent_run_id = %s ORDER BY o.received_at
            """,
            (context.tenant_id, parent_run_id),
        )
        by_turn: dict[str, list] = {}
        for turn_id, partial, result in outcomes:
            by_turn.setdefault(turn_id, []).append({"partial": partial, "result": result})
        return {
            "turns": [
                {
                    "turn_id": turn_id,
                    "status": status,
                    "deliveries": by_turn.get(turn_id, []),
                }
                for turn_id, status, _deadline in turns
            ],
            "final": [t for t in (
                {"turn_id": turn_id, "results": [d["result"] for d in by_turn.get(turn_id, []) if not d["partial"]]}
                for turn_id, status, _deadline in turns
            ) if t["results"]],
        }

    def request_cancel_running(self, context: IdentityContext, turn_id: str) -> bool:
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE turns SET status = 'cancelled', terminal_at = now()
                WHERE tenant_id = %s AND turn_id = %s AND status = 'queued'
                """,
                (context.tenant_id, turn_id),
            )
            return cursor.rowcount > 0


class RunCanceller:
    """RUN-006: effect-aware cancellation of a parent run and its children."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def cancel(self, context: IdentityContext, parent_run_id: str) -> dict:
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute("SELECT set_config('app.mutation_context', 'graph_transaction', true)")
                connection.execute(
                    """
                    UPDATE runs SET status = 'cancelled', terminal_at = now(), updated_at = now()
                    WHERE tenant_id = %s AND run_id = %s AND status IN ('pending','running','suspended')
                    """,
                    (context.tenant_id, parent_run_id),
                )
                # Queued children: prevented from starting.
                queued = connection.execute(
                    """
                    UPDATE turns SET status = 'cancelled', terminal_at = now()
                    WHERE tenant_id = %s AND parent_run_id = %s AND status = 'queued'
                    """,
                    (context.tenant_id, parent_run_id),
                ).rowcount
                # Running children: cancellation *requested*; they settle themselves.
                running = connection.execute(
                    """
                    UPDATE turns SET status = 'cancelled', terminal_at = now()
                    WHERE tenant_id = %s AND parent_run_id = %s AND status = 'running'
                    """,
                    (context.tenant_id, parent_run_id),
                ).rowcount
                # Committed external effects are preserved verbatim.
                committed_effects = connection.execute(
                    """
                    SELECT count(*) FROM effects
                    WHERE tenant_id = %s AND run_id = %s AND status = 'committed'
                    """,
                    (context.tenant_id, parent_run_id),
                ).fetchone()[0]
        return {
            "cancelled_queued": queued,
            "requested_running_cancel": running,
            "committed_effects_preserved": committed_effects,
        }

    def settle_running_cancelled(self, context: IdentityContext, turn_id: str, result: dict) -> bool:
        """A running child acknowledges cancellation with its partial state."""
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE turns SET status = 'cancelled', terminal_at = now()
                WHERE tenant_id = %s AND turn_id = %s AND status = 'running'
                """,
                (context.tenant_id, turn_id),
            )
            return cursor.rowcount > 0

    def rollback_committed_effect(self, context: IdentityContext, effect_id: str) -> bool:
        """RUN-006-N01: cancellation alone can never rewrite committed
        external effect history — the storage guard rejects the transition."""
        try:
            with self._db.connection() as connection:
                connection.execute(
                    """
                    UPDATE effects SET status = 'rolled_back'
                    WHERE tenant_id = %s AND effect_id = %s AND status = 'committed'
                    """,
                    (context.tenant_id, effect_id),
                )
        except psycopg.errors.RaiseException:
            return False
        row = self._db.query_one(
            "SELECT status FROM effects WHERE tenant_id = %s AND effect_id = %s",
            (context.tenant_id, effect_id),
        )
        return row is not None and row[0] == "rolled_back"


class BudgetLedger:
    """RUN-007: atomic hierarchical budget reservations."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def reserve(
        self,
        context: IdentityContext,
        parent_run_id: str,
        idempotency_key: str,
        amount_cents: int,
        worker_generation: int = 1,
    ) -> dict:
        """Reserve budget under the parent ceiling.

        - same idempotency key: returns the original reservation (no double
          spend);
        - stale worker generation (lower than the highest seen): rejected;
        - over-ceiling requests rejected; the advisory lock serializes racers.
        """
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))",
                    (f"budget:{context.tenant_id}:{parent_run_id}",),
                )
                existing = connection.execute(
                    """
                    SELECT reservation_id::text, reserved_cents, status FROM budget_reservations
                    WHERE tenant_id = %s AND parent_run_id = %s AND idempotency_key = %s
                    """,
                    (context.tenant_id, parent_run_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    return {
                        "reservation_id": existing[0],
                        "reserved_cents": existing[1],
                        "status": existing[2],
                        "duplicate": True,
                    }
                ceiling = connection.execute(
                    "SELECT budget_cents FROM runs WHERE tenant_id = %s AND run_id = %s",
                    (context.tenant_id, parent_run_id),
                ).fetchone()
                if ceiling is None:
                    raise AdmissionError("parent run unknown")
                spent = connection.execute(
                    """
                    SELECT COALESCE(SUM(reserved_cents), 0) FROM budget_reservations
                    WHERE tenant_id = %s AND parent_run_id = %s AND status IN ('reserved','settling')
                    """,
                    (context.tenant_id, parent_run_id),
                ).fetchone()[0]
                if spent + amount_cents > ceiling[0]:
                    raise BudgetExceededError("budget ceiling exceeded")
                highest_generation = connection.execute(
                    "SELECT COALESCE(MAX(worker_generation), 0) FROM budget_reservations WHERE tenant_id = %s AND parent_run_id = %s",
                    (context.tenant_id, parent_run_id),
                ).fetchone()[0]
                if worker_generation < highest_generation:
                    raise AdmissionError(
                        f"stale worker generation {worker_generation}; current is {highest_generation}"
                    )
                reservation_id = str(uuid.uuid4())
                connection.execute(
                    """
                    INSERT INTO budget_reservations
                        (tenant_id, reservation_id, parent_run_id, idempotency_key,
                         amount_cents, status, reserved_cents, worker_generation)
                    VALUES (%s, %s, %s, %s, %s, 'reserved', %s, %s)
                    """,
                    (context.tenant_id, reservation_id, parent_run_id, idempotency_key,
                     amount_cents, amount_cents, worker_generation),
                )
        return {
            "reservation_id": reservation_id,
            "reserved_cents": amount_cents,
            "status": "reserved",
            "duplicate": False,
        }

    def apply_late_usage(self, context: IdentityContext, reservation_id: str, usage_cents: int) -> dict:
        """RUN-007-R01: settle exactly once when late usage arrives.

        The reservation stays settling until final usage is applied; applying
        it commits the used amount and releases the unused remainder, which
        closes the reservation. A second application is a no-op.
        """
        with self._db.connection() as connection:
            with connection.transaction():
                row = connection.execute(
                    """
                    SELECT status, reserved_cents, committed_cents FROM budget_reservations
                    WHERE tenant_id = %s AND reservation_id = %s FOR UPDATE
                    """,
                    (context.tenant_id, reservation_id),
                ).fetchone()
                if row is None:
                    raise AdmissionError("reservation unknown")
                status, reserved, committed = row
                if status in ("settled", "released"):
                    return {"settled": True, "already": True, "released_cents": 0}
                newly_committed = min(usage_cents, reserved - committed)
                connection.execute(
                    """
                    UPDATE budget_reservations
                    SET committed_cents = committed_cents + %s,
                        status = 'released',
                        updated_at = now()
                    WHERE tenant_id = %s AND reservation_id = %s
                    """,
                    (newly_committed, context.tenant_id, reservation_id),
                )
                released = reserved - (committed + newly_committed)
        return {"settled": True, "already": False, "committed_cents": newly_committed, "released_cents": released}


class DurableWaits:
    """RUN-008: suspend/resume on timer, approval and callback waits."""

    def __init__(self, database: PlatformDatabase, protocol: ProtocolStateStore):
        self._db = database
        self._protocol = protocol

    def suspend(self, context: IdentityContext, run_id: str, kind: str, payload: dict,
                resume_at: datetime | None = None, protocol_id: str | None = None) -> str:
        protocol_id = self._protocol.open_wait(
            context, kind, run_id, payload, protocol_id=protocol_id, resume_at=resume_at
        )
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE runs SET status = 'suspended', updated_at = now()
                WHERE tenant_id = %s AND run_id = %s AND status = 'running'
                """,
                (context.tenant_id, run_id),
            )
        return protocol_id

    def resume(self, context: IdentityContext, run_id: str, protocol_id: str, outcome: dict) -> bool:
        """Resume exactly once from the durable wait identity.

        Settling an outstanding wait lets the run continue; if the run is
        already running (another wait resumed it first), the settle still
        succeeds exactly once for this wait.
        """
        wait = self._protocol.get(context, protocol_id)
        if wait is None or wait["status"] != "waiting":
            return False
        self._protocol.settle(context, protocol_id, outcome)
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE runs SET status = 'running', updated_at = now()
                WHERE tenant_id = %s AND run_id = %s AND status = 'suspended'
                """,
                (context.tenant_id, run_id),
            )
        return True

    def deliver_callback(self, context: IdentityContext, run_id: str, protocol_id: str, callback: dict) -> bool:
        """Deliver an external callback exactly once; expired/cancelled waits
        never advance the graph."""
        wait = self._protocol.get(context, protocol_id)
        if wait is None or wait["status"] != "waiting":
            return False
        if wait.get("resume_at") is not None and wait["resume_at"] < datetime.now(timezone.utc):
            return False
        return self.resume(context, run_id, protocol_id, {"callback": callback})
