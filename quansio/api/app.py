"""quansio-api: authenticated public command admission (DAT-001).

The API authenticates transport identity, resolves tenant/workspace/session
from server state, and rejects any client-supplied authoritative identity
field that does not match the server-resolved context — before any
authoritative read or write. It never executes graphs, holds provider
credentials or settles effects. Admitted commands are forwarded to the
quansio-runtime admission authority, which persists them durably and creates
the run they produce; the API holds no command or run truth of its own.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.identity import ControlService, IdentityContextError
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase, database_config

FORBIDDEN_CLIENT_FIELDS = {"tenant_id", "user_id", "session_id", "workspace_id", "actor_id"}

DEFAULT_RUNTIME_URL = "http://127.0.0.1:8087"


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


def _forward_to_runtime(
    runtime_url: str, envelope: dict, authorization: str, transport
) -> dict:
    """Forward the admitted command to the runtime admission authority.

    ``transport`` is injectable for qualification; production uses HTTP with
    the caller's own bearer session so the runtime re-resolves identity from
    the same control authority — the API never delegates its own authority.
    """
    if transport is not None:
        return transport(envelope, authorization)
    try:
        response = httpx.post(
            f"{runtime_url}/v9/admissions",
            json=envelope,
            headers={"authorization": authorization},
            timeout=15.0,
        )
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"runtime admission unavailable; retry with the same idempotency_key: {error}",
        ) from error
    if response.status_code >= 400:
        detail = response.json().get("detail") if response.content else response.text
        raise HTTPException(status_code=response.status_code, detail=detail)
    return response.json()["admission"]


def create_app(
    database: PlatformDatabase | None = None,
    runtime_base_url: str | None = None,
    runtime_transport=None,
) -> FastAPI:
    app = FastAPI(title="quansio-api", version="9.0.0")
    db = database or PlatformDatabase(database_config())
    control = ControlService(db)
    runtime_url = runtime_base_url or os.environ.get(
        "QUANSIO_RUNTIME_URL", DEFAULT_RUNTIME_URL
    )

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

    @app.post("/v9/sessions")
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

    @app.delete("/v9/sessions/current")
    def close_session(authorization: str = Header(default="")) -> dict:
        context = _resolve(authorization, control)
        control.revoke_session(context.session_id)
        return {"revoked": context.session_id}

    @app.get("/v9/identity")
    def identity(authorization: str = Header(default="")) -> dict:
        context = _resolve(authorization, control)
        return {"identity": _identity_view(context)}

    @app.post("/v9/commands")
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
        admission = _forward_to_runtime(
            runtime_url,
            {
                "command_id": envelope["command_id"],
                "command_type": envelope["command_type"],
                "arguments": envelope["arguments"],
                "idempotency_key": envelope["idempotency_key"],
            },
            authorization,
            runtime_transport,
        )
        return {
            "admitted": True,
            "command": envelope,
            "admission": admission,
            "run_id": admission.get("run_id"),
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
