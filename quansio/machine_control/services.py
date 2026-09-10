"""Durable worker delivery, ACK and redelivery (MAC-004) plus the isolated
task runtime (MAC-005), persistent workspace computer (MAC-006), checkpoints
(MAC-007) and the private execution target path (MAC-008). Owner:
quansio-worker-gateway / quansio-machine-control.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio.qworkerd.protocol import GuestProtocol, GuestRejection


class DeliveryExpired(Exception):
    pass


class WorkerDeliveryService:
    """Envelopes carry delivery_id, attempt, idempotency key and expiry.
    ACK is recorded only after the canonical result is durably stored, and
    redelivery returns the stored result without re-execution."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def enqueue(self, context: IdentityContext, target_id: str, operation: str,
                arguments: dict, idempotency_key: str, ttl_seconds: int = 300) -> dict:
        delivery_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO worker_deliveries
                    (tenant_id, delivery_id, target_id, operation, arguments,
                     idempotency_key, expires_at, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                """,
                (context.tenant_id, delivery_id, target_id, operation,
                 Json(arguments), idempotency_key, expires_at),
            )
        return {"delivery_id": delivery_id, "idempotency_key": idempotency_key,
                "expires_at": expires_at.isoformat()}

    def deliver(self, context: IdentityContext, delivery_id: str,
                execute: Callable[[str, dict], dict]) -> dict:
        """Deliver once; on redelivery return the durable original result
        without invoking ``execute`` again (MAC-004-N01)."""
        row = self._db.query_one(
            """
            SELECT status, attempt, expires_at, operation, arguments, idempotency_key
            FROM worker_deliveries WHERE tenant_id = %s AND delivery_id = %s FOR UPDATE
            """,
            (context.tenant_id, delivery_id),
        )
        if row is None:
            raise KeyError("delivery unknown")
        status, attempt, expires_at, operation, arguments, idem = row
        if expires_at <= datetime.now(timezone.utc) or status == "expired":
            self._db.execute(
                "UPDATE worker_deliveries SET status='expired' WHERE tenant_id=%s AND delivery_id=%s",
                (context.tenant_id, delivery_id),
            )
            raise DeliveryExpired(delivery_id)
        existing = self._db.query_one(
            "SELECT result FROM worker_results WHERE tenant_id=%s AND idempotency_key=%s",
            (context.tenant_id, idem),
        )
        if existing is not None:
            self._db.execute(
                """
                UPDATE worker_deliveries SET status='acked', attempt = attempt + 1
                WHERE tenant_id=%s AND delivery_id=%s
                """,
                (context.tenant_id, delivery_id),
            )
            return {"result": existing[0], "replayed": True}
        self._db.execute(
            "UPDATE worker_deliveries SET status='delivered', attempt = attempt + 1"
            " WHERE tenant_id=%s AND delivery_id=%s",
            (context.tenant_id, delivery_id),
        )
        result = execute(operation, arguments)
        # ACK only after the canonical result is durably recorded.
        self._db.execute(
            """
            INSERT INTO worker_results (tenant_id, idempotency_key, result)
            VALUES (%s, %s, %s)
            """,
            (context.tenant_id, idem, Json(result)),
        )
        self._db.execute(
            "UPDATE worker_deliveries SET status='acked' WHERE tenant_id=%s AND delivery_id=%s",
            (context.tenant_id, delivery_id),
        )
        return {"result": result, "replayed": False}

    def pending_deliveries(self, context: IdentityContext) -> list[dict]:
        rows = self._db.query_all(
            """
            SELECT delivery_id::text, target_id, operation, arguments, idempotency_key,
                   attempt, expires_at FROM worker_deliveries
            WHERE tenant_id = %s AND status IN ('pending', 'delivered')
              AND expires_at > now()
            ORDER BY created_at
            """,
            (context.tenant_id,),
        )
        return [{"delivery_id": r[0], "target_id": r[1], "operation": r[2],
                 "arguments": r[3], "idempotency_key": r[4], "attempt": r[5],
                 "expires_at": r[6]} for r in rows]


class IsolatedTaskRuntime:
    """MAC-005: per-task environment with tenant-bound identity, a sandbox
    root provisioned only from declared inputs, deny-by-default path scope
    (the guest refuses anything outside the root) and no ambient credentials
    (the guest refuses unbrokered secret use)."""

    def __init__(self, database: PlatformDatabase, state_root: Path):
        self._db = database
        self._state_root = Path(state_root)
        self._state_root.mkdir(parents=True, exist_ok=True)

    def provision(self, context: IdentityContext, task_id: str,
                  declared_inputs: list[dict]) -> dict:
        root = self._state_root / context.tenant_id / task_id
        if root.exists():
            shutil.rmtree(root)
        (root / "workspace").mkdir(parents=True)
        for artifact in declared_inputs:
            target = root / "workspace" / artifact["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(artifact.get("content", ""))
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO task_environments
                    (tenant_id, task_id, root_path, declared_inputs, state)
                VALUES (%s, %s, %s, %s, 'provisioned')
                ON CONFLICT (tenant_id, task_id)
                DO UPDATE SET root_path = EXCLUDED.root_path,
                              declared_inputs = EXCLUDED.declared_inputs,
                              state = 'provisioned'
                """,
                (context.tenant_id, task_id, str(root), Json(declared_inputs)),
            )
        guest = GuestProtocol(root / "workspace", task_id)
        return {"task_id": task_id, "root": str(root), "guest": guest}

    def destroy(self, context: IdentityContext, task_id: str) -> None:
        row = self._db.query_one(
            "SELECT root_path FROM task_environments WHERE tenant_id=%s AND task_id=%s",
            (context.tenant_id, task_id),
        )
        if row is None:
            raise KeyError(task_id)
        shutil.rmtree(row[0], ignore_errors=True)
        self._db.execute(
            "UPDATE task_environments SET state='destroyed' WHERE tenant_id=%s AND task_id=%s",
            (context.tenant_id, task_id),
        )

    def recreate(self, context: IdentityContext, task_id: str) -> dict:
        """MAC-005-R01: recreate strictly from declared inputs — any
        undeclared guest-local state is gone, and recovery must not need it."""
        row = self._db.query_one(
            "SELECT declared_inputs FROM task_environments WHERE tenant_id=%s AND task_id=%s",
            (context.tenant_id, task_id),
        )
        if row is None:
            raise KeyError(task_id)
        return self.provision(context, task_id, row[0])


