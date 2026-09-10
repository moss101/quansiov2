"""Argument-bound policy decisions (SEC-002, owner quansio-control).

Every consequential operation gets a versioned PolicyDecision computed from
actor, semantic operation, normalized arguments, target, data
classification and the admitted capability snapshot. The decision binds the
normalized argument scope digest: re-using a decision after any
consequential argument changes fails the scope check before execution.
While the policy service is unavailable the engine fails closed — pending
consequential work requires a fresh decision after recovery.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase

POLICY_REVISION = "policy/1"
DECISION_TTL_MINUTES = 15
CONSEQUENTIAL_ARGUMENT_KEYS = {
    "amount", "payee", "target", "path", "url", "recipient", "account",
    "operation", "resource", "query", "receiver",
}


class PolicyUnavailable(Exception):
    """The policy service cannot produce a decision (fail closed)."""


class PolicyDenied(Exception):
    """Policy denied the operation."""


class ScopeDigestMismatch(Exception):
    """Execution arguments no longer match the bound decision scope."""


class PolicyEngine:
    def __init__(self, database: PlatformDatabase, dependency_available: bool = True):
        self._db = database
        self._available = dependency_available

    def set_dependency_available(self, available: bool) -> None:
        self._available = available

    @staticmethod
    def normalize_arguments(arguments: dict) -> dict:
        """Canonical argument normalization: sorted keys, trimmed strings,
        consequential keys only — this is what the scope digest binds."""
        normalized = {}
        for key in sorted(arguments):
            if key in CONSEQUENTIAL_ARGUMENT_KEYS:
                value = arguments[key]
                normalized[key] = value.strip() if isinstance(value, str) else value
        return normalized

    @staticmethod
    def scope_digest(arguments: dict) -> str:
        normalized = PolicyEngine.normalize_arguments(arguments)
        return hashlib.sha256(
            json.dumps(normalized, sort_keys=True).encode()
        ).hexdigest()

    def decide(
        self,
        context: IdentityContext,
        actor_id: str,
        operation: str,
        arguments: dict,
        target: str,
        data_classification: list[str],
        capability_snapshot_id: str | None = None,
    ) -> dict:
        if not self._available:
            raise PolicyUnavailable("policy service unavailable; refusing to decide (fail closed)")
        digest = self.scope_digest(arguments)
        if "secret" in data_classification and operation != "secret.read":
            decision = "DENY"
        elif operation in ("payment.transfer", "email.send", "file.publish"):
            decision = "REQUIRE_APPROVAL"
        else:
            decision = "DENY" if "restricted" in data_classification else "ALLOW"
        policy_decision_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=DECISION_TTL_MINUTES)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO policy_decisions
                    (tenant_id, policy_decision_id, actor_id, operation,
                     argument_scope_digest, target, data_classification,
                     capability_snapshot_id, decision, policy_revision, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (context.tenant_id, policy_decision_id, actor_id, operation,
                 digest, target, Json(data_classification),
                 capability_snapshot_id, decision, POLICY_REVISION, expires_at),
            )
        return {
            "policy_decision_id": policy_decision_id,
            "decision": decision,
            "argument_scope_digest": digest,
            "policy_revision": POLICY_REVISION,
            "expires_at": expires_at,
        }

    def check_scope(self, decision: dict, arguments: dict) -> None:
        """Bind execution to the decision: normalized arguments must hash to
        the recorded scope digest (MOD-style gate before any actuation)."""
        current = self.scope_digest(arguments)
        if current != decision["argument_scope_digest"]:
            raise ScopeDigestMismatch(
                f"argument scope mismatch: decision bound {decision['argument_scope_digest'][:12]}, "
                f"execution arguments hash {current[:12]}"
            )

    def require_fresh(self, decision: dict) -> dict:
        """Pending consequential work may not execute on stale or
        unknown-state decisions; recovery demands a fresh evaluation."""
        if decision["expires_at"] <= datetime.now(timezone.utc):
            raise PolicyUnavailable("decision expired; fresh decision required")
        return decision
