"""quansio-context HTTP surface: Context Projection, SearchProgram
execution, research records, Knowledge Fabric queries, automation
schedules and collaboration projections.

All routes resolve identity from a quansio-control bearer session. The
service owns retrieval coordination and evidence assembly; it never owns a
task scheduler beyond canonical automation schedules, and never holds an
effect path.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.identity import ControlService
from quansio.context.collaboration import (
    CollaborationOwnershipViolation,
    CollaborationProjection,
    HandoffRefused,
    HandoffService,
)
from quansio.context.executor import ExecutionError, ProgramExecutor
from quansio.context.knowledge import (
    KnowledgeFabricRecoveryRefused,
    QualificationRejected,
    StaleSynthesis,
    KnowledgeFabric,
)
from quansio.context.research_record import ResearchRecordStore
from quansio.context.retrieval import HttpRetrievalAdapter
from quansio.context.scheduler import (
    AmbiguousSchedule,
    AutomationDenied,
    AutomationService,
)
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import (
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)


class AutomationCreate(BaseModel):
    name: str
    tz_name: str
    cron: str
    fold_gap_policy: str
    catchup_policy: str
    catchup_max: int
    work_template: dict


class AutomationFireWindow(BaseModel):
    from_utc: datetime | None = None
    to_utc: datetime | None = None


class ProgramExecute(BaseModel):
    spec: dict
    seed_urls: list[str] | None = None
    program_id: str | None = None


class KnowledgeCandidateSubmit(BaseModel):
    fabric_kind: str
    content: dict
    provenance: dict
    evidence_refs: list[str]
    source_epoch: str
    confidence: float
    producer: str
    run_id: str | None = None


class SynthesisCommit(BaseModel):
    producer: str
    content: dict
    evidence_refs: list[str]
    source_epoch_at_start: str
    task_epoch_at_start: str
    current_source_epoch: str
    current_task_epoch: str


class RoomCreate(BaseModel):
    name: str


class RoomJoin(BaseModel):
    agent_id: str
    role: str = "member"


class MessagePost(BaseModel):
    sender_agent: str
    payload: dict
    turn_id: str | None = None
    capability_context: str = "task"
    artifact_refs: list[str] | None = None


class HandoffDeliver(BaseModel):
    room_id: str
    sender_agent: str
    recipient_agent: str
    target_turn_id: str
    payload: dict
    capability_context: str
    artifact_refs: list[str] | None = None
    worker_status: str = "running"


def create_app(database: PlatformDatabase | None = None) -> FastAPI:
    app = FastAPI(title="quansio-context", version="9.0.0")
    db = database or default_database()
    control = ControlService(db)
    automations = AutomationService(db)
    executor = ProgramExecutor(db, HttpRetrievalAdapter(), ResearchRecordStore(db))
    knowledge = KnowledgeFabric(db)
    rooms = CollaborationProjection(db)
    handoffs = HandoffService(db)

    add_health_routes(app, db, "quansio-context")

    # -- automation schedules (AUT-*) ----------------------------------------

    @app.post("/v9/automations")
    def create_automation(body: AutomationCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return automations.create(
                context, body.name, body.tz_name, body.cron,
                body.fold_gap_policy, body.catchup_policy, body.catchup_max,
                body.work_template,
            )
        except AmbiguousSchedule as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/v9/automations/{automation_id}/fires")
    def emit_fires(automation_id: str, body: AutomationFireWindow, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        from_utc = body.from_utc or datetime.now(timezone.utc) - timedelta(days=1)
        to_utc = body.to_utc or datetime.now(timezone.utc) + timedelta(seconds=1)
        try:
            return automations.emit_fires(context, automation_id, from_utc, to_utc)
        except (KeyError, AutomationDenied) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/v9/automations/{automation_id}/{lifecycle}")
    def set_automation_lifecycle(automation_id: str, lifecycle: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        if lifecycle not in ("pause", "resume", "delete"):
            raise HTTPException(status_code=404, detail="unknown lifecycle transition")
        try:
            result = getattr(automations, lifecycle)(context, automation_id)
        except (KeyError, AutomationDenied) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"automation_id": automation_id, "lifecycle": result}

    # -- SearchProgram execution ----------------------------------------------

    @app.post("/v9/programs/execute")
    def execute_program(body: ProgramExecute, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return executor.execute(
                context, body.spec, seed_urls=body.seed_urls,
                program_id=body.program_id,
            )
        except ExecutionError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    # -- Knowledge Fabric -------------------------------------------------------

    @app.post("/v9/knowledge/candidates")
    def submit_candidate(body: KnowledgeCandidateSubmit, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return knowledge.submit_candidate(
                context, body.fabric_kind, body.content, body.provenance,
                body.evidence_refs, body.source_epoch, body.confidence,
                body.producer, run_id=body.run_id,
            )
        except QualificationRejected as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/v9/knowledge/syntheses")
    def commit_synthesis(body: SynthesisCommit, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return knowledge.commit_synthesis(
                context, body.producer, body.content, body.evidence_refs,
                body.source_epoch_at_start, body.task_epoch_at_start,
                body.current_source_epoch, body.current_task_epoch,
            )
        except (StaleSynthesis, QualificationRejected) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/v9/knowledge")
    def query_knowledge(
        fabric_kind: str | None = None,
        authorization: str = Header(default=""),
    ) -> dict:
        context = resolve_bearer(authorization, control)
        return {"entries": knowledge.query(context, fabric_kind=fabric_kind)}

    # -- collaboration projections ---------------------------------------------

    @app.post("/v9/rooms")
    def create_room(body: RoomCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"room_id": rooms.create_room(context, body.name)}

    @app.post("/v9/rooms/{room_id}/participants")
    def join_room(room_id: str, body: RoomJoin, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        rooms.join(context, room_id, body.agent_id, body.role)
        return {"joined": body.agent_id}

    @app.post("/v9/rooms/{room_id}/messages")
    def post_message(room_id: str, body: MessagePost, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"message_id": rooms.post_message(
            context, room_id, body.sender_agent, body.payload,
            turn_id=body.turn_id, capability_context=body.capability_context,
            artifact_refs=body.artifact_refs,
        )}

    @app.get("/v9/rooms/{room_id}/projection")
    def room_projection(room_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return rooms.projection(context, room_id)

    @app.post("/v9/handoffs")
    def deliver_handoff(body: HandoffDeliver, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return handoffs.deliver(
                context, body.room_id, body.sender_agent, body.recipient_agent,
                body.target_turn_id, body.payload, body.capability_context,
                artifact_refs=body.artifact_refs, worker_status=body.worker_status,
            )
        except HandoffRefused as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/v9/rooms/{room_id}/ownership-check")
    def ownership_check(room_id: str, proposed_queue: dict, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            rooms.reject_shadow_queue(context, room_id, proposed_queue)
        except CollaborationOwnershipViolation as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"accepted": True}

    return app
