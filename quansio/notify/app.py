"""quansio-notify HTTP surface: durable attention/notification delivery.

All routes resolve identity from a quansio-control bearer session; the
tenant/workspace scope of every notification comes from the server-resolved
context, never from the request body. The service exposes only delivery and
receipt behavior — no approval truth and no task-state authority.
"""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from quansio.control.identity import ControlService
from quansio.notify.service import (
    NotificationRefused,
    NotificationService,
)
from quansio.platform.db import PlatformDatabase, database_config
from quansio.platform.service import (
    add_cors,
    add_health_routes,
    default_database,
    identity_view,
    resolve_bearer,
)


class NotificationCreate(BaseModel):
    recipient_id: str
    channel_class: str
    urgency: str
    deep_link: str
    payload: dict
    ttl_seconds: int = 3600


class AcknowledgeRequest(BaseModel):
    ack_by: str


def create_app(database: PlatformDatabase | None = None) -> FastAPI:
    app = FastAPI(title="quansio-notify", version="9.0.0")
    add_cors(app)
    db = database or default_database()
    control = ControlService(db)
    notifications = NotificationService(db)

    add_health_routes(app, db, "quansio-notify")

    @app.post("/v9/notifications")
    def create_notification(
        body: NotificationCreate, authorization: str = Header(default="")
    ) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            created = notifications.create(
                context,
                recipient_id=body.recipient_id,
                channel_class=body.channel_class,
                urgency=body.urgency,
                deep_link=body.deep_link,
                payload=body.payload,
                ttl_seconds=body.ttl_seconds,
            )
        except NotificationRefused as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"notification": created, "identity": identity_view(context)}

    @app.get("/v9/notifications/{notification_id}")
    def get_notification(
        notification_id: str, authorization: str = Header(default="")
    ) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return {"notification": notifications.get(context, notification_id)}
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/v9/notifications")
    def list_notifications(
        recipient_id: str,
        state: str | None = None,
        authorization: str = Header(default=""),
    ) -> dict:
        context = resolve_bearer(authorization, control)
        return {
            "notifications": notifications.list_for_recipient(
                context, recipient_id, state=state
            )
        }

    @app.post("/v9/notifications/{notification_id}/deliver")
    def deliver_notification(
        notification_id: str, authorization: str = Header(default="")
    ) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return notifications.deliver(context, notification_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/v9/notifications/{notification_id}/acknowledge")
    def acknowledge_notification(
        notification_id: str,
        body: AcknowledgeRequest,
        authorization: str = Header(default=""),
    ) -> dict:
        context = resolve_bearer(authorization, control)
        try:
            return notifications.acknowledge(
                context, notification_id,
                acknowledging_tenant=context.tenant_id,
                ack_by=body.ack_by,
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except (PermissionError, NotificationRefused) as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    @app.post("/v9/notifications/deliver-pending")
    def deliver_pending(authorization: str = Header(default="")) -> dict:
        context = resolve_bearer(authorization, control)
        delivered = notifications.deliver_pending_after_outage(context)
        return {"delivered": delivered}

    return app
