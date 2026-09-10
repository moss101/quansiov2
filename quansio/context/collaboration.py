"""Collaboration as runtime projections (COL-001), durable typed handoffs
(COL-002), attention/notifications (COL-003) and persistent teammate
routines (COL-004). Owners: quansio-runtime projections; quansio-notify
delivery.

Rooms/groups/threads are projections of participants and typed
turn/message relations over canonical agents — never a second scheduler or
task authority. Handoffs persist identity, sender, recipients, target turn,
payload/artifact refs, capability context and delivery outcome with
idempotent delivery. Notifications are derived from canonical events,
expire, and never own approval truth.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class CollaborationOwnershipViolation(Exception):
    """COL-001-N01: a collaboration-specific queue tried to mutate task state."""


class HandoffRefused(Exception):
    """COL-002-N01: duplicate handoff or cancelled/unauthorized target."""


class CollaborationProjection:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def create_room(self, context: IdentityContext, name: str) -> str:
        room_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO collaborator_rooms (tenant_id, room_id, name, workspace_id)
            VALUES (%s, %s, %s, %s)
            """,
            (context.tenant_id, room_id, name, context.workspace_id),
        )
        return room_id

    def join(self, context: IdentityContext, room_id: str, agent_id: str,
             role: str = "member") -> None:
        self._db.execute(
            """
            INSERT INTO room_participants (tenant_id, room_id, agent_id, role)
            VALUES (%s, %s, %s, %s)
            """,
            (context.tenant_id, room_id, agent_id, role),
        )

    def post_message(self, context: IdentityContext, room_id: str,
                     sender_agent: str, payload: dict,
                     turn_id: str | None = None,
                     capability_context: str = "task",
                     artifact_refs: list[str] | None = None,
                     delivery_state: str = "delivered") -> str:
        message_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO room_messages
                (message_id, tenant_id, room_id, turn_id, sender_agent, payload,
                 artifact_refs, capability_context, delivery_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (message_id, context.tenant_id, room_id, turn_id, sender_agent,
             Json(payload), artifact_refs or [], capability_context, delivery_state),
        )
        return message_id

    def projection(self, context: IdentityContext, room_id: str) -> dict:
        """COL-001-R01: rebuild the complete collaboration projection from
        canonical events/results — pure derived read."""
        participants = self._db.query_all(
            "SELECT agent_id::text, role FROM room_participants"
            " WHERE tenant_id=%s AND room_id=%s ORDER BY joined_at",
            (context.tenant_id, room_id),
        )
        messages = self._db.query_all(
            "SELECT message_id::text, sender_agent::text, payload, delivery_state,"
            " capability_context FROM room_messages"
            " WHERE tenant_id=%s AND room_id=%s ORDER BY created_at",
            (context.tenant_id, room_id),
        )
        return {
            "room_id": room_id,
            "participants": [{"agent_id": p[0], "role": p[1]} for p in participants],
            "messages": [{"message_id": m[0], "sender": m[1],
                          "payload": m[2], "delivery_state": m[3],
                          "capability_context": m[4]} for m in messages],
        }

    def reject_shadow_queue(self, context: IdentityContext, room_id: str,
                            proposed_queue: dict) -> None:
        """COL-001-N01: a collaboration-specific execution queue that could
        mutate task state independently is refused at ownership check."""
        if proposed_queue.get("mutates_task_state"):
            raise CollaborationOwnershipViolation(
                "collaboration projections cannot own task-state mutation;"
                " use the canonical runtime"
            )


class HandoffService:
    """COL-002: durable typed handoffs with idempotent delivery."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def deliver(self, context: IdentityContext, room_id: str,
                sender_agent: str, recipient_agent: str,
                target_turn_id: str, payload: dict,
                capability_context: str,
                artifact_refs: list[str] | None = None,
                worker_status: str = "running") -> dict:
        """Idempotent by (room, target turn, recipient): a duplicate delivery
        returns the original message without new work; a cancelled or
        unauthorized target worker refuses delivery."""
        if worker_status == "cancelled":
            raise HandoffRefused("target worker cancelled")
        if worker_status == "unauthorized":
            raise HandoffRefused("target worker unauthorized for this capability")
        existing = self._db.query_one(
            """
            SELECT message_id::text FROM room_messages
            WHERE tenant_id=%s AND room_id=%s AND turn_id=%s
              AND sender_agent=%s AND payload=%s::jsonb
            """,
            (context.tenant_id, room_id, target_turn_id, sender_agent,
             Json(payload)),
        )
        if existing is not None:
            return {"message_id": existing[0], "duplicate": True}
        message_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO room_messages
                (message_id, tenant_id, room_id, turn_id, sender_agent, payload,
                 artifact_refs, capability_context, delivery_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'delivered')
            """,
            (message_id, context.tenant_id, room_id, target_turn_id,
             sender_agent, Json(payload), artifact_refs or [],
             capability_context),
        )
        return {"message_id": message_id, "duplicate": False}

    def mark_failed(self, context: IdentityContext, message_id: str) -> None:
        self._db.execute(
            "UPDATE room_messages SET delivery_state='failed' WHERE tenant_id=%s"
            " AND message_id=%s AND delivery_state='pending'",
            (context.tenant_id, message_id),
        )


