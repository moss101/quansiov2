"""Platform runtime context: tenant/workspace/user identity scopes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IdentityContext:
    """Server-resolved authoritative identity for one authenticated request.

    Instances are constructed only from durable server state (a session row
    joined to user/workspace). Client-supplied identity fields are never
    accepted as inputs; the API layer rejects any attempt to smuggle them.
    """

    tenant_id: str
    workspace_id: str
    user_id: str
    session_id: str
    roles: tuple[str, ...]
    expires_at: datetime

    def require_role(self, role: str) -> None:
        if role not in self.roles:
            raise PermissionError(f"role {role} required")


class IdentityContextError(Exception):
    """Raised when an identity context cannot be resolved from server state."""
