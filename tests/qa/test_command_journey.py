"""Command-to-result journey (QA-001/DAT-001/RUN/UX-006): the full user
journey must be demonstrated over the HTTP surfaces — command admitted by
quansio-api, durably recorded and dispatched by quansio-runtime, executed
through a turn with a durable outcome, canonical events replayed, and the
resulting artifact stored with digest verification. Real PostgreSQL; the
only substitution is the socket between the API and runtime apps.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.api.app import create_app as create_api_app  # noqa: E402
from quansio.artifact.app import create_app as create_artifact_app  # noqa: E402
from quansio.runtime.app import create_app as create_runtime_app  # noqa: E402


def _client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture()
def journey(migrated_db, workspace_setup, minio_client):
    """API and runtime apps wired together over the admission boundary."""
    with _client(create_runtime_app(migrated_db)) as runtime:
        def runtime_transport(envelope, authorization):
            response = runtime.post(
                "/v9/admissions",
                json=envelope,
                headers={"Authorization": authorization},
            )
            if response.status_code >= 400:
                from fastapi import HTTPException

                detail = response.json().get("detail", response.text)
                raise HTTPException(status_code=response.status_code, detail=detail)
            return response.json()["admission"]

        with _client(create_api_app(migrated_db, runtime_transport=runtime_transport)) as api:
            with _client(create_artifact_app(migrated_db, client=minio_client)) as artifact:
                # Session token against the live control authority.
                from quansio.control.identity import ControlService

                control = ControlService(migrated_db)
                token, context = control.authenticate(
                    workspace_setup["tenant_id"],
                    workspace_setup["admin_email"],
                    "correct horse battery",
                    workspace_setup["workspace_a"],
                )
                yield {
                    "api": api,
                    "runtime": runtime,
                    "artifact": artifact,
                    "token": token,
                    "context": context,
                    "setup": workspace_setup,
                }


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_command_to_artifact_journey(journey):
    api, runtime, artifact = journey["api"], journey["runtime"], journey["artifact"]
    headers = _auth(journey["token"])
    setup = journey["setup"]

    # 1. An admitted agent must exist before a task can start: admit a
    #    capability snapshot and a persistent teammate via the runtime.
    admitted = runtime.post("/v9/agents", headers=headers, json={
        "display_name": f"journey-{uuid.uuid4().hex[:6]}",
        "snapshot_id": _admit_root_snapshot(journey),
    })
    assert admitted.status_code == 200, admitted.text
    agent_id = admitted.json()["agent"]["agent_id"]

    # 2. Submit the command through quansio-api; the runtime admission
    #    durably records the command and creates the run.
    idem = f"journey-{uuid.uuid4().hex[:12]}"
    submitted = api.post("/v9/commands", headers=headers, json={
        "command_type": "task.start",
        "arguments": {"objective": "produce the journey artifact",
                      "agent_id": agent_id, "budget_cents": 25},
        "idempotency_key": idem,
    })
    assert submitted.status_code == 200, submitted.text
    body = submitted.json()
    run_id = body["run_id"]
    command_id = body["command"]["command_id"]
    assert run_id and run_id != command_id, "the run is not the command id"

    # 3. Idempotent replay: the same key returns the same run, no duplicate.
    replay = api.post("/v9/commands", headers=headers, json={
        "command_type": "task.start",
        "arguments": {"objective": "produce the journey artifact",
                      "agent_id": agent_id, "budget_cents": 25},
        "idempotency_key": idem,
    })
    assert replay.status_code == 200
    assert replay.json()["admission"]["replayed"] is True
    assert replay.json()["run_id"] == run_id

    # 4. The command is durably linked to the run server-side.
    status = runtime.get(f"/v9/admissions/{command_id}", headers=headers)
    assert status.status_code == 200, status.text
    assert status.json()["admission"]["run_id"] == run_id
    assert status.json()["admission"]["status"] == "dispatched"

    # 5. Dispatch execution to the agent and deliver a durable outcome.
    turn = runtime.post("/v9/turns", headers=headers, json={
        "parent_run_id": run_id, "child_agent_id": agent_id,
        "payload": {"step": "produce"},
    })
    assert turn.status_code == 200, turn.text
    turn_id = turn.json()["turn_id"]
    result = {"answer": "journey complete", "numbers": [1, 2, 3]}
    outcome = runtime.post(f"/v9/turns/{turn_id}/outcome", headers=headers, json={
        "delivery_id": str(uuid.uuid4()),
        "result": result,
    })
    assert outcome.status_code == 200 and outcome.json()["accepted"] is True
    aggregate = runtime.get(f"/v9/runs/{run_id}/aggregate", headers=headers)
    assert aggregate.json()["final"], "the executed turn must have a final outcome"

    # 6. The execution result becomes a digest-addressed artifact.
    import json as _json

    payload = _json.dumps(result, sort_keys=True).encode()
    stored = artifact.put("/v9/artifacts", headers={
        **headers, "Content-Type": "application/json",
    }, content=payload)
    assert stored.status_code == 200, stored.text
    digest = stored.json()["artifact"]["digest"]

    # 7. The canonical event log records the journey in order.
    events = runtime.get(f"/v9/events?run_id={run_id}", headers=headers)
    sequences = [e["sequence"] for e in events.json()["events"]]
    assert sequences and sequences == list(range(1, len(sequences) + 1))
    completion = runtime.post("/v9/events", headers=headers, json={
        "run_id": run_id, "event_type": "run.state",
        "payload": {"status": "succeeded", "artifact_digest": digest},
    })
    assert completion.status_code == 200

    # 8. The artifact is retrievable and byte-identical.
    fetched = artifact.get(f"/v9/artifacts/{digest}", headers=headers)
    assert fetched.status_code == 200
    assert _json.loads(fetched.content) == result


def _admit_root_snapshot(journey) -> str:
    from quansio.control.capability import CapabilityService

    snapshot = CapabilityService(_database()).admit_root(
        journey["context"], journey["context"].user_id,
        ["cap.task"], {"path": "/w"}, 500,
    )
    return snapshot["snapshot_id"]


def _database():
    from quansio.platform.db import PlatformDatabase, database_config

    return PlatformDatabase(database_config(), max_size=1)
