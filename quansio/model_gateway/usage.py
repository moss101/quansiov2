"""Usage reservation and late settlement (MOD-005).

Usage is reserved against the parent run's budget before a provider call
starts (the reservation id travels in the request envelope). Streamed/final
usage is applied idempotently; the unused remainder is released only after
usage finality. Settlement history is append-only: late charges, duplicates
and over-ceiling adjustments are recorded as adjustment rows, never as
rewrites.
"""

from __future__ import annotations

import uuid
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio.runtime.orchestration import BudgetLedger


class OverCeilingAdjustment(Exception):
    """Final usage exceeds the reservation: policy handling is required."""


class ModelUsageLedger:
    def __init__(self, database: PlatformDatabase, budget: BudgetLedger):
        self._db = database
        self._budget = budget

    def reserve(self, context: IdentityContext, parent_run_id: str, request_id: str, amount_cents: int, worker_generation: int = 1) -> dict:
        return self._budget.reserve(
            context, parent_run_id, idempotency_key=f"model:{request_id}",
            amount_cents=amount_cents, worker_generation=worker_generation,
        )

    def apply_final_usage(self, context: IdentityContext, parent_run_id: str, request_id: str,
                          reservation_id: str, usage: dict, cancelled: bool = False) -> dict:
        """Apply final provider usage exactly once; release the unused part.

        A duplicate late charge produces no additional spend. A charge above
        the reserved ceiling triggers policy handling (typed outcome) and is
        recorded, never silently absorbed.
        """
        reservation = self._db.query_one(
            """
            SELECT status, reserved_cents, committed_cents FROM budget_reservations
            WHERE tenant_id = %s AND reservation_id = %s FOR UPDATE
            """,
            (context.tenant_id, reservation_id),
        )
        if reservation is None:
            raise KeyError("reservation unknown")
        status, reserved, committed = reservation
        if status in ("settled", "released"):
            # Duplicate late charge: no additional spend.
            return {"spend_applied": 0, "duplicate": True, "released_cents": 0, "policy_required": False}
        tokens = usage.get("total_tokens", usage.get("completion_tokens", 0))
        if not isinstance(tokens, int) or tokens < 0:
            raise ValueError("usage tokens missing or invalid")
        if committed > 0:
            # Usage was already applied via streamed deltas: final is a no-op.
            return {"spend_applied": 0, "duplicate": True, "released_cents": 0, "policy_required": False}
        with self._db.connection() as connection:
            with connection.transaction():
                charge = min(reserved, tokens)
                over = tokens - charge
                policy_required = over > 0
                new_status = "settled" if not cancelled or charge > 0 else "released"
                connection.execute(
                    """
                    UPDATE budget_reservations
                    SET committed_cents = %s, status = %s, updated_at = now()
                    WHERE tenant_id = %s AND reservation_id = %s
                    """,
                    (charge, new_status, context.tenant_id, reservation_id),
                )
                connection.execute(
                    """
                    INSERT INTO model_usage_settlements
                        (tenant_id, request_id, reservation_id, kind, tokens, cents, payload)
                    VALUES (%s, %s, %s, 'final', %s, %s, %s)
                    """,
                    (context.tenant_id, request_id, reservation_id, tokens, charge,
                     Json({"over_ceiling": over, "cancelled": cancelled})),
                )
                if policy_required:
                    connection.execute(
                        """
                        INSERT INTO model_usage_settlements
                            (tenant_id, request_id, reservation_id, kind, tokens, cents, payload)
                        VALUES (%s, %s, %s, 'policy_adjustment', %s, %s, %s)
                        """,
                        (context.tenant_id, request_id, reservation_id, over, 0,
                         Json({"reason": "final usage above reservation ceiling", "over_ceiling": over})),
                    )
        return {
            "spend_applied": charge,
            "duplicate": False,
            "released_cents": reserved - charge,
            "policy_required": policy_required,
        }

    def adjustments(self, context: IdentityContext, request_id: str) -> list[dict]:
        rows = self._db.query_all(
            """
            SELECT kind, tokens, cents, payload, created_at FROM model_usage_settlements
            WHERE tenant_id = %s AND request_id = %s ORDER BY created_at, kind
            """,
            (context.tenant_id, request_id),
        )
        return [{"kind": r[0], "tokens": r[1], "cents": r[2], "payload": r[3], "at": r[4]} for r in rows]
