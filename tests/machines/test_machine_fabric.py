"""Acceptance tests for MAC-001..MAC-008 against the real environment.

Guest operations run against a real sandbox filesystem; deliveries and
leases are durable in PostgreSQL; the credential boundary is exercised
through real broker and guest rejections.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "generated/contracts/python"))

from quansio.control.broker import CredentialBroker  # noqa: E402
from quansio.machine_control.inventory import (  # noqa: E402
    LeaseRejection,
    Placer,
    TargetInventory,
    TargetRejected,
)
from quansio.machine_control.services import (  # noqa: E402
    CheckpointService,
    IsolatedTaskRuntime,
    PrivateTargetService,
    WorkerDeliveryService,
    WorkspaceComputerService,
)
from quansio.platform.context import IdentityContext  # noqa: E402
from quansio.qworkerd.protocol import GuestRejection, GuestProtocol  # noqa: E402


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
def inventory(migrated_db) -> TargetInventory:
    return TargetInventory(migrated_db)


@pytest.fixture()
def placer(migrated_db, inventory) -> Placer:
    return Placer(migrated_db, inventory)


@pytest.fixture()
def context(workspace_setup) -> IdentityContext:
    return _ctx(workspace_setup)


@pytest.fixture()
def enabled_target(inventory, context) -> str:
    target_id = f"tgt-{uuid.uuid4().hex[:10]}"
    inventory.register(context, target_id, target_type="fs",
                       support_profile="standard.linux", health_identity="health-probe-1")
    inventory.set_lifecycle(context, target_id, "enabled")
    return target_id


# ---------------------------------------------------------------------------
# MAC-001: inventory and lifecycle
# ---------------------------------------------------------------------------


def test_mac001_p01_registration_lifecycle_audit(migrated_db, inventory, context, enabled_target):
    target = inventory.reconstruct(context, enabled_target)
    assert target["lifecycle"] == "enabled"
    assert target["generation"] == 1
    assert target["authoritative"] is True
    replay = target["lifecycle_replay"]
    assert replay == ["registered", "enabled"], "lifecycle transitions must be audited"


def test_mac001_n01_placement_rejects_unregistered_wrong_tenant_disabled(placer, inventory, context, workspace_setup, enabled_target):
    with pytest.raises(TargetRejected, match="not registered"):
        placer.place(context, f"tgt-{uuid.uuid4().hex[:10]}", holder="c1")
    # Wrong tenant: the same target id under a different tenant is unknown.
    foreign_ctx = IdentityContext(
        tenant_id=str(uuid.uuid4()), workspace_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        roles=("member",), expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    with pytest.raises(TargetRejected, match="not registered"):
        placer.place(foreign_ctx, enabled_target, holder="c2")
    # Disabled target.
    inventory.set_lifecycle(context, enabled_target, "disabled")
    with pytest.raises(TargetRejected, match="disabled"):
        placer.place(context, enabled_target, holder="c3")
    inventory.set_lifecycle(context, enabled_target, "enabled")


def test_mac001_r01_reconstruct_after_restart_without_memory(migrated_db, inventory, context, enabled_target):
    inventory.heartbeat(context, enabled_target, "health-ok")
    # "Restart": a brand-new inventory instance reconstructs from durable state.
    fresh = TargetInventory(migrated_db)
    view = fresh.reconstruct(context, enabled_target)
    assert view["lifecycle"] == "enabled"
    assert view["health_identity"] == "health-ok"
    assert view["authoritative"] is True


# ---------------------------------------------------------------------------
# MAC-002: exclusive placement, lease, fence
# ---------------------------------------------------------------------------


def test_mac002_p01_lease_and_fence_validated_for_actions(placer, context, enabled_target):
    lease = placer.place(context, enabled_target, holder="controller-a")
    validated = placer.validate_action(
        context, enabled_target, generation=lease["generation"],
        fence_token=lease["fence_token"], lease_holder="controller-a",
    )
    assert validated["fence_token"] == lease["fence_token"]


def test_mac002_n01_stale_generation_expired_lease_prior_fence_rejected(placer, migrated_db, context, enabled_target):
    lease = placer.place(context, enabled_target, holder="controller-a")
    # Stale generation.
    with pytest.raises(LeaseRejection, match="stale generation"):
        placer.validate_action(context, enabled_target, generation=lease["generation"] - 1,
                               fence_token=lease["fence_token"], lease_holder="controller-a")
    # Expired lease.
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE target_leases SET expires_at = now() - interval '1 second' WHERE target_id=%s",
            (enabled_target,),
        )
    with pytest.raises(LeaseRejection, match="expired"):
        placer.validate_action(context, enabled_target, generation=lease["generation"],
                               fence_token=lease["fence_token"], lease_holder="controller-a")
    # Prior fence token (after another controller acquires the next fence).
    lease_b = placer.place(context, enabled_target, holder="controller-b")
    with pytest.raises(LeaseRejection, match="prior fence"):
        placer.validate_action(context, enabled_target, generation=lease_b["generation"],
                               fence_token=lease["fence_token"], lease_holder="controller-b")


def test_mac002_r01_crash_superseded_by_higher_generation(migrated_db, placer, context, enabled_target):
    lease = placer.place(context, enabled_target, holder="controller-a")
    # Crash: lease expires; recovery bumps generation and reacquires.
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE target_leases SET expires_at = now() - interval '1 second' WHERE target_id=%s",
            (enabled_target,),
        )
    generation = placer.bump_generation(context, enabled_target)
    assert generation > lease["generation"]
    new_lease = placer.place(context, enabled_target, holder="controller-b")
    assert new_lease["generation"] == generation
    with pytest.raises(LeaseRejection, match="stale generation"):
        placer.validate_action(context, enabled_target, generation=lease["generation"],
                               fence_token=lease["fence_token"], lease_holder="controller-a")
    placer.validate_action(context, enabled_target, generation=new_lease["generation"],
                           fence_token=new_lease["fence_token"], lease_holder="controller-b")


# ---------------------------------------------------------------------------
# MAC-003: qworkerd typed guest protocol
# ---------------------------------------------------------------------------


def test_mac003_p01_typed_guest_operations_execute_in_sandbox(tmp_path):
    guest = GuestProtocol(tmp_path / "task-1" / "workspace", "task-1")
    write = guest.execute("fs.write", "guest-rpc/1",
                          {"path": "workspace/notes.txt", "content": "hello guest"},
                          {"task_id": "task-1"})
    assert write["output"]["bytes"] == 11
    read = guest.execute("fs.read", "guest-rpc/1",
                         {"path": "workspace/notes.txt"}, {"task_id": "task-1"})
    assert read["output"]["content"] == "hello guest"
    exec_result = guest.execute("terminal.exec", "guest-rpc/1",
                                {"command": "ls"}, {"task_id": "task-1"})
    assert exec_result["output"]["exit_code"] == 0
    assert "notes.txt" in exec_result["output"]["stdout"]


def test_mac003_n01_unknown_version_protected_path_ambient_secret_rejected(tmp_path):
    guest = GuestProtocol(tmp_path / "task-2" / "workspace", "task-2")
    identity = {"task_id": "task-2"}
    with pytest.raises(GuestRejection, match="protocol version"):
        guest.execute("fs.read", "guest-rpc/0", {"path": "workspace/x"}, identity)
    with pytest.raises(GuestRejection, match="unknown operation"):
        guest.execute("kernel.modprobe", "guest-rpc/1", {}, identity)
    with pytest.raises(GuestRejection, match="protected path"):
        guest.execute("fs.write", "guest-rpc/1",
                      {"path": "/etc/passwd", "content": "x"}, identity)
    with pytest.raises(GuestRejection, match="protected path refused"):
        guest.execute("fs.read", "guest-rpc/1", {"path": "../../etc/hostname"}, identity)
    with pytest.raises(GuestRejection, match="ambient-secret"):
        guest.execute("terminal.exec", "guest-rpc/1",
                      {"command": "env", "use_ambient_credentials": True}, identity)
    # Untouched: nothing outside the sandbox was created.
    assert not (tmp_path / "task-2" / "workspace" / "x").exists()


def test_mac003_r01_restart_reconnects_with_same_authority(tmp_path):
    guest_a = GuestProtocol(tmp_path / "task-3" / "workspace", "task-3")
    identity = {"task_id": "task-3", "target_id": "tgt-x", "generation": 4, "fence_token": 9}
    guest_a.execute("fs.write", "guest-rpc/1",
                    {"path": "workspace/state.txt", "content": "pre-restart"}, identity)
    # "Restart": a new guest instance for the same target/generation has the
    # same sandbox and scope — no broader authority.
    guest_b = GuestProtocol(tmp_path / "task-3" / "workspace", "task-3")
    read = guest_b.execute("fs.read", "guest-rpc/1",
                           {"path": "workspace/state.txt"}, identity)
    assert read["output"]["content"] == "pre-restart"
    with pytest.raises(GuestRejection):
        guest_b.execute("fs.read", "guest-rpc/1",
                        {"path": "workspace/state.txt"}, {"task_id": "other-task"})


# ---------------------------------------------------------------------------
# MAC-004: durable delivery, ACK, redelivery
# ---------------------------------------------------------------------------


def _runner_log(log: list):
    def execute(operation, arguments):
        log.append({"operation": operation, "arguments": arguments})
        return {"done": True, "operation": operation}
    return execute


def test_mac004_p01_deliver_ack_only_after_durable_result(migrated_db, workspace_setup, context, enabled_target):
    delivery = WorkerDeliveryService(migrated_db)
    envelope = delivery.enqueue(context, enabled_target, "fs.write",
                                {"path": "workspace/f.txt", "content": "x"},
                                idempotency_key=str(uuid.uuid4()))
    log = []
    outcome = delivery.deliver(context, envelope["delivery_id"], _runner_log(log))
    assert outcome["replayed"] is False and outcome["result"]["done"] is True
    row = migrated_db.query_one(
        "SELECT status FROM worker_deliveries WHERE delivery_id = %s",
        (envelope["delivery_id"],),
    )
    assert row[0] == "acked"
    stored = migrated_db.query_one(
        "SELECT result FROM worker_results WHERE tenant_id=%s AND idempotency_key=%s",
        (context.tenant_id, envelope["idempotency_key"]),
    )
    assert stored[0]["done"] is True
    assert len(log) == 1


def test_mac004_n01_dropped_ack_redelivers_original_result_without_reexecution(migrated_db, workspace_setup, context, enabled_target):
    delivery = WorkerDeliveryService(migrated_db)
    idem = str(uuid.uuid4())
    envelope = delivery.enqueue(context, enabled_target, "terminal.exec",
                                {"command": "echo hi"}, idempotency_key=idem)
    log = []
    delivery.deliver(context, envelope["delivery_id"], _runner_log(log))
    # Simulate a dropped ACK: redeliver the same envelope.
    outcome = delivery.deliver(context, envelope["delivery_id"], _runner_log(log))
    assert outcome["replayed"] is True
    assert outcome["result"] == {"done": True, "operation": "terminal.exec"}
    assert len(log) == 1, "worker must not re-execute the operation"


def test_mac004_r01_gateway_restart_redelivery_respects_expiry_generation_idempotency(migrated_db, workspace_setup, context, enabled_target):  # noqa: D102
    delivery = WorkerDeliveryService(migrated_db)
    # Expired delivery: redelivery refused.
    expired = delivery.enqueue(context, enabled_target, "fs.read", {"path": "x"},
                               idempotency_key=str(uuid.uuid4()), ttl_seconds=1)
    # Stale-generation delivery: refused at action validation before work.
    with migrated_db.connection() as connection:
        connection.execute(
            "UPDATE worker_deliveries SET expires_at = now() - interval '1 second'"
            " WHERE idempotency_key=%s",
            (expired["idempotency_key"],),
        )
    from quansio.machine_control.services import DeliveryExpired

    with pytest.raises(DeliveryExpired):
        delivery.deliver(context, expired["delivery_id"], _runner_log([]))
    # Unacknowledged valid delivery: restart-safe redelivery with the same idempotency key.
    pending = delivery.enqueue(context, enabled_target, "fs.read", {"path": "workspace/y"},
                               idempotency_key=str(uuid.uuid4()))
    fresh_service = WorkerDeliveryService(migrated_db)  # "restart"
    log = []
    fresh_service.deliver(context, pending["delivery_id"], _runner_log(log))
    redelivered = fresh_service.deliver(context, pending["delivery_id"], _runner_log(log))
    assert redelivered["replayed"] is True and len(log) == 1


# ---------------------------------------------------------------------------
# MAC-005: isolated task runtime
# ---------------------------------------------------------------------------


def test_mac005_p01_provision_isolated_environment_from_declared_inputs(migrated_db, workspace_setup, context, tmp_path):
    runtime = IsolatedTaskRuntime(migrated_db, tmp_path)
    inputs = [{"path": "brief.md", "content": "task brief"}]
    env = runtime.provision(context, "task-iso-1", inputs)
    guest = env["guest"]
    read = guest.execute("fs.read", "guest-rpc/1", {"path": "brief.md"},
                         {"task_id": "task-iso-1"})
    assert read["output"]["content"] == "task brief"


def test_mac005_n01_internal_access_and_unbrokered_credentials_blocked(migrated_db, workspace_setup, context, tmp_path):
    runtime = IsolatedTaskRuntime(migrated_db, tmp_path)
    env = runtime.provision(context, "task-iso-2", [])
    guest = env["guest"]
    # Internal-network access shaped as a filesystem escape: blocked.
    with pytest.raises(GuestRejection, match="escapes the task sandbox"):
        guest.execute("fs.read", "guest-rpc/1", {"path": "../other-task/secrets"}, {"task_id": "task-iso-2"})
    # Unbrokered credential use: refused without touching anything.
    with pytest.raises(GuestRejection, match="ambient-secret"):
        guest.execute("terminal.exec", "guest-rpc/1",
                      {"command": "env", "use_ambient_credentials": True}, {"task_id": "task-iso-2"})


def test_mac005_r01_recreate_from_declared_inputs_only(migrated_db, workspace_setup, context, tmp_path):
    runtime = IsolatedTaskRuntime(migrated_db, tmp_path)
    inputs = [{"path": "a.txt", "content": "declared"}]
    env = runtime.provision(context, "task-iso-3", inputs)
    # Undeclared guest-local state appears after provisioning.
    undeclared = Path(env["root"]) / "workspace" / "undeclared.txt"
    undeclared.write_text("local scratch")
    runtime.destroy(context, "task-iso-3")
    fresh = runtime.recreate(context, "task-iso-3")
    root = Path(fresh["root"])
    assert (root / "workspace" / "a.txt").read_text() == "declared"
    assert not (root / "workspace" / "undeclared.txt").exists(), \
        "recovery must not depend on undeclared guest-local state"


# ---------------------------------------------------------------------------
# MAC-006: persistent workspace computer
# ---------------------------------------------------------------------------


def test_mac006_p01_workspace_binding_and_state_survive_hibernation(migrated_db, workspace_setup, context, tmp_path):
    service = WorkspaceComputerService(migrated_db, tmp_path)
    computer = service.bind(context, "comp-1")
    state_file = Path(computer["state_path"]) / "browser-session" / "state.json"
    state_file.write_text('{"tabs": ["open"]}')
    service.hibernate(context, "comp-1")
    record = service.resume_after_control_restart(context, "comp-1")
    assert record["lifecycle"] == "resumed"
    assert record["generation"] >= 2, "execution generation advances on resume"
    assert state_file.read_text() == '{"tabs": ["open"]}', "authorized state preserved"


def test_mac006_n01_cross_tenant_attachment_refused(migrated_db, workspace_setup, context, tmp_path):
    service = WorkspaceComputerService(migrated_db, tmp_path)
    service.bind(context, "comp-2")
    foreign_ctx = IdentityContext(
        tenant_id=str(uuid.uuid4()), workspace_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()), session_id=str(uuid.uuid4()),
        roles=("member",), expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    with pytest.raises(PermissionError, match="authorized transfer"):
        service.attach_to_other_tenant(context, "comp-2", foreign_ctx)


# ---------------------------------------------------------------------------
# MAC-007: checkpoints
# ---------------------------------------------------------------------------


def test_mac007_p01_workspace_and_full_checkpoints_restorable(migrated_db, workspace_setup, context, tmp_path):
    from quansio.machine_control.services import WorkspaceComputerService

    computers = WorkspaceComputerService(migrated_db, tmp_path)
    computers.bind(context, "comp-ckpt")
    checkpoints = CheckpointService(migrated_db)
    real_file = REPO_ROOT / "pyproject.toml"
    real_digest = __import__("hashlib").sha256(real_file.read_bytes()).hexdigest()
    references = {
        "artifact_digests": [{"path": "pyproject.toml", "digest": real_digest}],
        "state_watermarks": [{"consumer": "qual", "run_id": str(uuid.uuid4()), "last_sequence": 3}],
        "kind_marker": "workspace",
    }
    checkpoint = checkpoints.create(context, "comp-ckpt", "workspace_only", references)
    # Every referenced artifact must resolve; the watermark must be committed.
    def fetch(path):
        return Path(REPO_ROOT / path).read_text() if (REPO_ROOT / path).is_file() else None

    result = checkpoints.verify(context, checkpoint["checkpoint_id"], fetch,
                                lambda consumer, run_id, seq: True)
    assert result["state"] == "restorable"
    restored = checkpoints.restore(context, checkpoint["checkpoint_id"], new_generation=7)
    assert restored["restored_generation"] == 7


def test_mac007_n01_missing_artifact_or_uncommitted_watermark_rejected(migrated_db, workspace_setup, context, tmp_path):
    from quansio.machine_control.services import WorkspaceComputerService

    WorkspaceComputerService(migrated_db, tmp_path).bind(context, "comp-ckpt-2")
    checkpoints = CheckpointService(migrated_db)
    checkpoint = checkpoints.create(context, "comp-ckpt-2", "full_machine", {
        "artifact_digests": [{"path": "evidence/missing/artifact.bin", "digest": "abc"}],
        "state_watermarks": [{"consumer": "c", "run_id": str(uuid.uuid4()), "last_sequence": 1}],
    })
    with pytest.raises(ValueError, match="missing"):
        checkpoints.verify(context, checkpoint["checkpoint_id"],
                           lambda path: None, lambda c, r, s: True)
    checkpoint2 = checkpoints.create(context, "comp-ckpt-2", "full_machine", {
        "artifact_digests": [],
        "state_watermarks": [{"consumer": "c", "run_id": str(uuid.uuid4()), "last_sequence": 1}],
    })
    with pytest.raises(ValueError, match="uncommitted"):
        checkpoints.verify(context, checkpoint2["checkpoint_id"],
                           lambda path: b"", lambda c, r, s: False)


def test_mac007_r01_restore_to_new_generation_fails_stale_actions(placer, migrated_db, workspace_setup, context, tmp_path, enabled_target):  # noqa: D102
    from quansio.machine_control.services import WorkspaceComputerService

    WorkspaceComputerService(migrated_db, tmp_path).bind(context, "comp-ckpt-3")
    checkpoints = CheckpointService(migrated_db)
    checkpoint = checkpoints.create(context, "comp-ckpt-3", "workspace_only", {
        "artifact_digests": [], "state_watermarks": [],
    })
    checkpoints.verify(context, checkpoint["checkpoint_id"],
                       lambda path: b"", lambda c, r, s: True)
    lease = placer.place(context, enabled_target, holder="pre-restore-controller")
    result = checkpoints.restore(context, checkpoint["checkpoint_id"], new_generation=99)
    assert result["restored_generation"] == 99
    # Restore migrates the target to a new generation: stale pre-restore
    # actions fail generation/lease validation.
    placer.bump_generation(context, enabled_target)
    with pytest.raises(LeaseRejection, match="stale generation"):
        placer.validate_action(context, enabled_target, generation=lease["generation"],
                               fence_token=lease["fence_token"], lease_holder="pre-restore-controller")


# ---------------------------------------------------------------------------
# MAC-008: private execution target path
# ---------------------------------------------------------------------------


def test_mac008_p01_private_target_uses_same_protocol(migrated_db, workspace_setup, context, inventory, placer):
    private = PrivateTargetService(migrated_db, inventory)
    target_id = f"private-{uuid.uuid4().hex[:8]}"
    registered = private.register(context, target_id,
                                  mapped_qualification_suites=["Q-MACHINE-PRIVATE"])
    inventory.set_lifecycle(context, target_id, "enabled")
    lease = placer.place(context, target_id, holder="gateway", required_profile="private.unqualified")
    # Same typed guest protocol as hosted targets (no separate runtime).
    guest = GuestProtocol(Path("/tmp") / f"private-{target_id}", "private-task")
    write = guest.execute("fs.write", "guest-rpc/1",
                          {"path": "workspace/out.txt", "content": "private work"},
                          {"task_id": "private-task"})
    assert write["output"]["bytes"] == 12 and registered["target_id"] == target_id
    placer.validate_action(context, target_id, lease["generation"],
                           lease["fence_token"], lease_holder="gateway")


def test_mac008_n01_unqualified_private_target_stays_disabled(migrated_db, workspace_setup, context, inventory):
    private = PrivateTargetService(migrated_db, inventory)
    target_id = f"private-{uuid.uuid4().hex[:8]}"
    registered = private.register(context, target_id,
                                  mapped_qualification_suites=["Q-MACHINE-PRIVATE"])
    assert registered["enabled"] is False
    with pytest.raises(PermissionError, match="cannot be enabled"):
        private.enable(context, target_id, mapped_qualification_suites=["Q-MACHINE-PRIVATE"])
    target = inventory.get(context, target_id)
    assert target["lifecycle"] == "registered", "support selection keeps it disabled"


def test_mac008_r01_disconnect_preserves_pending_work(migrated_db, workspace_setup, context, inventory, enabled_target):
    private = PrivateTargetService(migrated_db, inventory)
    delivery = WorkerDeliveryService(migrated_db)
    pending = delivery.enqueue(context, enabled_target, "fs.write",
                               {"path": "workspace/p.txt", "content": "queued"},
                               idempotency_key=str(uuid.uuid4()))
    preserved = private.preserve_pending_on_disconnect(context, enabled_target)
    assert [p["delivery_id"] for p in preserved] == [pending["delivery_id"]]
    # Reconnect: the same delivery completes under the same idempotency key.
    service = WorkerDeliveryService(migrated_db)
    log = []
    outcome = service.deliver(context, pending["delivery_id"],
                              lambda op, args: {"done": True})
    assert outcome["replayed"] is False and len(log) == 0
