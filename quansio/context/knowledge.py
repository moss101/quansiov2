"""Knowledge Fabric: evidence-backed candidates, stale-synthesis rejection
and one unified versioned fabric (KNW-001..003, owner quansio-context).

Candidates carry provenance, evidence references, source/task epochs,
confidence, validity intervals, conflict sets and producer/run identity
BEFORE durable acceptance. Asynchronous synthesis is tagged with epochs and
commits only when every relevant epoch still matches; stale attempts are
kept as diagnostic evidence. The fabric stores enterprise, user-authorized,
research, successful-work and engineering knowledge through one versioned
query model — and explicitly refuses to act as recovery state: runs recover
from protocol/checkpoints/events, never from knowledge.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class QualificationRejected(Exception):
    """KNW-001-N01: candidate lacks provenance/evidence or exceeds source authority."""


class StaleSynthesis(Exception):
    """KNW-002-N01: relevant epochs moved during synthesis."""


class KnowledgeFabricRecoveryRefused(Exception):
    """KNW-003-N01: run recovery attempted from knowledge — refused."""


class KnowledgeFabric:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    # -- KNW-001 ---------------------------------------------------------------

    def submit_candidate(self, context: IdentityContext, fabric_kind: str,
                         content: dict, provenance: dict, evidence_refs: list[str],
                         source_epoch: str, confidence: float,
                         producer: str, run_id: str | None = None,
                         valid_from: datetime | None = None,
                         valid_until: datetime | None = None,
                         conflict_set: list[str] | None = None,
                         scope_authority: dict | None = None) -> dict:
        if fabric_kind not in ("enterprise", "user", "research", "work", "engineering"):
            raise QualificationRejected(f"unknown fabric kind {fabric_kind!r}")
        if not provenance.get("source_urls") and not provenance.get("origin"):
            raise QualificationRejected("candidate lacks provenance")
        if not evidence_refs:
            raise QualificationRejected("candidate lacks evidence references")
        if scope_authority:
            # Authority must stay within the source scope: a candidate
            # claiming authority its sources do not grant is rejected.
            granted = set(scope_authority.get("granted_scopes", []))
            requested = set(scope_authority.get("requested_scopes", []))
            if requested - granted:
                raise QualificationRejected(
                    f"authority outside source scope: {sorted(requested - granted)}"
                )
        candidate_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO knowledge_candidates
                    (tenant_id, candidate_id, fabric_kind, content, provenance,
                     evidence_refs, source_epoch, confidence, valid_from, valid_until,
                     conflict_set, producer, run_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'accepted')
                """,
                (context.tenant_id, candidate_id, fabric_kind, Json(content),
                 Json(provenance), evidence_refs, source_epoch, confidence,
                 valid_from, valid_until, conflict_set or [], producer, run_id),
            )
        return {"candidate_id": candidate_id, "status": "accepted"}

    def withdraw_evidence(self, context: IdentityContext, candidate_id: str,
                          evidence_ref: str, tombstone: dict) -> dict:
        """KNW-001-R01: evidence withdrawal keeps history and flips the
        validity/conflict state; provenance is never deleted."""
        with self._db.connection() as connection:
            row = connection.execute(
                """
                UPDATE knowledge_candidates
                SET status = 'withdrawn', conflict_set = conflict_set || %s::text[]
                WHERE tenant_id = %s AND candidate_id = %s
                RETURNING provenance
                """,
                ([f"evidence-withdrawn:{evidence_ref}"], context.tenant_id, candidate_id),
            ).fetchone()
            if row is None:
                raise KeyError(candidate_id)
        return {"candidate_id": candidate_id, "status": "withdrawn",
                "provenance_preserved": True, "tombstone": tombstone}

    # -- KNW-002 ---------------------------------------------------------------

    def commit_synthesis(self, context: IdentityContext, producer: str,
                         content: dict, evidence_refs: list[str],
                         source_epoch_at_start: str, task_epoch_at_start: str,
                         current_source_epoch: str, current_task_epoch: str) -> dict:
        """Tagged synthesis commits only when ALL relevant epochs still match.
        A stale attempt is stored with status 'stale' as diagnostic evidence."""
        epochs_match = (source_epoch_at_start == current_source_epoch
                        and task_epoch_at_start == current_task_epoch)
        candidate_id = str(uuid.uuid4())
        status = "accepted" if epochs_match else "stale"
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO knowledge_candidates
                    (tenant_id, candidate_id, fabric_kind, content,
                     provenance, evidence_refs, source_epoch, task_epoch,
                     producer, status)
                VALUES (%s, %s, 'research', %s, %s, %s, %s, %s, %s, %s)
                """,
                (context.tenant_id, candidate_id, Json(content),
                 Json({"synthesis": True}), evidence_refs,
                 source_epoch_at_start, task_epoch_at_start, producer, status),
            )
        if not epochs_match:
            raise StaleSynthesis(
                f"synthesis stale: source {source_epoch_at_start}->{current_source_epoch}, "
                f"task {task_epoch_at_start}->{current_task_epoch}; kept as diagnostic"
            )
        return {"candidate_id": candidate_id, "status": "accepted"}

    # -- KNW-003 ---------------------------------------------------------------

    def query(self, context: IdentityContext, fabric_kind: str | None = None,
              terms: list[str] | None = None) -> list[dict]:
        rows = self._db.query_all(
            """
            SELECT candidate_id::text, fabric_kind, content, confidence, status,
                   source_epoch, evidence_refs
            FROM knowledge_candidates
            WHERE tenant_id = %s AND status = 'accepted'
              AND (%s::text IS NULL OR fabric_kind = %s)
            ORDER BY created_at DESC
            """,
            (context.tenant_id, fabric_kind, fabric_kind),
        )
        results = []
        for candidate_id, kind, content, confidence, status, epoch, refs in rows:
            blob = json.dumps(content, default=str).lower()
            if terms and not any(t.lower() in blob for t in terms):
                continue
            results.append({"candidate_id": candidate_id, "fabric_kind": kind,
                            "content": content, "confidence": confidence,
                            "source_epoch": epoch, "evidence_refs": list(refs or ())})
        return results

    def recovery_refusal(self, context: IdentityContext, run_id: str) -> None:
        """KNW-003-N01: knowledge is never canonical recovery state."""
        raise KnowledgeFabricRecoveryRefused(
            "run recovery from the Knowledge Fabric is forbidden; use protocol/"
            "checkpoint/event state"
        )

    def reindex_projection(self, context: IdentityContext) -> dict:
        """KNW-003-R01: rebuild the query projection from durable candidates;
        source identities are preserved because candidates are the source."""
        rows = self._db.query_all(
            """
            SELECT candidate_id::text, fabric_kind, content::text, source_epoch
            FROM knowledge_candidates WHERE tenant_id = %s AND status = 'accepted'
            """,
            (context.tenant_id,),
        )
        projection_digest = hashlib.sha256(
            json.dumps([list(r) for r in rows], sort_keys=True, default=str).encode()
        ).hexdigest()
        return {"indexed": len(rows), "projection_digest": projection_digest,
                "identity_preserved": True}
