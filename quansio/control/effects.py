"""Universal Effect Ledger, durable approvals, UNKNOWN reconciliation
(EFF-001..003, owner quansio-control).

One effect path: an EffectRecord is created BEFORE any consequential
actuation and carries policy, approval, execution, outcome, receipt and
evidence correlation. Actuators refuse operations without an effect id.
An ambiguous timeout marks the effect UNKNOWN; the engine refuses a second
actuation until reconciliation queries the target's idempotency state and
records an explicit reconciled terminal (COMMITTED, FAILED or a safe
retry). Reconciliation restarts continue with the same effect and
idempotency identity. Approvals are durable and scoped to the exact
normalized arguments — including payee, amount, currency and ceilings for
financial effects — and a changed amount or substituted payee denies
execution even with the receipt present.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import psycopg
from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class EffectRequired(Exception):
    """Actuation attempted without an EffectRecord (EFF-001-N01)."""


class EffectStateError(Exception):
    """The transition violates the ledger state machine."""


class ApprovalMismatch(Exception):
    """Execution arguments no longer match the approved scope (EFF-002-N01)."""


class BlindRetryBlocked(Exception):
    """An UNKNOWN effect was retried without reconciliation (EFF-003-N01)."""


class EffectLedger:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def propose(
        self,
        context: IdentityContext,
        run_id: str,
        operation: str,
        arguments: dict,
        target: str,
        policy_decision_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        effect_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO effects
                    (tenant_id, workspace_id, effect_id, run_id, operation,
                     arguments, status, policy_decision_id, idempotency_key)
                VALUES (%s, %s, %s, %s, %s, %s, 'proposed', %s, %s)
                """,
                (context.tenant_id, context.workspace_id, effect_id, run_id,
                 operation, Json(arguments), policy_decision_id, idempotency_key),
            )
        return {"effect_id": effect_id, "status": "proposed", "operation": operation,
                "run_id": run_id, "idempotency_key": idempotency_key}

    def authorize(self, context: IdentityContext, effect_id: str,
                  policy_decision_id: str, approval_id: str | None = None) -> None:
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE effects SET status = 'authorized', policy_decision_id = %s,
                                   approval_id = COALESCE(%s, approval_id), updated_at = now()
                WHERE tenant_id = %s AND effect_id = %s AND status = 'proposed'
                """,
                (policy_decision_id, approval_id, context.tenant_id, effect_id),
            )
            if cursor.rowcount != 1:
                raise EffectStateError("effect not in proposed state")

    def start_execution(self, context: IdentityContext, effect_id: str) -> None:
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE effects SET status = 'actuating', attempt = attempt + 1, updated_at = now()
                WHERE tenant_id = %s AND effect_id = %s AND status = 'authorized'
                """,
                (context.tenant_id, effect_id),
            )
            if cursor.rowcount != 1:
                raise EffectStateError("effect not authorized for execution")

    def mark_unknown(self, context: IdentityContext, effect_id: str, detail: dict) -> None:
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE effects SET status = 'unknown', state_details = state_details || %s::jsonb,
                                   updated_at = now()
                WHERE tenant_id = %s AND effect_id = %s AND status = 'actuating'
                """,
                (Json(detail), context.tenant_id, effect_id),
            )

    def complete(self, context: IdentityContext, effect_id: str, outcome: dict,
                 receipt: dict | None = None) -> None:
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE effects SET status = 'committed', result = %s, receipt = %s,
                                   updated_at = now()
                WHERE tenant_id = %s AND effect_id = %s AND status IN ('actuating','unknown')
                """,
                (Json(outcome), Json(receipt or {}), context.tenant_id, effect_id),
            )

    def fail(self, context: IdentityContext, effect_id: str, error: str) -> None:
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE effects SET status = 'failed', result = %s, updated_at = now()
                WHERE tenant_id = %s AND effect_id = %s AND status IN ('actuating','unknown')
                """,
                (Json({"error": error}), context.tenant_id, effect_id),
            )

    def require_effect(self, context: IdentityContext, effect_id: str, expected_status: str) -> dict:
        row = self._db.query_one(
            """
            SELECT effect_id::text, operation, arguments, status, idempotency_key, attempt
            FROM effects WHERE tenant_id = %s AND effect_id = %s
            """,
            (context.tenant_id, effect_id),
        )
        if row is None:
            raise EffectRequired(f"effect {effect_id} does not exist")
        if expected_status and row[3] != expected_status:
            raise EffectStateError(f"effect {effect_id} is {row[3]!r}, expected {expected_status!r}")
        return {"effect_id": row[0], "operation": row[1], "arguments": row[2],
                "status": row[3], "idempotency_key": row[4], "attempt": row[5]}

    def recover_actuating(self, context: IdentityContext) -> list[dict]:
        """EFF-001-R01: effects left EXECUTING by a crash are recovered under
        their SAME effect identity — reconciliation, never a new effect."""
        rows = self._db.query_all(
            "SELECT effect_id::text, operation, idempotency_key FROM effects "
            "WHERE tenant_id = %s AND status = 'actuating'",
            (context.tenant_id,),
        )
        return [{"effect_id": r[0], "operation": r[1], "idempotency_key": r[2]} for r in rows]


class ApprovalService:
    def __init__(self, database: PlatformDatabase, policy_engine):
        self._db = database
        self._policy = policy_engine

    def request(
        self, context: IdentityContext, run_id: str, effect_id: str,
        operation: str, arguments: dict, target: str,
        financial: dict | None = None,
    ) -> dict:
        """Create a durable approval bound to the exact normalized scope."""
        scope_digest = self._policy.scope_digest(arguments)
        approval_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO approvals
                    (tenant_id, workspace_id, approval_id, run_id, capability,
                     arguments, scope, status, argument_scope_digest,
                     amount_minor, ceiling_minor, currency, payee)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, %s, %s, %s)
                """,
                (context.tenant_id, context.workspace_id, approval_id, run_id,
                 operation, Json(arguments),
                 Json({"target": target, "scope_digest": scope_digest,
                       "financial": financial or {}}),
                 scope_digest,
                 (financial or {}).get("amount_minor"),
                 (financial or {}).get("ceiling_minor"),
                 (financial or {}).get("currency"),
                 (financial or {}).get("payee")),
            )
            connection.execute(
                "UPDATE effects SET approval_id = %s WHERE tenant_id = %s AND effect_id = %s",
                (approval_id, context.tenant_id, effect_id),
            )
        return {"approval_id": approval_id, "argument_scope_digest": scope_digest}

    def decide(self, context: IdentityContext, approval_id: str,
               approved: bool, approver_id: str) -> dict:
        """Durable decision, idempotent: a second decision on a settled
        approval is refused without duplicating anything (EFF-002-R01)."""
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT status FROM approvals WHERE tenant_id=%s AND approval_id=%s FOR UPDATE",
                (context.tenant_id, approval_id),
            ).fetchone()
            if row is None:
                raise KeyError("approval unknown")
            if row[0] != "pending":
                return {"approval_id": approval_id, "status": row[0], "already_decided": True}
            connection.execute(
                """
                UPDATE approvals SET status = %s, decided_by = %s, decided_at = now()
                WHERE tenant_id = %s AND approval_id = %s
                """,
                ("approved" if approved else "denied", approver_id,
                 context.tenant_id, approval_id),
            )
        return {"approval_id": approval_id,
                "status": "approved" if approved else "denied",
                "already_decided": False}

    def verify_execution_scope(self, context: IdentityContext, approval_id: str,
                               arguments: dict) -> None:
        """EFF-002-N01: execution must match the approved scope exactly.
        A one-minor-unit amount change or substituted payee fails here —
        before provider invocation."""
        row = self._db.query_one(
            """
            SELECT status, argument_scope_digest, amount_minor, payee
            FROM approvals WHERE tenant_id = %s AND approval_id = %s
            """,
            (context.tenant_id, approval_id),
        )
        if row is None:
            raise KeyError("approval unknown")
        status, digest, amount_minor, payee = row
        if status != "approved":
            raise ApprovalMismatch(f"approval status {status!r} does not permit execution")
        if "amount" in arguments and amount_minor is not None and arguments["amount"] != amount_minor:
            raise ApprovalMismatch(
                f"approved amount {amount_minor} != execution amount {arguments['amount']}"
            )
        if "payee" in arguments and payee is not None and arguments["payee"] != payee:
            raise ApprovalMismatch(f"approved payee {payee!r} != execution payee {arguments['payee']!r}")
        if self._policy.scope_digest(arguments) != digest:
            raise ApprovalMismatch("execution arguments differ from approved scope")


