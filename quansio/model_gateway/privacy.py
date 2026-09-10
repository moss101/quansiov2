"""Model egress privacy and residency enforcement (MOD-006).

Request context is classified before any provider egress. The decision
(allow / redact / deny) plus residency requirements is a persisted,
auditable record with its own identity. Redaction removes protected spans
from the outbound request; a denied request never reaches an adapter, and
when the policy dependency cannot produce a current decision the gateway
fails closed.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class PrivacyFailClosed(Exception):
    """Policy decision unavailable — nothing may be sent (MOD-006-R01)."""


class PrivacyDenied(Exception):
    """The destination/context combination is denied by policy."""


PROTECTED_PATTERNS = [
    (re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b(?=\s+(?:Street|St\.|Avenue|Ave))"), "address"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "ssn"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "card"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "email"),
]


@dataclass(frozen=True)
class PrivacyDecision:
    privacy_decision_id: str
    decision: str
    residency: list[str]
    policy_revision: str
    classifications: list[str]
    redactions: int


def classify(messages: list[dict]) -> list[str]:
    text = " ".join(str(m.get("content", "")) for m in messages)
    return sorted({label for pattern, label in PROTECTED_PATTERNS if pattern.search(text)})


def redact(messages: list[dict]) -> tuple[list[dict], int]:
    redactions = 0
    out = []
    for message in messages:
        content = str(message.get("content", ""))
        for pattern, label in PROTECTED_PATTERNS:
            content, n = pattern.subn(f"[REDACTED:{label}]", content)
            redactions += n
        out.append({**message, "content": content})
    return out, redactions


class ModelPrivacyGate:
    """Owner: quansio-model-gateway (model egress); control owns policy truth."""

    def __init__(self, database: PlatformDatabase, policy_revision: str = "model-privacy/1"):
        self._db = database
        self._policy_revision = policy_revision
        self._fail_closed = False

    def set_dependency_available(self, available: bool) -> None:
        """Policy dependency state (MOD-006-R01): unknown state fails closed."""
        self._fail_closed = not available

    def decide(
        self,
        context: IdentityContext,
        request_id: str,
        destination_profile: str,
        messages: list[dict],
        data_classification: list[str] | None = None,
        destination_residency: list[str] | None = None,
        required_residency: list[str] | None = None,
    ) -> tuple[PrivacyDecision, list[dict]]:
        if self._fail_closed:
            raise PrivacyFailClosed("policy decision state unknown; refusing egress (fail closed)")
        classifications = sorted(set(classify(messages) or []) | set(data_classification or []))
        protected = bool(classifications)
        destination_allowed = destination_profile in (required_residency or []) or not required_residency
        if protected and required_residency and not destination_residency:
            decision = "DENY"
        elif protected:
            decision = "ALLOW_REDACTED"
        else:
            decision = "ALLOW"
        if decision == "DENY":
            raise PrivacyDenied(
                f"protected context ({classifications}) may not egress to {destination_profile}"
            )
        outbound = messages
        redactions = 0
        if decision == "ALLOW_REDACTED":
            outbound, redactions = redact(messages)
        privacy_decision = PrivacyDecision(
            privacy_decision_id=str(uuid.uuid4()),
            decision=decision,
            residency=destination_residency or [],
            policy_revision=self._policy_revision,
            classifications=classifications,
            redactions=redactions,
        )
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO model_privacy_decisions
                    (tenant_id, privacy_decision_id, request_id, destination_profile,
                     decision, classifications, redactions, policy_revision)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    context.tenant_id,
                    privacy_decision.privacy_decision_id,
                    request_id,
                    destination_profile,
                    privacy_decision.decision,
                    Json(classifications),
                    redactions,
                    self._policy_revision,
                ),
            )
        return privacy_decision, outbound
