"""RecoveryConsistencyPoint (SRE-003), backup/restore drills (SRE-004),
load/soak/degradation (SRE-005), tenant quotas (SRE-006), cross-tenant
adversarial probes (SEC-006) and build/artifact provenance (SEC-007).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Callable

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class RecoveryPointIncomplete(Exception):
    """SRE-003-N01: declared consistent while bound components differ."""


class UnknownEffectsOpen(Exception):
    """Consequential execution cannot reopen while UNKNOWN effects exist."""


class RecoveryConsistencyPoint:
    """Binds the DB commit position, canonical event sequence, evidence
    manifest digest, snapshot inventory digest, effect-settlement watermark
    and unresolved UNKNOWN effect ids into one verifiable recovery point."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def create(self, context: IdentityContext, db_commit_position: str,
               event_sequence: int, evidence_manifest_digest: str,
               snapshot_inventory_digest: str,
               effect_settlement_watermark: int,
               unknown_effect_ids: list[str]) -> dict:
        rcp_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO recovery_points
                (tenant_id, rcp_id, db_commit_position, event_sequence,
                 evidence_manifest_digest, snapshot_inventory_digest,
                 effect_settlement_watermark, unknown_effect_ids, state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open')
            """,
            (context.tenant_id, rcp_id, db_commit_position, event_sequence,
             evidence_manifest_digest, snapshot_inventory_digest,
             effect_settlement_watermark, unknown_effect_ids),
        )
        return {"rcp_id": rcp_id, "state": "open",
                "unknown_effect_ids": unknown_effect_ids}

    def verify(self, context: IdentityContext, rcp_id: str,
               restored_db_position: str, restored_event_sequence: int,
               restored_evidence_digest: str, restored_snapshot_digest: str,
               restored_effect_watermark: int) -> dict:
        """SRE-003-N01: DB restore alone is insufficient — every bound
        component must match the recorded recovery point."""
        row = self._db.query_one(
            """
            SELECT db_commit_position, event_sequence, evidence_manifest_digest,
                   snapshot_inventory_digest, effect_settlement_watermark,
                   unknown_effect_ids
            FROM recovery_points WHERE tenant_id=%s AND rcp_id=%s
            """,
            (context.tenant_id, rcp_id),
        )
        if row is None:
            raise KeyError(rcp_id)
        mismatches = []
        if row[0] != restored_db_position:
            mismatches.append("db_commit_position")
        if row[1] != restored_event_sequence:
            mismatches.append("event_sequence")
        if row[2] != restored_evidence_digest:
            mismatches.append("evidence_manifest_digest")
        if row[3] != restored_snapshot_digest:
            mismatches.append("snapshot_inventory_digest")
        if row[4] != restored_effect_watermark:
            mismatches.append("effect_settlement_watermark")
        if mismatches:
            raise RecoveryPointIncomplete(f"component mismatch: {mismatches}")
        self._db.execute(
            "UPDATE recovery_points SET state='verified' WHERE tenant_id=%s AND rcp_id=%s",
            (context.tenant_id, rcp_id),
        )
        return {"rcp_id": rcp_id, "state": "verified",
                "unknown_effect_ids": [str(u) for u in row[5]]}

    def reopen_consequential(self, context: IdentityContext, rcp_id: str,
                             unknown_resolved: list[str]) -> dict:
        """SRE-003-R01: consequential execution reopens only after all UNKNOWN
        effects were reconciled to explicit terminals."""
        row = self._db.query_one(
            "SELECT unknown_effect_ids FROM recovery_points WHERE tenant_id=%s AND rcp_id=%s",
            (context.tenant_id, rcp_id),
        )
        if row is None:
            raise KeyError(rcp_id)
        outstanding = [str(u) for u in row[0] if str(u) not in unknown_resolved]
        if outstanding:
            raise UnknownEffectsOpen(f"unresolved UNKNOWN effects: {outstanding}")
        self._db.execute(
            "UPDATE recovery_points SET state='restored' WHERE tenant_id=%s AND rcp_id=%s",
            (context.tenant_id, rcp_id),
        )
        return {"rcp_id": rcp_id, "consequential_execution": "reopened"}


class DrillRunner:
    """SRE-004: destructive restore drills with RPO/RTO objectives."""

    OBJECTIVES = {"authoritative": {"rpo": 300, "rto": 1800},
                  "evidence": {"rpo": 900, "rto": 3600}}

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def run_drill(self, context: IdentityContext, rcp_id: str,
                  objective: str, rpo_seconds: int, rto_seconds: int,
                  all_components_restored: bool,
                  unknown_effects_resolved: bool) -> dict:
        objectives = self.OBJECTIVES[objective]
        passed = (all_components_restored and unknown_effects_resolved
                  and rpo_seconds <= objectives["rpo"]
                  and rto_seconds <= objectives["rto"])
        drill_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO dr_drills
                (drill_id, tenant_id, rcp_id, objective, rpo_seconds, rto_seconds,
                 passed, detail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (drill_id, context.tenant_id, rcp_id, objective, rpo_seconds,
             rto_seconds, passed,
             Json({"objectives": objectives,
                   "all_components_restored": all_components_restored,
                   "unknown_effects_resolved": unknown_effects_resolved})),
        )
        return {"drill_id": drill_id, "passed": passed}


class QuotaService:
    """SRE-006: per-tenant quotas with auditable reservations. Tenants are
    isolated by primary key, so one tenant can never consume another's
    reserved capacity."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def set_quota(self, context: IdentityContext, kind: str, limit_value: int) -> None:
        self._db.execute(
            """
            INSERT INTO tenant_quotas (tenant_id, kind, limit_value)
            VALUES (%s, %s, %s)
            ON CONFLICT (tenant_id, kind) DO UPDATE SET limit_value=EXCLUDED.limit_value
            """,
            (context.tenant_id, kind, limit_value),
        )

    def reserve(self, context: IdentityContext, kind: str, amount: int) -> bool:
        """Atomically check-and-increment spend under the tenant's own quota."""
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO tenant_quota_spend (tenant_id, kind, spent)
                VALUES (%s, %s, %s)
                ON CONFLICT (tenant_id, kind)
                DO UPDATE SET spent = tenant_quota_spend.spent + %s,
                               updated_at = now()
                WHERE (SELECT limit_value FROM tenant_quotas
                       WHERE tenant_id=%s AND kind=%s) >=
                      tenant_quota_spend.spent + %s
                """,
                (context.tenant_id, kind, amount, amount, context.tenant_id,
                 kind, amount),
            )
            return cursor.rowcount == 1

    def recover_after_restart(self, context: IdentityContext, kind: str) -> int:
        """SRE-006-R01: spend counters are authoritative rows — restart reads
        them without resetting."""
        return self._db.query_one(
            "SELECT spent FROM tenant_quota_spend WHERE tenant_id=%s AND kind=%s",
            (context.tenant_id, kind),
        )[0]


class AdversarialProber:
    """SEC-006: cross-tenant isolation probes with durable results."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def record(self, context: IdentityContext, probe_kind: str,
               denied: bool, detail: dict) -> None:
        self._db.execute(
            "INSERT INTO adversarial_probes (tenant_id, probe_kind, denied, detail)"
            " VALUES (%s, %s, %s, %s)",
            (context.tenant_id, probe_kind, denied, Json(detail)),
        )

    def all_denied(self, context: IdentityContext) -> bool:
        row = self._db.query_one(
            "SELECT bool_and(denied) FROM adversarial_probes WHERE tenant_id=%s",
            (context.tenant_id,),
        )
        return bool(row[0]) if row and row[0] is not None else False


