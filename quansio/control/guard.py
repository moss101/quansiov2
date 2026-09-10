"""Behavior-sequence guard (SEC-005, owner quansio-control).

Evaluates the canonical effect/event history so a configured dangerous
sequence can block or escalate the next operation before actuation. Each
operation type may be independently valid in isolation while the sequence
(for example secret-read followed by outbound upload) is forbidden. Rule
updates re-evaluate pending sequence state deterministically; historical
events are never deleted.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class SequenceBlocked(Exception):
    """The configured sequence guard blocked or escalated this operation."""


class BehaviorSequenceGuard:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def add_rule(self, context: IdentityContext, rule_id: str,
                 sequence: list[str], action: str) -> None:
        if action not in ("block", "escalate"):
            raise ValueError(action)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO behavior_rules (tenant_id, rule_id, sequence, action)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tenant_id, rule_id)
                DO UPDATE SET sequence = EXCLUDED.sequence,
                              action = EXCLUDED.action,
                              enabled = true,
                              updated_at = now()
                """,
                (context.tenant_id, rule_id, Json(sequence), action),
            )

    def history(self, context: IdentityContext, limit: int = 50) -> list[str]:
        """Canonical operation history (effects then events, newest last)."""
        rows = self._db.query_all(
            """
            SELECT operation FROM (
                SELECT operation, created_at FROM effects WHERE tenant_id = %s
                UNION ALL
                SELECT 'event.' || event_type AS operation, committed_at AS created_at
                FROM runtime_events WHERE tenant_id = %s
            ) h ORDER BY created_at ASC LIMIT %s
            """,
            (context.tenant_id, context.tenant_id, limit),
        )
        return [r[0] for r in rows]

    def check(self, context: IdentityContext, next_operation: str) -> dict:
        """Evaluate every enabled rule against history + the candidate
        operation BEFORE actuation. Returns the decision; raises
        SequenceBlocked when a blocking rule matches."""
        history = self.history(context)
        rules = self._db.query_all(
            """
            SELECT rule_id, sequence, action FROM behavior_rules
            WHERE tenant_id = %s AND enabled = true
            """,
            (context.tenant_id,),
        )
        sequence_all = history + [next_operation]
        decision = {"operation": next_operation, "action": "allow", "matched_rule": None}
        for rule_id, sequence, action in rules:
            pattern = list(sequence)
            matched = _contains_subsequence(sequence_all, pattern)
            self._db.execute(
                "INSERT INTO behavior_evaluations (tenant_id, rule_id, matched) VALUES (%s, %s, %s)",
                (context.tenant_id, rule_id, matched),
            )
            if matched:
                decision = {"operation": next_operation, "action": action, "matched_rule": rule_id}
                break
        if decision["action"] == "block":
            raise SequenceBlocked(
                f"operation {next_operation!r} blocked by sequence rule {decision['matched_rule']}"
            )
        return decision

    def pending_escalations(self, context: IdentityContext) -> list[dict]:
        """Escalated operations awaiting a decision, from the evaluation trail
        against current rules (deterministic re-evaluation, no deletions)."""
        rows = self._db.query_all(
            """
            SELECT e.rule_id, r.action, e.evaluated_at FROM behavior_evaluations e
            JOIN behavior_rules r ON r.tenant_id = e.tenant_id AND r.rule_id = e.rule_id
            WHERE e.tenant_id = %s AND e.matched = true
            ORDER BY e.evaluated_at
            """,
            (context.tenant_id,),
        )
        return [{"rule_id": r[0], "action": r[1], "at": r[2]} for r in rows]


def _contains_subsequence(haystack: list[str], needle: list[str]) -> bool:
    if not needle:
        return False
    for start in range(len(haystack) - len(needle) + 1):
        if haystack[start:start + len(needle)] == needle:
            return True
    return False