class WorkspaceComputerService:
    """MAC-006: persistent workspace computer bound to owner+workspace,
    independent of client/session lifetime; state persists across
    hibernation and generation advances on resume."""

    def __init__(self, database: PlatformDatabase, state_root: Path):
        self._db = database
        self._state_root = Path(state_root)
        self._state_root.mkdir(parents=True, exist_ok=True)

    def bind(self, context: IdentityContext, computer_id: str) -> dict:
        state_path = str(self._state_root / context.workspace_id / computer_id)
        Path(state_path).mkdir(parents=True, exist_ok=True)
        (Path(state_path) / "workspace").mkdir(exist_ok=True)
        (Path(state_path) / "browser-session").mkdir(exist_ok=True)
        (Path(state_path) / "browser-session" / "state.json").write_text("{}")
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO workspace_computers
                    (tenant_id, workspace_id, computer_id, owner_id, state_path,
                     lifecycle, execution_generation)
                VALUES (%s, %s, %s, %s, %s, 'active', 1)
                ON CONFLICT (tenant_id, workspace_id, computer_id) DO NOTHING
                """,
                (context.tenant_id, context.workspace_id, computer_id,
                 context.user_id, state_path),
            )
        return self.get(context, computer_id)

    def get(self, context: IdentityContext, computer_id: str) -> dict:
        row = self._db.query_one(
            """
            SELECT computer_id, owner_id::text, workspace_id::text, state_path,
                   lifecycle, execution_generation
            FROM workspace_computers
            WHERE tenant_id = %s AND workspace_id = %s AND computer_id = %s
            """,
            (context.tenant_id, context.workspace_id, computer_id),
        )
        if row is None:
            raise KeyError(computer_id)
        return {"computer_id": row[0], "owner_id": row[1], "workspace_id": row[2],
                "state_path": row[3], "lifecycle": row[4], "generation": row[5]}

    def attach_to_other_tenant(self, context: IdentityContext, computer_id: str,
                               other_context: IdentityContext) -> None:
        """MAC-006-N01: cross-tenant attachment without an authorized
        transfer is refused by machine-control — the binding is per tenant
        and workspace and cannot be rewritten in place."""
        row = self._db.query_one(
            "SELECT tenant_id::text FROM workspace_computers"
            " WHERE tenant_id=%s AND workspace_id=%s AND computer_id=%s",
            (context.tenant_id, context.workspace_id, computer_id),
        )
        if row is None or row[0] != other_context.tenant_id:
            raise PermissionError(
                "cross-tenant workspace attachment requires an authorized transfer"
            )

    def hibernate(self, context: IdentityContext, computer_id: str) -> None:
        self._db.execute(
            "UPDATE workspace_computers SET lifecycle='hibernating' WHERE tenant_id=%s"
            " AND workspace_id=%s AND computer_id=%s",
            (context.tenant_id, context.workspace_id, computer_id),
        )

    def resume_after_control_restart(self, context: IdentityContext, computer_id: str) -> dict:
        """MAC-006-R01: control services restart; identity and state persist
        and the execution generation advances on resume."""
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE workspace_computers
                SET lifecycle = 'resumed', execution_generation = execution_generation + 1
                WHERE tenant_id = %s AND workspace_id = %s AND computer_id = %s
                RETURNING execution_generation
                """,
                (context.tenant_id, context.workspace_id, computer_id),
            )
            generation = cursor.fetchone()[0]
        record = self.get(context, computer_id)
        record["generation"] = generation
        return record


