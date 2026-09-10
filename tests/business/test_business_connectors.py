"""Acceptance tests for BUS-001..005 and EXT-001..003 against the real
environment, with a real HTTP webhook boundary for ingress tests.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tests/control"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from effect_target import start_effect_target

from quansio.control.broker import CredentialBroker  # noqa: E402
from quansio.control.capability_packs import (  # noqa: E402
    BindFailure,
    CapabilityCompiler,
    CapabilityPackService,
    PackBinder,
    PackInvalid,
    PackPublisher,
    PublicationBlocked,
)
from quansio.control.connectors import (  # noqa: E402
    ConnectorBroker,
    EffectRequired,
    ToolRegistry,
    UnsafeDeclaration,
    WebhookIngress,
)
from quansio.control.effects import EffectLedger  # noqa: E402
from quansio.control.policy import PolicyEngine  # noqa: E402
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


def _full_pack() -> dict:
    return {
        "identity": {"pack_id": "invoice-ops", "vendor": "quansio", "domain": "finance"},
        "requirements": {"skills": ["invoice-triage"], "tools": ["ledger.post"],
                         "connectors": ["bank-api"], "knowledge": ["finance-fabric"]},
        "rbac": {"classify-invoice": "finance.role", "classify-invoice:role": "member",
                 "post-ledger": "finance.role", "post-ledger:role": "member"},
        "policy": {"permissions": {"classify-invoice": "finance.read",
                                   "post-ledger": "finance.write"},
                   "approvals": {"post-ledger": "payment.approval"},
                   "rules": {"classify-invoice": "finance.classify",
                             "post-ledger": "finance.post"}},
        "approvals": [{"name": "payment.approval", "ceiling_minor": 500000}],
        "workflows": [{"procedure": "invoice-flow"}],
        "io_contract": {"input": "invoice.stream", "output": "ledger.entries"},
        "evidence_policy": {"identities": ["receipt", "digest"], "retention_days": 365},
        "evaluations": [
            {"name": "classify-happy", "threshold": 1.0, "mandatory": True},
            {"name": "post-happy", "threshold": 1.0, "mandatory": True},
            {"name": "post-ceiling-denied", "threshold": 1.0, "mandatory": True},
        ],
        "compatibility": {"min_runtime": "9.0.0"},
    }


# ---------------------------------------------------------------------------
# BUS-001: pack contract
# ---------------------------------------------------------------------------


def test_bus001_p01_full_pack_reaches_draft(migrated_db, workspace_setup, context):
    service = CapabilityPackService(migrated_db)
    version = service.create_pack(context, "invoice-ops", _full_pack())
    pack = service.get_pack(context, "invoice-ops", version)
    assert pack["lifecycle"] == "draft"
    for section in ("identity", "requirements", "rbac", "policy", "approvals",
                    "workflows", "io_contract", "evidence_policy", "evaluations",
                    "compatibility"):
        assert section in pack


def test_bus001_n01_missing_thresholds_rbac_or_compatibility_never_publishable(migrated_db, workspace_setup, context):
    service = CapabilityPackService(migrated_db)
    broken_variants = []
    for missing in ("evaluations", "rbac", "policy", "compatibility"):
        pack = _full_pack()
        pack[missing] = {} if missing in ("rbac", "policy", "compatibility") else []
        broken_variants.append((missing, pack))
    for missing, pack in broken_variants:
        with pytest.raises(PackInvalid, match=missing.split("_")[0]):
            service.create_pack(context, f"broken-{missing}", pack)
    # And nothing reached even draft state.
    assert migrated_db.query_one(
        "SELECT count(*) FROM capability_packs WHERE tenant_id=%s", (context.tenant_id,)
    )[0] == 0


def test_bus001_r01_rollback_loads_prior_version_preserving_identities(migrated_db, workspace_setup, context):
    service = CapabilityPackService(migrated_db)
    base_version = service.create_pack(context, "invoice-ops", _full_pack())
    pack_v2 = _full_pack()
    pack_v2["identity"]["domain"] = "finance-revised"
    service.create_pack(context, "invoice-ops", pack_v2)
    migrated_db.execute(
        "UPDATE capability_packs SET rollback_version=%s WHERE tenant_id=%s"
        " AND pack_id='invoice-ops' AND version=2",
        (base_version, context.tenant_id),
    )
    result = service.rollback(context, "invoice-ops")
    assert result["active_version"] == base_version
    assert result["evidence_identities"] == ["receipt", "digest"]
    active = service.get_pack(context, "invoice-ops", v1)
    assert active["lifecycle"] == "published"


# ---------------------------------------------------------------------------
# BUS-002/003: compiler
# ---------------------------------------------------------------------------


def test_bus002_p01_authoritative_material_decomposes(migrated_db, workspace_setup, context):
    compiler = CapabilityCompiler(migrated_db)
    sources = [
        {"source_ref": "policy-book", "authority": "authoritative",
         "content": {"rules": True},
         "components": [
             {"kind": "rule", "name": "approval-over-limit",
              "statement": "invoices over 500000 minor require approval"},
             {"kind": "entity", "name": "vendor", "statement": "registered vendors"},
             {"kind": "permission", "name": "finance.write", "statement": "ledger writes"},
             {"kind": "procedure", "name": "invoice-flow", "statement": "steps"},
             {"kind": "input_output", "name": "invoice-stream", "statement": "in"},
             {"kind": "evidence_source", "name": "ledger", "statement": "digests"},
         ]},
    ]
    model = compiler.ingest(context, "invoice-ops", 1, sources)
    assert len(model["rules"]) == 1 and model["unresolved_conflicts"] == []
    assert model["entities"] and model["permissions"] and model["procedures"]


def test_bus002_n01_contradiction_yields_explicit_conflict_not_invented_rules(migrated_db, workspace_setup, context):
    compiler = CapabilityCompiler(migrated_db)
    sources = [
        {"source_ref": "policy-book-v1", "authority": "authoritative",
         "content": {}, "components": [
             {"kind": "rule", "name": "approval-over-limit",
              "statement": "threshold 500000"}]},
        {"source_ref": "policy-book-v2", "authority": "authoritative",
         "content": {}, "components": [
             {"kind": "rule", "name": "approval-over-limit",
              "statement": "threshold 100000"}]},
        {"source_ref": "wiki-note", "authority": "supplementary",
         "content": {}, "components": [
             {"kind": "rule", "name": "approval-under-limit",
              "statement": "never requires approval"}]},
    ]
    model = compiler.ingest(context, "invoice-ops", 1, sources)
    assert len(model["rules"]) == 1, "contradictory rules must not both compile"
    assert len(model["unresolved_conflicts"]) == 2
    assert any(c.get("rule") == "approval-over-limit" for c in model["unresolved_conflicts"])
    assert any("supplementary" in c.get("reason", "") for c in model["unresolved_conflicts"])


def test_bus003_p01_process_reconstruction_binds_skills_workflows(migrated_db, workspace_setup, context):
    CapabilityPackService(migrated_db).create_pack(context, "invoice-ops", _full_pack())
    compiler = CapabilityCompiler(migrated_db)
    sources = [
        {"source_ref": "runbook", "authority": "authoritative", "content": {},
         "components": [
             {"kind": "procedure", "name": "invoice-flow", "statement": "flow",
              "steps": [
                  {"name": "classify-invoice", "skill_ref": "invoice-triage",
                   "permission": "finance.read"},
                  {"name": "post-ledger", "skill_ref": "ledger-poster",
                   "permission": "finance.write", "approval": "payment.approval"}],
              "failure_paths": ["on mismatch: route to manual queue"]}]},
    ]
    model = compiler.ingest(context, "invoice-ops", 1, sources)
    pack_policy = {"permissions": {"finance.read": True, "finance.write": True},
                   "approvals": {"payment.approval": True}}
    reconstruction = compiler.reconstruct(context, "invoice-ops", 1, model, pack_policy)
    flow = reconstruction["workflows"][0]
    assert flow["fully_resolved"] is True
    assert flow["failure_paths"] == ["on mismatch: route to manual queue"]


def test_bus003_n01_workflow_with_absent_permission_stays_unresolved(migrated_db, workspace_setup, context):
    CapabilityPackService(migrated_db).create_pack(context, "invoice-ops", _full_pack())
    compiler = CapabilityCompiler(migrated_db)
    sources = [
        {"source_ref": "runbook", "authority": "authoritative", "content": {},
         "components": [
             {"kind": "procedure", "name": "invoice-flow", "statement": "flow",
              "steps": [{"name": "post-ledger", "skill_ref": "ledger-poster",
                         "permission": "finance.root", "approval": "payment.approval"}]}]},
    ]
    model = compiler.ingest(context, "invoice-ops", 1, sources)
    pack_policy = {"permissions": {"finance.read": True}, "approvals": {}}
    reconstruction = compiler.reconstruct(context, "invoice-ops", 1, model, pack_policy)
    flow = reconstruction["workflows"][0]
    assert flow["fully_resolved"] is False
    assert any("finance.root" in u.get("reason", "") for u in reconstruction["unresolved"])


def test_bus003_r01_dependency_change_regen_preserves_stable_ids(migrated_db, workspace_setup, context):
    CapabilityPackService(migrated_db).create_pack(context, "invoice-ops", _full_pack())
    compiler = CapabilityCompiler(migrated_db)
    sources_before = [
        {"source_ref": "runbook", "authority": "authoritative", "content": {},
         "components": [
             {"kind": "procedure", "name": "invoice-flow", "statement": "flow",
              "steps": [{"name": "classify-invoice", "skill_ref": "invoice-triage",
                         "permission": "finance.read"}]}]},
    ]
    model_before = compiler.ingest(context, "invoice-ops", 1, sources_before)
    before_entity = model_before["entities"]
    sources_after = sources_before + [
        {"source_ref": "addendum", "authority": "authoritative", "content": {},
         "components": [
             {"kind": "rule", "name": "rounding", "statement": "round half even"}]},
    ]
    model_after = compiler.ingest(context, "invoice-ops", 1, sources_after)
    assert model_after["entities"] == before_entity, "unaffected components stable"


# ---------------------------------------------------------------------------
# EXT-001: tool registry + fidelity contract
# ---------------------------------------------------------------------------


def test_ext001_p01_register_and_resolve_operations(migrated_db, workspace_setup, context):
    registry = ToolRegistry(migrated_db)
    registered = registry.register(
        context, "ledger.post", 1, schema={"amount": "int"},
        effect_class="consequential", fidelity_class="lossless",
        capability_need="finance.write", policy_need="payment.approval",
        timeout_ms=5000, idempotent=True, evidence_contract="receipt+digest",
    )
    resolved = registry.resolve(context, "ledger.post")
    assert resolved["version"] == 1 and resolved["effect_class"] == "consequential"
    assert resolved["evidence_contract"] == "receipt+digest"


def test_ext001_n01_unsafe_declarations_rejected(migrated_db, workspace_setup, context):
    registry = ToolRegistry(migrated_db)
    with pytest.raises(UnsafeDeclaration, match="without evidence contract"):
        registry.register(context, "payment.send", 1, schema={}, effect_class="consequential",
                          fidelity_class="lossless", capability_need="pay",
                          policy_need="approval", timeout_ms=1000, idempotent=False,
                          evidence_contract="none")
    with pytest.raises(UnsafeDeclaration, match="cannot be lossless"):
        registry.register(context, "summary.compress", 1, schema={}, effect_class="degrading",
                          fidelity_class="lossless", capability_need="read",
                          policy_need="none", timeout_ms=1000, idempotent=True,
                          evidence_contract="receipt")


def test_ext001_r01_deprecation_pins_running_steps(migrated_db, workspace_setup, context):
    registry = ToolRegistry(migrated_db)
    registry.register(context, "ledger.post", 1, schema={}, effect_class="state_changing",
                      fidelity_class="lossless", capability_need="finance.write",
                      policy_need="p", timeout_ms=1000, idempotent=True,
                      evidence_contract="receipt")
    registry.register(context, "ledger.post", 2, schema={}, effect_class="state_changing",
                      fidelity_class="lossless", capability_need="finance.write",
                      policy_need="p", timeout_ms=1000, idempotent=True,
                      evidence_contract="receipt+digest")
    registry.deprecate(context, "ledger.post", 1)
    # Admitted running step pinned to version 1 still resolves.
    pinned = registry.resolve(context, "ledger.post", max_version=1)
    assert pinned["version"] == 1 and pinned["lifecycle"] == "deprecated"
    # New admissions resolve only the supported version.
    fresh = registry.resolve(context, "ledger.post")
    assert fresh["version"] == 2 and fresh["lifecycle"] == "active"


# ---------------------------------------------------------------------------
# BUS-004: bindings
# ---------------------------------------------------------------------------


def test_bus004_p01_operations_bound_to_tools_rbac_policy_evidence(migrated_db, workspace_setup, context):
    registry = ToolRegistry(migrated_db)
    registry.register(context, "ledger.post", 1, schema={}, effect_class="consequential",
                      fidelity_class="lossless", capability_need="finance.write",
                      policy_need="payment.approval", timeout_ms=1000, idempotent=True,
                      evidence_contract="receipt+digest")
    binder = PackBinder(migrated_db)
    bindings = binder.bind(
        context, "invoice-ops", 1,
        workflow_steps=[{"name": "post-ledger"}],
        registry_rows={"post-ledger": {"operation": "ledger.post", "version": 1,
                                       "effect_class": "consequential",
                                       "fidelity_class": "lossless",
                                       "capability": "finance.write",
                                       "policy": "payment.approval"}},
        pack_rbac={"post-ledger": "finance.write", "post-ledger:role": "member"},
        policy_rules={"post-ledger": "payment.approval"},
    )
    assert bindings[0]["approval_required"] is True
    assert bindings[0]["evidence_requirement"] == "receipt+digest"
    stored = migrated_db.query_one(
        "SELECT operation_name, permission FROM pack_bindings WHERE step_ref='post-ledger'"
    )
    assert stored == ("ledger.post", "finance.write")


def test_bus004_n01_fidelity_or_permission_failure_blocks(migrated_db, workspace_setup, context):
    registry = ToolRegistry(migrated_db)
    binder = PackBinder(migrated_db)
    with pytest.raises(BindFailure, match="cannot be carried"):
        binder.bind(context, "invoice-ops", 1, [{"name": "post-ledger"}],
                    {"post-ledger": {"operation": "ledger.post", "version": 1,
                                     "effect_class": "consequential",
                                     "fidelity_class": "lossy",
                                     "capability": "finance.write", "policy": "p"}},
                    {"post-ledger": "finance.write"}, {"post-ledger": "p"})
    with pytest.raises(BindFailure, match="permission unresolved"):
        binder.bind(context, "invoice-ops", 1, [{"name": "post-ledger"}],
                    {"post-ledger": {"operation": "ledger.post", "version": 1,
                                     "effect_class": "state_changing",
                                     "fidelity_class": "lossless",
                                     "capability": "finance.write", "policy": "p"}},
                    {}, {"post-ledger": "p"})


def test_bus004_r01_rotation_requires_compat_rerun(migrated_db, workspace_setup, context):
    registry = ToolRegistry(migrated_db)
    binder = PackBinder(migrated_db)
    registry.register(context, "ledger.post", 1, schema={}, effect_class="state_changing",
                      fidelity_class="lossless", capability_need="finance.write",
                      policy_need="p", timeout_ms=1000, idempotent=True,
                      evidence_contract="receipt")
    registry.register(context, "ledger.post", 2, schema={}, effect_class="state_changing",
                      fidelity_class="lossless", capability_need="finance.write",
                      policy_need="p", timeout_ms=1000, idempotent=True,
                      evidence_contract="receipt+digest")
    bindings = binder.bind(
        context, "invoice-ops", 1, [{"name": "post-ledger"}],
        {"post-ledger": {"operation": "ledger.post", "version": 1,
                         "effect_class": "state_changing", "fidelity_class": "lossless",
                         "capability": "finance.write", "policy": "p"}},
        {"post-ledger": "finance.write"}, {"post-ledger": "p"})
    with pytest.raises(BindFailure, match="compatibility/evaluation not re-run"):
        binder.rebind_after_rotation(context, "invoice-ops", 1, "post-ledger", 2,
                                     compat_check=lambda: False)
    result = binder.rebind_after_rotation(context, "invoice-ops", 1, "post-ledger", 2,
                                          compat_check=lambda: True)
    assert result["operation_version"] == 2


# ---------------------------------------------------------------------------
# BUS-005: qualify and publish
# ---------------------------------------------------------------------------


def test_bus005_p01_publish_only_when_all_mandatory_pass(migrated_db, workspace_setup, context):
    CapabilityPackService(migrated_db).create_pack(context, "invoice-ops", _full_pack())
    publisher = PackPublisher(migrated_db)
    case_results = [
        {"case": "classify-happy", "passed": True},
        {"case": "post-happy", "passed": True},
        {"case": "post-ceiling-denied", "passed": True},
    ]
    outcome = publisher.qualify_and_publish(
        context, "invoice-ops", 1, case_results,
        publish_execution=lambda v: {"runtime_confirmed": v},
    )
    assert outcome["published"] is True
    lifecycle = migrated_db.query_one(
        "SELECT lifecycle FROM capability_packs WHERE tenant_id=%s AND pack_id='invoice-ops' AND version=1",
        (context.tenant_id,),
    )[0]
    assert lifecycle == "published"


def test_bus005_n01_mandatory_failure_blocks_despite_high_aggregate(migrated_db, workspace_setup, context):
    CapabilityPackService(migrated_db).create_pack(context, "invoice-ops", _full_pack())
    publisher = PackPublisher(migrated_db)
    case_results = [
        {"case": "classify-happy", "passed": True},
        {"case": "post-happy", "passed": True},
        {"case": "post-ceiling-denied", "passed": False},  # mandatory, aggregate = 2/3
    ]
    with pytest.raises(PublicationBlocked, match="post-ceiling-denied"):
        publisher.qualify_and_publish(
            context, "invoice-ops", 1, case_results,
            publish_execution=lambda v: {"runtime_confirmed": v})


def test_bus005_r01_rollback_resolves_rollback_version(migrated_db, workspace_setup, context):
    publisher = PackPublisher(migrated_db)
    service = CapabilityPackService(migrated_db)
    base_version = service.create_pack(context, "invoice-ops", _full_pack())
    pack_v2 = _full_pack()
    service.create_pack(context, "invoice-ops", pack_v2)
    migrated_db.execute(
        "UPDATE capability_packs SET rollback_version=%s WHERE tenant_id=%s"
        " AND pack_id='invoice-ops' AND version=2",
        (base_version, context.tenant_id),
    )
    rolled = publisher.rollback_published(context, "invoice-ops")
    assert rolled["active_version"] == v1
    historical = migrated_db.query_one(
        "SELECT lifecycle FROM capability_packs WHERE tenant_id=%s AND pack_id='invoice-ops' AND version=2",
        (context.tenant_id,),
    )[0]
    assert historical == "rolled_back"


# ---------------------------------------------------------------------------
# EXT-002: governed integration broker
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def effect_target_factory():
    servers = []

    def factory(delay_seconds: float = 0.0):
        server, port, recorded = start_effect_target(delay_seconds=delay_seconds)
        servers.append(server)
        return {"base": f"http://127.0.0.1:{port}", "recorded": recorded}

    yield factory
    for server in servers:
        server.shutdown()


@pytest.fixture()
def broker_setup(migrated_db, workspace_setup, context, effect_target_factory):
    policy = PolicyEngine(migrated_db)
    broker = CredentialBroker(migrated_db)
    ledger = EffectLedger(migrated_db)
    target = effect_target_factory()
    broker.register_secret(context, "bank-api", "bank", "real-bank-secret")
    handle = broker.issue(context, "bank-api", "connector.submit", "external:bank",
                          capability="connector")
    run_id = _parent_run(migrated_db, context)
    effect = ledger.propose(context, run_id=run_id, operation="connector.submit",
                            arguments={"amount": 100}, target="external:bank",
                            idempotency_key=str(uuid.uuid4()))
    ledger.authorize(context, effect["effect_id"], str(uuid.uuid4()))
    connector = ConnectorBroker(migrated_db, broker, ledger, policy)
    return {
        "context": context, "connector": connector, "handle_id": handle["handle_id"],
        "effect_id": effect["effect_id"], "idempotency_key": effect["idempotency_key"],
        "run_id": run_id, "policy": policy, "ledger": ledger, "target": target,
    }


def _parent_run(db, context) -> str:
    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', %s)",
            (context.tenant_id, context.workspace_id, agent_id, f"ext-{agent_id[:8]}"),
        )
    run_id = TenantRepository(db).create_run(context, agent_id)
    with db.connection() as connection:
        connection.execute("UPDATE runs SET status='running' WHERE tenant_id=%s AND run_id=%s",
                           (context.tenant_id, run_id))
    return run_id


def test_ext002_p01_mediated_connector_execution_with_receipt(migrated_db, broker_setup):
    setup = broker_setup
    calls = []

    def transport(material, operation, target, arguments):
        calls.append(material)
        return {"accepted": True, "receipt": "rcpt-1"}

    outcome = setup["connector"].execute_connector_operation(
        setup["context"], setup["effect_id"], setup["handle_id"],
        "connector.submit", "external:bank", {"amount": 100}, transport,
    )
    assert outcome["receipt"]["accepted"] is True
    assert calls == ["real-bank-secret"], "secret exchanged server-side exactly once"
    row = migrated_db.query_one(
        "SELECT status, receipt FROM effects WHERE effect_id=%s", (setup["effect_id"],)
    )
    assert row[0] == "committed" and row[1]["accepted"] is True


def test_ext002_n01_direct_path_and_missing_effect_refused(migrated_db, broker_setup):
    setup = broker_setup
    with pytest.raises(EffectRequired, match="forbidden"):
        setup["connector"].direct_adapter_call_refused("raw-secret")
    # Consequential connector op without an effect: refused.
    with pytest.raises(EffectRequired):
        setup["connector"].execute_connector_operation(
            setup["context"], str(uuid.uuid4()), setup["handle_id"],
            "connector.submit", "external:bank", {}, transport=lambda *a: {"ok": True})


def test_ext002_r01_ambiguous_timeout_creates_unknown_and_reconciles(migrated_db, broker_setup):
    setup = broker_setup

    def transport(material, operation, target, arguments):
        raise TimeoutError("connector timeout")

    with pytest.raises(TimeoutError):
        setup["connector"].execute_connector_operation(
            setup["context"], setup["effect_id"], setup["handle_id"],
            "connector.submit", "external:bank", {}, transport)
    state = migrated_db.query_one("SELECT status FROM effects WHERE effect_id=%s",
                                  (setup["effect_id"],))[0]
    assert state == "unknown"
    # Probe says the connector actually committed: reconcile to committed.
    reconciler = __import__("quansio.control.effects", fromlist=["UnknownEffectReconciler"]).UnknownEffectReconciler(migrated_db, setup["ledger"])
    outcome = reconciler.probe(
        setup["context"], setup["effect_id"],
        target_query=lambda key: "committed" if key == setup["idempotency_key"] else "not_found",
    )
    assert outcome["final"] == "reconciled"


# ---------------------------------------------------------------------------
# EXT-003: authenticated idempotent webhook ingress
# ---------------------------------------------------------------------------


@pytest.fixture()
def webhook(migrated_db, workspace_setup, context):
    created_work = []

    def work_creator(payload):
        ref = f"work-{uuid.uuid4().hex[:8]}"
        created_work.append(ref)
        return ref

    secrets = {"ledger-system": "webhook-shared-secret"}
    ingress = WebhookIngress(migrated_db, secrets, work_creator)
    return {"ingress": ingress, "context": context, "created": created_work,
            "secrets": secrets}


def test_ext003_p01_authenticated_ingress_creates_work_once(webhook, migrated_db, context):
    body = json.dumps({"event": "ledger.posted", "amount": 100}).encode()
    signature = hmac.new(webhook["secrets"]["ledger-system"].encode(),
                         body, hashlib.sha256).hexdigest()
    ingress = webhook["ingress"]
    received = ingress.ingress(webhook["context"], "ledger-system", body, signature,
                               event_identity=f"evt-001-{uuid.uuid4().hex[:8]}")
    assert received["duplicate"] is False
    work = ingress.create_work(webhook["context"], received["webhook_id"])
    assert work["created_now"] is True and work["work_ref"]
    # Correlation recorded: tenant + tool/work linkage.
    row = migrated_db.query_one(
        "SELECT source_name, state, work_ref FROM webhook_ingress WHERE tenant_id=%s AND webhook_id=%s",
        (context.tenant_id, received["webhook_id"]),
    )
    assert row[0] == "ledger-system" and row[1] == "work_created"
    assert row[2] == work["work_ref"]


def test_ext003_n01_replay_and_invalid_signature_rejected(webhook):
    evt_replay_id = f"evt-replay-{uuid.uuid4().hex[:8]}"
    body = json.dumps({"event": "ledger.posted", "amount": 200}).encode()
    signature = hmac.new(webhook["secrets"]["ledger-system"].encode(),
                         body, hashlib.sha256).hexdigest()
    ingress = webhook["ingress"]
    first = ingress.ingress(webhook["context"], "ledger-system", body, signature,
                            event_identity=evt_replay_id)
    work = ingress.create_work(webhook["context"], first["webhook_id"])
    # Replay: same event identity must not create new work.
    replay = ingress.ingress(webhook["context"], "ledger-system", body, signature,
                             event_identity=evt_replay_id)
    assert replay["duplicate"] is True
    replay_work = ingress.create_work(webhook["context"], replay["webhook_id"])
    assert replay_work["created_now"] is False
    assert replay_work["work_ref"] == work["work_ref"]
    # Invalid source authentication.
    with pytest.raises(PermissionError, match="invalid webhook source"):
        ingress.ingress(webhook["context"], "ledger-system", body, "bad-signature",
                        event_identity=f"evt-bad-{uuid.uuid4().hex[:8]}")
    # Unknown source.
    with pytest.raises(PermissionError, match="invalid webhook source"):
        ingress.ingress(webhook["context"], "unknown-system", body, signature,
                        event_identity=f"evt-unk-{uuid.uuid4().hex[:8]}")


def test_ext003_r01_crash_between_ingress_and_work_resumes_once(webhook):
    evt_crash_id = f"evt-crash-{uuid.uuid4().hex[:8]}"
    body = json.dumps({"event": "invoice.received"}).encode()
    signature = hmac.new(webhook["secrets"]["ledger-system"].encode(),
                         body, hashlib.sha256).hexdigest()
    ingress = webhook["ingress"]
    received = ingress.ingress(webhook["context"], "ledger-system", body, signature,
                               event_identity=evt_crash_id)
    # Crash after durable ingress record, before work creation.
    resumed = ingress.create_work(webhook["context"], received["webhook_id"])
    assert resumed["created_now"] is True
    # Repeat resume: exactly once.
    again = ingress.create_work(webhook["context"], received["webhook_id"])
    assert again["created_now"] is False
    assert len(webhook["created"]) == 1
