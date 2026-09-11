"""quansio-model-gateway HTTP surface: exclusive model fulfillment boundary.

Admission routes capability demand against the model catalog, enforces
privacy/residency, reserves usage and persists the canonical request — all
before any provider is contacted. Fulfillment streams canonical ModelEvents
from the real provider adapters; provider credentials never leave the
gateway boundary.
"""

from __future__ import annotations

import dataclasses
import json

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from quansio.control.identity import ControlService
from quansio.model_gateway.gateway import GatewayError, ModelGateway
from quansio.model_gateway.routing import NoQualifiedRoute
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import (
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)


class ModelAdmission(BaseModel):
    run_id: str
    step_id: str
    demand: dict
    messages: list[dict]
    policy_allowed_profiles: list[str]
    required_residency: list[str]
    context_tokens: int
    budget_cents: int
    sampling: dict | None = None
    catalog_version: str | None = None


class ModelFulfillment(BaseModel):
    request_id: str
    envelope: dict
    policy_allowed_profiles: list[str] | None = None


def _jsonl(events):
    for event in events:
        yield json.dumps(dataclasses.asdict(event), default=str) + "\n"


def create_app(database: PlatformDatabase | None = None) -> FastAPI:
    app = FastAPI(title="quansio-model-gateway", version="9.0.0")
    db = database or default_database()
    control = ControlService(db)
    gateway = ModelGateway(db)

    add_health_routes(app, db, "quansio-model-gateway")

    @app.post("/v9/model/admissions")
    def admit(body: ModelAdmission, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        catalog_snapshot = (
            (body.catalog_version, []) if body.catalog_version else None
        )
        try:
            envelope = gateway.admit(
                context, body.run_id, body.step_id, body.demand,
                body.messages, body.policy_allowed_profiles,
                body.required_residency, body.context_tokens,
                body.budget_cents, sampling=body.sampling,
                catalog_snapshot=catalog_snapshot,
            )
        except NoQualifiedRoute as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except GatewayError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"envelope": envelope, "identity": identity_view(context)}

    @app.post("/v9/model/fulfillments")
    def fulfill(body: ModelFulfillment, authorization: str = Header(default="")) -> StreamingResponse:
        context = resolve_bearer(authorization, control)
        events = gateway.fulfill(
            context, body.envelope,
            policy_allowed_profiles=body.policy_allowed_profiles,
        )
        return StreamingResponse(_jsonl(events), media_type="application/x-ndjson")

    return app