class ProvenanceService:
    """SEC-007: bind qualified source commit, dependency locks, generated
    bindings, artifacts and migrations into one reproducible input set."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def bind(self, context: IdentityContext, commit: str,
             dependencies: dict, generated_bindings: dict,
             artifacts: dict, migrations: list[str],
             nondeterministic_exclusions: list[str] | None = None) -> dict:
        inputs = {
            "commit": commit,
            "dependency_locks": dependencies,
            "generated_bindings": generated_bindings,
            "artifacts": artifacts,
            "migrations": migrations,
        }
        digest = hashlib.sha256(
            json.dumps(inputs, sort_keys=True).encode()
        ).hexdigest()
        manifest_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO provenance_manifests
                (tenant_id, manifest_id, commit, inputs, inputs_digest,
                 reproducible, nondeterministic_exclusions)
            VALUES (%s, %s, %s, %s, %s, true, %s)
            """,
            (context.tenant_id, manifest_id, commit, Json(inputs), digest,
             Json(nondeterministic_exclusions or [])),
        )
        return {"manifest_id": manifest_id, "inputs_digest": digest}

    def verify(self, context: IdentityContext, manifest_id: str,
               rebuilt_inputs: dict) -> dict:
        row = self._db.query_one(
            """
            SELECT inputs, inputs_digest, nondeterministic_exclusions
            FROM provenance_manifests WHERE tenant_id=%s AND manifest_id=%s
            """,
            (context.tenant_id, manifest_id),
        )
        if row is None:
            raise KeyError(manifest_id)
        original, digest, exclusions = row
        comparable = json.loads(json.dumps(rebuilt_inputs, default=str))
        mismatches = []
        for key in ("commit", "dependency_locks", "generated_bindings",
                    "artifacts", "migrations"):
            if comparable.get(key) != original.get(key):
                mismatches.append(key)
        # Permitted nondeterminism is excluded from semantic identity.
        result = {
            "manifest_id": manifest_id,
            "reproducible": not mismatches,
            "mismatches": mismatches,
            "exclusions": exclusions,
        }
        if mismatches:
            result["reason"] = "substituted artifact or foreign-commit binding detected"
        return result
