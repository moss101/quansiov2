"""quansio-integration-broker HTTP surface.

The broker mediates typed connector operations and webhook ingress. Secret
registration and handle issuance are exposed for configuration; handle
exchange happens only server-side inside the mediation path — no route ever
returns secret material. Webhook sources authenticate by per-source HMAC
plus a quansio-control session for tenant scoping.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

from quansio.control.broker import CredentialBroker, HandleRefused
from quansio.control.effects import EffectLedger, EffectRequired
from quansio.control.identity import ControlService
from quansio.integration_broker.adapters import ConnectorBroker
from quansio.integration_broker.webhooks import WebhookIngress
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import (
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)

CONNECTOR_TIMEOUT_SECONDS = float(os.environ.get("QUANSIO_CONNECTOR_TIMEOUT", "10"))


class SecretRegistration(BaseModel):
    secret_id: str
    provider: str
    secret_material: str


class HandleIssue(BaseModel):
    secret_id: str
    operation: str
    target: str
    capability: str


class ConnectorOperation(BaseModel):
    effect_id: str
    handle_id: str
    operation: str
    target: str
    arguments: dict


def _mediated_transport(material: str, operation: str, target: str,
                        arguments: dict) -> dict:
    """Perform the real external call inside the broker trust boundary.

    The target is a first-party connector endpoint; the broker-exchanged
    handle material is carried in the ``X-Quansio-Handle`` contract header.
    Deployments needing third-party authorization schemes inject a transport
    via ``create_app(connector_transport=...)``. Timeouts surface as UNKNOWN
    effects via the ledger.
    """
    try:
        response = httpx.post(
            target,
            json={"operation": operation, "arguments": arguments},
            headers={"X-Quansio-Handle": material},
            timeout=CONNECTOR_TIMEOUT_SECONDS,
        )
    except httpx.TimeoutException as error:
        raise TimeoutError(f"connector target {target} timed out") from error
    return {
        "status": response.status_code,
        "response": response.json() if response.content else {},
    }


def _default_work_creator(payload: dict) -> str:
    """Work creation without a runtime bound records an explicit pending
    work reference; the broker never invents task truth."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"pending-webhook-work-{stamp}"


def create_app(database: PlatformDatabase | None = None,
               webhook_secrets: dict[str, str] | None = None,
               work_creator=None) -> FastAPI:
    app = FastAPI(title="quansio-integration-broker", version="9.0.0")
    db = database or default_database()
    control = ControlService(db)
    credentials = CredentialBroker(db)
    effects = EffectLedger(db)
    connectors = ConnectorBroker(db, credentials, effects)
    secrets = webhook_secrets if webhook_secrets is not None else {
        name.removeprefix("QUANSIO_WEBHOOK_SECRET_").lower(): value
        for name, value in os.environ.items()
        if name.startswith("QUANSIO_WEBHOOK_SECRET_")
    }
    ingress = WebhookIngress(db, secrets, work_creator or _default_work_creator)

    add_health_routes(app, db, "quansio-integration-broker")

    @app.post("/v9/secrets")
    def register_secret(body: SecretRegistration, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        generation = credentials.register_secret(
            context, body.secret_id, body.provider, body.secret_material
        )
        # Only the generation is echoed; material is never returned.
        return {"secret_id": body.secret_id, "generation": generation}

    @app.post("/v9/secrets/{secret_id}/rotate")
    def rotate_secret(secret_id: str, body: SecretRegistration, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        generation = credentials.rotate(context, secret_id, body.secret_material)
        return {"secret_id": secret_id, "generation": generation,
                "outstanding_handles_invalidated": True}

    @app.post("/v9/secrets/{secret_id}/handles")
    def issue_handle(secret_id: str, body: HandleIssue, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            handle = credentials.issue(
                context, secret_id, body.operation, body.target, body.capability
            )
        except HandleRefused as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"handle": handle}

    @app.post("/v9/connector-operations")
    def execute_connector_operation(body: ConnectorOperation, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            outcome = connectors.execute_connector_operation(
                context, body.effect_id, body.handle_id, body.operation,
                body.target, body.arguments, _mediated_transport,
            )
        except TimeoutError as error:
            raise HTTPException(status_code=524, detail=str(error)) from error
        except (EffectRequired, HandleRefused, PermissionError, KeyError) as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        return {"outcome": outcome, "identity": identity_view(context)}

    @app.post("/v9/webhooks/{source_name}/ingest")
    async def ingest_webhook(
        source_name: str,
        request: Request,
        x_webhook_signature: str = Header(default=""),
        x_webhook_event_identity: str = Header(default=""),
        authorization: str = Header(default=""),
    ) -> dict:
        context = resolve_bearer(authorization, control)
        body = await request.body()
        try:
            received = ingress.ingress(
                context, source_name, body, x_webhook_signature,
                x_webhook_event_identity,
            )
        except PermissionError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
        return {"webhook": received}

    @app.post("/v9/webhooks/{webhook_id}/work")
    def create_webhook_work(webhook_id: str, authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return ingress.create_work(context, webhook_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    return app
