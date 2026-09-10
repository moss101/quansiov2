"""Bounded Context Projection (CTX-006).

Builds task-scoped model context from canonical history (runtime events),
indexed knowledge, tool outputs and verification evidence under explicit
token and data-class limits, with a projection version identity (digest of
inputs, source epoch and policy). Protected data classes and foreign-tenant
material are omitted before the model request is constructed; exceeding the
token budget truncates lowest-relevance sections first. A source-epoch
invalidation rebuilds the projection without touching the canonical
transcript, protocol state or recovery state.
"""

from __future__ import annotations

import hashlib
import json
import uuid

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext, IdentityContextError
from quansio.platform.db import PlatformDatabase

PROJECTION_POLICY_VERSION = "projection-policy/1"
TOKENS_PER_CHARACTER = 1 / 4


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) * TOKENS_PER_CHARACTER))


class ProjectionDenied(Exception):
    """The projection request violates tenant/data-class policy."""


class ContextProjector:
    """Owner: quansio-context."""

    def __init__(self, database: PlatformDatabase, index=None):
        self._db = database
        self._index = index

    def build(
        self,
        context: IdentityContext,
        run_id: str,
        step_id: str,
        allowed_data_classes: list[str],
        token_budget: int,
        source_epoch: str | None = None,
    ) -> dict:
        """Build the projection for one model step.

        ``source_epoch`` names the freshness epoch; passing a different epoch
        than the one a prior projection used simply rebuilds with current
        index content — the canonical transcript, protocol state and recovery
        state are never modified.
        """
        if "foreign_tenant" in allowed_data_classes or "*" in allowed_data_classes:
            raise ProjectionDenied("wildcard/foreign-tenant data classes are not permitted")

        sections: list[dict] = []
        events = self._db.query_all(
            """
            SELECT event_type, payload, committed_at FROM runtime_events
            WHERE tenant_id = %s AND run_id = %s ORDER BY sequence ASC LIMIT 200
            """,
            (context.tenant_id, run_id),
        )
        history = [
            {"kind": "history", "text": f"{e[0]}: {json.dumps(e[1], default=str)[:400]}", "class": "history"}
            for e in events
        ]
        sections.extend(history)

        if self._index is not None and "knowledge" in allowed_data_classes:
            for chunk in self._index.query(context, [], include_tombstoned=False)[:100]:
                sections.append({
                    "kind": "knowledge",
                    "text": f"[{chunk['source_id']}#{chunk['chunk_id']} r{chunk['revision']}] {chunk['content'][:400]}",
                    "class": "knowledge",
                })

        claims = self._db.query_all(
            """
            SELECT statement, verification FROM research_claims WHERE tenant_id = %s
            """,
            (context.tenant_id,),
        )
        for statement, verification in claims:
            if verification in ("unsupported", "conflicting") and "evidence" not in allowed_data_classes:
                continue
            sections.append({
                "kind": "evidence",
                "text": f"claim({verification}): {statement[:300]}",
                "class": "evidence",
            })

        allowed = [s for s in sections if s["class"] in allowed_data_classes or s["class"] == "history"]
        rank = {"history": 0, "evidence": 1, "knowledge": 2}
        allowed.sort(key=lambda s: (rank.get(s["class"], 9), s["text"]))
        selected = []
        used = 0
        for section in allowed:
            cost = estimate_tokens(section["text"])
            if used + cost > token_budget:
                continue
            selected.append(section)
            used += cost

        epoch = source_epoch or hashlib.sha256(str(used).encode()).hexdigest()[:16]
        digest = hashlib.sha256(
            json.dumps({"sections": selected, "epoch": epoch, "policy": PROJECTION_POLICY_VERSION},
                       sort_keys=True, default=str).encode()
        ).hexdigest()
        projection_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO context_projections
                    (tenant_id, projection_id, run_id, step_id, source_epoch,
                     projection_digest, token_budget, tokens_used, content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (context.tenant_id, projection_id, run_id, step_id, epoch,
                 digest, token_budget, used, Json(selected)),
            )
        return {
            "projection_id": projection_id,
            "projection_digest": digest,
            "source_epoch": epoch,
            "token_budget": token_budget,
            "tokens_used": used,
            "sections": selected,
        }
