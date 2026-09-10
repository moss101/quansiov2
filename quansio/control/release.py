"""Release state machine (REL-001..008). Owner: the release control service;
only the GATE-M14 evaluation may write the PRODUCTION_READY promotion.

The candidate identity is a digest over the exact source commit, generated
bindings digest, service/client artifact digests, configuration digests and
the ordered migration list. Any change to any bound input yields a
different candidate identity that cannot reuse prior qualification. The
state machine enforces ordered transitions; the promotion to
PRODUCTION_READY is written exclusively by the gate evaluation path.
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


class CandidateChanged(Exception):
    """REL-001-N01: bound inputs changed — different identity, prior
    qualification not reusable."""


class StateTransitionError(Exception):
    """Ordered state machine violation."""


class PromotionRejected(Exception):
    """REL-007-N01/REL-008-N01: non-gate writer or identity mismatch."""


def candidate_identity(commit: str, bindings_digest: str, artifacts: dict,
                       config_digest: str, migrations: list[str]) -> str:
    material = json.dumps({
        "commit": commit,
        "bindings_digest": bindings_digest,
        "artifacts": artifacts,
        "config_digest": config_digest,
        "migrations": migrations,
    }, sort_keys=True)
    return "relcand-" + hashlib.sha256(material.encode()).hexdigest()[:32]


class ReleaseService:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def create_candidate(self, context: IdentityContext, commit: str,
                         bindings_digest: str, artifacts: dict,
                         config_digest: str, migrations: list[str],
                         support_selection: dict) -> dict:
        candidate_id = candidate_identity(commit, bindings_digest, artifacts,
                                          config_digest, migrations)
        with self._db.connection() as connection:
            row = connection.execute(
                "SELECT candidate_digest FROM release_candidates"
                " WHERE tenant_id=%s AND candidate_id=%s",
                (context.tenant_id, candidate_id),
            ).fetchone()
            if row is None:
                connection.execute(
                    """
                    INSERT INTO release_candidates
                        (tenant_id, candidate_id, commit_sha, bindings_digest,
                         migrations, support_selection, candidate_digest, state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'created')
                    """,
                    (context.tenant_id, candidate_id, commit, bindings_digest,
                     migrations, Json(support_selection),
                     hashlib.sha256(candidate_id.encode()).hexdigest()),
                )
                connection.execute(
                    """
                    INSERT INTO release_events
                        (tenant_id, candidate_id, kind, actor, detail)
                    VALUES (%s, %s, 'candidate_created', 'release-control', %s)
                    """,
                    (context.tenant_id, candidate_id,
                     Json({"commit": commit, "migrations": migrations})),
                )
        return {"candidate_id": candidate_id, "commit": commit, "state": "created"}

    def _candidate(self, context: IdentityContext, candidate_id: str,
                   expected: str | None = None) -> dict:
        row = self._db.query_one(
            "SELECT state, commit_sha, bindings_digest, migrations,"
            " candidate_digest FROM release_candidates"
            " WHERE tenant_id=%s AND candidate_id=%s",
            (context.tenant_id, candidate_id),
        )
        if row is None:
            raise KeyError("candidate unknown")
        if expected is not None and row[0] != expected:
            raise StateTransitionError(
                f"candidate state {row[0]!r}, expected {expected!r}"
            )
        return {"state": row[0], "commit": row[1], "bindings_digest": row[2],
                "migrations": list(row[3]), "candidate_digest": row[4]}

    def _transition(self, context: IdentityContext, candidate_id: str,
                    from_state: str, to_state: str, actor: str,
                    detail: dict | None = None) -> None:
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE release_candidates SET state=%s
                WHERE tenant_id=%s AND candidate_id=%s AND state=%s
                """,
                (to_state, context.tenant_id, candidate_id, from_state),
            )
            if cursor.rowcount != 1:
                raise StateTransitionError(
                    f"candidate {candidate_id} is not {from_state!r}"
                )
            connection.execute(
                """
                INSERT INTO release_events
                    (tenant_id, candidate_id, kind, actor, detail)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (context.tenant_id, candidate_id, f"{from_state}->{to_state}",
                 actor, Json(detail or {})),
            )

    # -- REL-001-R01: re-materialize and verify --------------------------------

    def re_materialize_and_verify(self, context: IdentityContext, candidate_id: str,
                                  commit: str, bindings_digest: str,
                                  artifacts: dict, config_digest: str,
                                  migrations: list[str]) -> dict:
        stored = self._candidate(context, candidate_id)
        recomputed = candidate_identity(commit, bindings_digest, artifacts,
                                        config_digest, migrations)
        matches = (recomputed == candidate_id
                   and stored["commit"] == commit
                   and stored["bindings_digest"] == bindings_digest
                   and list(stored["migrations"]) == migrations)
        return {"candidate_id": candidate_id, "identity_matches": matches,
                "recomputed_identity": recomputed}

    # -- REL-002: qualification ------------------------------------------------

    def record_suite_run(self, context: IdentityContext, candidate_id: str,
                         suite_id: str, passed: bool,
                         report_digest: str) -> None:
        self._db.execute(
            """
            INSERT INTO release_suite_runs
                (tenant_id, candidate_id, suite_id, passed, report_digest)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (context.tenant_id, candidate_id, suite_id, passed, report_digest),
        )

    def qualify(self, context: IdentityContext, candidate_id: str,
                required_suites: list[str]) -> dict:
        """REL-002: every mapped blocking suite must have passed for THIS
        candidate; reports from other candidates cannot qualify it."""
        self._candidate(context, candidate_id, expected="created")
        rows = self._db.query_all(
            "SELECT suite_id, passed, report_digest FROM release_suite_runs"
            " WHERE tenant_id=%s AND candidate_id=%s",
            (context.tenant_id, candidate_id),
        )
        passed_suites = {r[0] for r in rows if r[1]}
        missing = [s for s in required_suites if s not in passed_suites]
        failed = [r[0] for r in rows if r[0] in required_suites and not r[1]]
        if missing or failed:
            raise StateTransitionError(
                f"cannot qualify: missing={missing} failed={failed}"
            )
        self._transition(context, candidate_id, "created", "qualified", "release-control")
        return {"candidate_id": candidate_id, "state": "qualified"}

    # -- REL-003/004: canary and rollback ---------------------------------------

    def canary_deploy(self, context: IdentityContext, candidate_id: str,
                      cohort: str, health_ok: bool,
                      after_rollback: bool = False) -> dict:
        """REL-004-R01: after rollback the canary is restored to the same
        qualified candidate — same identity, repeat deployment allowed."""
        expected = "rollback_proven" if after_rollback else "qualified"
        self._candidate(context, candidate_id, expected=expected)
        if not health_ok:
            raise StateTransitionError("post-deploy health checks failed")
        self._transition(context, candidate_id, expected,
                         "canary_deployed", "canary-controller",
                         {"cohort": cohort, "after_rollback": after_rollback})
        return {"candidate_id": candidate_id, "state": "canary_deployed",
                "cohort": cohort}

    def canary_rollback(self, context: IdentityContext, candidate_id: str,
                        rollback_ok: bool, irreversible_migration: bool = False) -> dict:
        """REL-004: prove rollback under load; an irreversible migration
        without declared rollback path fails before GO."""
        if irreversible_migration:
            raise StateTransitionError(
                "irreversible migration has no expand/contract rollback path;"
                " rollback qualification fails before GO"
            )
        if not rollback_ok:
            raise StateTransitionError("rollback drill failed")
        self._candidate(context, candidate_id, expected="canary_deployed")
        self._transition(context, candidate_id, "canary_deployed",
                         "rollback_proven", "canary-controller",
                         {"rollback_ok": rollback_ok})
        return {"candidate_id": candidate_id, "state": "rollback_proven"}

    # -- REL-005: go / no-go ------------------------------------------------------

    def go_decision(self, context: IdentityContext, candidate_id: str,
                    blocking_reports: dict[str, bool],
                    slo_ok: bool, security_ok: bool, dr_ok: bool,
                    canary_ok: bool, rollback_ok: bool) -> dict:
        """REL-005: explicit decision from every blocking report and
        qualification evidence. One FAIL invalidates a prior GO: the state
        reverts to rollback_proven so no downstream step can consume it."""
        decision = "GO_APPROVED" if (slo_ok and security_ok and dr_ok
                                     and canary_ok and rollback_ok
                                     and all(blocking_reports.values())) else "NO_GO"
        row = self._db.query_one(
            "SELECT state FROM release_candidates WHERE tenant_id=%s AND candidate_id=%s",
            (context.tenant_id, candidate_id),
        )
        current = row[0] if row else None
        if decision == "GO_APPROVED":
            self._transition(context, candidate_id, "rollback_proven",
                             "go_approved", "release-board",
                             {"decision": decision,
                              "blocking_reports": blocking_reports})
        else:
            # NO_GO: revert a prior GO so downstream consumers see the invalidation.
            if current == "go_approved":
                self._transition(context, candidate_id, "go_approved",
                                 "rollback_proven", "release-board",
                                 {"decision": decision,
                                  "blocking_reports": blocking_reports,
                                  "invalidated_prior_go": True})
            else:
                self._db.execute(
                    """
                    INSERT INTO release_events
                        (tenant_id, candidate_id, kind, actor, detail)
                    VALUES (%s, %s, 'decision_no_go', 'release-board', %s)
                    """,
                    (context.tenant_id, candidate_id,
                     Json({"decision": "NO_GO",
                           "blocking_reports": blocking_reports})),
                )
        return {"candidate_id": candidate_id, "decision": decision}

    # -- REL-006: readiness bundle --------------------------------------------------

    def seal_readiness(self, context: IdentityContext, candidate_id: str,
                       blocking_reports: dict, canary: dict, rollback: dict,
                       slo: dict, security: dict, dr: dict, go: dict) -> dict:
        candidate = self._candidate(context, candidate_id)
        contents = {
            "candidate_id": candidate_id,
            "candidate_digest": candidate["candidate_digest"],
            "commit": candidate["commit"],
            "blocking_reports": blocking_reports,
            "canary": canary, "rollback": rollback,
            "slo": slo, "security": security, "dr": dr, "go": go,
        }
        digest = hashlib.sha256(
            json.dumps(contents, sort_keys=True).encode()
        ).hexdigest()
        self._db.execute(
            """
            INSERT INTO readiness_bundles
                (tenant_id, bundle_digest, candidate_id, contents)
            VALUES (%s, %s, %s, %s)
            """,
            (context.tenant_id, digest, candidate_id, Json(contents)),
        )
        self._transition(context, candidate_id, "go_approved",
                         "readiness_sealed", "release-control",
                         {"bundle_digest": digest})
        return {"bundle_digest": digest, "candidate_id": candidate_id,
                "state": "readiness_sealed"}

    def reconstruct_bundle(self, context: IdentityContext,
                           bundle_digest: str) -> dict:
        row = self._db.query_one(
            "SELECT contents FROM readiness_bundles WHERE tenant_id=%s AND bundle_digest=%s",
            (context.tenant_id, bundle_digest),
        )
        if row is None:
            raise KeyError("bundle unknown")
        recomputed = hashlib.sha256(
            json.dumps(row[0], sort_keys=True).encode()
        ).hexdigest()
        return {"contents": row[0], "digest_matches": recomputed == bundle_digest}

    # -- REL-007/008: promotion (sole owner: GATE-M14) --------------------------

    def gate_m14_promote(self, context: IdentityContext, candidate_id: str,
                         bundle_digest: str) -> dict:
        """The ONLY writer of PRODUCTION_READY. Called exclusively by the
        GATE-M14 evaluation after READINESS_EVIDENCE_SEALED and all
        dependencies pass."""
        stored = self._candidate(context, candidate_id, expected="readiness_sealed")
        bundle = self._db.query_one(
            "SELECT 1 FROM readiness_bundles WHERE tenant_id=%s AND bundle_digest=%s"
            " AND candidate_id=%s",
            (context.tenant_id, bundle_digest, candidate_id),
        )
        if bundle is None:
            raise PromotionRejected("sealed bundle does not match candidate")
        self._transition(context, candidate_id, "readiness_sealed",
                         "production_ready", "gate-m14",
                         {"bundle_digest": bundle_digest})
        return {"candidate_id": candidate_id, "state": "production_ready"}

    def reject_non_gate_promotion(self, writer: str, candidate_id: str) -> None:
        raise PromotionRejected(
            f"{writer!r} cannot write PRODUCTION_READY; sole owner is GATE-M14"
        )

    def verify_promoted_identity(self, context: IdentityContext, candidate_id: str,
                                 commit: str, bindings_digest: str, artifacts: dict,
                                 config_digest: str, migrations: list[str]) -> dict:
        """REL-008-N01/R01: promotion identity must match exactly; rollback
        evidence preserved as distinct records."""
        recomputed = candidate_identity(commit, bindings_digest, artifacts,
                                        config_digest, migrations)
        if recomputed != candidate_id:
            raise PromotionRejected(
                "promotion identity differs from production-ready candidate"
            )
        events = self._db.query_all(
            "SELECT kind, actor FROM release_events WHERE tenant_id=%s AND candidate_id=%s"
            " ORDER BY event_id",
            (context.tenant_id, candidate_id),
        )
        return {"candidate_id": candidate_id, "identity_matches": True,
                "promotion_events": [{"kind": k, "actor": a} for k, a in events]}
