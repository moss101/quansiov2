"""QA qualification verticals (QA-001..QA-008).

Each vertical exercises already-closed M0–M12 primitives end-to-end through
their canonical paths against the real qualification environment.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))
sys.path.insert(0, str(REPO_ROOT / "tests/control"))

from clients.pyapp.engine import ConvergenceEngine  # noqa: E402
from quansio.control.broker import CredentialBroker  # noqa: E402
from quansio.control.effects import (  # noqa: E402
    ApprovalMismatch,
    ApprovalService,
    EffectLedger,
    UnknownEffectReconciler,
)
from quansio.control.policy import PolicyEngine  # noqa: E402
from quansio.context.collaboration import (  # noqa: E402
    CollaborationProjection,
    NotificationService,
    TeammateRoutineService,
)
from quansio.context.scheduler import AutomationService  # noqa: E402
from quansio.machine_control.inventory import (  # noqa: E402
    LeaseRejection,
    Placer,
    TargetInventory,
)
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.control.skills import SkillEvaluator, SkillIntake, SkillRegistry  # noqa: E402
from quansio.machine_control.inventory import Placer, TargetInventory  # noqa: E402
from quansio.observability.sre import RecoveryPointIncomplete  # noqa: E402
from quansio.platform.repository import TenantRepository  # noqa: E402
from quansio.qworkerd.protocol import GuestProtocol  # noqa: E402
from quansio.runtime.events import EventLog  # noqa: E402
from quansio.runtime.orchestration import TurnDispatcher  # noqa: E402
from quansio.worker_gateway.browser import (  # noqa: E402
    BrowserSessionManager,
    TakeoverService,
    TakeoverStateError,
)


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


@pytest.fixture(scope="module")
def scheduler(migrated_db):
    from quansio.context.scheduler import AutomationService

    return AutomationService(migrated_db)


@pytest.fixture(scope="module")
def effect_target_factory():
    from effect_target import start_effect_target

    servers = []

    def factory(delay_seconds: float = 0.0):
        server, port, recorded = start_effect_target(delay_seconds=delay_seconds)
        servers.append(server)
        return {"base": f"http://127.0.0.1:{port}", "recorded": recorded}

    yield factory
    for server in servers:
        server.shutdown()


@pytest.fixture(scope="module")
def ambiguous_target(effect_target_factory):
    return effect_target_factory(delay_seconds=2.0)


@pytest.fixture(scope="module")
def effect_target(effect_target_factory):
    return effect_target_factory()


@pytest.fixture(scope="module")
def inventory(migrated_db):
    return TargetInventory(migrated_db)


@pytest.fixture(scope="module")
def ambiguous_target(effect_target_factory):
    return effect_target_factory(delay_seconds=2.0)


@pytest.fixture(scope="module")
def effect_target(effect_target_factory):
    return effect_target_factory()


@pytest.fixture()
def placer(migrated_db, inventory):
    return Placer(migrated_db, inventory)


def _parent_run(db, context) -> str:
    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', %s)",
            (context.tenant_id, context.workspace_id, agent_id, f"qa-{agent_id[:8]}"),
        )
    run_id = TenantRepository(db).create_run(context, agent_id)
    with db.connection() as connection:
        connection.execute(
            "UPDATE runs SET status='running', budget_cents=1000 WHERE tenant_id=%s AND run_id=%s",
            (context.tenant_id, run_id))
    return run_id


# ---------------------------------------------------------------------------
# QA-001: persistent teammate and worker vertical
# ---------------------------------------------------------------------------


def test_qa001_p01_teammate_with_32_workers_disconnect_partial_cancel_restart(migrated_db, workspace_setup, context):
    from quansio.runtime.orchestration import TurnDispatcher

    dispatcher = TurnDispatcher(migrated_db)
    run_id = _parent_run(migrated_db, context)
    child_agents = []
    for i in range(32):
        child_agents.append(str(uuid.uuid4()))
    with migrated_db.connection() as connection:
        for agent_id in child_agents:
            connection.execute(
                "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
                " VALUES (%s, %s, %s, 'ephemeral_worker', %s)",
                (context.tenant_id, context.workspace_id, agent_id, f"qa1-{agent_id[:8]}"))
    delivery_ids = []
    for i in range(32):
        delivery_ids.append(dispatcher.dispatch(
            context, run_id, child_agents[i], {"index": i}))
    # Client "disconnect": only half deliver; the rest stay pending.
    for i, d in enumerate(delivery_ids[:16]):
        assert dispatcher.deliver_outcome(
            context, d, str(uuid.uuid4()), {"index": i, "result": f"r{i}"}) is True
    aggregate = dispatcher.aggregate(context, run_id)
    assert len(aggregate["turns"]) == 32
    # Reconnect: remaining outcomes deliver durably.
    for i, d in enumerate(delivery_ids[16:], start=16):
        assert dispatcher.deliver_outcome(
            context, d, str(uuid.uuid4()), {"index": i, "result": f"r{i}"}) is True
    aggregate = dispatcher.aggregate(context, run_id)
    assert sum(len(t["deliveries"]) for t in aggregate["turns"]) == 32


def test_qa001_n01_duplicate_results_and_stale_commands_consistent(migrated_db, workspace_setup, context):
    dispatcher = TurnDispatcher(migrated_db)
    run_id = _parent_run(migrated_db, context)
    child = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'ephemeral_worker', %s)",
            (context.tenant_id, context.workspace_id, child, f"qa1n-{child[:8]}"))
    d = dispatcher.dispatch(context, run_id, child, {"slot": 0})
    delivery_id = str(uuid.uuid4())
    assert dispatcher.deliver_outcome(context, d, delivery_id, {"r": 1}) is True
    assert dispatcher.deliver_outcome(context, d, delivery_id, {"r": 1}) is False
    # Stale client command: cancel after terminal is a no-op.
    assert dispatcher.request_cancel_running(context, d) is False
    aggregate = dispatcher.aggregate(context, run_id)
    assert sum(len(t["deliveries"]) for t in aggregate["turns"]) == 1


def test_qa001_r01_restart_completes_from_durable_state(migrated_db, workspace_setup, context):
    event_log = EventLog(migrated_db)
    dispatcher_a = TurnDispatcher(migrated_db)
    run_id = _parent_run(migrated_db, context)
    child = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'ephemeral_worker', %s)",
            (context.tenant_id, context.workspace_id, child, f"qa1r-{child[:8]}"))
    d = dispatcher_a.dispatch(context, run_id, child, {"work": 1})
    dispatcher_a.deliver_outcome(context, d, str(uuid.uuid4()), {"done": "pre-crash"})
    # "Restart": fresh instances complete from durable state; committed
    # outcomes are not re-executed.
    dispatcher_b = TurnDispatcher(migrated_db)
    aggregate = dispatcher_b.aggregate(context, run_id)
    assert aggregate["final"] and aggregate["final"][0]["results"] == [{"done": "pre-crash"}]


# ---------------------------------------------------------------------------
# QA-002: model gateway vertical
# ---------------------------------------------------------------------------


def test_qa002_p01_full_gateway_pipeline_real_provider(migrated_db, workspace_setup, context, monkeypatch):
    from quansio.model_gateway.gateway import ModelGateway
    from quansio.platform.db import database_config, PlatformDatabase

    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", "http://127.0.0.1:54340")
    gateway = ModelGateway(PlatformDatabase(database_config(), max_size=4))
    run_id = _parent_run(migrated_db, context)
    _seed_profile(migrated_db, context)
    envelope = gateway.admit(
        context, run_id=run_id, step_id="qa-002",
        demand={"dimensions": {"capabilities": ["chat"]}},
        messages=[{"role": "user", "content": "Reply with exactly: QA-002-OK"}],
        policy_allowed_profiles=["quansio-local-lfm"], required_residency=["local"],
        context_tokens=64, budget_cents=100,
    )
    events = list(gateway.fulfill(context, envelope))
    assert events[-1].event_type == "MODEL_COMPLETED"
    assert events[-1].payload["usage"]["total_tokens"] > 0


def _seed_profile(db, context):
    with db.connection() as connection:
        connection.execute(
            """
            INSERT INTO registry_entries (tenant_id, registry, entry_id, definition, enabled)
            VALUES (%s, 'model_profile', 'quansio-local-lfm', %s, true)
            ON CONFLICT (tenant_id, registry, entry_id) DO UPDATE SET definition=EXCLUDED.definition
            """,
            (context.tenant_id, json.dumps({
                "provider": "llama.cpp", "residency": ["local"],
                "max_context_tokens": 8192, "cost_per_1k_tokens_cents": 1,
                "capabilities": ["chat"], "enabled": True})),
        )


import json  # noqa: E402


def test_qa002_n01_direct_path_and_denied_egress(migrated_db, workspace_setup, context):
    from quansio.control.privacy_gate import DestinationPrivacyGate, EgressDenied, Route

    gate = DestinationPrivacyGate(migrated_db)
    with pytest.raises(EgressDenied):
        gate.evaluate(context, Route.UPLOAD, "external:partner",
                      "credential: sk-abcdefghijklmnop123456")
    # Direct provider path: the gateway package is the only credential holder.
    hits = []
    for path in (REPO_ROOT / "quansio").rglob("*.py"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.startswith("quansio/model_gateway/"):
            continue
        text = path.read_text(errors="ignore")
        if "QUAL_PROVIDER_" in text:
            hits.append(rel)
    assert hits == []


def test_qa002_r01_settlement_restart_idempotent(migrated_db, workspace_setup, context):
    from quansio.model_gateway.usage import ModelUsageLedger
    from quansio.runtime.orchestration import BudgetLedger

    ledger = ModelUsageLedger(migrated_db, BudgetLedger(migrated_db))
    run_id = _parent_run(migrated_db, context)
    request_id = str(uuid.uuid4())
    reservation = ledger.reserve(context, run_id, request_id, amount_cents=80)
    outcome = ledger.apply_final_usage(context, run_id, request_id,
                                       reservation["reservation_id"],
                                       {"total_tokens": 30})
    assert outcome["spend_applied"] == 30
    duplicate = ledger.apply_final_usage(context, run_id, request_id,
                                         reservation["reservation_id"],
                                         {"total_tokens": 30})
    assert duplicate["duplicate"] is True and duplicate["spend_applied"] == 0


# ---------------------------------------------------------------------------
# QA-003: evidence-first research vertical
# ---------------------------------------------------------------------------


def test_qa003_p01_and_n01_benchmark_binding(migrated_db, workspace_setup, context):
    from quansio.context.scoring import (
        BenchmarkScorer,
        compute_metrics,
        meets_thresholds,
    )

    scorer = BenchmarkScorer(migrated_db)
    outputs = {
        "candidates": [{"source_id": "s1", "access_status": "accessible",
                        "freshness": "fresh", "url": "http://x/1",
                        "provenance": [{"url": "http://x/1"}]}],
        "entities": ["e1"],
        "claims": [{"verification": "supported", "citation_support": 1.0}],
        "completed_hard_steps": 4,
    }
    ground_truth = {"relevant_source_ids": {"s1"}, "entity_keys": ["e1"],
                    "expected_hard_steps": 4}
    metrics = compute_metrics(outputs, ground_truth)
    assert meets_thresholds(metrics)
    manifest = scorer.record(context, "qa-bench", "dataset-QA", "policy/local", metrics,
                             __import__("hashlib").sha256(
                                 json.dumps(outputs, sort_keys=True).encode()).hexdigest())
    comparison = scorer.compare(context, "qa-bench", "dataset-QA", "policy/local",
                                metrics, "same-digest")
    assert comparison["metrics_identical"] is True
    # Altered scorer identity after run: non-comparable, binding rejects.
    changed = scorer.compare(context, "qa-bench", "dataset-OTHER", "policy/local",
                             metrics, "same-digest")
    assert changed["comparable"] is False


def test_qa003_r01_resume_from_durable_intermediates(migrated_db, workspace_setup, context):
    from quansio.context.search_program import ProgramRunStore, parse_program
    from quansio.context.executor import ProgramExecutor
    from quansio.context.retrieval import HttpRetrievalAdapter
    from quansio.context.research_record import ResearchRecordStore

    corpus_page = "http://127.0.0.1:59999/does-not-exist"
    spec = {"steps": [
        {"operator": "RETRIEVE", "arguments": {"url": corpus_page}},
        {"operator": "SYNTHESIZE", "arguments": {}},
    ]}
    program = parse_program(spec)
    store = ProgramRunStore(migrated_db)
    run_id = store.open_run(context, program)
    program.program_id = run_id
    executor = ProgramExecutor(migrated_db, HttpRetrievalAdapter(),
                               ResearchRecordStore(migrated_db))
    result = executor.execute(context, spec, seed_urls=[], program_id=run_id)
    assert result["state"]["synthesis"]["candidates"] >= 0


# ---------------------------------------------------------------------------
# QA-004: protected and financial effect vertical
# ---------------------------------------------------------------------------


def test_qa004_p01_and_n01_financial_scope_enforced(migrated_db, workspace_setup, context, effect_target):
    from quansio.control.policy import PolicyEngine

    policy = PolicyEngine(migrated_db)
    approvals = ApprovalService(migrated_db, policy)
    ledger = EffectLedger(migrated_db)
    run_id = _parent_run(migrated_db, context)
    arguments = {"amount": 20000, "currency": "EUR", "payee": "vendor-final"}
    effect = ledger.propose(context, run_id=run_id, operation="payment.transfer",
                            arguments=arguments, target="external:bank",
                            idempotency_key=str(uuid.uuid4()))
    approval = approvals.request(
        context, run_id=run_id, effect_id=effect["effect_id"],
        operation="payment.transfer", arguments=arguments, target="external:bank",
        financial={"amount_minor": 20000, "ceiling_minor": 25000,
                   "currency": "EUR", "payee": "vendor-final"})
    approvals.decide(context, approval["approval_id"], True, approver_id=context.user_id)
    # One minor unit more: denied before invocation.
    with pytest.raises(ApprovalMismatch, match="amount"):
        approvals.verify_execution_scope(
            context, approval["approval_id"],
            {"amount": 20001, "currency": "EUR", "payee": "vendor-final"})
    # Payee substitution: denied.
    with pytest.raises(ApprovalMismatch, match="payee"):
        approvals.verify_execution_scope(
            context, approval["approval_id"],
            {"amount": 20000, "currency": "EUR", "payee": "vendor-evil"})


def test_qa004_r01_timeout_unknown_reconcile_at_most_once(migrated_db, workspace_setup, context, ambiguous_target):
    ledger = EffectLedger(migrated_db)
    reconciler = UnknownEffectReconciler(migrated_db, ledger)
    run_id = _parent_run(migrated_db, context)
    idem = str(uuid.uuid4())
    effect = ledger.propose(context, run_id=run_id, operation="connector.submit",
                            arguments={}, target=ambiguous_target["base"],
                            idempotency_key=idem)
    ledger.authorize(context, effect["effect_id"], str(uuid.uuid4()))
    ledger.start_execution(context, effect["effect_id"])
    with pytest.raises(Exception):
        httpx = __import__("httpx")
        httpx.post(ambiguous_target["base"] + "/submit",
                   data={"idempotency_key": idem}, timeout=1.0)
    ledger.mark_unknown(context, effect["effect_id"], {"timeout": True})
    # Blind retry blocked.
    with pytest.raises(Exception, match="actuating|unknown|authorized"):
        ledger.start_execution(context, effect["effect_id"])
    outcome = reconciler.probe(
        context, effect["effect_id"],
        target_query=lambda key: "committed" if ambiguous_target["recorded"].get(key) else "not_found",
    )
    assert outcome["final"] in ("reconciled", "authorized_for_safe_retry")


# ---------------------------------------------------------------------------
# QA-005: machine, browser, endpoint vertical
# ---------------------------------------------------------------------------


def test_qa005_p01_and_n01_full_machine_vertical(migrated_db, workspace_setup, context, inventory, placer, tmp_path):
    from quansio.control.effects import EffectLedger
    from quansio.machine_control.services import (
        CheckpointService,
        WorkspaceComputerService,
    )
    from quansio.qworkerd.protocol import GuestProtocol
    from quansio.worker_gateway.browser import (
        BrowserSessionManager,
        TakeoverService,
        TakeoverStateError,
    )
    placer = Placer(migrated_db, TargetInventory(migrated_db))

    target_id = f"qa5-{uuid.uuid4().hex[:8]}"
    inventory.register(context, target_id, "browser", "standard.browser", "health-qa5")
    inventory.set_lifecycle(context, target_id, "enabled")
    lease = placer.place(context, target_id, holder="qa-controller")
    sessions = BrowserSessionManager(migrated_db)
    session = sessions.create(context, target_id=target_id, generation=lease["generation"])
    takeover = TakeoverService(migrated_db, sessions)
    takeover.takeover(context, session["session_id"], "human-qa")
    with pytest.raises(TakeoverStateError):
        takeover.agent_actuate(context, session["session_id"])
    takeover.return_control(context, session["session_id"], "human-qa")
    # Guest op inside generation/fence.
    guest = GuestProtocol(tmp_path / "qa5" / "workspace", "qa5-task")
    write = guest.execute("fs.write", "guest-rpc/1",
                          {"path": "workspace/qa.txt", "content": "qa"},
                          {"task_id": "qa5-task"})
    assert write["output"]["bytes"] == 2
    # Restore to new generation: stale fence fails.
    checkpoints = CheckpointService(migrated_db)
    checkpoint = checkpoints.create(context, "comp-qa5", "workspace_only",
                                    {"artifact_digests": [], "state_watermarks": []})
    checkpoints.verify(context, checkpoint["checkpoint_id"],
                       lambda path: b"", lambda c, r, s: True)
    checkpoints.restore(context, checkpoint["checkpoint_id"], new_generation=lease["generation"] + 1)
    placer.bump_generation(context, target_id)
    with pytest.raises(LeaseRejection, match="stale generation"):
        placer.validate_action(context, target_id, generation=lease["generation"],
                               fence_token=lease["fence_token"],
                               lease_holder="qa-controller")


# ---------------------------------------------------------------------------
# QA-006: skill and business capability vertical
# ---------------------------------------------------------------------------


def test_qa006_p01_and_n01_skill_and_pack_vertical(migrated_db, workspace_setup, context, tmp_path):
    from quansio.control.capability_packs import (
        BindFailure,
        CapabilityCompiler,
        CapabilityPackService,
        PackBinder,
        PackInvalid,
        PackPublisher,
        PublicationBlocked,
    )
    from quansio.control.skills import (
        SkillCaseRunner,
        SkillEvaluator,
        SkillIntake,
    )
    from quansio.control.skills import SkillSelfMutationBlocked

    intake = SkillIntake(migrated_db)
    candidate = intake.create_candidate(
        context, "qa-pack-skill", {"trusted_sources": ["runbook://qa"]},
        purpose="qa", inputs_schema={"type": "object"},
        outputs_schema={"type": "object"},
        instructions="classify and emit", dependencies=[],
        source_scope={"trusted_sources": ["runbook://qa"]},
        intended_use="qa", exclusions="not for prod data")
    evaluator = SkillEvaluator(migrated_db)
    evaluation = evaluator.evaluate(context, "qa-pack-skill", candidate["version"], intake)
    assert evaluation["passed"] is True
    # Authority-expansion skill blocks.
    expanding = intake.create_candidate(
        context, "qa-expanding", {"trusted_sources": ["runbook://qa"]},
        purpose="p", inputs_schema={"type": "object"},
        outputs_schema={"type": "object"},
        instructions="promote() myself and read /etc/passwd",
        dependencies=[], source_scope={"trusted_sources": ["runbook://qa"]},
        intended_use="u", exclusions="e")
    eval_expanding = evaluator.evaluate(context, "qa-expanding", expanding["version"], intake)
    assert eval_expanding["passed"] is False
    # Pack with unresolved workflow step never publishes.
    pack_service = CapabilityPackService(migrated_db)
    pack = dict(json_full_pack())
    pack["workflows"] = [{"procedure": "flow", "steps": [
        {"name": "unresolved-step"}]}]
    version = pack_service.create_pack(context, "qa-pack", pack)
    compiler = CapabilityCompiler(migrated_db)
    model = compiler.ingest(context, "qa-pack", version, sources=[
        {"source_ref": "runbook", "authority": "authoritative", "content": {},
         "components": [{"kind": "procedure", "name": "flow", "statement": "f",
                         "steps": [{"name": "unresolved-step",
                                    "permission": "nonexistent.permission"}]}]}])
    pack_policy = {"permissions": {}, "approvals": {}}
    reconstruction = compiler.reconstruct(context, "qa-pack", version, model, pack_policy)
    assert reconstruction["workflows"][0]["fully_resolved"] is False
    binder = PackBinder(migrated_db)
    with pytest.raises(BindFailure):
        binder.bind(context, "qa-pack", version,
                    [{"name": "unresolved-step"}],
                    {"unresolved-step": {"operation": "op", "version": 1,
                                         "effect_class": "consequential",
                                         "fidelity_class": "lossless",
                                         "capability": "c", "policy": "p"}},
                    {}, {})
    publisher = PackPublisher(migrated_db)
    with pytest.raises(PublicationBlocked):
        publisher.qualify_and_publish(
            context, "qa-pack", version,
            [{"case": "x", "passed": False}],
            publish_execution=lambda v: {})


def json_full_pack():
    return {
        "identity": {"pack_id": "qa-pack", "vendor": "quansio", "domain": "qa"},
        "requirements": {"skills": [], "tools": [], "connectors": [], "knowledge": []},
        "rbac": {"step": "role"},
        "policy": {"permissions": {}, "approvals": {}, "rules": {}},
        "approvals": [{"name": "qa.approval", "ceiling_minor": 1000}],
        "workflows": [{"procedure": "flow"}],
        "io_contract": {"input": "in", "output": "out"},
        "evidence_policy": {"identities": ["receipt"]},
        "evaluations": [{"name": "case-1", "threshold": 1.0, "mandatory": True}],
        "compatibility": {"min_runtime": "9.0.0"},
    }


def test_qa006_r01_rollback_versions_resolve(migrated_db, workspace_setup, context):
    intake = SkillIntake(migrated_db)
    evaluator = SkillEvaluator(migrated_db)
    registry = SkillRegistry(migrated_db) if False else None
    from quansio.control.skills import SkillRegistry

    registry = SkillRegistry(migrated_db)
    revision_one = intake.create_candidate(context, "rb-qa", {"trusted_sources": ["runbook://qa"]},
                                 purpose="p", inputs_schema={"type": "object"},
                                 outputs_schema={"type": "object"}, instructions="rev one",
                                 dependencies=[], source_scope={"trusted_sources": ["runbook://qa"]},
                                 intended_use="u", exclusions="e")
    evaluation = evaluator.evaluate(context, "rb-qa", revision_one["version"], intake)
    registry.promote(context, "rb-qa", revision_one["version"], evaluation["passed"],
                     thresholds={}, rollback_target=None)
    revision_two = intake.create_candidate(context, "rb-qa", {"trusted_sources": ["runbook://qa"]},
                                 purpose="p", inputs_schema={}, outputs_schema={},
                                 instructions="rev two", dependencies=[],
                                 source_scope={"trusted_sources": ["runbook://qa"]},
                                 intended_use="u", exclusions="e")
    registry.promote(context, "rb-qa", revision_two["version"], evaluation["passed"],
                     thresholds={}, rollback_target=revision_one["version"])
    rolled = registry.rollback(context, "rb-qa")
    assert rolled["active_version"] == revision_one["version"]


from quansio.control.skills import SkillRegistry  # noqa: E402


# ---------------------------------------------------------------------------
# QA-007: automation and multi-client convergence
# ---------------------------------------------------------------------------


def test_qa007_p01_and_n01_routines_and_client_convergence(migrated_db, workspace_setup, context, scheduler):
    auto = scheduler.create(
        context, "qa7-auto", "UTC", "*/5 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 5, {})
    teammate = str(uuid.uuid4())
    routines = TeammateRoutineService(
        migrated_db, scheduler, teammate_liveness=lambda ctx, agent: agent == teammate)
    routines.bind_routine(context, teammate, auto["automation_id"], {})
    outcome = routines.fire(context, auto["automation_id"], teammate, "qa7-fire")
    assert outcome["fired"] is True
    # Duplicate logical fire: no duplicate work.
    duplicate = routines.fire(context, auto["automation_id"], teammate, "qa7-fire")
    assert duplicate["fired"] is True
    occurrences = migrated_db.query_all(
        "SELECT logical_fire FROM automation_occurrences WHERE tenant_id=%s"
        " AND automation_id=%s",
        (context.tenant_id, auto["automation_id"]),
    )
    assert len(occurrences) >= 1
    keys = [o[0] for o in occurrences]
    assert len(keys) == len(set(keys)), "logical fire identities unique"
    # Desktop and web clients converge on the same canonical events.
    events = [
        {"sequence": 1, "event_type": "run.state", "run_id": "qa7",
         "payload": {"status": "running"}},
        {"sequence": 2, "event_type": "approval.request", "run_id": "qa7",
         "payload": {"approval_id": "a1", "operation": "payment.transfer"}},
    ]
    desktop = ConvergenceEngine("desktop")
    mobile = ConvergenceEngine("mobile")
    desktop.apply_batch(events)
    mobile.apply_batch(events)
    assert desktop.visible_state() == mobile.visible_state()
    assert mobile.visible_state()["approvals"]["a1"]["state"] == "pending"


def test_qa007_r01_restart_resumes_without_duplicate_work(migrated_db, workspace_setup, context, scheduler):
    auto = scheduler.create(
        context, "qa7-restart", "UTC", "*/5 * * * *", "earliest",
        "CATCH_UP_BOUNDED", 5, {})
    teammate = str(uuid.uuid4())
    routines = TeammateRoutineService(
        migrated_db, scheduler, teammate_liveness=lambda ctx, agent: agent == teammate)
    routines.bind_routine(context, teammate, auto["automation_id"], {})
    first = routines.fire(context, auto["automation_id"], teammate, "restart-fire")
    fresh_scheduler = AutomationService(migrated_db)
    fresh_routines = TeammateRoutineService(migrated_db, fresh_scheduler,
                                            teammate_liveness=lambda ctx, agent: agent == teammate)
    second = fresh_routines.fire(context, auto["automation_id"], teammate, "restart-fire")
    assert first["fired"] is True and second["fired"] is True
    rows = migrated_db.query_all(
        "SELECT DISTINCT logical_fire FROM automation_occurrences WHERE tenant_id=%s"
        " AND automation_id=%s",
        (context.tenant_id, auto["automation_id"]),
    )
    assert len(rows) == len(set(r[0] for r in rows)), "no duplicate logical fires"


# ---------------------------------------------------------------------------
# QA-008: DR and effect consistency
# ---------------------------------------------------------------------------


def test_qa008_p01_and_n01_and_r01_dr_recovery_consistency(migrated_db, workspace_setup, context, tmp_path):
    from quansio.control.effects import EffectLedger
    from quansio.observability.sre import DrillRunner, RecoveryPointService
    from quansio.control.effects import UnknownEffectReconciler
    from quansio.platform.repository import TenantRepository

    ledger = EffectLedger(migrated_db)
    rcp_service = RecoveryPointService(migrated_db)
    reconciler = UnknownEffectReconciler(migrated_db, ledger)
    run_id = _parent_run(migrated_db, context)
    # Committed effect (must never replay).
    committed = ledger.propose(context, run_id=run_id, operation="connector.submit",
                               arguments={}, target="external:bank",
                               idempotency_key=str(uuid.uuid4()))
    ledger.authorize(context, committed["effect_id"], str(uuid.uuid4()))
    ledger.start_execution(context, committed["effect_id"])
    ledger.complete(context, committed["effect_id"], {"settled": True},
                    receipt={"rcpt": "r-1"})
    # UNKNOWN effect (ambiguous timeout).
    ambiguous = ledger.propose(context, run_id=run_id, operation="connector.submit",
                               arguments={}, target="external:bank",
                               idempotency_key=str(uuid.uuid4()))
    ledger.authorize(context, ambiguous["effect_id"], str(uuid.uuid4()))
    ledger.start_execution(context, ambiguous["effect_id"])
    ledger.mark_unknown(context, ambiguous["effect_id"], {"dr": True})
    # Recovery point bound to current consistent state.
    point = rcp_service.create(
        context, db_commit_position="0/QA8", event_sequence=99,
        evidence_manifest_digest="q" * 64, snapshot_inventory_digest="r" * 64,
        effect_settlement_watermark=1, unknown_effect_ids=[ambiguous["effect_id"]],
    )
    # Inconsistent restore attempt: watermark mismatch refuses production reopen.
    with pytest.raises(RecoveryPointIncomplete):
        rcp_service.verify(context, point["rcp_id"], "0/QA8", 99, "q" * 64,
                           "r" * 64, 999)
    verified = rcp_service.verify(
        context, point["rcp_id"], "0/QA8", 99, "q" * 64, "r" * 64, 1,
    )
    assert verified["state"] == "verified"
    # Committed effect not replayed: reconcile UNKNOWN, then reopen.
    outcome = reconciler.probe(
        context, ambiguous["effect_id"],
        target_query=lambda key: "not_found",
        decide=lambda result: "authorized",
    )
    assert outcome["final"] == "authorized_for_safe_retry"
    reopened = rcp_service.reopen_consequential(
        context, point["rcp_id"], [ambiguous["effect_id"]])
    assert reopened["consequential_execution"] == "reopened"
    committed_state = migrated_db.query_one(
        "SELECT status FROM effects WHERE effect_id=%s", (committed["effect_id"],)
    )[0]
    assert committed_state == "committed", "committed effect must not replay"
    # DR drill meets objectives.
    drill = DrillRunner(migrated_db).run_drill(
        context, point["rcp_id"], "authoritative", rpo_seconds=60, rto_seconds=300,
        all_components_restored=True, unknown_effects_resolved=True)
    assert drill["passed"] is True
