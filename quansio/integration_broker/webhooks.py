"""Authenticated idempotent webhook ingress (EXT-003, owner
quansio-integration-broker).

Webhook sources authenticate by per-source HMAC; ingress records are
idempotent by event identity, and work creation resumes exactly once after a
crash between the ingress record and work creation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from typing import Callable

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class WebhookIngress:
    def __init__(self, database: PlatformDatabase, source_secrets: dict[str, str],
                 work_creator: Callable[[dict], str]):
        self._db = database
        self._secrets = source_secrets
        self._work_creator = work_creator

    def verify_signature(self, source_name: str, body: bytes,
                         provided_signature: str) -> bool:
        secret = self._secrets.get(source_name)
        if secret is None:
            return False
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, provided_signature)

    def ingress(self, context: IdentityContext, source_name: str, body: bytes,
                provided_signature: str, event_identity: str) -> dict:
        if not self.verify_signature(source_name, body, provided_signature):
            raise PermissionError(f"invalid webhook source authentication for {source_name}")
        existing = self._db.query_one(
            "SELECT webhook_id::text, state, work_ref FROM webhook_ingress WHERE tenant_id=%s AND event_identity=%s",
            (context.tenant_id, event_identity),
        )
        if existing is not None:
            return {"webhook_id": existing[0], "state": existing[1],
                    "work_ref": existing[2], "duplicate": True}
        webhook_id = str(uuid.uuid4())
        payload = json.loads(body.decode() or "{}")
        self._db.execute(
            """
            INSERT INTO webhook_ingress
                (tenant_id, webhook_id, source_name, signature_valid,
                 event_identity, payload, state)
            VALUES (%s, %s, %s, true, %s, %s, 'received')
            """,
            (context.tenant_id, webhook_id, source_name, event_identity, Json(payload)),
        )
        return {"webhook_id": webhook_id, "state": "received", "duplicate": False}

    def create_work(self, context: IdentityContext, webhook_id: str) -> dict:
        """EXT-003-R01: resume exactly once from the recorded webhook
        identity after a crash between ingress record and work creation."""
        row = self._db.query_one(
            "SELECT state, work_ref, payload FROM webhook_ingress"
            " WHERE tenant_id=%s AND webhook_id=%s",
            (context.tenant_id, webhook_id),
        )
        if row is None:
            raise KeyError("webhook unknown")
        state, work_ref, payload = row
        if state == "work_created":
            return {"work_ref": work_ref, "created_now": False}
        work_ref = work_ref or self._work_creator(payload)
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE webhook_ingress SET state='work_created', work_ref=%s
                WHERE tenant_id=%s AND webhook_id=%s AND state='received'
                """,
                (work_ref, context.tenant_id, webhook_id),
            )
            created_now = cursor.rowcount == 1
        return {"work_ref": work_ref, "created_now": created_now}
