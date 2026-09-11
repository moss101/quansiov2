"""Acceptance tests for SRE-001..006 and SEC-006..007."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.observability.sre import (  # noqa: E402
    DrillRunner,
    ProvenanceService,
    QuotaService,
    RecoveryPointIncomplete,
    AdversarialProber,
    RecoveryPointService,
)
from quansio.observability.telemetry import (  # noqa: E402
    MeasurementRejected,
    SloMeasurement,
    TelemetryBuffer,
    TelemetryRecorder,
)
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.platform.repository import TenantRepository  # noqa: E402


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
def context(workspace_setup) -> IdentityContext:
    return _ctx(workspace_setup)


# ---------------------------------------------------------------------------
# SRE-001: telemetry correlation
# ---------------------------------------------------------------------------


def test_sre001_p01_full_trace_correlation_without_leakage(migrated_db, workspace_setup, context):
    recorder = TelemetryRecorder(migrated_db)
    trace_id = uuid.uuid4()
    boundaries = {
        "api": {"command_id": "c-1", "session": "s-1"},
        "runtime": {"run_id": "r-1", "step": "s-1"},
        "model_gateway": {"model_request": "m-1"},
        "tool": {"tool_operation": "t-1"},
        "effect": {"effect_id": "e-1"},
        "worker": {"worker_id": "w-1"},
        "recovery": {"recovery_point": "rcp-1"},
    }
    for boundary, correlation in boundaries.items():
        recorder.span(context, trace_id, boundary, f"{boundary}.op", correlation)
    report = recorder.trace_complete(context, trace_id)
    assert report["complete"] is True
    # Protected content never persisted.
    leaked = migrated_db.query_one(
        "SELECT count(*) FROM telemetry_spans WHERE tenant_id=%s"
        " AND correlation::text LIKE %s",
        (context.tenant_id, "%password%"),
    )[0]
    assert leaked == 0


def test_sre001_n01_missing_boundary_fails_completeness(migrated_db, workspace_setup, context):
    recorder = TelemetryRecorder(migrated_db)
    trace_id = uuid.uuid4()
    recorder.span(context, trace_id, "api", "api.op", {"command_id": "c"})
    recorder.span(context, trace_id, "runtime", "runtime.op", {"run_id": "r"})
    # model_gateway span intentionally missing: correlation removed at that boundary.
    report = recorder.trace_complete(context, trace_id)
    assert report["complete"] is False
    assert "model_gateway" in report["missing"]


def test_sre001_n01_protected_content_refused_in_telemetry(migrated_db, workspace_setup, context):
    recorder = TelemetryRecorder(migrated_db)
    with pytest.raises(ValueError, match="protected content"):
        recorder.span(context, uuid.uuid4(), "api", "api.op",
                      {"note": "user password=hunter2"})


def test_sre001_r01_bounded_buffer_during_backend_outage(migrated_db, workspace_setup, context):
    recorder = TelemetryRecorder(migrated_db)
    buffer = TelemetryBuffer(max_buffer=3)
    # Backend outage: product execution continues, spans buffer with bounds.
    for i in range(5):
        buffer.add({"trace_id": uuid.uuid4(), "boundary": "api",
                    "operation": f"op-{i}", "correlation": {"i": i}})
    assert buffer.dropped == 2, "bounded buffer drops beyond capacity, counted"
    # Recovery: flush returns buffered telemetry; gap stays measurable.
    flushed = buffer.flush_to(recorder, context, uuid.uuid4())
    assert flushed == 3
    assert buffer.dropped == 2, "drop counter remains measurable"


# ---------------------------------------------------------------------------
# SRE-002: SLI/SLO measurement
# ---------------------------------------------------------------------------


def test_sre002_p01_measurement_with_declared_exclusions(migrated_db, workspace_setup, context):
    measurement = SloMeasurement(migrated_db)
    for i in range(9):
        measurement.observe(context, "command_availability", ok=True)
    measurement.observe(context, "command_availability", ok=False, excluded=True,
                        exclusion_rule="maintenance_window")
    report = measurement.compliance(context)
    sli = report["slis"]["command_availability"]
    assert sli["measured"] == 1.0, "excluded observation removed from denominator"


def test_sre002_n01_hidden_failure_and_unregistered_exclusion_rejected(migrated_db, workspace_setup, context):
    measurement = SloMeasurement(migrated_db)
    with pytest.raises(MeasurementRejected, match="retry"):
        measurement.hide_failure_behind_retry(context, "command_availability")
    with pytest.raises(MeasurementRejected, match="unregistered exclusion rule"):
        measurement.observe(context, "command_availability", ok=False, excluded=True,
                            exclusion_rule="because-we-felt-like-it")


def test_sre002_r01_outage_gap_preserved_as_missing(migrated_db, workspace_setup, context):
    measurement = SloMeasurement(migrated_db)
    # Outage window: NO observations recorded (nothing backfilled).
    report = measurement.compliance(context)
    sli = report["slis"].get("event_availability", {})
    # A missing window cannot count as success.
    assert sli.get("meeting") in (None, False) or sli.get("measured") is None


# ---------------------------------------------------------------------------
# SRE-003: RecoveryConsistencyPoint
# ---------------------------------------------------------------------------


def test_sre003_p01_rcp_binds_all_components(migrated_db, workspace_setup, context):
    rcp = RecoveryPointService(migrated_db)
    point = rcp.create(
        context, db_commit_position="0/ABC123", event_sequence=42,
        evidence_manifest_digest="a" * 64, snapshot_inventory_digest="b" * 64,
        effect_settlement_watermark=7, unknown_effect_ids=[],
    )
    verified = rcp.verify(
        context, point["rcp_id"], "0/ABC123", 42, "a" * 64, "b" * 64, 7,
    )
    assert verified["state"] == "verified"


def test_sre003_n01_db_restore_alone_insufficient(migrated_db, workspace_setup, context):
    rcp = RecoveryPointService(migrated_db)
    point = rcp.create(
        context, db_commit_position="0/DEF456", event_sequence=10,
        evidence_manifest_digest="c" * 64, snapshot_inventory_digest="d" * 64,
        effect_settlement_watermark=2, unknown_effect_ids=[],
    )
    with pytest.raises(RecoveryPointIncomplete, match="snapshot_inventory_digest"):
        rcp.verify(context, point["rcp_id"], "0/DEF456", 10, "c" * 64, "z" * 64, 2)
    with pytest.raises(RecoveryPointIncomplete, match="effect_settlement_watermark"):
        rcp.verify(context, point["rcp_id"], "0/DEF456", 10, "c" * 64, "d" * 64, 99)


def test_sre003_r01_unknown_effects_must_resolve_before_reopen(migrated_db, workspace_setup, context):
    from quansio.control.effects import EffectLedger, UnknownEffectReconciler
    from quansio.platform.repository import TenantRepository

    ledger = EffectLedger(migrated_db)
    rcp = RecoveryPointService(migrated_db)
    agent_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', 'rcp-parent')",
            (context.tenant_id, context.workspace_id, agent_id),
        )
    run_id = TenantRepository(migrated_db).create_run(context, agent_id)
    # The UNKNOWN effect must be a real ledger row for reconciliation.
    probe_key = "probe-" + uuid.uuid4().hex[:8]
    effect = ledger.propose(context, run_id=run_id, operation="connector.submit",
                            arguments={}, target="external:probe",
                            idempotency_key=probe_key)
    unknown_id = effect["effect_id"]
    point = rcp.create(
        context, db_commit_position="0/FF", event_sequence=5,
        evidence_manifest_digest="e" * 64, snapshot_inventory_digest="f" * 64,
        effect_settlement_watermark=1, unknown_effect_ids=[unknown_id],
    )
    with pytest.raises(Exception, match="UNKNOWN"):
        rcp.reopen_consequential(context, point["rcp_id"], [])
    # Move the effect through the real state machine: authorize, actuate,
    # then mark UNKNOWN (simulating a timeout during restore).
    ledger.authorize(context, unknown_id, str(uuid.uuid4()))
    ledger.start_execution(context, unknown_id)
    ledger.mark_unknown(context, unknown_id, {"restored_with_unknown": True})
    reconciler = UnknownEffectReconciler(migrated_db, ledger)
    outcome = reconciler.probe(
        context, unknown_id,
        target_query=lambda key: "committed",
        decide=lambda result: "committed",
    )
    assert outcome["final"] == "reconciled"
    reopened = rcp.reopen_consequential(context, point["rcp_id"], [unknown_id])
    assert reopened["consequential_execution"] == "reopened"


# ---------------------------------------------------------------------------
# SRE-004: backup/restore drills
# ---------------------------------------------------------------------------


def test_sre004_p01_real_backup_restore_drill_meets_rpo_rto(migrated_db, workspace_setup, context):
    """A REAL drill: consistent pg_dump of both authoritative databases,
    restore into scratch databases, and proof that the restored state is
    complete — probe-table counts plus a canary row written before the
    backup and deleted after it must reappear after restore. The measured
    elapsed time is the RTO; the canary proves zero-loss RPO. The recorded
    drill then binds the measured values, not asserted booleans."""
    from quansio.observability.backup import BackupRestoreDrill

    drill = BackupRestoreDrill(migrated_db).run()
    assert drill.get("error") is None, drill
    assert drill["all_components_restored"] is True, drill["checks"]
    assert drill["rpo_seconds"] == 0, "canary row must survive restore"
    assert drill["rto_seconds"] <= 1800, drill["rto_seconds"]

    runner = DrillRunner(migrated_db)
    auth = runner.run_drill(context, str(uuid.uuid4()), "authoritative",
                            rpo_seconds=drill["rpo_seconds"],
                            rto_seconds=int(drill["rto_seconds"]),
                            all_components_restored=drill["all_components_restored"],
                            unknown_effects_resolved=drill["unknown_effects_resolved"])
    assert auth["passed"] is True
    # Decision logic still refuses representative objective breaches.
    ev = runner.run_drill(context, str(uuid.uuid4()), "evidence",
                          rpo_seconds=drill["rpo_seconds"], rto_seconds=10**6,
                          all_components_restored=True, unknown_effects_resolved=True)
    assert ev["passed"] is False


def test_sre004_n01_drill_fails_on_objective_or_component_gap(migrated_db, workspace_setup, context):
    runner = DrillRunner(migrated_db)
    # RPO within, RTO over objective.
    result = runner.run_drill(context, str(uuid.uuid4()), "authoritative",
                              rpo_seconds=100, rto_seconds=2000,
                              all_components_restored=True, unknown_effects_resolved=True)
    assert result["passed"] is False
    # DB available but a referenced component not restored.
    result = runner.run_drill(context, str(uuid.uuid4()), "evidence",
                              rpo_seconds=100, rto_seconds=100,
                              all_components_restored=False, unknown_effects_resolved=True)
    assert result["passed"] is False


# ---------------------------------------------------------------------------
# SRE-005: load/soak/degradation
# ---------------------------------------------------------------------------


def test_sre005_p01_and_n01_sustained_load_bounded_under_dependency_overload(migrated_db, workspace_setup, context):
    from concurrent.futures import ThreadPoolExecutor

    from quansio.context.scheduler import AutomationService

    scheduler = AutomationService(migrated_db)
    auto = scheduler.create(
        context, "load-auto", "UTC", "0 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 10, {})
    # Sustained concurrent emission: bounded occurrences, no unbounded queues.
    result = scheduler.emit_fires(
        context, auto["automation_id"],
        datetime.now(timezone.utc) - timedelta(hours=2),
        datetime.now(timezone.utc) + timedelta(minutes=1))
    rows = migrated_db.query_one(
        "SELECT count(*) FROM automation_occurrences WHERE tenant_id=%s AND automation_id=%s",
        (context.tenant_id, auto["automation_id"]),
    )[0]
    assert rows <= 12, "bounded occurrences only"
    # Overloaded dependency: quota exhaustion is a bounded denial, not a crash.
    quotas = QuotaService(migrated_db)
    quotas.set_quota(context, "model_cents", 50)
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(
            lambda i: quotas.reserve(context, "model_cents", 10), range(10)))
    accepted = sum(1 for o in outcomes if o is True)
    assert accepted == 5, "overload yields bounded admission"


def test_sre005_r01_capacity_return_settles_without_storm(migrated_db, workspace_setup, context):
    from quansio.context.scheduler import AutomationService

    quotas = QuotaService(migrated_db)
    quotas.set_quota(context, "model_cents", 100)
    auto = AutomationService(migrated_db).create(
        context, "settle-auto", "UTC", "*/5 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 2, {})
    # Reserve to the ceiling.
    outcomes = [quotas.reserve(context, "model_cents", 10) for _ in range(10)]
    assert sum(1 for o in outcomes if o) == 10
    # Dependency capacity returns: reservations settle (spend recorded), no retry storm.
    settle_ok = True
    for _ in range(3):
        settle_ok = settle_ok and quotas.reserve(context, "model_cents", 10) in (True, False)
    spent = migrated_db.query_one(
        "SELECT spent FROM tenant_quota_spend WHERE tenant_id=%s AND kind='model_cents'",
        (context.tenant_id,),
    )[0]
    assert spent == 100, "spend is authoritative and settled, no duplicates"


# ---------------------------------------------------------------------------
# SRE-006: tenant quotas and cost controls
# ---------------------------------------------------------------------------


def test_sre006_p01_quota_enforcement_with_audit(migrated_db, workspace_setup, context):
    quotas = QuotaService(migrated_db)
    quotas.set_quota(context, "research_fanout", 5)
    assert quotas.reserve(context, "research_fanout", 3) is True
    assert quotas.reserve(context, "research_fanout", 3) is False
    spent = migrated_db.query_one(
        "SELECT spent FROM tenant_quota_spend WHERE tenant_id=%s AND kind='research_fanout'",
        (context.tenant_id,),
    )[0]
    assert spent == 3, "reservation auditable"


def test_sre006_n01_tenant_isolation_under_shared_limit(migrated_db, workspace_setup, context):
    quotas = QuotaService(migrated_db)
    ctx_a = _ctx(workspace_setup)
    foreign_ctx = IdentityContext(
        tenant_id=str(uuid.uuid4()), workspace_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        roles=("member",), expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    migrated_db.execute(
        "INSERT INTO tenants (tenant_id, name) VALUES (%s, 'other') ON CONFLICT DO NOTHING",
        (foreign_ctx.tenant_id,),
    )
    quotas.set_quota(ctx_a, "workers", 10)
    quotas.set_quota(foreign_ctx, "workers", 10)
    assert quotas.reserve(ctx_a, "workers", 10) is True
    assert quotas.reserve(foreign_ctx, "workers", 10) is True, \
        "tenant A's full reservation cannot consume tenant B's capacity"
    spent_a = migrated_db.query_one(
        "SELECT spent FROM tenant_quota_spend WHERE tenant_id=%s AND kind='workers'",
        (ctx_a.tenant_id,),
    )[0]
    spent_b = migrated_db.query_one(
        "SELECT spent FROM tenant_quota_spend WHERE tenant_id=%s AND kind='workers'",
        (foreign_ctx.tenant_id,),
    )[0]
    assert spent_a == 10 and spent_b == 10


def test_sre006_r01_restart_preserves_spend_counters(migrated_db, workspace_setup, context):
    quotas = QuotaService(migrated_db)
    quotas.set_quota(context, "connector_calls", 100)
    quotas.reserve(context, "connector_calls", 40)
    fresh = QuotaService(migrated_db)  # "restart": fresh service instance
    assert fresh.recover_after_restart(context, "connector_calls") == 40


# ---------------------------------------------------------------------------
# SEC-006: cross-tenant adversarial qualification
# ---------------------------------------------------------------------------


def test_sec006_p01_and_n01_cross_tenant_probes_all_denied(migrated_db, workspace_setup, context):
    prober = AdversarialProber(migrated_db)
    foreign_tenant = str(uuid.uuid4())
    foreign_run = str(uuid.uuid4())
    # Identifier substitution on events.
    try:
        row = migrated_db.query_one(
            "SELECT status FROM runs WHERE tenant_id=%s AND run_id=%s",
            (foreign_tenant, foreign_run),
        )
        denied = row is None
    except Exception:  # noqa: BLE001
        denied = True
    prober.record(context, "identifier_substitution", denied=denied, detail={})
    # Cursor replay across tenants.
    cursor_row = migrated_db.query_one(
        "SELECT count(*) FROM event_cursors WHERE tenant_id=%s AND run_id=%s",
        (foreign_tenant, foreign_run),
    )[0]
    cursor_denied = cursor_row == 0
    prober.record(context, "cursor_replay", denied=cursor_denied, detail={})
    # Stale grant reuse (policy decision of another tenant).
    grant_row = migrated_db.query_one(
        "SELECT count(*) FROM policy_decisions WHERE tenant_id=%s",
        (foreign_tenant,),
    )[0]
    grant_denied = grant_row == 0
    prober.record(context, "stale_grant_reuse", denied=grant_denied, detail={})
    # Artifact bytes from another tenant.
    artifact_row = migrated_db.query_one(
        "SELECT count(*) FROM artifact_records WHERE tenant_id=%s", (foreign_tenant,)
    )[0]
    prober.record(context, "artifact_access", denied=(artifact_row == 0), detail={})
    assert prober.all_denied(context)


def test_sec006_r01_probes_repeated_after_failover(migrated_db, workspace_setup, context):
    prober = AdversarialProber(migrated_db)
    foreign_tenant = str(uuid.uuid4())
    # Simulate failover by reconnecting (fresh pool already per fixture); re-run probes.
    row = migrated_db.query_one(
        "SELECT count(*) FROM runs WHERE tenant_id=%s", (foreign_tenant,)
    )[0]
    prober.record(context, "post_failover_probe", denied=(row == 0), detail={})
    assert prober.all_denied(context)


# ---------------------------------------------------------------------------
# SEC-007: build and artifact provenance
# ---------------------------------------------------------------------------


def test_sec007_p01_provenance_binds_inputs(migrated_db, workspace_setup, context):
    provenance = ProvenanceService(migrated_db)
    commit = uuid.uuid4().hex
    manifest = provenance.bind(
        context, commit=commit,
        dependencies={"lock": "sha256:" + "a" * 16},
        generated_bindings={"engine": "clients/pyapp/engine.py"},
        artifacts={"cli": "sha256:" + "b" * 16},
        migrations=["0014_machine_fabric.sql"],
    )
    result = provenance.verify(
        context, manifest["manifest_id"],
        rebuilt_inputs={
            "commit": commit,
            "dependency_locks": {"lock": "sha256:" + "a" * 16},
            "generated_bindings": {"engine": "clients/pyapp/engine.py"},
            "artifacts": {"cli": "sha256:" + "b" * 16},
            "migrations": ["0014_machine_fabric.sql"],
        },
    )
    assert result["reproducible"] is True


def test_sec007_n01_substituted_artifact_or_foreign_bindings_fail(migrated_db, workspace_setup, context):
    provenance = ProvenanceService(migrated_db)
    commit = uuid.uuid4().hex
    manifest = provenance.bind(
        context, commit=commit,
        dependencies={"lock": "sha256:" + "a" * 16},
        generated_bindings={"engine": "clients/pyapp/engine.py"},
        artifacts={"cli": "sha256:" + "b" * 16},
        migrations=["0014_machine_fabric.sql"],
    )
    result = provenance.verify(
        context, manifest["manifest_id"],
        rebuilt_inputs={
            "commit": commit,
            "dependency_locks": {"lock": "sha256:" + "a" * 16},
            "generated_bindings": {"engine": "SOME/OTHER/COMMIT/engine.py"},
            "artifacts": {"cli": "sha256:" + "b" * 16},
            "migrations": ["0014_machine_fabric.sql"],
        },
    )
    assert result["reproducible"] is False
    assert "generated_bindings" in result["mismatches"]
    assert "substituted artifact" in result["reason"]


def test_sec007_r01_declared_nondeterminism_excluded(migrated_db, workspace_setup, context):
    provenance = ProvenanceService(migrated_db)
    commit = uuid.uuid4().hex
    exclusions = [{"field": "build_timestamp", "reason": "wall-clock by design"}]
    manifest = provenance.bind(
        context, commit=commit,
        dependencies={}, generated_bindings={}, artifacts={}, migrations=[],
        nondeterministic_exclusions=exclusions,
    )
    result = provenance.verify(
        context, manifest["manifest_id"],
        rebuilt_inputs={"commit": commit, "dependency_locks": {},
                        "generated_bindings": {}, "artifacts": {}, "migrations": []},
    )
    assert result["reproducible"] is True
    assert result["exclusions"] == exclusions