class UnknownEffectReconciler:
    """EFF-003: ambiguous timeouts resolve only through idempotency probes."""

    def __init__(self, database: PlatformDatabase, ledger: EffectLedger):
        self._db = database
        self._ledger = ledger

    def mark_unknown_on_timeout(self, context: IdentityContext, effect_id: str,
                                detail: dict) -> None:
        self._ledger.mark_unknown(context, effect_id, {"timeout": True, **detail})

    def probe(self, context: IdentityContext, effect_id: str,
              target_query: Callable[[str | None], str],
              decide: Callable[[str], str] | None = None) -> dict:
        """Query the target's idempotency state and record an explicit
        reconciled terminal.

        ``target_query`` receives the effect's idempotency key and returns
        'committed' | 'not_found' | 'unknown'. ``decide`` maps the probe
        result to the terminal transition (default: committed→committed,
        not_found→safe retry as authorized, unknown→stays unknown).
        Restart-safe: reconciliation attempts are recorded per effect and
        the same effect/idempotency identity continues until terminal.
        """
        effect = self._ledger.require_effect(context, effect_id, expected_status="unknown")
        idempotency_key = effect["idempotency_key"]
        probe_result = target_query(idempotency_key)
        attempt = self._next_attempt(context, effect_id)
        self._record_attempt(context, effect_id, attempt, probe_result, {})
        mapping = decide or (lambda result: "committed" if result == "committed"
                             else ("authorized" if result == "not_found" else "unknown"))
        transition = mapping(probe_result)
        if transition == "committed":
            self._ledger.complete(context, effect_id, {"reconciled": True},
                                  receipt={"probe": probe_result, "attempt": attempt})
            final = "reconciled"
        elif transition == "authorized":
            # Safe retry: the probe proved no side effect happened, so the
            # ledger returns the effect to authorized under the same identity.
            with self._db.connection() as connection:
                cursor = connection.execute(
                    """
                    UPDATE effects SET status = 'authorized', updated_at = now()
                    WHERE tenant_id = %s AND effect_id = %s AND status = 'unknown'
                    """,
                    (context.tenant_id, effect_id),
                )
                if cursor.rowcount != 1:
                    raise EffectStateError("unknown effect moved during reconciliation")
            final = "authorized_for_safe_retry"
        else:
            final = "unknown"
        return {"effect_id": effect_id, "probe_result": probe_result,
                "final": final, "attempt": attempt}

    def _policy_id(self, context: IdentityContext, effect_id: str) -> str:
        row = self._db.query_one(
            "SELECT policy_decision_id FROM effects WHERE tenant_id=%s AND effect_id=%s",
            (context.tenant_id, effect_id),
        )
        return row[0] if row and row[0] else str(uuid.uuid4())

    def _next_attempt(self, context: IdentityContext, effect_id: str) -> int:
        row = self._db.query_one(
            "SELECT COALESCE(MAX(attempt), 0) FROM effect_reconciliations WHERE tenant_id=%s AND effect_id=%s",
            (context.tenant_id, effect_id),
        )
        return row[0] + 1

    def _record_attempt(self, context: IdentityContext, effect_id: str,
                        attempt: int, probe_result: str, detail: dict) -> None:
        self._db.execute(
            """
            INSERT INTO effect_reconciliations (tenant_id, effect_id, attempt, probe_result, detail)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (context.tenant_id, effect_id, attempt, probe_result, Json(detail)),
        )
