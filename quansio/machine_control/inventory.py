"""Execution-target inventory and lifecycle (MAC-001) plus exclusive
placement, lease and fence (MAC-002). Owner: quansio-machine-control.

Targets are registered per tenant with type, lifecycle state, execution
generation, support profile and health identity; every lifecycle transition
is durable and audited in target_events. Placement consults only the
authoritative inventory — unregistered, wrong-tenant or disabled targets
are rejected before lease acquisition. Leases are exclusive per target with
a monotonic fence token bound to the target's execution generation; guest
actions must validate target+generation+fence together, and a crashed
controller's expired lease is superseded by a higher fence/generation that
permanently disqualifies the old controller.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class TargetRejected(Exception):
    """Placement refused the target before lease acquisition."""


class LeaseRejection(Exception):
    """A guest action failed generation/lease/fence validation."""


class TargetInventory:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def register(self, context: IdentityContext, target_id: str, target_type: str,
                 support_profile: str, health_identity: str) -> int:
        if target_type not in ("fs", "terminal", "browser", "computer", "private"):
            raise ValueError(f"unknown target type {target_type}")
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute(
                    """
                    INSERT INTO execution_targets
                        (tenant_id, target_id, target_type, lifecycle,
                         execution_generation, support_profile, health_identity,
                         last_heartbeat)
                    VALUES (%s, %s, %s, 'registered', 1, %s, %s, now())
                    ON CONFLICT (tenant_id, target_id) DO NOTHING
                    """,
                    (context.tenant_id, target_id, target_type,
                     support_profile, health_identity),
                )
                connection.execute(
                    """
                    INSERT INTO target_events (tenant_id, target_id, kind, detail)
                    VALUES (%s, %s, 'registered', %s)
                    """,
                    (context.tenant_id, target_id,
                     Json({"support_profile": support_profile, "health_identity": health_identity})),
                )
        return self.generation(context, target_id)

    def set_lifecycle(self, context: IdentityContext, target_id: str, lifecycle: str) -> None:
        if lifecycle not in ("registered", "enabled", "disabled", "retired"):
            raise ValueError(lifecycle)
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE execution_targets SET lifecycle = %s, last_heartbeat = now()
                WHERE tenant_id = %s AND target_id = %s
                """,
                (lifecycle, context.tenant_id, target_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"unknown target {target_id}")
            connection.execute(
                "INSERT INTO target_events (tenant_id, target_id, kind, detail)"
                " VALUES (%s, %s, %s, '{}'::jsonb)",
                (context.tenant_id, target_id, lifecycle),
            )

    def heartbeat(self, context: IdentityContext, target_id: str, health: str) -> None:
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE execution_targets SET last_heartbeat = now(), health_identity = %s"
                " WHERE tenant_id = %s AND target_id = %s",
                (health, context.tenant_id, target_id),
            )

    def get(self, context: IdentityContext, target_id: str) -> dict | None:
        row = self._db.query_one(
            """
            SELECT target_id, target_type, lifecycle, execution_generation,
                   support_profile, health_identity, last_heartbeat
            FROM execution_targets WHERE tenant_id = %s AND target_id = %s
            """,
            (context.tenant_id, target_id),
        )
        if row is None:
            return None
        return {"target_id": row[0], "type": row[1], "lifecycle": row[2],
                "generation": row[3], "support_profile": row[4],
                "health_identity": row[5], "last_heartbeat": row[6]}

    def generation(self, context: IdentityContext, target_id: str) -> int:
        row = self._db.query_one(
            "SELECT execution_generation FROM execution_targets WHERE tenant_id=%s AND target_id=%s",
            (context.tenant_id, target_id),
        )
        if row is None:
            raise KeyError(f"unknown target {target_id}")
        return row[0]

    def audit_events(self, context: IdentityContext, target_id: str) -> list[dict]:
        rows = self._db.query_all(
            "SELECT kind, detail, created_at FROM target_events"
            " WHERE tenant_id=%s AND target_id=%s ORDER BY event_id",
            (context.tenant_id, target_id),
        )
        return [{"kind": r[0], "detail": r[1], "at": r[2]} for r in rows]

    def reconstruct(self, context: IdentityContext, target_id: str) -> dict:
        """MAC-001-R01: rebuild runtime view from durable inventory and
        heartbeats only — no in-memory ownership survives a restart."""
        target = self.get(context, target_id)
        if target is None:
            raise KeyError(target_id)
        events = self.audit_events(context, target_id)
        target["lifecycle_replay"] = [e["kind"] for e in events]
        target["authoritative"] = True
        return target


