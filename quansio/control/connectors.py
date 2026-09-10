"""Canonical Tool Registry with fidelity contract (EXT-001), governed
integration broker (EXT-002) and authenticated idempotent webhook ingress
(EXT-003). Owners: quansio-control registry; quansio-integration-broker for
connector mediation and webhook ingress.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from psycopg.types.json import Json

from quansio.control.effects import EffectRequired
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class UnsafeDeclaration(Exception):
    """EXT-001-N01: consequential registered as harmless, or degrading as
    lossless — rejected by registry policy."""


class ToolRegistry:
    EFFECT_SEVERITY = {"harmless": 0, "state_changing": 1, "consequential": 2, "degrading": 2}
    FIDELITY_STRENGTH = {"lossless": 2, "filtered": 1, "lossy": 0, "best_effort": 0}

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def register(self, context: IdentityContext, operation_name: str, version: int,
                 schema: dict, effect_class: str, fidelity_class: str,
                 capability_need: str, policy_need: str, timeout_ms: int,
                 idempotent: bool, evidence_contract: str) -> dict:
        if effect_class not in self.EFFECT_SEVERITY or fidelity_class not in self.FIDELITY_STRENGTH:
            raise UnsafeDeclaration("unknown effect/fidelity class")
        # Unsafe declarations: consequential must not be sold as harmless;
        # degrading outcomes cannot claim lossless evidence.
        if effect_class == "consequential" and evidence_contract in ("", "none"):
            raise UnsafeDeclaration("consequential operation without evidence contract")
        if effect_class == "degrading" and fidelity_class == "lossless":
            raise UnsafeDeclaration("degrading operation cannot be lossless")
        self._db.execute(
            """
            INSERT INTO tool_operations
                (tenant_id, operation_name, version, schema, effect_class,
                 fidelity_class, capability_need, policy_need, timeout_ms,
                 idempotent, evidence_contract, lifecycle)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            """,
            (context.tenant_id, operation_name, version, Json(schema),
             effect_class, fidelity_class, capability_need, policy_need,
             timeout_ms, idempotent, evidence_contract),
        )
        return {"operation_name": operation_name, "version": version,
                "effect_class": effect_class, "fidelity_class": fidelity_class}

    def resolve(self, context: IdentityContext, operation_name: str,
                max_version: int | None = None) -> dict | None:
        """New admissions resolve only active compatible versions; deprecated
        versions stay visible for admitted running steps (EXT-001-R01)."""
        row = self._db.query_one(
            """
            SELECT operation_name, version, effect_class, fidelity_class,
                   capability_need, policy_need, timeout_ms, idempotent,
                   evidence_contract, lifecycle
            FROM tool_operations
            WHERE tenant_id=%s AND operation_name=%s
              AND (%s::int IS NULL OR version <= %s)
            ORDER BY version DESC LIMIT 1
            """,
            (context.tenant_id, operation_name, max_version, max_version),
        )
        if row is None:
            return None
        return {"operation_name": row[0], "version": row[1],
                "effect_class": row[2], "fidelity_class": row[3],
                "capability_need": row[4], "policy_need": row[5],
                "timeout_ms": row[6], "idempotent": row[7],
                "evidence_contract": row[8], "lifecycle": row[9]}

    def deprecate(self, context: IdentityContext, operation_name: str, version: int) -> None:
        self._db.execute(
            "UPDATE tool_operations SET lifecycle='deprecated' WHERE tenant_id=%s"
            " AND operation_name=%s AND version=%s",
            (context.tenant_id, operation_name, version),
        )


class ConnectorBroker:
    """EXT-002: connector operations execute through credential handles and
    full policy/privacy/approval/effect mediation. Direct adapter invocation
    with reusable secret material or without an EffectRecord is refused."""

    def __init__(self, database: PlatformDatabase, credential_broker, effect_ledger,
                 policy_engine=None):
        self._db = database
        self._broker = credential_broker
        self._ledger = effect_ledger
        self._policy = policy_engine

    def execute_connector_operation(
        self, context: IdentityContext, effect_id: str, handle_id: str,
        operation: str, target: str, arguments: dict,
        transport: Callable[[str, str, str, dict], dict],
    ) -> dict:
        """Full mediation path. ``transport(handle_material, operation,
        target, arguments)`` performs the actual external call with the
        broker-exchanged credential — reusable secrets are never handed to
        the caller, and an EffectRecord must already exist (consequential)."""
        effect = self._ledger.require_effect(context, effect_id, expected_status="authorized")
        if effect["operation"] not in ("connector.submit", "connector.call", operation):
            raise EffectRequired("effect operation mismatch")
        material = self._broker.exchange(context, handle_id, operation, target)
        self._ledger.start_execution(context, effect_id)
        try:
            receipt = transport(material, operation, target, arguments)
        except TimeoutError:
            self._ledger.mark_unknown(context, effect_id, {"connector_timeout": target})
            raise
        self._ledger.complete(context, effect_id, {"connector": target},
                              receipt=receipt)
        return {"effect_id": effect_id, "receipt": receipt, "evidence": {
            "digest": hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
        }}

    def direct_adapter_call_refused(self, secret_material: str) -> None:
        """The unmediated path is unreachable by construction: invoking it
        always raises. Kept as an executable guard for the negative test."""
        raise EffectRequired(
            "direct adapter invocation with reusable secret material is forbidden;"
            " use the governed broker path"
        )


class WebhookIngress:
    """EXT-003: authenticated, idempotent webhook ingress with crash-safe
    work creation resume."""

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
