"""Shared HTTP service plumbing for canonical deployables.

Every canonical service exposes the same transport contract: bearer session
identity resolved from server state by quansio-control, readiness backed by
the authoritative database, and structured error mapping. This module holds
only that shared plumbing — no domain authority lives here.
"""

from __future__ import annotations

from fastapi import Header, HTTPException

from quansio.control.identity import ControlService, IdentityContextError
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase, database_config


def resolve_bearer(
    authorization: str, control: ControlService
) -> IdentityContext:
    """Resolve the presented bearer token to a server-resolved identity."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="bearer session required")
    try:
        return control.resolve_session(token)
    except IdentityContextError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


def identity_view(context: IdentityContext) -> dict:
    return {
        "tenant_id": context.tenant_id,
        "workspace_id": context.workspace_id,
        "user_id": context.user_id,
        "session_id": context.session_id,
        "roles": list(context.roles),
        "expires_at": context.expires_at.isoformat(),
    }


def add_health_routes(app, database: PlatformDatabase, service: str) -> None:
    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "live", "service": service}

    @app.get("/readyz")
    def readyz() -> object:
        try:
            database.query_one("SELECT 1")
        except Exception as error:  # noqa: BLE001 - readiness reports degradation
            # A degraded service must not answer 200: load balancers and
            # orchestrators key on the status code.
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "service": service, "error": str(error)},
            )
        return {"status": "ready", "service": service}


def default_database() -> PlatformDatabase:
    return PlatformDatabase(database_config())
