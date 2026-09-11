"""quansio-machine-control HTTP surface: execution-target inventory,
exclusive placement/lease/fence, durable worker deliveries, isolated task
runtimes, persistent workspace computers, checkpoints and private targets.

Every route resolves identity from a quansio-control bearer session. Guest
actuation executed here goes through the qworkerd guest protocol after
target/generation/lease/fence validation — never around it.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.identity import ControlService
from quansio.machine_control.inventory import (
    LeaseRejection,
    Placer,
    TargetInventory,
    TargetRejected,
)
from quansio.machine_control.services import (
    CheckpointService,
    DeliveryExpired,
    IsolatedTaskRuntime,
    PrivateTargetService,
    WorkspaceComputerService,
    WorkerDeliveryService,
)
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import (
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)
from quansio.qworkerd.protocol import GuestProtocol, GuestRejection

STATE_ROOT = Path(os.environ.get("QUANSIO_MACHINE_STATE_ROOT", "/tmp/quansio-machine-state"))


class TargetRegister(BaseModel):
    target_id: str
    target_type: str
    support_profile: str
    health_identity: str


class LifecycleSet(BaseModel):
    lifecycle: str


class Heartbeat(BaseModel):
    health: str


class PlaceRequest(BaseModel):
    holder: str
    required_profile: str | None = None


class ValidateAction(BaseModel):
    generation: int
    fence_token: int
    lease_holder: str


class DeliveryEnqueue(BaseModel):
    target_id: str
    operation: str
    arguments: dict
    idempotency_key: str
    ttl_seconds: int = 300


class DeliveryExecute(BaseModel):
    task_id: str
    target_id: str
    generation: int
    fence_token: int
    protocol_version: str = "9.0.0"


class TaskEnvironment(BaseModel):
    declared_inputs: list[dict]


class CheckpointCreate(BaseModel):
    computer_id: str
    kind: str
    references: dict


class CheckpointRestore(BaseModel):
    new_generation: int


class PrivateTargetRegister(BaseModel):
    target_id: str
    mapped_qualification_suites: list[str]


def _artifact_fetch(digest_or_path: str):
    """Checkpoint verification fetches artifact bytes through the artifact
    catalog; machine-control holds no artifact authority of its own."""
    database = PlatformDatabase(database_config(), max_size=1)
    try:
        row = database.query_one(
            "SELECT 1 FROM artifact_records WHERE digest = %s", (digest_or_path,)
        )
        return b"" if row else None
    except Exception:  # noqa: BLE001 - fail closed on catalog unavailability
        return None
    finally:
        database.close()


def create_app(database: PlatformDatabase | None = None,
               artifact_fetch=None) -> FastAPI:
    app = FastAPI(title="quansio-machine-control", version="9.0.0")
    db = database or default_database()
    control = ControlService(db)
    inventory = TargetInventory(db)
    placer = Placer(db, inventory)
    deliveries = WorkerDeliveryService(db)
    tasks = IsolatedTaskRuntime(db, STATE_ROOT / "tasks")
    computers = WorkspaceComputerService(db, STATE_ROOT / "computers")
    checkpoints = CheckpointService(db)
    private_targets = PrivateTargetService(db, inventory)
    fetch = artifact_fetch or _artifact_fetch

    add_health_routes(app, db, "quansio-machine-control")

    # -- target inventory and placement --------------------------------------

    @app.post("/v9/targets")
    def register_target(body: TargetRegister, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            generation = inventory.register(
                context, body.target_id, body.target_type,
                body.support_profile, body.health_identity,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"target_id": body.target_id, "generation": generation}

    @app.post("/v9/targets/{target_id}/lifecycle")
    def set_lifecycle(target_id: str, body: LifecycleSet, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            inventory.set_lifecycle(context, target_id, body.lifecycle)
        except TargetRejected as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"target_id": target_id, "lifecycle": body.lifecycle}

    @app.post("/v9/targets/{target_id}/heartbeat")
    def heartbeat(target_id: str, body: Heartbeat, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        inventory.heartbeat(context, target_id, body.health)
        return {"target_id": target_id, "health": body.health}

    @app.get("/v9/targets/{target_id}")
    def get_target(target_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        target = inventory.get(context, target_id)
        if target is None:
            raise HTTPException(status_code=404, detail="target unknown")
        return {"target": target}

    @app.get("/v9/targets/{target_id}/audit")
    def target_audit(target_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"events": inventory.audit_events(context, target_id)}

    @app.post("/v9/targets/{target_id}/place")
    def place_target(target_id: str, body: PlaceRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"lease": placer.place(
                context, target_id, body.holder,
                required_profile=body.required_profile,
            )}
        except (TargetRejected, LeaseRejection) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/v9/targets/{target_id}/validate-action")
    def validate_action(target_id: str, body: ValidateAction, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"validated": placer.validate_action(
                context, target_id, body.generation, body.fence_token,
                body.lease_holder,
            )}
        except LeaseRejection as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    # -- durable worker deliveries (ACK/redelivery) ---------------------------

    @app.post("/v9/deliveries")
    def enqueue_delivery(body: DeliveryEnqueue, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"delivery": deliveries.enqueue(
            context, body.target_id, body.operation, body.arguments,
            body.idempotency_key, ttl_seconds=body.ttl_seconds,
        )}

    @app.get("/v9/deliveries/pending")
    def pending_deliveries(authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"deliveries": deliveries.pending_deliveries(context)}

    @app.post("/v9/deliveries/{delivery_id}/deliver")
    def deliver_delivery(delivery_id: str, body: DeliveryExecute, authorization: str = Header(default="")) -> dict:
        """Deliver to the guest actuator: lease/fence validation happens
        first, then the typed guest protocol executes inside the task
        sandbox. Redelivery replays the durable result."""
        context = resolve_bearer(authorization, control)

        def execute(operation: str, arguments: dict) -> dict:
            validated = placer.validate_action(
                context, body.target_id, body.generation,
                body.fence_token, context.user_id,
            )
            row = db.query_one(
                "SELECT root_path FROM task_environments WHERE tenant_id=%s AND task_id=%s",
                (context.tenant_id, body.task_id),
            )
            if row is None:
                raise KeyError("task environment unknown")
            guest = GuestProtocol(Path(row[0]), body.task_id,
                                  protocol_version=body.protocol_version)
            return guest.execute(
                operation, body.protocol_version, arguments,
                identity={
                    "task_id": body.task_id,
                    "target_id": body.target_id,
                    "generation": validated["generation"],
                    "fence_token": validated["fence_token"],
                },
            )

        try:
            outcome = deliveries.deliver(context, delivery_id, execute)
        except DeliveryExpired as error:
            raise HTTPException(status_code=410, detail=str(error)) from error
        except (KeyError, GuestRejection, LeaseRejection) as error:
            status = 404 if isinstance(error, KeyError) else 409
            raise HTTPException(status_code=status, detail=str(error)) from error
        return {"delivery": outcome}

    # -- isolated task runtimes ------------------------------------------------

    @app.put("/v9/tasks/{task_id}/environment")
    def provision_task(task_id: str, body: TaskEnvironment, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        result = tasks.provision(context, task_id, body.declared_inputs)
        # The sandbox path is internal state; the guest never receives it.
        return {"task_id": result["task_id"], "provisioned": True}

    @app.delete("/v9/tasks/{task_id}/environment")
    def destroy_task(task_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            tasks.destroy(context, task_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return {"task_id": task_id, "state": "destroyed"}

    @app.post("/v9/tasks/{task_id}/environment/recreate")
    def recreate_task(task_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            tasks.recreate(context, task_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return {"task_id": task_id, "provisioned": True, "recreated_from_declared_inputs": True}

    # -- persistent workspace computers ----------------------------------------

    @app.put("/v9/computers/{computer_id}")
    def bind_computer(computer_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"computer": computers.bind(context, computer_id)}

    @app.get("/v9/computers/{computer_id}")
    def get_computer(computer_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"computer": computers.get(context, computer_id)}
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/v9/computers/{computer_id}/hibernate")
    def hibernate_computer(computer_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        computers.hibernate(context, computer_id)
        return {"computer_id": computer_id, "lifecycle": "hibernated"}

    @app.post("/v9/computers/{computer_id}/resume")
    def resume_computer(computer_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"computer": computers.resume_after_control_restart(context, computer_id)}

    # -- checkpoints ----------------------------------------------------------

    @app.post("/v9/checkpoints")
    def create_checkpoint(body: CheckpointCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"checkpoint": checkpoints.create(
            context, body.computer_id, body.kind, body.references,
        )}

    @app.post("/v9/checkpoints/{checkpoint_id}/verify")
    def verify_checkpoint(checkpoint_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)

        def event_cursor_committed(consumer: str, run_id: str, last_sequence: int) -> bool:
            return db.query_one(
                "SELECT 1 FROM event_cursors WHERE tenant_id=%s AND consumer=%s AND run_id=%s AND last_sequence >= %s",
                (context.tenant_id, consumer, run_id, last_sequence),
            ) is not None

        try:
            return {"checkpoint": checkpoints.verify(
                context, checkpoint_id, fetch, event_cursor_committed,
            )}
        except (KeyError, ValueError) as error:
            status = 404 if isinstance(error, KeyError) else 409
            raise HTTPException(status_code=status, detail=str(error)) from error

    @app.post("/v9/checkpoints/{checkpoint_id}/restore")
    def restore_checkpoint(checkpoint_id: str, body: CheckpointRestore, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"checkpoint": checkpoints.restore(
                context, checkpoint_id, body.new_generation,
            )}
        except (KeyError, ValueError) as error:
            status = 404 if isinstance(error, KeyError) else 409
            raise HTTPException(status_code=status, detail=str(error)) from error

    # -- private targets ---------------------------------------------------------

    @app.post("/v9/private-targets")
    def register_private_target(body: PrivateTargetRegister, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"target": private_targets.register(
            context, body.target_id, body.mapped_qualification_suites,
        )}

    @app.post("/v9/private-targets/{target_id}/enable")
    def enable_private_target(target_id: str, body: PrivateTargetRegister, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            private_targets.enable(context, target_id, body.mapped_qualification_suites)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"target_id": target_id, "enabled": True}

    @app.post("/v9/private-targets/{target_id}/preserve-pending")
    def preserve_pending(target_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"preserved": private_targets.preserve_pending_on_disconnect(context, target_id)}

    return app
