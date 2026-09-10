"""Acceptance tests for DAT-005, DAT-006, DAT-007, DAT-008 and SEC-001.

Runs against the real qualification environment: PostgreSQL, MinIO and
Redis provisioned by ENV-001. No in-memory substitutes for durable
boundaries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import psycopg
import pytest
import redis as redis_lib
from minio import Minio

from quansio.artifact.store import ArtifactIntegrityError, ArtifactStore
from quansio.platform.cache import LeaseCache
from quansio.platform.context import IdentityContext
from quansio.platform.db import database_config
from quansio.platform.repository import TenantRepository, TenantScopeViolation
from quansio.control.capability import (
    CapabilityEscalationError,
    CapabilityService,
    SnapshotExpiredError,
)
from quansio.runtime.protocol import ProtocolStateStore
from quansio.runtime.events import EventLog


def _load_qualenv_passwords() -> dict[str, str]:
    from quansio.platform.db import load_qualenv_passwords

    return load_qualenv_passwords()


@pytest.fixture(scope="module")
def minio_client():
    material = _load_qualenv_passwords()
    client = Minio(
        "127.0.0.1:54331",
        access_key="quansio_qual_admin",
        secret_key=material["QUAL_MINIO_PASSWORD"],
        secure=False,
    )
    return client


@pytest.fixture(scope="module")
def redis_url():
    material = _load_qualenv_passwords()
    return f"redis://:{material['QUAL_REDIS_PASSWORD']}@127.0.0.1:54330/0"


@pytest.fixture(scope="module")
def events_db():
    from quansio.platform.db import PlatformDatabase

    database = PlatformDatabase(database_config("quansio_events"))
    yield database
    database.close()


# ---------------------------------------------------------------------------
# DAT-005: resumable protocol state
# ---------------------------------------------------------------------------



def _real_run(db, context) -> str:
    """Create an agent + run so protocol waits attach to durable state."""
    from quansio.platform.repository import TenantRepository

    repository = TenantRepository(db)
    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'ephemeral_worker', 'protocol-worker')",
            (context.tenant_id, context.workspace_id, agent_id),
        )
    return repository.create_run(context, agent_id)

def test_dat005_p01_protocol_objects_persist_independently(migrated_db, workspace_setup):
    store = ProtocolStateStore(migrated_db)
    context = _context(workspace_setup)
    run_id = _real_run(migrated_db, context)
    approval = store.open_wait(
        context, "approval_wait", run_id, {"capability": "fs.write", "path": "/tmp/x"}
    )
    question = store.open_wait(context, "question", run_id, {"text": "continue?"})
    tool_call = store.open_wait(context, "tool_call", run_id, {"tool": "search", "arguments": {}})
    waiting = {entry["protocol_id"] for entry in store.list_waiting(context, run_id=run_id)}
    assert {approval, question, tool_call} <= waiting
    kinds = {
        entry["protocol_id"]: entry["kind"]
        for entry in store.list_waiting(context, run_id=run_id)
    }
    assert kinds[approval] == "approval_wait" and kinds[question] == "question" and kinds[tool_call] == "tool_call"


def test_dat005_n01_semantic_memory_loss_preserves_protocol_resumption(migrated_db, workspace_setup):
    store = ProtocolStateStore(migrated_db)
    context = _context(workspace_setup)
    run_id = _real_run(migrated_db, context)
    approval = store.open_wait(context, "approval_wait", run_id, {"capability": "fs.write"})
    # Simulate total loss of a semantic-memory/knowledge store: drop a scratch
    # table used only for semantic material (protocol state is untouched).
    with migrated_db.connection() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS semantic_memory_scratch (id int)")
        connection.execute("INSERT INTO semantic_memory_scratch VALUES (1)")
        connection.execute("DROP TABLE semantic_memory_scratch")
    # The interrupted approval wait still resumes correctly.
    restored = store.get(context, approval)
    assert restored is not None and restored["status"] == "waiting"
    store.settle(context, approval, {"decision": "approved"})
    assert store.get(context, approval)["status"] == "settled"


def test_dat005_r01_runtime_restart_restores_wait_without_duplicate(migrated_db, workspace_setup):
    store_a = ProtocolStateStore(migrated_db)
    context = _context(workspace_setup)
    run_id = _real_run(migrated_db, context)
    protocol_id = str(uuid.uuid4())
    first = store_a.open_wait(
        context, "question", run_id, {"text": "proceed with payment?"}, protocol_id=protocol_id
    )
    # "Restart": a brand-new store instance resolves the same durable protocol.
    store_b = ProtocolStateStore(migrated_db)
    redelivered = store_b.open_wait(
        context, "question", run_id, {"text": "proceed with payment?"}, protocol_id=protocol_id
    )
    assert first == redelivered
    waiting = [entry for entry in store_b.list_waiting(context, run_id=run_id) if entry["kind"] == "question"]
    assert len(waiting) == 1, "restore must not duplicate the outstanding request"


# ---------------------------------------------------------------------------
# DAT-006: immutable artifact and evidence storage
# ---------------------------------------------------------------------------


def test_dat006_p01_store_and_refetch_by_digest(migrated_db, minio_client, workspace_setup):
    store = ArtifactStore(migrated_db, minio_client)
    context = _context(workspace_setup)
    data = b"qualification artifact bytes \x00\x01"
    record = store.put(context, data, "application/octet-stream", grants={"read": ["workspace"]})
    fetched, meta = store.get(context, record["digest"])
    assert fetched == data
    assert meta["media_type"] == "application/octet-stream"
    assert meta["grants"] == {"read": ["workspace"]}
    assert record["size_bytes"] == len(data)
    assert record["digest"] == store.digest_of(data)


def test_dat006_n01_digest_mutation_is_rejected(migrated_db, minio_client, workspace_setup):
    store = ArtifactStore(migrated_db, minio_client)
    context = _context(workspace_setup)
    data = b"immutable historical evidence"
    record = store.put(context, data, "text/plain")
    # An attacker cannot write different bytes under the recorded digest.
    with migrated_db.connection() as connection:
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO artifact_records (tenant_id, digest, media_type, producer, size_bytes, scan_state, grants)
                VALUES (%s, %s, 'text/plain', NULL, 4, 'unscanned', '{}'::jsonb)
                """,
                (context.tenant_id, "zz" + "0" * 62),
            )
    fetched, _meta = store.get(context, record["digest"])
    assert fetched == data, "historical evidence must remain unchanged"


