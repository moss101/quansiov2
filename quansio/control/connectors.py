"""Canonical Tool Registry with fidelity contract (EXT-001, owner
quansio-control).

The registry owns tool operation declarations and lifecycle. Connector
mediation and webhook ingress are owned by ``quansio-integration-broker``
(``quansio/integration_broker``) and re-exported here for compatibility.
"""

from __future__ import annotations

from psycopg.types.json import Json

# Canonical re-exports: single implementation, integration-broker owner.
from quansio.integration_broker.adapters import ConnectorBroker  # noqa: F401
from quansio.integration_broker.webhooks import WebhookIngress  # noqa: F401
from quansio.control.effects import EffectRequired  # noqa: F401


class UnsafeDeclaration(Exception):
    """EXT-001-N01: consequential registered as harmless, or degrading as
    lossless — rejected by registry policy."""


class ToolRegistry:
    EFFECT_SEVERITY = {"harmless": 0, "state_changing": 1, "consequential": 2, "degrading": 2}
    FIDELITY_STRENGTH = {"lossless": 2, "filtered": 1, "lossy": 0, "best_effort": 0}

    def __init__(self, database):
        self._db = database

    def register(self, context, operation_name: str, version: int,
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

    def resolve(self, context, operation_name: str,
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

    def deprecate(self, context, operation_name: str, version: int) -> None:
        self._db.execute(
            "UPDATE tool_operations SET lifecycle='deprecated' WHERE tenant_id=%s"
            " AND operation_name=%s AND version=%s",
            (context.tenant_id, operation_name, version),
        )
