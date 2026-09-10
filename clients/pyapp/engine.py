"""Canonical client convergence engine shared by desktop, web, mobile and
CLI surfaces (UX-002/006/007/008).

Clients are projections: the engine applies a server snapshot plus ordered
RuntimeEvents from a durable cursor. Duplicate and out-of-order events are
dropped (never locally re-sequenced), visible state always rebuilds from
server data after cache loss, and a degraded/offline connection is surfaced
explicitly without local UI state claiming task completion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClientState:
    last_cursor: int = 0
    offline: bool = False
    degraded: bool = False
    timeline: list[dict] = field(default_factory=list)
    task_status: dict[str, str] = field(default_factory=dict)
    approvals: dict[str, dict] = field(default_factory=dict)
    artifacts: dict[str, dict] = field(default_factory=dict)


class ConvergenceEngine:
    """Applies canonical events with a cursor. Identical input sequences
    converge every client instance to an identical projection."""

    def __init__(self, client_name: str):
        self.client_name = client_name
        self.state = ClientState()

    def apply_snapshot(self, snapshot: dict) -> None:
        """Full-state snapshot from the server: replaces local projection."""
        self.state.timeline = list(snapshot.get("timeline", []))
        self.state.task_status = dict(snapshot.get("task_status", {}))
        self.state.approvals = dict(snapshot.get("approvals", {}))
        self.state.artifacts = dict(snapshot.get("artifacts", {}))
        self.state.last_cursor = int(snapshot.get("cursor", 0))
        self.state.offline = False

    def apply_event(self, event: dict) -> bool:
        """Apply one canonical event. Returns True if accepted; duplicates
        and out-of-order events are rejected without inventing sequence."""
        sequence = int(event["sequence"])
        if sequence <= self.state.last_cursor:
            return False  # duplicate
        if sequence > self.state.last_cursor + 1:
            raise ValueError(
                f"gap in canonical stream: have {self.state.last_cursor}, got {sequence}"
            )
        kind = event["event_type"]
        payload = event.get("payload", {})
        if kind == "run.state":
            self.state.task_status[event["run_id"]] = payload.get("status", "unknown")
        elif kind == "approval.request":
            self.state.approvals[payload["approval_id"]] = {
                "operation": payload.get("operation"),
                "scope": payload.get("scope"),
                "state": "pending",
            }
        elif kind == "approval.decided":
            approval = self.state.approvals.get(payload["approval_id"])
            if approval is not None:
                approval["state"] = payload.get("decision", "decided")
        elif kind == "artifact.stored":
            self.state.artifacts[payload["artifact_id"]] = {
                "digest": payload.get("digest"), "state": payload.get("state"),
            }
        self.state.timeline.append({
            "sequence": sequence, "type": kind, "payload": payload,
        })
        self.state.last_cursor = sequence
        return True

    def apply_batch(self, events: list[dict]) -> int:
        applied = 0
        for event in events:
            try:
                if self.apply_event(event):
                    applied += 1
            except ValueError:
                # Gap: signal degraded; next snapshot repairs the projection.
                self.state.degraded = True
        return applied

    def mark_offline(self) -> None:
        self.state.offline = True

    def mark_online(self) -> None:
        self.state.offline = False
        self.state.degraded = False

    def export_cursor(self) -> int:
        """Durable cursor for reconnect/resume."""
        return self.state.last_cursor

    def visible_state(self) -> dict:
        return {
            "offline": self.state.offline,
            "degraded": self.state.degraded,
            "cursor": self.state.last_cursor,
            "task_status": dict(self.state.task_status),
            "approvals": dict(self.state.approvals),
            "artifacts": dict(self.state.artifacts),
        }
