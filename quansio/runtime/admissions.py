"""Durable command admission (runtime authority).

The runtime owns admission: every admitted public command is persisted
before the run it produces is created, and the run is linked on the command
row so the command-to-result journey is auditable. Admission is idempotent
by (tenant, idempotency_key): a replayed command returns the original run
without creating a second one. A crash between the durable admission and
the ``run.started`` event resumes exactly once on replay.
"""

from __future__ import annotations

import uuid

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class AdmissionRefused(Exception):
    """The command cannot be admitted (unknown agent, malformed arguments)."""


class CommandAdmission:
    def __init__(self, database: PlatformDatabase, events):
        self._db = database
        self._events = events

    def status(self, context: IdentityContext, command_id: str) -> dict | None:
        row = self._db.query_one(
            """
            SELECT command_id::text, run_id::text, status, command_type, admitted_at
            FROM commands WHERE tenant_id=%s AND command_id=%s
            """,
            (context.tenant_id, command_id),
        )
        if row is None:
            return None
        return {"command_id": row[0], "run_id": row[1], "status": row[2],
                "command_type": row[3], "admitted_at": row[4].isoformat()}

    def admit(
        self,
        context: IdentityContext,
        command_id: str,
        command_type: str,
        arguments: dict,
        idempotency_key: str,
    ) -> dict:
        existing = self._db.query_one(
            """
            SELECT command_id::text, run_id::text, status FROM commands
            WHERE tenant_id=%s AND idempotency_key=%s
            """,
            (context.tenant_id, idempotency_key),
        )
        if existing is not None:
            command_id, run_id, status = existing
            if status == "dispatched":
                return {"command_id": command_id, "run_id": run_id,
                        "status": status, "replayed": True}
            # Crash resume: run exists, run.started may be missing.
            self._emit_started(context, run_id, arguments)
            self._db.execute(
                "UPDATE commands SET status='dispatched', dispatched_at=now()"
                " WHERE tenant_id=%s AND command_id=%s AND status='admitted'",
                (context.tenant_id, command_id),
            )
            return {"command_id": command_id, "run_id": run_id,
                    "status": "dispatched", "replayed": True}

        if command_type != "task.start":
            raise AdmissionRefused(f"unsupported command type {command_type!r}")
        objective = arguments.get("objective")
        if not isinstance(objective, str) or not objective.strip():
            raise AdmissionRefused("task.start requires a non-empty objective")
        agent_id = arguments.get("agent_id")
        agent = self._db.query_one(
            "SELECT 1 FROM agents WHERE tenant_id=%s AND agent_id=%s",
            (context.tenant_id, agent_id),
        )
        if agent is None:
            raise AdmissionRefused(
                "task.start requires agent_id of an admitted agent; admit a"
                " teammate first — commands never invent execution authority"
            )
        budget_cents = arguments.get("budget_cents", 0)
        if not isinstance(budget_cents, int) or budget_cents < 0:
            raise AdmissionRefused("budget_cents must be a non-negative integer")

        run_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute(
                    """
                    INSERT INTO commands
                        (tenant_id, command_id, workspace_id, actor_id, session_id,
                         command_type, arguments, idempotency_key, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'admitted')
                    """,
                    (context.tenant_id, command_id, context.workspace_id,
                     context.user_id, context.session_id, command_type,
                     Json(arguments), idempotency_key),
                )
                connection.execute(
                    """
                    INSERT INTO runs (tenant_id, workspace_id, run_id, agent_id, status, budget_cents)
                    VALUES (%s, %s, %s, %s, 'pending', %s)
                    """,
                    (context.tenant_id, context.workspace_id, run_id,
                     agent_id, budget_cents),
                )
        self._emit_started(context, run_id, arguments)
        self._db.execute(
            "UPDATE commands SET run_id=%s, status='dispatched', dispatched_at=now()"
            " WHERE tenant_id=%s AND command_id=%s AND status='admitted'",
            (run_id, context.tenant_id, command_id),
        )
        return {"command_id": command_id, "run_id": run_id,
                "status": "dispatched", "replayed": False}

    def _emit_started(self, context: IdentityContext, run_id: str, arguments: dict) -> None:
        already = self._db.query_one(
            "SELECT 1 FROM runtime_events WHERE tenant_id=%s AND run_id=%s AND sequence=1",
            (context.tenant_id, run_id),
        )
        if already is None:
            self._events.append(
                context, run_id, "run.started",
                {"status": "running", "objective": arguments.get("objective", "")},
            )
