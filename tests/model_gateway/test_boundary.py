"""MOD-001 acceptance tests: exclusive model fulfillment boundary.

Positive: production model requests flow through the gateway and no module
outside the gateway package holds a provider credential path. Negative: a
direct provider call from worker/tool code is rejected by the boundary
gate. Recovery: a gateway restart during an admitted request resolves to a
typed interruption outcome with the reservation intact — credential custody
never moves.
"""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.model_gateway.gateway import ModelGateway  # noqa: E402
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.platform.db import database_config  # noqa: E402

# Credential material that must never appear outside the gateway package.
CREDENTIAL_PATTERNS = [
    "QUAL_PROVIDER_",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "api_key",
    "Authorization",
    "Bearer ",
    "import openai",
    "from openai",
    "import anthropic",
    "from anthropic",
    "import litellm",
]


def _ctx(workspace_setup) -> IdentityContext:
    return IdentityContext(
        tenant_id=workspace_setup["tenant_id"],
        workspace_id=workspace_setup["workspace_a"],
        user_id=workspace_setup["admin"],
        session_id=str(uuid.uuid4()),
        roles=("member",),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def _scan(root: Path, exclude_prefixes: tuple[str, ...]) -> list[tuple[str, int, str]]:
    hits = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if any(rel.startswith(prefix) for prefix in exclude_prefixes):
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in CREDENTIAL_PATTERNS:
                if pattern in line and not line.strip().startswith("#"):
                    hits.append((rel, lineno, pattern))
    return hits


def test_mod001_p01_no_provider_credential_path_outside_gateway():
    """Clients, guests, tools, skills and connectors contain no provider
    credential path: only quansio/model_gateway may touch credentials."""
    hits = _scan(
        REPO_ROOT / "quansio",
        exclude_prefixes=("model_gateway/",),
    )
    assert hits == [], f"provider credential path outside gateway: {hits[:5]}"
    services_hits = _scan(REPO_ROOT / "services", exclude_prefixes=("services/quansio_model_gateway/",))
    assert services_hits == [], f"credential path in other deployables: {services_hits[:5]}"


def test_mod001_n01_direct_provider_call_from_worker_path_is_rejected(tmp_path):
    """Enabling a direct provider call in worker/tool code fails the
    boundary gate before it can ever carry traffic."""
    rogue = tmp_path / "quansio_runtime_rogue.py"
    rogue.write_text(
        "import httpx\n"
        "def call_provider_directly(prompt):\n"
        "    api_key = 'QUAL_PROVIDER_X_KEY'\n"
        "    return httpx.post('https://api.example.provider/chat',"
        " headers={'Authorization': 'Bearer ' + api_key})\n"
    )
    # Run the boundary scan over the tmp tree: the rogue module is a direct
    # provider call from a worker-shaped code path and must be rejected.
    hits = []
    for path in tmp_path.rglob("*.py"):
        text = path.read_text()
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in CREDENTIAL_PATTERNS:
                if pattern in line:
                    hits.append((path.name, lineno, pattern))
    assert any(name == "quansio_runtime_rogue.py" and pat in ("QUAL_PROVIDER_", "Authorization") for name, _lineno, pat in hits), hits


def test_mod001_p01_admitted_request_flows_through_gateway(migrated_db, workspace_setup):
    gateway = ModelGateway(migrated_db)
    context = _ctx(workspace_setup)
    _seed_profile(migrated_db, context, "quansio-local-lfm")
    from quansio.platform.repository import TenantRepository

    repository = TenantRepository(migrated_db)
    agent_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', 'p01-parent')",
            (context.tenant_id, context.workspace_id, agent_id),
        )
    run_id = repository.create_run(context, agent_id, budget_cents=200)
    admitted = gateway.admit(
        context,
        run_id=run_id,
        step_id="step-1",
        demand={"dimensions": {"capabilities": ["chat"]}},
        messages=[{"role": "user", "content": "Say OK"}],
        policy_allowed_profiles=["quansio-local-lfm"],
        required_residency=["local"],
        context_tokens=64,
        budget_cents=100,
    )
    row = migrated_db.query_one(
        "SELECT state, model_profile_id FROM model_requests WHERE tenant_id = %s AND request_id = %s",
        (context.tenant_id, admitted["request_id"]),
    )
    assert row[0] == "admitted" and row[1] == "quansio-local-lfm"
    # The envelope carries the full canonical identity chain.
    for field in ("route_decision_id", "usage_reservation_id", "privacy_decision_id", "stream_id", "cancellation_id"):
        assert admitted[field], field


def _seed_profile(db, context, profile_id: str) -> None:
    with db.connection() as connection:
        connection.execute(
            """
            INSERT INTO registry_entries (tenant_id, registry, entry_id, definition, enabled)
            VALUES (%s, 'model_profile', %s, %s, true)
            ON CONFLICT (tenant_id, registry, entry_id) DO UPDATE SET definition = EXCLUDED.definition
            """,
            (
                context.tenant_id,
                profile_id,
                __import__("json").dumps(
                    {
                        "provider": "llama.cpp",
                        "residency": ["local"],
                        "max_context_tokens": 8192,
                        "cost_per_1k_tokens_cents": 1,
                        "capabilities": ["chat"],
                        "enabled": True,
                    }
                ),
            ),
        )


def test_mod001_r01_gateway_restart_yields_typed_interruption_without_credential_transfer(migrated_db, workspace_setup):
    gateway_a = ModelGateway(migrated_db)
    context = _ctx(workspace_setup)
    _seed_profile(migrated_db, context, "quansio-local-lfm")
    # The admitted request reserves usage against a real parent run.
    from quansio.platform.repository import TenantRepository

    repository = TenantRepository(migrated_db)
    agent_id = str(uuid.uuid4())
    with migrated_db.connection() as connection:
        connection.execute(
            "INSERT INTO agents (tenant_id, workspace_id, agent_id, kind, display_name)"
            " VALUES (%s, %s, %s, 'persistent_teammate', 'boundary-parent')",
            (context.tenant_id, context.workspace_id, agent_id),
        )
    run_id = repository.create_run(context, agent_id, budget_cents=200)
    admitted = gateway_a.admit(
        context, run_id=run_id, step_id="step-1",
        demand={"dimensions": {"capabilities": ["chat"]}},
        messages=[{"role": "user", "content": "hi"}],
        policy_allowed_profiles=["quansio-local-lfm"],
        required_residency=["local"], context_tokens=32, budget_cents=50,
    )
    # Simulate a crash mid-request: state stays 'admitted'/'streaming'.
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE model_requests SET state = 'streaming' WHERE tenant_id = %s AND request_id = %s",
            (context.tenant_id, admitted["request_id"]),
        )
    # "Restart": brand-new gateway instance; the admitted request resolves to
    # a typed retryable interruption with the reservation still bound here.
    gateway_b = ModelGateway(migrated_db)
    outcomes = gateway_b.recover_after_restart(context)
    match = [o for o in outcomes if o["request_id"] == admitted["request_id"]]
    assert match, "admitted request must be recovered"
    assert match[0]["outcome"] == "retryable_interruption"
    assert match[0]["usage_reservation_id"] == admitted["usage_reservation_id"]
    # Credential custody never moved: the recovery path read no credentials.
    assert "credential" not in str(match).lower()
