"""Foundational immutable CapabilitySnapshot (SEC-001, owner quansio-control).

Admission freezes the exact authority a principal holds: capability atoms,
target/data constraints, budget ceiling, expiry, parent reference and
revision. Children are admitted only as strict subsets of the parent
snapshot, before any worker/model/tool/machine execution becomes externally
visible. Post-admission mutation is denied at the storage layer; expiry
forces fresh admission before resumed work may execute.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg
from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class CapabilityEscalationError(PermissionError):
    """A child snapshot requested authority outside its parent."""


class SnapshotExpiredError(PermissionError):
    """A snapshot no longer grants authority; fresh admission is required."""


def _canonical(capabilities: list[str], constraints: dict, budget_cents: int, expires_at: datetime) -> str:
    material = json.dumps(
        {
            "budget_cents": budget_cents,
            "capabilities": sorted(capabilities),
            "constraints": constraints,
            "expires_at": expires_at.isoformat(),
        },
        sort_keys=True,
    )
    return hashlib.sha256(material.encode()).hexdigest()


def _path_within(child_path: str, parent_path: str) -> bool:
    """Glob-style containment: /tmp/work/** is within /tmp/**."""
    parent_base = parent_path.rstrip("*")
    child_base = child_path.rstrip("*")
    return child_base.startswith(parent_base)


def _is_subset(child: Any, parent: Any, key_path: tuple = ()) -> bool:
    if isinstance(parent, dict) and isinstance(child, dict):
        for key, value in child.items():
            if key in parent:
                if not _is_subset(value, parent[key], key_path + (key,)):
                    return False
                continue
            # Target trees: a child path may refine an allowed parent path.
            if key_path and key_path[-1] == "targets" and isinstance(value, list):
                matched = any(
                    _path_within(key, parent_key)
                    and _is_subset(value, parent_value, key_path + (parent_key,))
                    for parent_key, parent_value in parent.items()
                    if isinstance(parent_value, list)
                )
                if not matched:
                    return False
                continue
            return False
        return True
    if isinstance(parent, list) and isinstance(child, list):
        return all(any(_is_subset(item, candidate, key_path) for candidate in parent) for item in child)
    return child == parent


class CapabilityService:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def admit_root(
        self,
        context: IdentityContext,
        principal_id: str,
        capabilities: list[str],
        constraints: dict,
        budget_cents: int,
        ttl_seconds: int = 3600,
    ) -> dict:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        return self._admit(
            context,
            principal_id=principal_id,
            parent_snapshot_id=None,
            parent=None,
            capabilities=capabilities,
            constraints=constraints,
            budget_cents=budget_cents,
            expires_at=expires_at,
        )

    def admit_child(
        self,
        context: IdentityContext,
        parent_snapshot_id: str,
        principal_id: str,
        capabilities: list[str],
        constraints: dict,
        budget_cents: int,
    ) -> dict:
        parent = self.require_active(context, parent_snapshot_id)
        expires_at = min(
            parent["expires_at"],
            datetime.now(timezone.utc) + timedelta(hours=1),
        )
        return self._admit(
            context,
            principal_id=principal_id,
            parent_snapshot_id=parent_snapshot_id,
            parent=parent,
            capabilities=capabilities,
            constraints=constraints,
            budget_cents=budget_cents,
            expires_at=expires_at,
        )

    def _admit(
        self,
        context: IdentityContext,
        principal_id: str,
        parent_snapshot_id: str | None,
        parent: dict | None,
        capabilities: list[str],
        constraints: dict,
        budget_cents: int,
        expires_at: datetime,
    ) -> dict:
        # Strict-subset enforcement happens before the snapshot exists and
        # therefore before any execution can become externally visible.
        if parent is not None:
            if not _is_subset(capabilities, parent["capabilities"]):
                raise CapabilityEscalationError("child capability atoms exceed parent authority")
            if not _is_subset(constraints, parent["constraints"]):
                raise CapabilityEscalationError("child constraints exceed parent authority")
            if budget_cents > parent["budget_cents"]:
                raise CapabilityEscalationError("child budget exceeds parent ceiling")
            if expires_at > parent["expires_at"]:
                raise CapabilityEscalationError("child expiry exceeds parent validity")

        snapshot_id = str(uuid.uuid4())
        revision = 1 if parent is None else parent["revision"] + 1
        digest = _canonical(capabilities, constraints, budget_cents, expires_at)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO capability_snapshots
                    (tenant_id, snapshot_id, parent_snapshot_id, principal_id, revision,
                     capabilities, constraints, budget_cents, content_digest, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    context.tenant_id,
                    snapshot_id,
                    parent_snapshot_id,
                    principal_id,
                    revision,
                    Json(capabilities),
                    Json(constraints),
                    budget_cents,
                    digest,
                    expires_at,
                ),
            )
        return self.require_active(context, snapshot_id)

    def require_active(self, context: IdentityContext, snapshot_id: str) -> dict:
        row = self._db.query_one(
            """
            SELECT snapshot_id::text, parent_snapshot_id::text, principal_id::text, revision,
                   capabilities, constraints, budget_cents, expires_at, revoked_at
            FROM capability_snapshots
            WHERE tenant_id = %s AND snapshot_id = %s
            """,
            (context.tenant_id, snapshot_id),
        )
        if row is None:
            raise KeyError(f"unknown snapshot {snapshot_id}")
        snapshot = {
            "snapshot_id": row[0],
            "parent_snapshot_id": row[1],
            "principal_id": row[2],
            "revision": row[3],
            "capabilities": row[4],
            "constraints": row[5],
            "budget_cents": row[6],
            "expires_at": row[7],
            "revoked_at": row[8],
        }
        if snapshot["revoked_at"] is not None or snapshot["expires_at"] <= datetime.now(timezone.utc):
            raise SnapshotExpiredError(
                f"snapshot {snapshot_id} expired or revoked; fresh admission required before execution"
            )
        return snapshot

    def revoke(self, context: IdentityContext, snapshot_id: str) -> None:
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE capability_snapshots SET revoked_at = now() WHERE tenant_id = %s AND snapshot_id = %s",
                (context.tenant_id, snapshot_id),
            )