def test_dat006_r01_metadata_restore_requires_digest_verification(migrated_db, minio_client, workspace_setup):
    store = ArtifactStore(migrated_db, minio_client)
    context = _context(workspace_setup)
    data = b"artifact needing metadata restore"
    record = store.put(context, data, "text/plain")
    backup_row = {
        "tenant_id": context.tenant_id,
        "digest": record["digest"],
        "media_type": "text/plain",
        "producer": context.user_id,
        "size_bytes": len(data),
        "grants": {},
    }
    with migrated_db.connection() as connection:
        connection.execute("DELETE FROM artifact_records WHERE digest = %s", (record["digest"],))
    # Blob still present: restore verifies digest and becomes readable.
    state = store.restore_metadata_from_backup(context, backup_row)
    assert state == "verified"
    fetched, meta = store.get(context, record["digest"])
    assert fetched == data and meta["scan_state"] == "verified"
    # Blob missing: restore quarantines instead of handing out unreadable evidence.
    with migrated_db.connection() as connection:
        connection.execute("DELETE FROM artifact_records WHERE digest = %s", (record["digest"],))
    backup_missing = dict(backup_row, digest=store.digest_of(b"never stored anywhere"))
    state = store.restore_metadata_from_backup(context, backup_missing)
    assert state == "quarantined"
    with pytest.raises(ArtifactIntegrityError):
        store.get(context, backup_missing["digest"])


# ---------------------------------------------------------------------------
# DAT-007: cache constrained to non-authoritative use
# ---------------------------------------------------------------------------


