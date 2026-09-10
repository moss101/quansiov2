"""Tenant-safe repository and query layer (DAT-008).

Every repository operation is bound to one server-resolved ``IdentityContext``
and embeds the tenant scope into the query itself. A foreign tenant id passed
as a data parameter is rejected before any data materializes.
"""

from __future__ import annotations

import uuid
from typing import Any

from quansio.platform.context import IdentityContext, IdentityContextError
from quansio.platform.db import PlatformDatabase


class TenantScopeViolation(PermissionError):
    """A query attempted to escape the caller's tenant scope."""


class TenantRepository:
    """Canonical tenant-scoped read/write access to authoritative aggregates."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def _tenant(self, context: IdentityContext, claimed_tenant: str | None = None) -> str:
        if claimed_tenant is not None and claimed_tenant != context.tenant_id:
            raise TenantScopeViolation(
                f"foreign tenant identifier {claimed_tenant} does not match session tenant"
            )
        return context.tenant_id

    # -- writes ---------------------------------------------------------------

    def create_run(self, context: IdentityContext, agent_id: str, budget_cents: int = 0) -> str:
        tenant = self._tenant(context)
        run_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO runs (tenant_id, workspace_id, run_id, agent_id, status, budget_cents)
                VALUES (%s, %s, %s, %s, 'pending', %s)
                """,
                (tenant, context.workspace_id, run_id, agent_id, budget_cents),
            )
        return run_id

    def update_run_status(self, context: IdentityContext, run_id: str, status: str) -> bool:
        tenant = self._tenant(context)
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE runs SET status = %s, updated_at = now()
                WHERE tenant_id = %s AND run_id = %s
                """,
                (status, tenant, run_id),
            )
            return cursor.rowcount > 0

    # -- reads ----------------------------------------------------------------

    def get_run(self, context: IdentityContext, run_id: str, claimed_tenant: str | None = None) -> dict[str, Any] | None:
        tenant = self._tenant(context, claimed_tenant)
        row = self._db.query_one(
            """
            SELECT tenant_id::text, workspace_id::text, run_id::text, agent_id::text, status, generation, budget_cents
            FROM runs WHERE tenant_id = %s AND run_id = %s
            """,
            (tenant, run_id),
        )
        if row is None:
            return None
        return {
            "tenant_id": row[0],
            "workspace_id": row[1],
            "run_id": row[2],
            "agent_id": row[3],
            "status": row[4],
            "generation": row[5],
            "budget_cents": row[6],
        }

    def list_runs(self, context: IdentityContext) -> list[dict[str, Any]]:
        tenant = self._tenant(context)
        rows = self._db.query_all(
            """
            SELECT run_id::text, status, created_at FROM runs
            WHERE tenant_id = %s AND workspace_id = %s
            ORDER BY created_at DESC
            """,
            (tenant, context.workspace_id),
        )
        return [{"run_id": r[0], "status": r[1], "created_at": r[2]} for r in rows]
