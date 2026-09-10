"""Resumable protocol state (DAT-005, owner quansio-runtime).

Protocol objects — tool calls, approval waits, questions, worker lifecycle,
browser/control ownership, cancellations and durable waits — persist in
``protocol_state``, independent of any semantic memory store. Restores are
idempotent by protocol identity: restarting during an outstanding wait never
duplicates a request.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase

PROTOCOL_KINDS = (
    "tool_call",
    "approval_wait",
    "question",
    "worker_lifecycle",
    "browser_ownership",
    "cancellation",
    "durable_wait",
    "timer_wait",
    "callback_wait",
)


class ProtocolStateStore:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def open_wait(
        self,
        context: IdentityContext,
        state_kind: str,
        run_id: str,
        payload: dict,
        protocol_id: str | None = None,
        resume_at: datetime | None = None,
    ) -> str:
        """Open a protocol wait; idempotent by protocol_id.

        An existing open protocol object with the same identity is returned
        unchanged — restoring after a runtime restart never duplicates a
        request (approval, question, tool call).
        """
        if state_kind not in PROTOCOL_KINDS:
            raise ValueError(f"unknown protocol kind {state_kind}")
        protocol_id = protocol_id or str(uuid.uuid4())
        with self._db.connection() as connection:
            row = connection.execute(
                """
                SELECT state_id FROM protocol_state
                WHERE tenant_id = %s AND state_id = %s AND status IN ('waiting', 'open')
                """,
                (context.tenant_id, protocol_id),
            ).fetchone()
            if row is not None:
                return _s(row[0])
            connection.execute(
                """
                INSERT INTO protocol_state
                    (tenant_id, workspace_id, state_id, run_id, state_kind, status, payload, resume_at)
                VALUES (%s, %s, %s, %s, %s, 'waiting', %s, %s)
                """,
                (
                    context.tenant_id,
                    context.workspace_id,
                    protocol_id,
                    run_id,
                    state_kind,
                    Json(payload),
                    resume_at,
                ),
            )
        return protocol_id

    def get(self, context: IdentityContext, protocol_id: str) -> dict[str, Any] | None:
        row = self._db.query_one(
            """
            SELECT state_id::text, state_kind, status, payload, run_id::text, resume_at, created_at, updated_at
            FROM protocol_state WHERE tenant_id = %s AND state_id = %s
            """,
            (context.tenant_id, protocol_id),
        )
        if row is None:
            return None
        return {
            "protocol_id": row[0],
            "kind": row[1],
            "status": row[2],
            "payload": row[3],
            "run_id": row[4],
            "resume_at": row[5],
            "created_at": row[6],
            "updated_at": row[7],
        }

    def settle(self, context: IdentityContext, protocol_id: str, outcome: dict) -> None:
        """Close a wait (approval decided, answer received, callback delivered)."""
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE protocol_state
                SET status = 'settled', payload = payload || %s::jsonb, updated_at = now()
                WHERE tenant_id = %s AND state_id = %s AND status = 'waiting'
                """,
                (Json({"outcome": outcome}), context.tenant_id, protocol_id),
            )

    def list_waiting(self, context: IdentityContext, run_id: str | None = None) -> list[dict]:
        rows = self._db.query_all(
            """
            SELECT state_id::text, state_kind, status, payload, run_id::text, resume_at
            FROM protocol_state
            WHERE tenant_id = %s AND status = 'waiting' AND (%s::uuid IS NULL OR run_id = %s::uuid)
            ORDER BY created_at
            """,
            (context.tenant_id, run_id, run_id),
        )
        return [
            {
                "protocol_id": r[0],
                "kind": r[1],
                "status": r[2],
                "payload": r[3],
                "run_id": r[4],
                "resume_at": r[5],
            }
            for r in rows
        ]


def _s(value):
    return str(value) if value is not None and not isinstance(value, (str, dict, list, int, float, bool)) else value
