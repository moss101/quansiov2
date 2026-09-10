"""Agent lifecycle: persistent teammates and ephemeral workers (RUN-002).

A persistent teammate is a durable identity bound to one workspace; it
survives runtime restarts indefinitely. An ephemeral worker is a
task-scoped identity whose admission expires; expired ephemeral identities
can never be promoted or reused as persistent teammates, and restart
cleanup retires them while persistent binding is untouched. Every agent
admission freezes an immutable CapabilitySnapshot (SEC-001) whose authority
the agent cannot exceed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from psycopg.types.json import Json

from quansio.control.capability import CapabilityService, SnapshotExpiredError
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class AgentLifecycleError(Exception):
    """An agent lifecycle transition violates admission rules."""


class AgentRegistry:
    """Owner: quansio-runtime (registry truth shared with quansio-control)."""

    def __init__(self, database: PlatformDatabase, capabilities: CapabilityService):
        self._db = database
        self._capabilities = capabilities

    def create_persistent_teammate(
        self, context: IdentityContext, display_name: str, snapshot_id: str, agent_id: str | None = None
    ) -> str:
        # The admitted snapshot must be active at admission time.
        self._capabilities.require_active(context, snapshot_id)
        if agent_id is not None:
            # Identity reuse attempt: a retired/expired ephemeral worker
            # identity can never become a persistent teammate.
            prior = self.get_agent(context, agent_id)
            if prior is not None and prior["kind"] == "ephemeral_worker":
                raise AgentLifecycleError(
                    "an ephemeral worker identity cannot be reused as a persistent teammate"
                )
        else:
            agent_id = str(uuid.uuid4())
        try:
            with self._db.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)
                    VALUES (%s, %s, %s, 'persistent_teammate', %s)
                    """,
                    (context.tenant_id, context.workspace_id, agent_id, display_name),
                )
        except psycopg.errors.UniqueViolation as error:
            raise AgentLifecycleError("display name already bound in workspace") from error
        return agent_id

    def create_ephemeral_worker(
        self,
        context: IdentityContext,
        parent_agent_id: str,
        display_name: str,
        snapshot_id: str,
        ttl_seconds: int = 600,
    ) -> dict:
        """Admit an ephemeral worker with an expiring admission grant.

        The worker's authority is frozen in its own capability snapshot and
        expires with the admission; it is always a strict child of its
        persistent parent.
        """
        parent = self.get_agent(context, parent_agent_id)
        if parent is None:
            raise AgentLifecycleError("parent agent unknown")
        if parent["kind"] != "persistent_teammate":
            raise AgentLifecycleError("ephemeral workers admit only under persistent teammates")
        try:
            self._capabilities.require_active(context, snapshot_id)
        except SnapshotExpiredError as error:
            raise AgentLifecycleError("admission snapshot expired before worker start") from error
        agent_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name,
                                    parent_agent_id, admission_expires_at, admission_snapshot_id)
                VALUES (%s, %s, %s, 'ephemeral_worker', %s, %s, %s, %s)
                """,
                (context.tenant_id, context.workspace_id, agent_id, display_name,
                 parent_agent_id, expires_at, snapshot_id),
            )
        return {
            "agent_id": agent_id,
            "parent_agent_id": parent_agent_id,
            "admission_expires_at": expires_at.isoformat(),
            "snapshot_id": snapshot_id,
        }

    def get_agent(self, context: IdentityContext, agent_id: str) -> dict[str, Any] | None:
        row = self._db.query_one(
            """
            SELECT agent_id::text, tenant_id::text, workspace_id::text, kind, display_name,
                   parent_agent_id::text, created_at, retired_at
            FROM agents WHERE tenant_id = %s AND agent_id = %s
            """,
            (context.tenant_id, agent_id),
        )
        if row is None:
            return None
        return {
            "agent_id": row[0],
            "tenant_id": row[1],
            "workspace_id": row[2],
            "kind": row[3],
            "display_name": row[4],
            "parent_agent_id": row[5],
            "created_at": row[6],
            "retired_at": row[7],
        }

    def cleanup_expired_ephemeral(self, context: IdentityContext) -> int:
        """Runtime-restart cleanup: retire expired ephemeral workers.

        Persistent teammates are never touched; their identity/workspace
        binding survives restarts untouched.
        """
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE agents SET retired_at = now()
                WHERE tenant_id = %s AND kind = 'ephemeral_worker' AND retired_at IS NULL
                  AND admission_expires_at < now()
                """,
                (context.tenant_id,),
            )
            return cursor.rowcount
