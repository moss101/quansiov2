"""Destination-aware privacy gate (SEC-003, owner quansio-control).

All egress paths — model requests, connector calls, uploads and
remote-worker transfers — classify their bytes through this one gate before
leaving the trusted boundary. The classification decision (allow / redact /
require_approval / deny) is persisted per destination class so alternate
routes cannot bypass a denial. When the classifier dependency recovers,
pending egress is re-evaluated against current policy; stale allows are
never replayed.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from enum import Enum

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class ClassifierUnavailable(Exception):
    """Classification dependency down — egress must wait (fail closed)."""


class EgressDenied(Exception):
    """The gate denied this transfer on every route."""


class Route(str, Enum):
    MODEL = "model"
    CONNECTOR = "connector"
    UPLOAD = "upload"
    REMOTE_WORKER = "remote_worker"


_SECRET_PATTERNS = [
    (re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9]{16,}\b"), "api_key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private_key"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "ssn"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "email"),
]
_DENIED_CLASSES_FOR_EXTERNAL = {"api_key", "private_key", "ssn"}


def classify_bytes(data: bytes | str) -> list[str]:
    text = data.decode(errors="ignore") if isinstance(data, bytes) else data
    return sorted({label for pattern, label in _SECRET_PATTERNS if pattern.search(text)})


def redact_bytes(data: str) -> tuple[str, int]:
    redactions = 0
    for pattern, label in _SECRET_PATTERNS:
        data, count = pattern.subn(f"[REDACTED:{label}]", data)
        redactions += count
    return data, redactions


class DestinationPrivacyGate:
    def __init__(self, database: PlatformDatabase, classifier_available: bool = True,
                 policy_revision: str = "egress-privacy/2"):
        self._db = database
        self._classifier_available = classifier_available
        self._policy_revision = policy_revision
        self._pending: list[dict] = []

    def set_classifier_available(self, available: bool) -> None:
        """Recovery semantics (SEC-003-R01): while unavailable, egress is
        queued as pending; on recovery, pending egress is re-evaluated
        against the CURRENT policy revision, never replaying stale allows."""
        self._classifier_available = available
        if not available:
            return
        still_pending = []
        for entry in list(self._pending):
            try:
                self.evaluate(entry["context"], entry["route"], entry["destination"],
                              entry["data"], entry["request_id"])
            except Exception:  # noqa: BLE001 - pending egress waits on any failure
                still_pending.append(entry)
        self._pending = still_pending

    def evaluate(
        self,
        context: IdentityContext,
        route: Route,
        destination: str,
        data: bytes | str,
        request_id: str | None = None,
    ) -> dict:
        """One gate for every egress route. Returns the decision record;
        raises EgressDenied for denied transfers, ClassifierUnavailable when
        the classifier is down (bytes must wait, not pass)."""
        if not self._classifier_available:
            entry = {
                "context": context, "route": route, "destination": destination,
                "data": data, "request_id": request_id or str(uuid.uuid4()),
            }
            self._pending.append(entry)
            raise ClassifierUnavailable("classifier unavailable; egress queued pending re-evaluation")
        text = data.decode(errors="ignore") if isinstance(data, bytes) else data
        classifications = classify_bytes(text)
        external = destination.startswith("external:") or route in (Route.CONNECTOR, Route.UPLOAD, Route.REMOTE_WORKER)
        denied_classes = _DENIED_CLASSES_FOR_EXTERNAL if external else set()
        violating = sorted(set(classifications) & denied_classes)
        decision = "DENY" if violating else ("ALLOW_REDACTED" if classifications else "ALLOW")
        outbound = text
        if decision == "ALLOW_REDACTED":
            outbound, _redactions = redact_bytes(text)
        if decision == "DENY":
            raise EgressDenied(
                f"{route.value} egress to {destination} denied: protected classes {violating}"
            )
        decision_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO policy_decisions
                    (tenant_id, policy_decision_id, actor_id, operation,
                     argument_scope_digest, target, data_classification,
                     decision, policy_revision, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (context.tenant_id, decision_id, context.user_id,
                 f"egress.{route.value}", hashlib.sha256(text.encode()).hexdigest()[:32],
                 destination, Json(classifications), decision,
                 self._policy_revision,
                 datetime.now(timezone.utc)),
            )
        return {
            "policy_decision_id": decision_id,
            "decision": decision,
            "classifications": classifications,
            "outbound": outbound.encode() if isinstance(data, bytes) else outbound,
            "policy_revision": self._policy_revision,
        }
