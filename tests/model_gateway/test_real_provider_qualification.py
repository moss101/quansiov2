"""MOD-008: qualification of the enabled model profile at the real boundary.

Executes real request, streaming, cancellation, usage extraction,
malformed-response handling and outage/failover against the real llama.cpp
provider serving a real model, binds the results (including real provider
usage evidence) to the exact adapter/config artifacts, and proves
evidence-integrity semantics: qualification run without the real boundary
or without provider response evidence cannot complete, and results remain
reproducible across gateway restarts.
"""

from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.model_gateway.adapters import (  # noqa: E402
    CanonicalRequest,
    ProviderCredentials,
    ProviderProtocolFailure,
    adapter_for,
)
from quansio.model_gateway.gateway import ModelGateway  # noqa: E402
from quansio.model_gateway.streaming import BoundedEventChannel  # noqa: E402
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.platform.repository import TenantRepository  # noqa: E402
from tests.model_gateway.conftest import PROVIDER_BASE  # noqa: E402

PROFILE = "quansio-local-lfm"


def _ctx(workspace_setup) -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup["workspace_a"],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def _seed_enabled_profile(db, context) -> dict:
    definition = {
        "provider": "llama.cpp",
        "residency": ["local"],
        "max_context_tokens": 8192,
        "cost_per_1k_tokens_cents": 1,
        "capabilities": ["chat"],
        "enabled": True,
        "endpoint": PROVIDER_BASE,
    }
    with db.connection() as connection:
        connection.execute(
            """
            INSERT INTO registry_entries (tenant_id, registry, entry_id, definition, enabled)
            VALUES (%s, 'model_profile', %s, %s, true)
            ON CONFLICT (tenant_id, registry, entry_id) DO UPDATE SET definition = EXCLUDED.definition
            """,
            (context.tenant_id, PROFILE, json.dumps(definition)),
        )
    return definition


def _parent_run(db, context) -> str:
    repository = TenantRepository(db)
    agent_id = str(uuid.uuid4())
    with db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', %s)",
            (context.tenant_id, context.workspace_id, agent_id, f"qual-{agent_id[:8]}"),
        )
    run_id = repository.create_run(context, agent_id, budget_cents=500)
    with db.connection() as connection:
        connection.execute("UPDATE runs SET status='running' WHERE tenant_id=%s AND run_id=%s",
                           (context.tenant_id, run_id))
    return run_id


@pytest.fixture()
def qual_env(migrated_db, workspace_setup, real_provider, monkeypatch):
    context = _ctx(workspace_setup)
    definition = _seed_enabled_profile(migrated_db, context)
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", PROVIDER_BASE)
    run_id = _parent_run(migrated_db, context)
    return {
        "context": context,
        "definition": definition,
        "run_id": run_id,
        "gateway": ModelGateway(migrated_db),
        "db": migrated_db,
    }


def _adapter() -> object:
    return adapter_for(ProviderCredentials(
        profile_id=PROFILE, base_url=PROVIDER_BASE, api_key=None, protocol="openai-chat"))


def test_mod008_p01_real_request_streaming_usage_and_evidence(qual_env, tmp_path):
    gateway = qual_env["gateway"]
    context = qual_env["context"]
    envelope = gateway.admit(
        context, run_id=qual_env["run_id"], step_id="qual-stream",
        demand={"dimensions": {"capabilities": ["chat"]}},
        messages=[{"role": "user", "content": "Name three rivers, one per line."}],
        policy_allowed_profiles=[PROFILE], required_residency=["local"],
        context_tokens=64, budget_cents=100,
    )
    events = list(gateway.fulfill(context, envelope))
    types = [e.event_type for e in events]
    assert types[0] == "MODEL_STARTED"
    assert types.count("MODEL_COMPLETED") == 1
    assert any(t == "OUTPUT_DELTA" for t in types)
    usage = events[-1].payload["usage"]
    assert usage["prompt_tokens"] > 0 and usage["completion_tokens"] > 0
    output_text = events[-1].payload["output_text"]
    assert len(output_text) > 3, "real model output required as provider response evidence"
    # Persist the qualification evidence bound to this run.
    evidence = {
        "request_id": envelope["request_id"],
        "profile": PROFILE,
        "endpoint": PROVIDER_BASE,
        "event_types": types,
        "usage": usage,
        "output_sha256": hashlib.sha256(output_text.encode()).hexdigest(),
        "output_text": output_text,
    }
    out = REPO_ROOT / "evidence/model_gateway/mod008-real-stream.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")