class Placer:
    def __init__(self, database: PlatformDatabase, inventory: TargetInventory,
                 lease_ttl_seconds: int = 60):
        self._db = database
        self._inventory = inventory
        self._ttl = lease_ttl_seconds

    def place(self, context: IdentityContext, target_id: str,
              holder: str, required_profile: str | None = None) -> dict:
        """MAC-001-N01: inventory validation happens BEFORE lease
        acquisition; MAC-002-P01: exclusive lease + fence for the current
        generation."""
        target = self._inventory.get(context, target_id)
        if target is None:
            raise TargetRejected(f"target {target_id} not registered")
        if target["lifecycle"] != "enabled":
            raise TargetRejected(f"target {target_id} is {target['lifecycle']}")
        if required_profile and target["support_profile"] != required_profile:
            raise TargetRejected(
                f"support profile mismatch: {target['support_profile']!r} != {required_profile!r}"
            )
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))",
                    (f"lease:{context.tenant_id}:{target_id}",),
                )
                connection.execute("DELETE FROM target_leases WHERE tenant_id=%s AND target_id=%s AND expires_at < now()",
                                   (context.tenant_id, target_id))
                existing = connection.execute(
                    "SELECT fence_token, generation, holder, expires_at FROM target_leases"
                    " WHERE tenant_id=%s AND target_id=%s",
                    (context.tenant_id, target_id),
                ).fetchone()
                if existing is not None and existing[3] > datetime.now(timezone.utc):
                    raise TargetRejected(f"target {target_id} already leased by {existing[2]}")
                fence_row = connection.execute(
                    """
                    INSERT INTO fence_counters AS f (tenant_id, target_id, fence_token)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (tenant_id, target_id)
                    DO UPDATE SET fence_token = f.fence_token + 1
                    RETURNING fence_token
                    """,
                    (context.tenant_id, target_id),
                ).fetchone()[0]
                generation = self._inventory.generation(context, target_id)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._ttl)
                connection.execute(
                    """
                    INSERT INTO target_leases
                        (tenant_id, target_id, fence_token, generation, holder, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id, target_id)
                    DO UPDATE SET fence_token = EXCLUDED.fence_token,
                                  generation = EXCLUDED.generation,
                                  holder = EXCLUDED.holder,
                                  expires_at = EXCLUDED.expires_at
                    """,
                    (context.tenant_id, target_id, fence_row, generation,
                     holder, expires_at),
                )
        return {"target_id": target_id, "fence_token": fence_row,
                "generation": generation, "holder": holder,
                "expires_at": expires_at.isoformat()}

    def bump_generation(self, context: IdentityContext, target_id: str) -> int:
        """MAC-002-R01: superseding a crashed controller requires a higher
        generation; the old controller's fence is then invalid."""
        with self._db.connection() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))",
                               (f"lease:{context.tenant_id}:{target_id}",))
            generation = connection.execute(
                """
                UPDATE execution_targets SET execution_generation = execution_generation + 1
                WHERE tenant_id = %s AND target_id = %s RETURNING execution_generation
                """,
                (context.tenant_id, target_id),
            ).fetchone()
            if generation is None:
                raise KeyError(target_id)
            connection.execute(
                """
                UPDATE target_leases SET expires_at = now() - interval '1 second',
                                         generation = %s
                WHERE tenant_id=%s AND target_id=%s
                """,
                (generation[0], context.tenant_id, target_id),
            )
        return generation[0]

    def validate_action(self, context: IdentityContext, target_id: str,
                        generation: int, fence_token: int, lease_holder: str) -> dict:
        """MAC-002-N01: every guest/endpoint action validates target +
        generation + lease + fence before actuation."""
        row = self._db.query_one(
            """
            SELECT fence_token, generation, holder, expires_at FROM target_leases
            WHERE tenant_id = %s AND target_id = %s
            """,
            (context.tenant_id, target_id),
        )
        if row is None:
            raise LeaseRejection("no active lease for target")
        current_fence, current_generation, holder, expires_at = row
        if generation != current_generation:
            raise LeaseRejection(f"stale generation {generation}; current {current_generation}")
        if expires_at <= datetime.now(timezone.utc):
            raise LeaseRejection("lease expired")
        if fence_token != current_fence:
            raise LeaseRejection(
                f"prior fence token {fence_token}; current {current_fence}"
            )
        if holder != lease_holder:
            raise LeaseRejection(f"lease held by {holder}, not {lease_holder}")
        return {"fence_token": current_fence, "generation": current_generation, "holder": holder}
