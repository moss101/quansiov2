"""quansio-worker-gateway HTTP surface: governed file transfer, personal
endpoint relay, browser sessions and observation evidence.

Typed worker/guest transport with lease/generation validation lives with the
machine-control owner; this gateway owns the worker-facing transport of
transfers, relay envelopes and browser observations over authenticated
routes.
"""

from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.identity import ControlService
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import (
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)
from quansio.worker_gateway.browser import (
    BrowserAccessDenied,
    BrowserSessionManager,
    DegradedObservation,
    EffectClassificationRequired,
    SemanticEffectClassifier,
    StalePageIdentity,
    StructuredBrowserController,
    TakeoverService,
    TakeoverStateError,
)
from quansio.worker_gateway.transfer_relay import (
    EnvelopeRefused,
    EndpointRelay,
    GovernedFileTransfer,
    ObservationEvidenceStore,
    TransferDenied,
)

RELAY_TIMEOUT_SECONDS = float(os.environ.get("QUANSIO_RELAY_TIMEOUT", "10"))


class TransferUploadGrant(BaseModel):
    session_id: str
    artifact_digest: str


class TransferDownloadGrant(BaseModel):
    session_id: str
    artifact_digest: str
    content: str | bytes


class TransferComplete(BaseModel):
    final_digest: str


class RelayDispatch(BaseModel):
    envelope: dict


class ObservationPersist(BaseModel):
    session_id: str
    run_id: str
    step_id: str
    page_epoch: int
    kind: str
    content: dict


class BrowserCreate(BaseModel):
    target_id: str
    generation: int


class BrowserAct(BaseModel):
    session_id: str
    action: str
    arguments: dict
    page_epoch: int
    run_id: str
    step_id: str
    declared_effect_class: str | None = None


class BrowserObserve(BaseModel):
    session_id: str
    run_id: str
    step_id: str
    structured_available: bool = True


class TakeoverRequest(BaseModel):
    human_id: str


def _endpoint_actuator(envelope: dict) -> dict:
    """Actuate a personal-endpoint envelope against its configured relay.

    The relay URL for an endpoint is configured out of band
    (``QUANSIO_ENDPOINT_RELAY_URL_<ENDPOINT_ID>``); an unconfigured endpoint
    is a typed refusal, never a simulated success.
    """
    url = os.environ.get(f"QUANSIO_ENDPOINT_RELAY_URL_{envelope['endpoint_id']}")
    if not url:
        raise EnvelopeRefused(
            f"no relay configured for endpoint {envelope['endpoint_id']}"
        )
    try:
        response = httpx.post(
            url, json={"envelope": envelope}, timeout=RELAY_TIMEOUT_SECONDS
        )
    except httpx.TimeoutException as error:
        raise TimeoutError(f"endpoint relay {envelope['endpoint_id']} timed out") from error
    return {"status": response.status_code,
            "response": response.json() if response.content else {}}


def _artifact_record(digest: str):
    """Artifact existence check through the artifact catalog; the gateway
    holds no artifact authority and fails closed when the catalog is
    unreachable."""
    try:
        database = PlatformDatabase(database_config(), max_size=1)
    except Exception:  # noqa: BLE001 - no artifact boundary configured
        return None
    try:
        row = database.query_one(
            "SELECT digest, scan_state FROM artifact_records WHERE digest = %s",
            (digest,),
        )
        return {"digest": row[0], "scan_state": row[1]} if row else None
    except Exception:  # noqa: BLE001 - fail closed
        return None
    finally:
        database.close()


def create_app(database: PlatformDatabase | None = None,
               endpoint_actuator=None) -> FastAPI:
    app = FastAPI(title="quansio-worker-gateway", version="9.0.0")
    db = database or default_database()
    control = ControlService(db)
    transfers = GovernedFileTransfer(db, artifact_lookup=_artifact_record)
    relay = EndpointRelay(db)
    observations = ObservationEvidenceStore(db)
    sessions = BrowserSessionManager(db)
    controller = StructuredBrowserController(db, sessions)
    classifier = SemanticEffectClassifier(db, ledger=None)
    takeover = TakeoverService(db, sessions)
    actuate = endpoint_actuator or _endpoint_actuator

    add_health_routes(app, db, "quansio-worker-gateway")

    @app.post("/v9/transfers/uploads/grants")
    def grant_upload(body: TransferUploadGrant, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return transfers.grant_upload(
                context, body.session_id, body.artifact_digest
            )
        except TransferDenied as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @app.post("/v9/transfers/downloads/grants")
    def grant_download(body: TransferDownloadGrant, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return transfers.grant_download(
                context, body.session_id, body.artifact_digest, body.content
            )
        except TransferDenied as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @app.post("/v9/transfers/{transfer_id}/complete")
    def complete_transfer(transfer_id: str, body: TransferComplete, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return transfers.complete(context, transfer_id, body.final_digest)
        except (TransferDenied, KeyError) as error:
            status = 404 if isinstance(error, KeyError) else 409
            raise HTTPException(status_code=status, detail=str(error)) from error

    @app.post("/v9/relay/dispatch")
    def dispatch_relay(body: RelayDispatch, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return relay.dispatch(context, body.envelope, actuate)
        except EnvelopeRefused as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except TimeoutError as error:
            raise HTTPException(status_code=524, detail=str(error)) from error

    @app.post("/v9/observations")
    def persist_observation(body: ObservationPersist, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return observations.persist(
            context, body.session_id, body.run_id, body.step_id,
            body.page_epoch, body.kind, body.content,
        )

    @app.post("/v9/browser/sessions")
    def create_browser_session(body: BrowserCreate, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        return {"session": sessions.create(context, body.target_id, body.generation)}

    @app.get("/v9/browser/sessions/{session_id}")
    def get_browser_session(session_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"session": sessions.get(context, session_id)}
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/v9/browser/act")
    def browser_act(body: BrowserAct, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        classified = classifier.classify(body.action, body.arguments)
        # A consequential classification must be declared and matched;
        # harmless actions actuate without an effect record.
        if classified is not None and classified != body.declared_effect_class:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"action classifies as consequential {classified!r}; declared "
                    f"effect class {body.declared_effect_class!r} does not match"
                ),
            )
        try:
            return {"result": controller.act(
                context, body.session_id, body.action, body.arguments,
                page_epoch=body.page_epoch, run_id=body.run_id,
                step_id=body.step_id,
            )}
        except (BrowserAccessDenied, StalePageIdentity, DegradedObservation,
                EffectClassificationRequired) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/v9/browser/observe")
    def browser_observe(body: BrowserObserve, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"observation": controller.observe(
                context, body.session_id, body.run_id, body.step_id,
                structured_available=body.structured_available,
            )}
        except DegradedObservation as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/v9/browser/sessions/{session_id}/takeover")
    def browser_takeover(session_id: str, body: TakeoverRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"takeover": takeover.takeover(context, session_id, body.human_id)}
        except TakeoverStateError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.post("/v9/browser/sessions/{session_id}/return-control")
    def browser_return(session_id: str, body: TakeoverRequest, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"control": takeover.return_control(context, session_id, body.human_id)}
        except TakeoverStateError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return app