def test_mod008_p01_cancellation_mid_stream_settles(real_provider, monkeypatch):
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", PROVIDER_BASE)
    adapter = _adapter()
    request = CanonicalRequest(str(uuid.uuid4()), PROFILE,
                               [{"role": "user", "content": "Count from 1 to 200, one number per line."}],
                               {"max_tokens": 512}, "t")
    channel = BoundedEventChannel(maxsize=1)
    cancel_event = threading.Event()
    producer_stopped = threading.Event()

    def produce():
        try:
            for event in adapter.stream(request, cancel_event=cancel_event):
                if not channel.put(event, timeout=10):
                    return
        finally:
            producer_stopped.set()

    worker = threading.Thread(target=produce, daemon=True)
    worker.start()
    got = 0
    while got < 3:
        if channel.get(timeout=30) is not None:
            got += 1
    # Cancel during active real streaming: the provider request unwinds.
    cancel_event.set()
    channel.cancel()
    worker.join(timeout=60)
    assert producer_stopped.is_set(), "provider streaming must unwind after cancellation"


def test_mod008_p01_malformed_response_is_typed_protocol_failure(stub_provider_factory, monkeypatch):
    base = stub_provider_factory("malformed_json")
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_LOCAL_LFM_BASE_URL", base)
    adapter = adapter_for(ProviderCredentials(
        profile_id=PROFILE, base_url=base, api_key=None, protocol="openai-chat"))
    request = CanonicalRequest(str(uuid.uuid4()), PROFILE,
                               [{"role": "user", "content": "hi"}], {}, "t")
    with pytest.raises(ProviderProtocolFailure):
        list(adapter.stream(request))


def test_mod008_p01_outage_failover_completes_on_healthy_profile(qual_env, monkeypatch, stub_provider_factory):
    gateway = qual_env["gateway"]
    context = qual_env["context"]
    _seed_profiles = qual_env["definition"]
    # Register a second enabled profile whose endpoint is dead: outage.
    qual_env["db"].execute(
        """
        INSERT INTO registry_entries (tenant_id, registry, entry_id, definition, enabled)
        VALUES (%s, 'model_profile', 'quansio-outage', %s, true)
        """,
        (context.tenant_id, json.dumps({
            "provider": "llama.cpp", "residency": ["local"], "max_context_tokens": 8192,
            "cost_per_1k_tokens_cents": 0, "capabilities": ["chat"], "enabled": True,
            "endpoint": "http://127.0.0.1:59999",
        })),
    )
    monkeypatch.setenv("QUAL_PROVIDER_QUANSIO_OUTAGE_BASE_URL", "http://127.0.0.1:59999")
    envelope = gateway.admit(
        context, run_id=qual_env["run_id"], step_id="qual-failover",
        demand={"dimensions": {"capabilities": ["chat"]}},
        messages=[{"role": "user", "content": "Reply with exactly: FAILOVER-OK"}],
        policy_allowed_profiles=["quansio-outage", PROFILE],
        required_residency=["local"], context_tokens=64, budget_cents=100,
    )
    events = list(gateway.fulfill(context, envelope,
                                  policy_allowed_profiles=["quansio-outage", PROFILE]))
    assert events[-1].event_type == "MODEL_COMPLETED"
    assert "FAILOVER-OK" in events[-1].payload["output_text"]
    health = qual_env["db"].query_one(
        "SELECT state FROM provider_health WHERE tenant_id=%s AND profile_id='quansio-outage'",
        (context.tenant_id,),
    )
    assert health is not None and health[0] == "down"


