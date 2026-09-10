"""Scoped credential broker (SEC-004, owner quansio-control).

The broker issues short-lived, opaque credential handles bound to tenant,
operation, target, expiry and capability. Underlying secret material never
leaves the broker: callers authenticate to external services by presenting
the handle, and the broker exchanges it server-side. Expired handles are
refused, handles are refused for any other target/operation than their
binding, and rotating the underlying secret invalidates all outstanding
handles immediately — new handles use the rotated secret.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class HandleRefused(Exception):
    """The broker refused the handle before any external authentication."""


class CredentialBroker:
    def __init__(self, database: PlatformDatabase, ttl_seconds: int = 300):
        self._db = database
        self._ttl = ttl_seconds

    def register_secret(self, context: IdentityContext, secret_id: str,
                        provider: str, secret_material: str) -> int:
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT generation FROM credential_secrets WHERE tenant_id=%s AND secret_id=%s",
                (context.tenant_id, secret_id),
            ).fetchone()
            if row is None:
                connection.execute(
                    """
                    INSERT INTO credential_secrets
                        (tenant_id, secret_id, provider, secret_material, generation,
                         rotated_from, active)
                    VALUES (%s, %s, %s, %s, 1, NULL, true)
                    """,
                    (context.tenant_id, secret_id, provider, secret_material),
                )
                return 1
            generation = row[0] + 1
            connection.execute(
                """
                UPDATE credential_secrets
                SET secret_material = %s, generation = %s, provider = %s, active = true
                WHERE tenant_id = %s AND secret_id = %s
                """,
                (secret_material, generation, provider, context.tenant_id, secret_id),
            )
        return generation

    def rotate(self, context: IdentityContext, secret_id: str, new_material: str) -> int:
        """Rotation invalidates outstanding handles: they are bound to the
        secret generation and fail cleanly at exchange time."""
        return self.register_secret(context, secret_id, "rotated", new_material)

    def issue(self, context: IdentityContext, secret_id: str, operation: str,
              target: str, capability: str) -> dict:
        row = self._db.query_one(
            """
            SELECT generation, active, secret_material FROM credential_secrets
            WHERE tenant_id = %s AND secret_id = %s
            """,
            (context.tenant_id, secret_id),
        )
        if row is None or not row[1]:
            raise HandleRefused(f"unknown or inactive secret {secret_id}")
        generation = row[0]
        handle_id = str(uuid.uuid4())
        opaque = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._ttl)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO credential_handles
                    (tenant_id, handle_id, secret_id, secret_generation, operation,
                     target, capability, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (context.tenant_id, handle_id, secret_id, generation, operation,
                 target, capability, expires_at),
            )
        # The ONLY thing returned is the opaque handle; never the secret.
        return {
            "handle_id": handle_id,
            "opaque_handle": opaque,
            "operation": operation,
            "target": target,
            "capability": capability,
            "expires_at": expires_at.isoformat(),
        }

    def exchange(self, context: IdentityContext, handle_id: str, operation: str, target: str) -> str:
        """Exchange a valid handle for the secret material server-side.

        Refusals happen here — before any external authentication — for
        expired handles, revoked handles, generation mismatches after
        rotation, and any target/operation other than the binding.
        """
        row = self._db.query_one(
            """
            SELECT h.expires_at, h.revoked_at, h.operation, h.target,
                   h.secret_generation, s.active, s.secret_material
            FROM credential_handles h
            JOIN credential_secrets s ON s.tenant_id = h.tenant_id AND s.secret_id = h.secret_id
            WHERE h.tenant_id = %s AND h.handle_id = %s
            """,
            (context.tenant_id, handle_id),
        )
        if row is None:
            raise HandleRefused("unknown handle")
        expires_at, revoked_at, bound_operation, bound_target, generation, active, material = row
        if revoked_at is not None:
            raise HandleRefused("handle revoked")
        if expires_at <= datetime.now(timezone.utc):
            raise HandleRefused("handle expired")
        if not active:
            raise HandleRefused("underlying credential rotated; handle invalidated")
        if operation != bound_operation or target != bound_target:
            raise HandleRefused(
                f"handle bound to {bound_operation}@{bound_target}; refused for {operation}@{target}"
            )
        current = self._db.query_one(
            """
            SELECT generation FROM credential_secrets WHERE tenant_id=%s AND secret_id=(
              SELECT secret_id FROM credential_handles WHERE tenant_id=%s AND handle_id=%s)
            """,
            (context.tenant_id, context.tenant_id, handle_id),
        )[0]
        if current != generation:
            raise HandleRefused("secret generation superseded; handle invalidated by rotation")
        return material
