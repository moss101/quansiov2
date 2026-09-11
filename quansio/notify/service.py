"""Durable attention/notification delivery with receipt tracking (COL-003,
owner quansio-notify).

Notification records are derived from canonical events and stored durably.
Delivery is idempotent and tenant-safe, notifications expire, and receipts
(delivered_at, acknowledged_by) are tracked on the durable record. The
service never owns approval truth or task-state authority: acknowledgement
from a foreign tenant is refused and no route exists to mutate runs,
approvals or effects.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase

VALID_CHANNEL_CLASSES = {"inbox", "email", "push", "webhook"}
VALID_URGENCIES = {"low", "normal", "high", "critical"}


class NotificationRefused(Exception):
    """Notification creation refused (unknown channel/urgency or recipient)."""


class NotificationService:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def create(self, context: IdentityContext, recipient_id: str,
               channel_class: str, urgency: str, deep_link: str,
               payload: dict, ttl_seconds: int = 3600) -> dict:
        if channel_class not in VALID_CHANNEL_CLASSES:
            raise NotificationRefused(f"unknown channel class {channel_class}")
        if urgency not in VALID_URGENCIES:
            raise NotificationRefused(f"unknown urgency {urgency}")
        if ttl_seconds <= 0:
            raise NotificationRefused("ttl must be positive")
        if not isinstance(payload, dict):
            raise NotificationRefused("payload must be an object")
        notification_id = str(uuid.uuid4())
        expires_at = _expires(ttl_seconds)
        self._db.execute(
            """
            INSERT INTO notifications
                (notification_id, tenant_id, recipient_id, channel_class,
                 urgency, expires_at, deep_link, payload, state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            """,
            (notification_id, context.tenant_id, recipient_id, channel_class,
             urgency, expires_at, deep_link, Json(payload)),
        )
        return {"notification_id": notification_id, "state": "pending",
                "recipient_id": recipient_id, "channel_class": channel_class,
                "urgency": urgency}

    def get(self, context: IdentityContext, notification_id: str) -> dict:
        row = self._db.query_one(
            """
            SELECT notification_id::text, recipient_id::text, channel_class,
                   urgency, deep_link, payload, state, delivered_at,
                   acknowledged_by::text, expires_at, created_at
            FROM notifications WHERE tenant_id=%s AND notification_id=%s
            """,
            (context.tenant_id, notification_id),
        )
        if row is None:
            raise KeyError("notification unknown")
        return {
            "notification_id": row[0], "recipient_id": row[1],
            "channel_class": row[2], "urgency": row[3], "deep_link": row[4],
            "payload": row[5], "state": row[6],
            "delivered_at": _iso(row[7]), "acknowledged_by": row[8],
            "expires_at": _iso(row[9]), "created_at": _iso(row[10]),
        }

    def list_for_recipient(self, context: IdentityContext, recipient_id: str,
                           state: str | None = None) -> list[dict]:
        """Receipt view for one recipient; never exposes other tenants."""
        rows = self._db.query_all(
            """
            SELECT notification_id::text, channel_class, urgency, deep_link,
                   payload, state, delivered_at, acknowledged_by::text, expires_at
            FROM notifications
            WHERE tenant_id=%s AND recipient_id=%s AND (%s::text IS NULL OR state=%s)
            ORDER BY created_at DESC
            """,
            (context.tenant_id, recipient_id, state, state),
        )
        return [
            {
                "notification_id": r[0], "channel_class": r[1],
                "urgency": r[2], "deep_link": r[3], "payload": r[4],
                "state": r[5], "delivered_at": _iso(r[6]),
                "acknowledged_by": r[7], "expires_at": _iso(r[8]),
            }
            for r in rows
        ]

    def deliver(self, context: IdentityContext, notification_id: str) -> dict:
        """Idempotent delivery; expired notifications expire instead."""
        row = self._db.query_one(
            "SELECT state, expires_at FROM notifications WHERE tenant_id=%s"
            " AND notification_id=%s",
            (context.tenant_id, notification_id),
        )
        if row is None:
            raise KeyError("notification unknown")
        state, expires_at = row
        if state in ("delivered", "acknowledged"):
            return {"notification_id": notification_id, "state": state,
                    "duplicate": True}
        if expires_at <= datetime.now(timezone.utc):
            self._db.execute(
                "UPDATE notifications SET state='expired' WHERE tenant_id=%s"
                " AND notification_id=%s",
                (context.tenant_id, notification_id),
            )
            return {"notification_id": notification_id, "state": "expired"}
        self._db.execute(
            """
            UPDATE notifications SET state='delivered', delivered_at=now()
            WHERE tenant_id=%s AND notification_id=%s AND state='pending'
            """,
            (context.tenant_id, notification_id),
        )
        return {"notification_id": notification_id, "state": "delivered",
                "duplicate": False}

    def acknowledge(self, context: IdentityContext, notification_id: str,
                    acknowledging_tenant: str, ack_by: str) -> dict:
        """Receipt tracking: acknowledgement is recorded on the durable
        record; a foreign-tenant acknowledgement is refused (COL-003-N01).
        The acknowledging tenant must match the server-resolved context."""
        if acknowledging_tenant != context.tenant_id:
            raise PermissionError("wrong tenant acknowledgement refused")
        updated = 0
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE notifications SET state='acknowledged', acknowledged_by=%s
                WHERE tenant_id=%s AND notification_id=%s AND state='delivered'
                """,
                (ack_by, context.tenant_id, notification_id),
            )
            updated = cursor.rowcount
        if updated != 1:
            row = self._db.query_one(
                "SELECT state FROM notifications WHERE tenant_id=%s AND notification_id=%s",
                (context.tenant_id, notification_id),
            )
            if row is None:
                raise KeyError("notification unknown")
            raise NotificationRefused(
                f"notification in state {row[0]} cannot be acknowledged"
            )
        return {"notification_id": notification_id, "state": "acknowledged",
                "acknowledged_by": ack_by}

    def deliver_pending_after_outage(self, context: IdentityContext) -> int:
        """COL-003-R01: deliver eligible pending notifications after a
        delivery outage without touching task/approval state."""
        row = self._db.query_one(
            """
            SELECT count(*) FROM notifications
            WHERE tenant_id=%s AND state='pending' AND expires_at > now()
            """,
            (context.tenant_id,),
        )
        pending = row[0]
        if pending:
            self._db.execute(
                """
                UPDATE notifications SET state='delivered', delivered_at=now()
                WHERE tenant_id=%s AND state='pending' AND expires_at > now()
                """,
                (context.tenant_id,),
            )
        return pending


def _expires(ttl_seconds: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)


def _iso(value):
    return value.isoformat() if value is not None else None