def test_mod008_n01_qualification_without_real_boundary_cannot_complete(tmp_path):
    """Completion evidence with real_boundary=false for this boundary-required
    task must be rejected by the authority evidence validator."""
    import subprocess

    task = next(t for t in json.loads((REPO_ROOT / "registries/tasks.json").read_text())
                if t["task_id"] == "MOD-008")
    assert task["real_boundary_required"] is True
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "q@qual.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "q"], check=True)
    (repo / "artifact.bin").write_bytes(b"no-real-provider-response")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    report = {
        "schema_revision": "9.0.0", "report_id": "rep-fake", "task_id": "MOD-008",
        "repository_id": "repo-q", "git_commit": commit, "protected_ref": "HEAD",
        "environment_id": "env", "configuration_digest": "0" * 64, "status": "PASS",
        "assertion_results": [
            {"assertion_id": "MOD-008-P01", "blocking": True, "status": "PASS"},
            {"assertion_id": "MOD-008-N01", "blocking": True, "status": "PASS"},
            {"assertion_id": "MOD-008-R01", "blocking": True, "status": "PASS"},
            {"assertion_id": "MOD-007-A01", "blocking": True, "status": "PASS"},
        ],
        "artifact_records": [{"path_or_uri": "artifact.bin",
                              "digest": hashlib.sha256(b"no-real-provider-response").hexdigest(),
                              "verification_method": "LOCAL_HASH", "verification_receipt_ref": None}],
        "real_boundary": False,
        "executed_at": "2026-09-10T00:00:00Z",
    }
    (repo / "report.json").write_text(json.dumps(report))
    evidence = {
        "schema_revision": "9.0.0", "evidence_id": "ev-fake", "task_id": "MOD-008",
        "requirement_ids": ["MOD-007"], "task_assertion_ids": ["MOD-008-P01", "MOD-008-N01", "MOD-008-R01"],
        "requirement_assertion_ids": ["MOD-007-A01"], "repository_id": "repo-q",
        "git_commit": commit, "report_path": "report.json",
        "report_digest": hashlib.sha256((repo / "report.json").read_bytes()).hexdigest(),
        "status": "PASS", "real_boundary": False,
        "artifact_digests": {"artifact.bin": hashlib.sha256(b"no-real-provider-response").hexdigest()},
        "rollback_verified": True, "created_at": "2026-09-10T00:00:00Z",
    }
    (repo / "evidence.json").write_text(json.dumps(evidence))
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/validate_implementation_evidence.py"),
         "--repo", str(repo), "--evidence", str(repo / "evidence.json"), "--protected-ref", "HEAD"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "real boundary required but false" in result.stdout + result.stderr


def test_mod008_r01_restart_reproducibility_without_stale_charges(qual_env):
    gateway = qual_env["gateway"]
    context = qual_env["context"]
    first_envelope = gateway.admit(
        context, run_id=qual_env["run_id"], step_id="qual-restart",
        demand={"dimensions": {"capabilities": ["chat"]}},
        messages=[{"role": "user", "content": "Reply with exactly: RESTART-OK"}],
        policy_allowed_profiles=[PROFILE], required_residency=["local"],
        context_tokens=64, budget_cents=100,
    )
    first_events = list(gateway.fulfill(context, first_envelope))
    assert first_events[-1].event_type == "MODEL_COMPLETED"
    # Gateway restart: nothing is mid-flight, so nothing may resume as a charge.
    assert gateway.recover_after_restart(context) == []
    second_envelope = gateway.admit(
        context, run_id=qual_env["run_id"], step_id="qual-restart-2",
        demand={"dimensions": {"capabilities": ["chat"]}},
        messages=[{"role": "user", "content": "Reply with exactly: RESTART-OK"}],
        policy_allowed_profiles=[PROFILE], required_residency=["local"],
        context_tokens=64, budget_cents=100,
    )
    second_events = list(gateway.fulfill(context, second_envelope))
    assert second_events[-1].event_type == "MODEL_COMPLETED"
    # Distinct result identities per run; usage recorded twice, append-only.
    assert first_envelope["request_id"] != second_envelope["request_id"]
    assert first_events[-1].event_id != second_events[-1].event_id
    settlements = qual_env["db"].query_all(
        "SELECT request_id::text, kind FROM model_usage_settlements WHERE tenant_id = %s ORDER BY created_at",
        (context.tenant_id,),
    )
    requests = {r[0] for r in settlements}
    assert {first_envelope["request_id"], second_envelope["request_id"]} <= requests

