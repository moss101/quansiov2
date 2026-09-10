"""Acceptance tests for RUN-001, RUN-002, RUN-003.

WorkGraph persistence guarded by GraphTransaction, agent lifecycle with
distinct persistent/ephemeral semantics, and atomic multi-object
transitions with event identity — all against the real qualification
PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from quansio.control.capability import CapabilityService
from quansio.platform.context import IdentityContext
from quansio.platform.repository import TenantRepository
from quansio.runtime.agents import AgentLifecycleError, AgentRegistry
from quansio.runtime.events import EventLog
from quansio.runtime.graphs import GraphTransactionError, WorkGraphStore


@pytest.fixture()
def context(workspace_setup) -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup["workspace_a"],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@pytest.fixture()
def run_id(migrated_db, context) -> str:
    repository = TenantRepository(migrated_db)
    agent_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'ephemeral_worker', 'graph-worker')",
            (context.tenant_id, context.workspace_id, agent_id),
        )
    return repository.create_run(context, agent_id)


@pytest.fixture()
def store(migrated_db, migrated_events) -> WorkGraphStore:
    return WorkGraphStore(migrated_db, migrated_events)


@pytest.fixture(scope="module")
def migrated_events(migrated_db):
    # The canonical event log currently lives in the platform database
    # (migration 0003); quansio_events is reserved for the transport split.
    return EventLog(migrated_db)


@pytest.fixture()
def events(migrated_events) -> EventLog:
    return migrated_events


def _two_node_graph(store, context, run_id) -> str:
    graph = store.create_graph(
        context,
        run_id=run_id,
        spec={"objective": "qualify graph persistence"},
        nodes=[
            {"node_id": "research", "kind": "task", "payload": {"tool": "search"}},
            {"node_id": "report", "kind": "task", "payload": {"format": "md"}},
        ],
        edges=[{"from": "research", "to": "report"}],
        deadlines={"report": "2026-12-01T00:00:00Z"},
    )
    return graph["graph_id"]


def test_run001_p01_create_version_and_resume_graph(store, context, run_id):
    graph_id = _two_node_graph(store, context, run_id)
    graph = store.get_graph(context, graph_id)
    assert graph["revision"] == 1
    assert {n["node_id"]: n["status"] for n in graph["nodes"]} == {"research": "pending", "report": "pending"}
    assert graph["spec"]["edges"] == [{"from": "research", "to": "report"}]

    # Mutate only through a GraphTransaction: version bumps, state persists.
    outcome = (
        store.transaction(context, graph_id)
        .update_node("research", expected_status="pending", new_status="succeeded", payload_merge={"summary": "done"})
        .commit("graph.research.succeeded")
    )
    assert outcome["applied"] is True and outcome["revision"] == 2
    resumed = store.get_graph(context, graph_id)
    assert resumed["revision"] == 2
    node = next(n for n in resumed["nodes"] if n["node_id"] == "research")
    assert node["status"] == "succeeded" and node["payload"]["summary"] == "done"


def test_run001_n01_direct_node_update_outside_transaction_is_rejected(store, context, run_id, migrated_db):
    graph_id = _two_node_graph(store, context, run_id)
    with pytest.raises(psycopg.errors.RaiseException, match="GraphTransaction"):
        with migrated_db.connection() as connection:
            connection.execute(
                """
                UPDATE graph_nodes SET status = 'succeeded'
                WHERE tenant_id = %s AND graph_id = %s AND node_id = 'research'
                """,
                (context.tenant_id, graph_id),
            )
    graph = store.get_graph(context, graph_id)
    assert {n["status"] for n in graph["nodes"]} == {"pending"}


def test_run001_r01_replay_resumes_from_last_committed_transition(store, context, run_id, events):
    graph_id = _two_node_graph(store, context, run_id)
    first = (
        store.transaction(context, graph_id)
        .update_node("research", "pending", "succeeded")
        .commit("graph.research.succeeded")
    )
    replayed = [e for e in events.replay(context.tenant_id, graph_id, after_sequence=0)]
    assert [e.event_type for e in replayed] == ["graph.research.succeeded"]
    # A crash mid-transition leaves the first commit intact; the retry with a
    # NEW transition id applies only the remaining work.
    crashed = store.transaction(context, graph_id)
    crashed.update_node("report", "pending", "running")
    with pytest.raises(GraphTransactionError):
        crashed.update_node("research", "pending", "running").commit("graph.report.running")
    graph = store.get_graph(context, graph_id)
    assert next(n for n in graph["nodes"] if n["node_id"] == "research")["status"] == "succeeded"
    retried = (
        store.transaction(context, graph_id)
        .update_node("report", "pending", "running")
        .commit("graph.report.running")
    )
    assert retried["applied"] is True
    assert retried["transition_id"] != first["transition_id"]
    events_after = [e.event_type for e in events.replay(context.tenant_id, graph_id)]
    assert "graph.report.running" in events_after
    graph = store.get_graph(context, graph_id)
    by_id = {n["node_id"]: n for n in graph["nodes"]}
    assert by_id["research"]["status"] == "succeeded" and by_id["report"]["status"] == "running"


def test_run003_p01_multi_object_transition_is_atomic_and_emits_one_event(store, context, run_id, events):
    graph_id = _two_node_graph(store, context, run_id)
    outcome = (
        store.transaction(context, graph_id)
        .update_node("research", "pending", "succeeded")
        .update_node("report", "pending", "running")
        .commit("graph.advance", {"stage": 2})
    )
    assert outcome["applied"] is True
    graph_events = events.replay(context.tenant_id, graph_id)
    assert len(graph_events) == 1, "one event per committed transition"
    assert graph_events[0].payload["updates"] == [
        {"node_id": "research", "from": "pending", "to": "succeeded"},
        {"node_id": "report", "from": "pending", "to": "running"},
    ]


def test_run003_n01_precondition_failure_commits_nothing(store, context, run_id, events):
    graph_id = _two_node_graph(store, context, run_id)
    with pytest.raises(GraphTransactionError, match="precondition failed"):
        (
            store.transaction(context, graph_id)
            .update_node("research", "pending", "succeeded")
            .update_node("report", "running", "succeeded")  # wrong expectation
            .commit("graph.advance")
        )
    graph = store.get_graph(context, graph_id)
    assert all(n["status"] == "pending" for n in graph["nodes"]), "no partial mutation may remain"
    assert graph["revision"] == 1, "revision must not move on failed transition"
    assert events.replay(context.tenant_id, graph_id) == [], "no event may exist for a failed transition"


def test_run003_r01_transaction_identity_prevents_second_mutation(store, context, run_id, events):
    graph_id = _two_node_graph(store, context, run_id)
    transition_id = str(uuid.uuid4())
    first = (
        store.transaction(context, graph_id, transition_id=transition_id)
        .update_node("research", "pending", "succeeded")
        .commit("graph.research.succeeded")
    )
    assert first["applied"] is True
    # Crash after commit before projection delivery: recovery replays the
    # same transition identity — it must be a no-op.
    replay = (
        store.transaction(context, graph_id, transition_id=transition_id)
        .update_node("research", "pending", "succeeded")
        .commit("graph.research.succeeded")
    )
    assert replay["applied"] is False and replay["reason"] == "already applied"
    graph = store.get_graph(context, graph_id)
    assert graph["revision"] == 2, "revision may not advance twice"
    assert len(events.replay(context.tenant_id, graph_id)) == 1, "no duplicate event"


# ---------------------------------------------------------------------------
# RUN-002: agent lifecycle
# ---------------------------------------------------------------------------


def test_run002_p01_teammate_and_worker_have_distinct_lifecycles(migrated_db, workspace_setup):
    control = CapabilityService(migrated_db)
    registry = AgentRegistry(migrated_db, control)
    context = _ctx(workspace_setup)
    snapshot = control.admit_root(
        context,
        principal_id=workspace_setup["member"],
        capabilities=["fs.read"],
        constraints={"targets": {"/tmp/**": ["read"]}},
        budget_cents=100,
    )
    teammate = registry.create_persistent_teammate(context, "researcher", snapshot["snapshot_id"])
    worker = registry.create_ephemeral_worker(
        context, parent_agent_id=teammate, display_name="worker-1",
        snapshot_id=snapshot["snapshot_id"], ttl_seconds=60,
    )
    teammate_row = registry.get_agent(context, teammate)
    worker_row = registry.get_agent(context, worker["agent_id"])
    assert teammate_row["kind"] == "persistent_teammate" and teammate_row["parent_agent_id"] is None
    assert worker_row["kind"] == "ephemeral_worker"
    assert worker_row["parent_agent_id"] == teammate
    assert datetime.fromisoformat(worker["admission_expires_at"]) > datetime.now(timezone.utc)
    assert worker["snapshot_id"] == snapshot["snapshot_id"]


def _ctx(workspace_setup) -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup["workspace_a"],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def test_run002_n01_expired_worker_identity_cannot_become_teammate(migrated_db, workspace_setup):
    control = CapabilityService(migrated_db)
    registry = AgentRegistry(migrated_db, control)
    context = _ctx(workspace_setup)
    snapshot = control.admit_root(
        context, principal_id=workspace_setup["member"],
        capabilities=["fs.read"], constraints={"targets": {"/tmp/**": ["read"]}}, budget_cents=100,
    )
    worker = registry.create_ephemeral_worker(
        context, parent_agent_id=_make_teammate(registry, context, snapshot["snapshot_id"]),
        display_name="short-lived", snapshot_id=snapshot["snapshot_id"], ttl_seconds=1,
    )
    import time

    time.sleep(1.2)
    with pytest.raises(AgentLifecycleError, match="cannot be reused as a persistent teammate"):
        registry.create_persistent_teammate(
            context, display_name="impersonated", snapshot_id=snapshot["snapshot_id"],
            agent_id=worker["agent_id"],
        )


def _make_teammate(registry, context, snapshot_id) -> str:
    return registry.create_persistent_teammate(context, "parent", snapshot_id)


def test_run002_r01_restart_preserves_teammate_and_cleans_expired_worker(migrated_db, workspace_setup):
    control = CapabilityService(migrated_db)
    registry = AgentRegistry(migrated_db, control)
    context = _ctx(workspace_setup)
    snapshot = control.admit_root(
        context, principal_id=workspace_setup["member"],
        capabilities=["fs.read"], constraints={"targets": {"/tmp/**": ["read"]}}, budget_cents=100,
    )
    teammate = registry.create_persistent_teammate(context, "durable teammate", snapshot["snapshot_id"])
    worker = registry.create_ephemeral_worker(
        context, parent_agent_id=teammate, display_name="expired worker",
        snapshot_id=snapshot["snapshot_id"], ttl_seconds=1,
    )
    import time

    time.sleep(1.2)
    # "Restart": a brand-new registry instance performs cleanup.
    fresh_registry = AgentRegistry(migrated_db, control)
    cleaned = fresh_registry.cleanup_expired_ephemeral(context)
    assert cleaned >= 1
    teammate_after = fresh_registry.get_agent(context, teammate)
    assert teammate_after["retired_at"] is None, "persistent teammate must survive restart"
    assert teammate_after["workspace_id"] == workspace_setup["workspace_a"]
    worker_after = fresh_registry.get_agent(context, worker["agent_id"])
    assert worker_after["retired_at"] is not None, "expired ephemeral worker must be retired"