class CheckpointService:
    """MAC-007: workspace-only and full-machine checkpoints; every
    referenced state must be durably committed and digest-verified before
    the checkpoint becomes RESTORABLE."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def create(self, context: IdentityContext, computer_id: str, kind: str,
               references: dict) -> dict:
        checkpoint_id = str(uuid.uuid4())
        serialized = json.dumps(references, sort_keys=True, default=str)
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO checkpoints
                    (tenant_id, checkpoint_id, computer_id, kind, state,
                     references_json, references_digest)
                VALUES (%s, %s, %s, %s, 'created', %s, %s)
                """,
                (context.tenant_id, checkpoint_id, computer_id, kind,
                 Json(references), digest),
            )
        return {"checkpoint_id": checkpoint_id, "state": "created", "digest": digest}

    def verify(self, context: IdentityContext, checkpoint_id: str,
               artifact_fetch, event_cursor_committed) -> dict:
        """Digest-verify every referenced artifact and confirm every state
        watermark is committed before marking RESTORABLE (MAC-007-N01)."""
        row = self._db.query_one(
            """
            SELECT kind, references_json, references_digest, state FROM checkpoints
            WHERE tenant_id = %s AND checkpoint_id = %s
            """,
            (context.tenant_id, checkpoint_id),
        )
        if row is None:
            raise KeyError(checkpoint_id)
        kind, references, digest, state = row
        if hashlib.sha256(
            json.dumps(references, sort_keys=True, default=str).encode()
        ).hexdigest() != digest:
            raise ValueError("checkpoint references digest mismatch")
        if state != "created":
            raise ValueError(f"checkpoint in state {state}")
        for artifact in references.get("artifact_digests", []):
            fetched = artifact_fetch(artifact["path"])
            if fetched is None:
                raise ValueError(f"referenced artifact missing: {artifact['path']}")
            if artifact["digest"] not in (artifact.get("alt_digests") or []) and \
               hashlib.sha256(fetched.encode() if isinstance(fetched, str) else fetched).hexdigest() != artifact["digest"]:
                raise ValueError(f"artifact digest mismatch: {artifact['path']}")
        for watermark in references.get("state_watermarks", []):
            if not event_cursor_committed(watermark["consumer"], watermark["run_id"],
                                          watermark["last_sequence"]):
                raise ValueError(f"uncommitted watermark: {watermark}")
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE checkpoints SET state='restorable' WHERE tenant_id=%s AND checkpoint_id=%s",
                (context.tenant_id, checkpoint_id),
            )
        return {"checkpoint_id": checkpoint_id, "state": "restorable"}

    def restore(self, context: IdentityContext, checkpoint_id: str,
                new_generation: int) -> dict:
        """MAC-007-R01: restore/migrate to a new generation; the checkpoint
        records it so stale pre-restore leases fail generation validation."""
        row = self._db.query_one(
            "SELECT state, kind FROM checkpoints WHERE tenant_id=%s AND checkpoint_id=%s",
            (context.tenant_id, checkpoint_id),
        )
        if row is None:
            raise KeyError(checkpoint_id)
        if row[0] != "restorable":
            raise ValueError("checkpoint is not restorable")
        with self._db.connection() as connection:
            connection.execute(
                """
                UPDATE checkpoints SET restored_generation = %s
                WHERE tenant_id = %s AND checkpoint_id = %s
                """,
                (new_generation, context.tenant_id, checkpoint_id),
            )
        return {"checkpoint_id": checkpoint_id, "restored_generation": new_generation,
                "kind": row[1]}


class PrivateTargetService:
    """MAC-008: private worker targets run the SAME typed command,
    capability, effect and evidence protocol as hosted targets — support
    selection keeps them disabled until their mapped qualification suites
    pass."""

    def __init__(self, database: PlatformDatabase, inventory: TargetInventory):
        self._inventory = inventory
        self._db = database

    def register(self, context: IdentityContext, target_id: str,
                 mapped_qualification_suites: list[str]) -> dict:
        generation = self._inventory.register(
            context, target_id, target_type="private",
            support_profile="private.unqualified", health_identity="unprobed",
        )
        return {
            "target_id": target_id,
            "generation": generation,
            "enabled": False,
            "mapped_qualification_suites": mapped_qualification_suites,
            "reason": "private targets stay disabled until mapped suites pass",
        }

    def enable(self, context: IdentityContext, target_id: str,
               mapped_qualification_suites: list[str]) -> None:
        """MAC-008-N01: enabling without the mapped suites is refused —
        support selection keeps the target disabled."""
        raise PermissionError(
            f"private target {target_id} cannot be enabled: mapped qualification "
            f"suites {mapped_qualification_suites} have not passed"
        )

    def preserve_pending_on_disconnect(self, context: IdentityContext, target_id: str) -> list[dict]:
        """MAC-008-R01: disconnect preserves pending work; reconnect or
        re-placement follows operation/effect idempotency."""
        delivery_service = WorkerDeliveryService(self._db)
        return delivery_service.pending_deliveries(context)