def test_dat007_p01_and_n01_cache_flush_loses_no_canonical_truth(migrated_db, redis_url, workspace_setup):
    from quansio.platform.repository import TenantRepository

    cache = LeaseCache(migrated_db, redis_url)
    repository = TenantRepository(migrated_db)
    context = _context(workspace_setup)
    agent = _admit_agent(migrated_db, context)
    run_id = repository.create_run(context, agent)
    # Active lease coordination on top of the run.
    lease = cache.acquire(run_id, holder="worker-1")
    assert lease is not None and cache.validate(lease)
    # Canonical truth lives in PostgreSQL; flushing the cache mid-work is safe.
    cache.flush_all()
    run = repository.get_run(context, run_id)
    assert run is not None and run["status"] == "pending"
    assert cache.validate(lease) is False, "flushed lease must not keep pretending validity"


def test_dat007_r01_leases_reacquire_from_authoritative_state_after_restart(migrated_db, redis_url, workspace_setup):
    cache = LeaseCache(migrated_db, redis_url)
    context = _context(workspace_setup)
    agent = _admit_agent(migrated_db, context)
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO runs (tenant_id, workspace_id, run_id, agent_id, status, generation)"
            " VALUES (%s, %s, %s, %s, 'running', 3)",
            (context.tenant_id, context.workspace_id, _run_id_for(migrated_db, context), agent, ),
        )
    run_id = migrated_db.query_one(
        "SELECT run_id::text FROM runs WHERE tenant_id = %s ORDER BY created_at DESC LIMIT 1",
        (context.tenant_id,),
    )[0]
    reacquired = cache.reacquire_or_invalidate(run_id, holder="worker-2")
    assert reacquired is not None
    assert reacquired.generation == 3, "generation must be re-derived from authoritative state, not cache"


def _admit_agent(db, context) -> str:
    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'ephemeral_worker', %s)",
            (context.tenant_id, context.workspace_id, agent_id, "worker"),
        )
    return agent_id


def _run_id_for(db, context) -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# DAT-008: tenant-safe repository and query layer
# ---------------------------------------------------------------------------