class NotificationService:
    """COL-003: attention/notification records derived from canonical
    events. Delivery is idempotent and tenant-safe; the service never owns
    approval truth."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def create(self, context: IdentityContext, recipient_id: str,
               channel_class: str, urgency: str, deep_link: str,
               payload: dict, ttl_seconds: int = 3600) -> dict:
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
        return {"notification_id": notification_id, "state": "pending"}

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
        if expires_at <= _expires(0):
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
        return {"notification_id": notification_id, "state": "delivered"}

    def acknowledge(self, context: IdentityContext, notification_id: str,
                    acknowledging_tenant: str, ack_by: str) -> dict:
        """COL-003-N01: acknowledgement from the wrong tenant is refused."""
        if acknowledging_tenant != context.tenant_id:
            raise PermissionError("wrong tenant acknowledgement refused")
        self._db.execute(
            """
            UPDATE notifications SET state='acknowledged', acknowledged_by=%s
            WHERE tenant_id=%s AND notification_id=%s AND state='delivered'
            """,
            (ack_by, context.tenant_id, notification_id),
        )
        return {"notification_id": notification_id, "acknowledged_by": ack_by}

    def deliver_pending_after_outage(self, context: IdentityContext) -> int:
        """COL-003-R01: deliver eligible pending notifications without
        touching task/approval state."""
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


def _expires(ttl_seconds: int):
    from datetime import datetime, timedelta, timezone

    return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)


def _now_utc():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


class TeammateRoutineService:
    """COL-004: routines bound to a persistent teammate identity and
    schedule; each fire resolves current identity/capabilities and applies
    the missed-fire policy with durable logical-fire identities."""

    def __init__(self, database: PlatformDatabase, scheduler,
                 teammate_liveness: Callable[[IdentityContext, str], bool]):
        self._db = database
        self._scheduler = scheduler
        self._teammate_liveness = teammate_liveness

    def bind_routine(self, context: IdentityContext, teammate_agent_id: str,
                     automation_id: str, work_template: dict) -> dict:
        self._db.execute(
            """
            UPDATE automations SET work_template = work_template || %s::jsonb
            WHERE tenant_id=%s AND automation_id=%s
            """,
            (Json({"routine": {"teammate_agent_id": teammate_agent_id,
                               **work_template}}),
             context.tenant_id, automation_id),
        )
        return {"teammate_agent_id": teammate_agent_id,
                "automation_id": automation_id}

    def fire(self, context: IdentityContext, automation_id: str,
             teammate_agent_id: str, logical_fire: str) -> dict:
        """Resolve the teammate identity at fire time; a deleted/disabled
        teammate means no orphan routine starts."""
        alive = self._teammate_liveness(context, teammate_agent_id)
        if not alive:
            return {"fired": False, "reason": "teammate identity stale or retired"}
        try:
            from datetime import datetime, timedelta, timezone

            now = datetime.now(timezone.utc)
            result = self._scheduler.emit_fires(
                context, automation_id,
                now - timedelta(days=1), now + timedelta(seconds=1),
                authority_resolver=lambda c, tpl: self._resolve_authority(c, teammate_agent_id),
            )
        except Exception as error:  # noqa: BLE001 - blocked fires recorded durably
            return {"fired": False, "reason": str(error)}
        return {"fired": True, **result}

    def _resolve_authority(self, context: IdentityContext, teammate_agent_id: str) -> str:
        if not self._teammate_liveness(context, teammate_agent_id):
            raise PermissionError("teammate authority revoked before fire")
        return f"work-for-{teammate_agent_id}"
