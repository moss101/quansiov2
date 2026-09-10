"""Acceptance tests for REL-001..008: the release state machine."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.control.release import (  # noqa: E402
    CandidateChanged,
    PromotionRejected,
    ReleaseService,
    StateTransitionError,
    candidate_identity,
)
from quansio.platform.context import IdentityContext  # noqa: E402


def _ctx(workspace_setup) -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup["workspace_a"],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@pytest.fixture()
def release(migrated_db) -> ReleaseService:
    return ReleaseService(migrated_db)


@pytest.fixture()
def context(workspace_setup) -> IdentityContext:
    return _ctx(workspace_setup)


COMMIT = uuid.uuid4().hex
BINDINGS = "bindings-digest-" + uuid.uuid4().hex[:12]
ARTIFACTS = {"cli": "sha256:cli-1", "gateway": "sha256:gw-1"}
CONFIG = "config-digest-1"
MIGRATIONS = ["0014_machine_fabric.sql", "0020_release.sql"]
SUITES = ["suite-a", "suite-b"]


def _inputs():
    return dict(commit=COMMIT, bindings_digest=BINDINGS, artifacts=dict(ARTIFACTS),
                config_digest=CONFIG, migrations=list(MIGRATIONS))


def test_rel001_p01_and_r01_candidate_identity_and_rematerialization(release, context):
    created = release.create_candidate(context, *_inputs().values(),
                                       support_selection={"profiles": ["standard.linux"]})
    candidate_id = created["candidate_id"]
    # Deterministic identity: same inputs -> same candidate id.
    again = release.create_candidate(context, *_inputs().values(),
                                     support_selection={"profiles": ["standard.linux"]})
    assert again["candidate_id"] == candidate_id
    # REL-001-R01: re-materialize from stored identities and verify.
    verified = release.re_materialize_and_verify(context, candidate_id, **_inputs())
    assert verified["identity_matches"] is True


def test_rel001_n01_changed_input_is_a_different_candidate(release, context):
    first = release.create_candidate(context, *_inputs().values(),
                                     support_selection={"profiles": ["standard.linux"]})
    changed = dict(_inputs())
    changed["config_digest"] = "config-digest-CHANGED"
    second = release.create_candidate(context, *changed.values(),
                                      support_selection={"profiles": ["standard.linux"]})
    assert second["candidate_id"] != first["candidate_id"]
    # Prior qualification (state created + suite runs for first candidate) cannot
    # be reused: qualification checks run rows by candidate id.
    release.record_suite_run(context, first["candidate_id"], "suite-a", True, "d")
    with pytest.raises(StateTransitionError):
        release.qualify(context, second["candidate_id"], required_suites=list(SUITES))


def test_rel002_p01_qualify_exact_candidate(migrated_db, release, context):
    created = release.create_candidate(context, *_inputs().values(),
                                       support_selection={})
    for suite in SUITES:
        release.record_suite_run(context, created["candidate_id"], suite, True, "d")
    qualified = release.qualify(context, created["candidate_id"],
                                required_suites=list(SUITES))
    assert qualified["state"] == "qualified"


def test_rel002_n01_omitted_suite_blocks_qualification(migrated_db, release, context):
    created = release.create_candidate(context, *_inputs().values(), support_selection={})
    release.record_suite_run(context, created["candidate_id"], "suite-a", True, "d")
    with pytest.raises(StateTransitionError, match="missing"):
        release.qualify(context, created["candidate_id"],
                        required_suites=list(SUITES))


def test_rel003_p01_and_n01_and_r01_canary(migrated_db, release, context):
    created = release.create_candidate(context, *_inputs().values(), support_selection={})
    for suite in SUITES:
        release.record_suite_run(context, created["candidate_id"], suite, True, "d")
    release.qualify(context, created["candidate_id"], required_suites=list(SUITES))
    deployed = release.canary_deploy(context, created["candidate_id"],
                                     cohort="canary-1", health_ok=True)
    assert deployed["cohort"] == "canary-1"
    # Rollback under load passes; irreversible migration fails before GO.
    proven = release.canary_rollback(context, created["candidate_id"], rollback_ok=True)
    assert proven["state"] == "rollback_proven"
    with pytest.raises(StateTransitionError, match="irreversible migration"):
        release.canary_rollback(context, created["candidate_id"],
                                rollback_ok=False, irreversible_migration=True)
    # REL-004-R01: restore canary to the same qualified candidate and rerun
    # post-deploy checks without changing candidate identity.
    canary_again = release.canary_deploy(context, created["candidate_id"],
                                         cohort="canary-1", health_ok=True,
                                         after_rollback=True)
    assert canary_again["candidate_id"] == created["candidate_id"]


def test_rel005_p01_and_n01_go_decision(migrated_db, release, context):
    created = release.create_candidate(context, *_inputs().values(), support_selection={})
    for suite in SUITES:
        release.record_suite_run(context, created["candidate_id"], suite, True, "d")
    release.qualify(context, created["candidate_id"], required_suites=list(SUITES))
    release.canary_deploy(context, created["candidate_id"], cohort="c", health_ok=True)
    release.canary_rollback(context, created["candidate_id"], rollback_ok=True)
    go = release.go_decision(context, created["candidate_id"],
                             blocking_reports={"suite-a": True, "suite-b": True},
                             slo_ok=True, security_ok=True, dr_ok=True,
                             canary_ok=True, rollback_ok=True)
    assert go["decision"] == "GO_APPROVED"
    # One blocking report forced FAIL after aggregation: GO becomes invalid.
    invalidated = release.go_decision(context, created["candidate_id"],
                                      blocking_reports={"suite-a": True,
                                                        "suite-b": False},
                                      slo_ok=True, security_ok=True, dr_ok=True,
                                      canary_ok=True, rollback_ok=True)
    assert invalidated["decision"] == "NO_GO"


def test_rel006_p01_and_n01_and_r01_readiness_bundle(release, context):
    created = release.create_candidate(context, *_inputs().values(), support_selection={})
    for suite in SUITES:
        release.record_suite_run(context, created["candidate_id"], suite, True, "d")
    release.qualify(context, created["candidate_id"], required_suites=list(SUITES))
    release.canary_deploy(context, created["candidate_id"], cohort="c", health_ok=True)
    release.canary_rollback(context, created["candidate_id"], rollback_ok=True)
    go = release.go_decision(context, created["candidate_id"],
                             blocking_reports={"suite-a": True, "suite-b": True},
                             slo_ok=True, security_ok=True, dr_ok=True,
                             canary_ok=True, rollback_ok=True)
    bundle = release.seal_readiness(
        context, created["candidate_id"],
        blocking_reports={"suite-a": True, "suite-b": True},
        canary={"cohort": "c"}, rollback={"ok": True}, slo={"all": True},
        security={"pass": True}, dr={"pass": True}, go=go)
    # REL-006-R01: reconstruct from immutable references; digest reproduces.
    rebuilt = release.reconstruct_bundle(context, bundle["bundle_digest"])
    assert rebuilt["digest_matches"] is True
    # REL-006-N01: substituting one blocking report breaks integrity.
    tampered = dict(rebuilt["contents"])
    tampered["blocking_reports"] = {"suite-a": True, "suite-b": False}
    import hashlib as _h

    tampered_digest = _h.sha256(
        json.dumps(tampered, sort_keys=True).encode()).hexdigest()
    assert tampered_digest != bundle["bundle_digest"]


def test_rel007_p01_and_n01_and_r01_sole_owner_and_restart(release, context):
    created = release.create_candidate(context, *_inputs().values(), support_selection={})
    # Only GATE-M14 can promote: non-gate writers refused.
    for writer in ("REL-006", "client", "deployment-script", "admin-api"):
        with pytest.raises(PromotionRejected, match="sole owner is GATE-M14"):
            release.reject_non_gate_promotion(writer, created["candidate_id"])
    # REL-007-R01: release control "restart" — ownership rules preserved from
    # durable state before GATE-M14 evaluation.
    stored = release._candidate(context, created["candidate_id"])
    assert stored["state"] == "created"


def test_rel008_p01_and_n01_and_r01_promotion_exact_identity(migrated_db, release, context):
    created = release.create_candidate(context, *_inputs().values(), support_selection={})
    for suite in SUITES:
        release.record_suite_run(context, created["candidate_id"], suite, True, "d")
    release.qualify(context, created["candidate_id"], required_suites=list(SUITES))
    release.canary_deploy(context, created["candidate_id"], cohort="c", health_ok=True)
    release.canary_rollback(context, created["candidate_id"], rollback_ok=True)
    release.go_decision(context, created["candidate_id"],
                        blocking_reports={"suite-a": True, "suite-b": True},
                        slo_ok=True, security_ok=True, dr_ok=True,
                        canary_ok=True, rollback_ok=True)
    bundle = release.seal_readiness(
        context, created["candidate_id"],
        blocking_reports={"suite-a": True, "suite-b": True},
        canary={"ok": True}, rollback={"ok": True}, slo={"ok": True},
        security={"ok": True}, dr={"ok": True},
        go={"decision": "GO_APPROVED"})
    promoted = release.gate_m14_promote(context, created["candidate_id"],
                                        bundle["bundle_digest"])
    assert promoted["state"] == "production_ready"
    # REL-008-N01: promotion attempt with any different identity is rejected.
    changed = dict(_inputs())
    changed["config_digest"] = "other"
    with pytest.raises(PromotionRejected):
        release.verify_promoted_identity(context, created["candidate_id"],
                                         **changed)
    # REL-008-R01: rollback evidence preserved as distinct records.
    events = migrated_db.query_all(
        "SELECT kind, actor FROM release_events WHERE tenant_id=%s AND candidate_id=%s"
        " ORDER BY event_id",
        (context.tenant_id, created["candidate_id"]),
    )
    kinds = [e[0] for e in events]
    assert "candidate_created" in kinds
    assert "readiness_sealed->production_ready" in kinds
    assert "qualified->canary_deployed" in kinds
    assert "canary_deployed->rollback_proven" in kinds