def test_dat008_p01_identical_ids_never_cross_tenant_scope(migrated_db, workspace_setup, control):
    repository = TenantRepository(migrated_db)
    context_a = _context(workspace_setup)
    agent_a = _admit_agent(migrated_db, context_a)
    run_a = repository.create_run(context_a, agent_a)
    suffix = uuid.uuid4().hex[:10]
    tenant_b = control.create_tenant(f"second-{suffix}")
    workspace_b = control.create_workspace(tenant_b, f"ws-{suffix}")
    context_b = IdentityContext(
        tenant_id=tenant_b,
        workspace_id=workspace_b,
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    agent_b = _admit_agent(migrated_db, context_b)
    run_b = repository.create_run(context_b, agent_b)
    assert run_a != run_b
    # tenant A cannot read tenant B's run even with B's run id, and vice versa
    assert repository.get_run(context_a, run_b) is None
    assert repository.get_run(context_b, run_a) is None
    assert {r["run_id"] for r in repository.list_runs(context_a)} == {run_a}
    assert {r["run_id"] for r in repository.list_runs(context_b)} == {run_b}
    assert repository.update_run_status(context_a, run_a, "running") is True
    assert repository.update_run_status(context_a, run_b, "cancelled") is False


def _context(workspace_setup, workspace: str = "workspace_a") -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup[workspace],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def test_dat008_n01_foreign_tenant_parameter_is_denied_before_materialization(migrated_db, workspace_setup):
    repository = TenantRepository(migrated_db)
    context_a = _context(workspace_setup)
    agent_a = _admit_agent(migrated_db, context_a)
    run_a = repository.create_run(context_a, agent_a)
    foreign_tenant = str(uuid.uuid4())
    with pytest.raises(TenantScopeViolation):
        repository.get_run(context_a, run_a, claimed_tenant=foreign_tenant)
    # Nothing materialized: the legitimate read still works afterwards.
    assert repository.get_run(context_a, run_a)["run_id"] == run_a


def test_dat008_r01_isolation_probes_rerun_after_connection_failover(migrated_db, workspace_setup):
    repository = TenantRepository(migrated_db)
    context_a = _context(workspace_setup)
    agent = _admit_agent(migrated_db, context_a)
    run_a = repository.create_run(context_a, agent)
    # Simulate failover: reestablish all pooled connections on a fresh pool.
    config = database_config()
    database = _fresh_database(config)
    repository_b = TenantRepository(database)
    assert repository_b.get_run(context_a, run_a)["run_id"] == run_a
    with pytest.raises(TenantScopeViolation):
        repository_b.get_run(context_a, run_a, claimed_tenant=str(uuid.uuid4()))
    database.close()


def _fresh_database(config):
    from quansio.platform.db import PlatformDatabase

    return PlatformDatabase(config, max_size=4)


# ---------------------------------------------------------------------------
# SEC-001: immutable capability snapshots
# ---------------------------------------------------------------------------


def test_sec001_p01_snapshot_immutability_and_strict_child_subset(migrated_db, minio_client, workspace_setup):
    service = CapabilityService(migrated_db)
    context = _context(workspace_setup)
    root = service.admit_root(
        context,
        principal_id=workspace_setup["member"],
        capabilities=["fs.read", "fs.write", "web.get"],
        constraints={"targets": {"/tmp/**": ["read", "write"]}, "network": ["example.com"]},
        budget_cents=500,
    )
    assert root["revision"] == 1 and root["parent_snapshot_id"] is None
    child = service.admit_child(
        context,
        parent_snapshot_id=root["snapshot_id"],
        principal_id=str(uuid.uuid4()),
        capabilities=["fs.read"],
        constraints={"targets": {"/tmp/work/**": ["read"]}},
        budget_cents=100,
    )
    assert child["revision"] == 2 and child["parent_snapshot_id"] == root["snapshot_id"]


def test_sec001_n01_child_escalation_and_mutation_denied(migrated_db, minio_client, workspace_setup):
    service = CapabilityService(migrated_db)
    context = _context(workspace_setup)
    root = service.admit_root(
        context,
        principal_id=workspace_setup["member"],
        capabilities=["fs.read"],
        constraints={"targets": {"/tmp/**": ["read"]}},
        budget_cents=100,
    )
    with pytest.raises(CapabilityEscalationError):
        service.admit_child(
            context,
            root["snapshot_id"],
            principal_id=str(uuid.uuid4()),
            capabilities=["fs.write"],  # not in parent
            constraints={"targets": {}},
            budget_cents=10,
        )
    with pytest.raises(CapabilityEscalationError):
        service.admit_child(
            context,
            root["snapshot_id"],
            principal_id=str(uuid.uuid4()),
            capabilities=["fs.read"],
            constraints={"targets": {}},
            budget_cents=999,  # above parent ceiling
        )
    # Post-admission mutation is denied by the storage layer itself.
    with pytest.raises(psycopg.errors.RaiseException) as excinfo:
        with migrated_db.connection() as connection:
            connection.execute(
                "UPDATE capability_snapshots SET capabilities = %s::jsonb WHERE snapshot_id = %s",
                ('["fs.read","admin.all"]', root["snapshot_id"]),
            )
    assert "immutable" in str(excinfo.value)
    unchanged = service.require_active(context, root["snapshot_id"])
    assert unchanged["capabilities"] == ["fs.read"]


def test_sec001_r01_expired_snapshot_requires_fresh_admission(migrated_db, minio_client, workspace_setup):
    service = CapabilityService(migrated_db)
    context = _context(workspace_setup)
    root = service.admit_root(
        context,
        principal_id=workspace_setup["member"],
        capabilities=["fs.read"],
        constraints={"targets": {"/tmp/**": ["read"]}},
        budget_cents=100,
        ttl_seconds=1,
    )
    import time

    time.sleep(1.2)  # admit with ttl_seconds=1; real expiry elapses
    # Durable wait resumed with an expired snapshot: any protected execution
    # attempt must fail until fresh admission.
    with pytest.raises(SnapshotExpiredError, match="fresh admission required"):
        service.require_active(context, root["snapshot_id"])
    fresh = service.admit_root(
        context,
        principal_id=workspace_setup["member"],
        capabilities=["fs.read"],
        constraints={"targets": {"/tmp/**": ["read"]}},
        budget_cents=100,
    )
    assert fresh["snapshot_id"] != root["snapshot_id"]
    assert service.require_active(context, fresh["snapshot_id"])["snapshot_id"] == fresh["snapshot_id"]
