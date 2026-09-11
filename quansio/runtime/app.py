"""quansio-runtime HTTP surface: canonical graph execution authority.

Exposes admission, WorkGraph persistence, canonical RuntimeEvent append and
replay, worker admission, turn dispatch/aggregation, effect-aware
cancellation, hierarchical budget reservation and durable waits — all backed
by the canonical runtime packages with server-resolved identity on every
route. The runtime never touches provider credentials or settles external
effects itself.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.capability import (
    CapabilityEscalationError,
    CapabilityService,
)
from quansio.control.identity import ControlService
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.repository import TenantRepository
from quansio.platform.service import (
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)
from quansio.runtime.admissions import AdmissionRefused, CommandAdmission
from quansio.runtime.agents import AgentLifecycleError, AgentRegistry
from quansio.runtime.events import EventAppendError, EventLog
from quansio.runtime.graphs import GraphTransactionError, WorkGraphStore
from quansio.runtime.orchestration import (
    AdmissionError,
    BudgetExceededError,
    BudgetLedger,
    DurableWaits,
    RunCanceller,
    TurnDispatcher,
    WorkerAdmission,
)
from quansio.runtime.protocol import ProtocolStateStore


class RunCreate(BaseModel):
    agent_id: str
    budget_cents: int = 0


class EventAppend(BaseModel):
    run_id: str
    event_type: str
    payload: dict
    sequence: int | None = None
    execution_generation: int = 1
    outbox: bool = True


class GraphCreate(BaseModel):
    run_id: str
    spec: dict
    nodes: list[dict]
    edges: list[dict]
    deadlines: dict[str, str] | None = None


class WorkerAdmit(BaseModel):
    parent_run_id: str
    parent_agent_id: str
    display_name: str
    capabilities: list[str]
    constraints: dict
    budget_cents: int
    worker_generation: int = 1


class TurnDispatchRequest(BaseModel):
    parent_run_id: str
    child_agent_id: str
    payload: dict
    deadline_at: datetime | None = None


class TurnOutcomeRequest(BaseModel):
    delivery_id: str
    result: dict
    partial: bool = False


class BudgetReserve(BaseModel):
    parent_run_id: str
    idempotency_key: str
    amount_cents: int
    worker_generation: int = 1


class BudgetSettle(BaseModel):
    reservation_id: str
    usage_cents: int


class WaitSuspend(BaseModel):
    run_id: str
    kind: str
    payload: dict
    resume_at: datetime | None = None
    protocol_id: str | None = None


class WaitResume(BaseModel):
    run_id: str
    protocol_id: str
    outcome: dict


class AgentCreate(BaseModel):
    display_name: str
    snapshot_id: str
    agent_id: str | None = None
    parent_agent_id: str | None = None
    ttl_seconds: int = 600


class CommandAdmit(BaseModel):
    command_id: str
    command_type: str
    arguments: dict
    idempotency_key: str


def create_app(database: PlatformDatabase | None = None) -> FastAPI:
    app = FastAPI(title="quansio-runtime", version="9.0.0")
    db = database or default_database()
    control = ControlService(db)
    capabilities = CapabilityService(db)
    events = EventLog(db)
    graphs = WorkGraphStore(db, events)
    admission = WorkerAdmission(db, capabilities)
    turns = TurnDispatcher(db)
    canceller = RunCanceller(db)
    budgets = BudgetLedger(db)
    protocol = ProtocolStateStore(db)
    waits = DurableWaits(db, protocol)
    agents = AgentRegistry(db, capabilities)
    repository = TenantRepository(db)
    commands = CommandAdmission(db, events)

    add_health_routes(app, db, "quansio-runtime")

    @app.post("/v9/admissions")
    def admit_command(body: CommandAdmit, authorization: str = Header(default="")) -> dict:
        """Durable command admission: persists the command, creates the run
        it produces and emits the canonical run.started event. Idempotent by
        the caller's idempotency key."""
        context = resolve_bearer(authorization, control)
        try:
            result = commands.admit(
                context, body.command_id, body.command_type,
                body.arguments, body.idempotency_key,
            )
        except AdmissionRefused as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"admission": result, "identity": identity_view(context)}

    @app.get("/v9/admissions/{command_id}")
    def get_admission(command_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        status = commands.status(context, command_id)
        if status is None:
            raise HTTPException(status_code=404, detail="command unknown")
        return {"admission": status}

    @app.post("/v9/runs")
    def create_run(body: RunCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        run_id = repository.create_run(context, body.agent_id, body.budget_cents)
        return {"run_id": run_id}

    @app.get("/v9/runs/{run_id}")
    def get_run(run_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        run = repository.get_run(context, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run unknown")
        return {"run": run}

    @app.post("/v9/events")
    def append_event(body: EventAppend, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            event = events.append(
                context, body.run_id, body.event_type, body.payload,
                sequence=body.sequence,
                execution_generation=body.execution_generation,
                outbox=body.outbox,
            )
        except EventAppendError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"event": dataclasses.asdict(event)}

    @app.get("/v9/events")
    def replay_events(
        run_id: str,
        after_sequence: int = 0,
        consumer: str | None = None,
        authorization: str = Header(default=""),
    ) -> dict:
        context = resolve_bearer(authorization, control)
        found = events.replay(context.tenant_id, run_id, after_sequence=after_sequence)
        payload = [
            {
                "sequence": e.sequence,
                "event_id": e.event_id,
                "event_type": e.event_type,
                "run_id": e.run_id,
                "payload": e.payload,
                "occurred_at": e.occurred_at,
                "committed_at": e.committed_at,
                "producer_id": e.producer_id,
                "execution_generation": e.execution_generation,
            }
            for e in found
        ]
        response = {"events": payload}
        if consumer:
            cursor = events.cursor(context.tenant_id, consumer, run_id)
            response["stored_cursor"] = cursor
        return response

    @app.post("/v9/events/cursors")
    def advance_cursor(
        run_id: str, consumer: str, last_sequence: int,
        authorization: str = Header(default=""),
    ) -> dict:
        context = resolve_bearer(authorization, control)
        events.advance_cursor(context.tenant_id, consumer, run_id, last_sequence)
        return {"consumer": consumer, "run_id": run_id, "last_sequence": last_sequence}

    @app.post("/v9/graphs")
    def create_graph(body: GraphCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        graph = graphs.create_graph(
            context, body.run_id, body.spec, body.nodes, body.edges,
            deadlines=body.deadlines,
        )
        return {"graph": graph}

    @app.get("/v9/graphs/{graph_id}")
    def get_graph(graph_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        graph = graphs.get_graph(context, graph_id)
        if graph is None:
            raise HTTPException(status_code=404, detail="graph unknown")
        return {"graph": graph}

    @app.post("/v9/workers")
    def admit_worker(body: WorkerAdmit, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            result = admission.admit_worker(
                context, body.parent_run_id, body.parent_agent_id,
                body.display_name, body.capabilities, body.constraints,
                body.budget_cents, worker_generation=body.worker_generation,
            )
        except BudgetExceededError as error:
            raise HTTPException(status_code=402, detail=str(error)) from error
        except (AdmissionError, CapabilityEscalationError) as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"worker": result}

    @app.post("/v9/turns")
    def dispatch_turn(body: TurnDispatchRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        turn_id = turns.dispatch(
            context, body.parent_run_id, body.child_agent_id, body.payload,
            deadline_at=body.deadline_at,
        )
        return {"turn_id": turn_id}

    @app.post("/v9/turns/{turn_id}/outcome")
    def deliver_outcome(turn_id: str, body: TurnOutcomeRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        accepted = turns.deliver_outcome(
            context, turn_id, body.delivery_id, body.result, partial=body.partial
        )
        return {"turn_id": turn_id, "accepted": accepted}

    @app.get("/v9/runs/{parent_run_id}/aggregate")
    def aggregate(parent_run_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return turns.aggregate(context, parent_run_id)

    @app.post("/v9/runs/{parent_run_id}/cancel")
    def cancel_run(parent_run_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return canceller.cancel(context, parent_run_id)

    @app.post("/v9/budgets/reservations")
    def reserve_budget(body: BudgetReserve, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return budgets.reserve(
                context, body.parent_run_id, body.idempotency_key,
                body.amount_cents, worker_generation=body.worker_generation,
            )
        except (AdmissionError, BudgetExceededError) as error:
            raise HTTPException(status_code=402, detail=str(error)) from error

    @app.post("/v9/budgets/settlements")
    def settle_budget(body: BudgetSettle, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return budgets.apply_late_usage(context, body.reservation_id, body.usage_cents)
        except (AdmissionError, KeyError) as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/v9/waits")
    def suspend_wait(body: WaitSuspend, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            protocol_id = waits.suspend(
                context, body.run_id, body.kind, body.payload,
                resume_at=body.resume_at, protocol_id=body.protocol_id,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"protocol_id": protocol_id}

    @app.post("/v9/waits/resume")
    def resume_wait(body: WaitResume, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        resumed = waits.resume(context, body.run_id, body.protocol_id, body.outcome)
        return {"resumed": resumed}

    @app.post("/v9/agents")
    def create_agent(body: AgentCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            if body.parent_agent_id:
                created = agents.create_ephemeral_worker(
                    context, body.parent_agent_id, body.display_name,
                    body.snapshot_id, ttl_seconds=body.ttl_seconds,
                )
            else:
                agent_id = agents.create_persistent_teammate(
                    context, body.display_name, body.snapshot_id,
                    agent_id=body.agent_id,
                )
                created = {"agent_id": agent_id, "kind": "persistent_teammate"}
        except AgentLifecycleError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"agent": created}

    @app.get("/v9/agents/{agent_id}")
    def get_agent(agent_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        agent = agents.get_agent(context, agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="agent unknown")
        return {"agent": agent}

    @app.get("/v9/waits")
    def list_waits(run_id: str | None = None, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"waits": protocol.list_waiting(context, run_id=run_id)}

    return app
