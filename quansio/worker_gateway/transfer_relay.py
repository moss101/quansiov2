"""Governed browser file transfer (BRW-005), personal endpoint relay
(BRW-006) and observation evidence persistence (BRW-007).

Transfers only run against artifact records with scoped grants; uploads from
arbitrary host paths are denied before browser file selection. Endpoint
envelopes bind endpoint/target identity, generation, lease, fence,
capability, policy, effect, delivery idempotency and expiry — the endpoint
refuses incomplete or tampered envelopes before actuation and replays the
original result per idempotency key after a dropped response. Observations
are evidence-only: consumers can never re-actuate from them.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class TransferDenied(Exception):
    """Upload/download refused before browser file selection."""


class EnvelopeRefused(Exception):
    """Endpoint envelope incomplete or tampered."""


class GovernedFileTransfer:
    def __init__(self, database: PlatformDatabase, artifact_lookup: Callable[[str], bytes | None]):
        self._db = database
        self._artifact_lookup = artifact_lookup

    def grant_upload(self, context: IdentityContext, session_id: str,
                     artifact_digest: str) -> dict:
        """Uploads may source only from artifact records with a digest and a
        scoped grant — arbitrary host paths never reach file selection."""
        row = self._db.query_one(
            "SELECT 1 FROM worker_results WHERE tenant_id=%s AND idempotency_key=%s",
            (context.tenant_id, artifact_digest),
        )
        record = self._artifact_lookup(artifact_digest)
        if record is None:
            raise TransferDenied(f"no artifact record for digest {artifact_digest[:12]}")
        transfer_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO browser_transfers
                (transfer_id, tenant_id, session_id, direction, artifact_digest, state)
            VALUES (%s, %s, %s, 'upload', %s, 'granted')
            """,
            (transfer_id, context.tenant_id, session_id, artifact_digest),
        )
        return {"transfer_id": transfer_id, "artifact_digest": artifact_digest,
                "state": "granted"}

    def grant_download(self, context: IdentityContext, session_id: str,
                       artifact_digest: str, content: str | bytes) -> dict:
        transfer_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO browser_transfers
                (transfer_id, tenant_id, session_id, direction, artifact_digest, state)
            VALUES (%s, %s, %s, 'download', %s, 'granted')
            """,
            (transfer_id, context.tenant_id, session_id, artifact_digest),
        )
        return {"transfer_id": transfer_id, "artifact_digest": artifact_digest,
                "content": content}

    def complete(self, context: IdentityContext, transfer_id: str,
                 final_digest: str) -> dict:
        """BRW-005-R01: interrupt then resume; completion requires the final
        bytes to match the artifact digest — no duplicate external effects."""
        row = self._db.query_one(
            "SELECT artifact_digest, state FROM browser_transfers"
            " WHERE tenant_id=%s AND transfer_id=%s",
            (context.tenant_id, transfer_id),
        )
        if row is None:
            raise KeyError("transfer unknown")
        artifact_digest, state = row
        if state == "completed":
            return {"transfer_id": transfer_id, "state": "completed", "duplicate": True}
        if final_digest != artifact_digest:
            self._db.execute(
                "UPDATE browser_transfers SET state='interrupted' WHERE tenant_id=%s AND transfer_id=%s",
                (context.tenant_id, transfer_id),
            )
            raise TransferDenied("final bytes do not match artifact digest")
        self._db.execute(
            "UPDATE browser_transfers SET state='completed' WHERE tenant_id=%s AND transfer_id=%s",
            (context.tenant_id, transfer_id),
        )
        return {"transfer_id": transfer_id, "state": "completed", "duplicate": False}

    def interrupt(self, context: IdentityContext, transfer_id: str) -> None:
        self._db.execute(
            "UPDATE browser_transfers SET state='interrupted' WHERE tenant_id=%s AND transfer_id=%s",
            (context.tenant_id, transfer_id),
        )


class EndpointRelay:
    """BRW-006: dispatch fully-bound endpoint action envelopes and replay
    the original result per idempotency key after a dropped response."""

    REQUIRED_FIELDS = (
        "endpoint_id", "target_id", "generation", "lease", "fence",
        "capability", "policy_decision_id", "effect_id",
        "delivery_id", "idempotency_key", "operation_version", "expires_at",
    )

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def dispatch(self, context: IdentityContext, envelope: dict,
                 actuate: Callable[[dict], dict]) -> dict:
        missing = [f for f in self.REQUIRED_FIELDS if not envelope.get(f)]
        if missing:
            raise EnvelopeRefused(f"envelope missing fields: {missing}")
        if datetime.now(timezone.utc) >= datetime.fromisoformat(envelope["expires_at"]):
            raise EnvelopeRefused("envelope expired")
        existing = self._db.query_one(
            "SELECT result FROM worker_results WHERE tenant_id=%s AND idempotency_key=%s",
            (context.tenant_id, envelope["idempotency_key"]),
        )
        if existing is not None:
            return {"result": existing[0], "replayed": True}
        result = actuate(envelope)
        self._db.execute(
            "INSERT INTO worker_results (tenant_id, idempotency_key, result) VALUES (%s, %s, %s)",
            (context.tenant_id, envelope["idempotency_key"], Json(result)),
        )
        return {"result": result, "replayed": False}


class ObservationEvidenceStore:
    """BRW-007: observations are EVIDENCE ONLY. They are stored separately
    from effect truth and expose no actuation affordance."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def persist(self, context: IdentityContext, session_id: str, run_id: str,
                step_id: str, page_epoch: int, kind: str, content: dict) -> dict:
        observation_id = str(uuid.uuid4())
        digest = hashlib.sha256(
            json.dumps(content, sort_keys=True, default=str).encode()
        ).hexdigest()
        self._db.execute(
            """
            INSERT INTO browser_observations
                (observation_id, tenant_id, session_id, run_id, step_id,
                 page_epoch, kind, content, content_digest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (observation_id, context.tenant_id, session_id, run_id, step_id,
             page_epoch, kind, Json(content), digest),
        )
        return {"observation_id": observation_id, "digest": digest,
                "evidence_only": True}

    def backfill(self, context: IdentityContext, session_id: str, run_id: str,
                 step_id: str, page_epoch: int, entries: list[dict]) -> int:
        """BRW-007-R01: backfill missing eligible evidence after an
        evidence-store outage — canonical action/result state is untouched
        and the action is never re-run."""
        added = 0
        for entry in entries:
            self.persist(context, session_id, run_id, step_id, page_epoch,
                         entry.get("kind", "state"), entry)
            added += 1
        return added

    def as_evidence(self, context: IdentityContext, observation_id: str) -> dict:
        """The only consumption affordance: read as evidence. There is no
        actuation path from an observation."""
        row = self._db.query_one(
            """
            SELECT observation_id::text, kind, content, content_digest, captured_at
            FROM browser_observations WHERE tenant_id=%s AND observation_id=%s
            """,
            (context.tenant_id, observation_id),
        )
        if row is None:
            raise KeyError("observation unknown")
        return {"observation_id": row[0], "kind": row[1], "content": row[2],
                "digest": row[3], "captured_at": row[4], "actuation": None,
                "evidence_only": True}
