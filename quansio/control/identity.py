"""Tenant and authenticated session authority (DAT-001, owner quansio-control).

Identity truth lives in durable server state: tenants, users, workspaces and
sessions. Every command admitted by ``quansio-api`` resolves its
``IdentityContext`` from the session row joined to user and workspace —
never from client-supplied fields. Session tokens are stored only as
sha256 hashes; the raw token exists solely with the presenting client.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg.types.json import Json

from quansio.platform.context import IdentityContext, IdentityContextError
from quansio.platform.db import PlatformDatabase

SESSION_TTL_HOURS = 12
MIN_PASSWORD_LENGTH = 10


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
    return hmac.compare_digest(candidate.hex(), digest_hex)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class ControlService:
    """Canonical owner of tenant/identity/session configuration truth."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    # -- tenant provisioning ------------------------------------------------

    def create_tenant(self, name: str) -> str:
        tenant_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                "INSERT INTO tenants (tenant_id, name) VALUES (%s, %s)",
                (tenant_id, name),
            )
        return tenant_id

    def create_workspace(self, tenant_id: str, name: str) -> str:
        workspace_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                "INSERT INTO workspaces (tenant_id, workspace_id, name) VALUES (%s, %s, %s)",
                (tenant_id, workspace_id, name),
            )
        return workspace_id

    def create_user(
        self,
        tenant_id: str,
        email: str,
        display_name: str,
        password: str,
        role: str = "member",
        workspace_id: str | None = None,
    ) -> str:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
        user_id = str(uuid.uuid4())
        try:
            with self._db.connection() as connection:
                with connection.transaction():
                    connection.execute(
                        "INSERT INTO users (tenant_id, user_id, email, display_name, password_hash)"
                        " VALUES (%s, %s, %s, %s, %s)",
                        (tenant_id, user_id, email, display_name, _hash_password(password)),
                    )
                    connection.execute(
                        "INSERT INTO role_bindings (tenant_id, user_id, workspace_id, role)"
                        " VALUES (%s, %s, %s, %s)",
                        (tenant_id, user_id, workspace_id, role),
                    )
        except psycopg.errors.UniqueViolation as error:
            raise ValueError("user already exists for tenant") from error
        return user_id

    # -- session lifecycle --------------------------------------------------

    def authenticate(self, tenant_id: str, email: str, password: str, workspace_id: str) -> tuple[str, IdentityContext]:
        """Verify credentials against durable state and open a session.

        Returns the raw bearer token (client-held) plus the server-resolved
        identity context.
        """
        row = self._db.query_one(
            """
            SELECT u.tenant_id, u.user_id, u.password_hash
            FROM users u
            WHERE u.tenant_id = %s AND u.email = %s
            """,
            (tenant_id, email),
        )
        if row is None or not _verify_password(password, row[2]):
            raise IdentityContextError("authentication failed")
        workspace = self._db.query_one(
            "SELECT workspace_id FROM workspaces WHERE tenant_id = %s AND workspace_id = %s",
            (tenant_id, workspace_id),
        )
        if workspace is None:
            raise IdentityContextError("workspace unknown for tenant")
        role_rows = self._db.query_all(
            """
            SELECT role FROM role_bindings
            WHERE tenant_id = %s AND user_id = %s AND (workspace_id = %s OR workspace_id IS NULL)
            """,
            (tenant_id, row[1], workspace_id),
        )
        if not role_rows:
            raise IdentityContextError("no authority in workspace")

        token = secrets.token_urlsafe(32)
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO sessions (session_id, tenant_id, user_id, workspace_id, token_hash, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (session_id, tenant_id, row[1], workspace_id, _hash_token(token), expires_at),
            )
        context = IdentityContext(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=row[1],
            session_id=session_id,
            roles=tuple(sorted({r[0] for r in role_rows})),
            expires_at=expires_at,
        )
        return token, context

    def resolve_session(self, token: str) -> IdentityContext:
        """Resolve one bearer token to its authoritative identity context.

        The context comes exclusively from the sessions row joined to
        workspaces and role bindings; expired or revoked sessions do not
        resolve.
        """
        if not token:
            raise IdentityContextError("missing session token")
        row = self._db.query_one(
            """
            SELECT s.session_id, s.tenant_id, s.workspace_id, s.user_id, s.expires_at, s.revoked_at,
                   COALESCE(
                     (SELECT array_agg(rb.role ORDER BY rb.role)
                      FROM role_bindings rb
                      WHERE rb.tenant_id = s.tenant_id AND rb.user_id = s.user_id
                        AND (rb.workspace_id = s.workspace_id OR rb.workspace_id IS NULL)),
                     '{}')
            FROM sessions s
            WHERE s.token_hash = %s
            """,
            (_hash_token(token),),
        )
        if row is None:
            raise IdentityContextError("session unknown")
        session_id, tenant_id, workspace_id, user_id, expires_at, revoked_at, roles = row
        if revoked_at is not None or expires_at <= datetime.now(timezone.utc):
            raise IdentityContextError("session expired or revoked")
        roles = roles or []
        if "member" not in roles and "workspace_admin" not in roles and "tenant_admin" not in roles:
            raise IdentityContextError("no authority in workspace")
        return IdentityContext(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            session_id=session_id,
            roles=tuple(roles),
            expires_at=expires_at,
        )

    def revoke_session(self, session_id: str) -> None:
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE sessions SET revoked_at = now() WHERE session_id = %s AND revoked_at IS NULL",
                (session_id,),
            )
