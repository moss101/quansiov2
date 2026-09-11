"""qworkerd HTTP surface: guest actuation for assigned operations.

The daemon executes typed guest operations strictly inside one task sandbox.
Before any operation runs, the caller's lease is validated against the
machine-control placement authority (target + generation + fence + holder),
ambient-secret requests are refused, and the operation set is limited to the
typed guest protocol. qworkerd holds no ambient cloud authority and no
provider credentials.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.identity import ControlService
from quansio.machine_control.inventory import LeaseRejection, Placer, TargetInventory
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import add_health_routes, default_database, resolve_bearer
from quansio.qworkerd.protocol import GUEST_PROTOCOL_VERSION, GuestProtocol, GuestRejection

SANDBOX_ROOT = Path(os.environ.get("QUANSIO_GUEST_SANDBOX_ROOT", "/tmp/quansio-qworkerd"))


class GuestExecute(BaseModel):
    task_id: str
    target_id: str
    generation: int
    fence_token: int
    operation: str
    version: str = GUEST_PROTOCOL_VERSION
    arguments: dict


def create_app(database: PlatformDatabase | None = None) -> FastAPI:
    app = FastAPI(title="qworkerd", version="9.0.0")
    db = database or default_database()
    control = ControlService(db)
    placer = Placer(db, TargetInventory(db))

    add_health_routes(app, db, "qworkerd")

    @app.post("/v9/guest/execute")
    def guest_execute(body: GuestExecute, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        # Lease and fence validation before any actuation (MAC-002-N01).
        try:
            validated = placer.validate_action(
                context, body.target_id, body.generation,
                body.fence_token, context.user_id,
            )
        except LeaseRejection as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        row = db.query_one(
            "SELECT root_path FROM task_environments WHERE tenant_id=%s AND task_id=%s",
            (context.tenant_id, body.task_id),
        )
        if row is None:
            raise HTTPException(status_code=404, detail="task environment unknown")
        guest = GuestProtocol(
            Path(row[0]), body.task_id,
            protocol_version=body.version,
        )
        try:
            result = guest.execute(
                body.operation, body.version, body.arguments,
                identity={
                    "task_id": body.task_id,
                    "target_id": body.target_id,
                    "generation": validated["generation"],
                    "fence_token": validated["fence_token"],
                },
            )
        except GuestRejection as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"result": result}

    return app
