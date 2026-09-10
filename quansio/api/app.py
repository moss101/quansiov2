"""quansio-api: authenticated public command admission (DAT-001).

The API authenticates transport identity, resolves tenant/workspace/session
from server state, and rejects any client-supplied authoritative identity
field that does not match the server-resolved context — before any
authoritative read or write. It never executes graphs, holds provider
credentials or settles effects.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.identity import ControlService, IdentityContextError
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase, database_config

FORBIDDEN_CLIENT_FIELDS = {"tenant_id", "user_id", "session_id", "workspace_id", "actor_id"}


class LoginRequest(BaseModel):
    tenant_id: str
    workspace_id: str
    email: str
    password: str


class CommandRequest(BaseModel):
    command_type: str
    arguments: dict[str, Any]
    idempotency_key: str
    submitted_at: datetime | None = None


def create_app(database: PlatformDatabase | None = None) -> FastAPI:
    app = FastAPI(title="quansio-api", version="9.0.0")
    db = database or PlatformDatabase(database_config())
    control = ControlService(db)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "live", "service": "quansio-api"}

    @app.get("/readyz")
    def readyz() -> dict:
        try:
            applied = db.query_one(
                "SELECT count(*) FROM schema_migrations WHERE direction = 'up'"
            )
            return {"status": "ready", "applied_migrations": applied[0]}
        except Exception as error:  # noqa: BLE001 - readiness reports, never masks
            raise HTTPException(status_code=503, detail=f"not ready: {error}") from error

    @app.post("/v1/sessions")
    def open_session(body: LoginRequest) -> dict:
        try:
            token, context = control.authenticate(
                tenant_id=body.tenant_id,
                email=body.email,
                password=body.password,
                workspace_id=body.workspace_id,
            )
        except IdentityContextError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
        return {
            "token": token,
            "identity": _identity_view(context),
        }

    @app.delete("/v1/sessions/current")
    def close_session(authorization: str = Header(default="")) -> dict:
        context = _resolve(authorization, control)
        control.revoke_session(context.session_id)
        return {"revoked": context.session_id}

    @app.get("/v1/identity")
    def identity(authorization: str = Header(default="")) -> dict:
        context = _resolve(authorization, control)
        return {"identity": _identity_view(context)}

    @app.post("/v1/commands")
    def admit_command(body: CommandRequest, authorization: str = Header(default="")) -> dict:
        # Reject client-supplied authoritative identity before any
        # authoritative read or write happens in this handler.
        extra = set(body.arguments) & FORBIDDEN_CLIENT_FIELDS
        if extra:
            raise HTTPException(
                status_code=403,
                detail=f"client-supplied authoritative identity fields are not accepted: {sorted(extra)}",
            )
        context = _resolve(authorization, control)
        envelope = {
            "schema_revision": "9.0.0",
            "command_id": str(uuid.uuid4()),
            "tenant_id": context.tenant_id,
            "workspace_id": context.workspace_id,
            "actor_id": context.user_id,
            "session_id": context.session_id,
            "command_type": body.command_type,
            "arguments": body.arguments,
            "idempotency_key": body.idempotency_key,
            "submitted_at": (body.submitted_at or datetime.now(timezone.utc)).isoformat(),
        }
        return {
            "admitted": True,
            "command": envelope,
            "identity": _identity_view(context),
        }

    return app


def _resolve(authorization: str, control: ControlService) -> IdentityContext:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="bearer session required")
    try:
        return control.resolve_session(token)
    except IdentityContextError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


def _identity_view(context: IdentityContext) -> dict:
    return {
        "tenant_id": context.tenant_id,
        "workspace_id": context.workspace_id,
        "user_id": context.user_id,
        "session_id": context.session_id,
        "roles": list(context.roles),
        "expires_at": context.expires_at.isoformat(),
    }
