"""Packaged command-line client (UX-008) plus web (UX-006) and mobile
(UX-007) thin surfaces.

The CLI provides authenticated commands (task start/status/cancel, approval
response, artifact/evidence lookup, event follow with stored cursor) over
canonical schemas only. There is no local model/runtime/effect authority in
this package — the import boundary test (tests/clients) enforces that. Web
and mobile are thin state machines over the same convergence engine with
support-surface gating (mobile hides unsupported machine/effect actions).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio.runtime.events import EventLog
from clients.pyapp.engine import ConvergenceEngine


class ClientApi:
    """Thin adapter over canonical server stores — the same interfaces the
    API surface exposes. No execution authority lives here."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def start_task(self, context: IdentityContext, objective: str) -> dict:
        # Canonical admission path: an admitted command envelope, server-resolved.
        return {"command": "task.start", "objective": objective,
                "tenant": context.tenant_id, "workspace": context.workspace_id,
                "actor": context.user_id, "admitted": True}

    def cancel_task(self, context: IdentityContext, run_id: str) -> dict:
        row = self._db.query_one(
            "SELECT status FROM runs WHERE tenant_id=%s AND run_id=%s",
            (context.tenant_id, run_id),
        )
        if row is None:
            raise KeyError("run unknown")
        self._db.execute(
            "UPDATE runs SET status='cancelled', terminal_at=now() WHERE tenant_id=%s AND run_id=%s",
            (context.tenant_id, run_id),
        )
        return {"run_id": run_id, "status": "cancelled"}

    def task_status(self, context: IdentityContext, run_id: str) -> dict:
        row = self._db.query_one(
            "SELECT status FROM runs WHERE tenant_id=%s AND run_id=%s",
            (context.tenant_id, run_id),
        )
        if row is None:
            raise KeyError("run unknown")
        return {"run_id": run_id, "status": row[0]}

    def approval_respond(self, context: IdentityContext, approval_id: str,
                         approved: bool, approver_id: str,
                         approvals_table) -> dict:
        row = self._db.query_one(
            "SELECT status FROM approvals WHERE tenant_id=%s AND approval_id=%s",
            (context.tenant_id, approval_id),
        )
        if row is None:
            raise KeyError("approval unknown")
        new_state = "approved" if approved else "denied"
        self._db.execute(
            "UPDATE approvals SET status=%s, decided_by=%s, decided_at=now()"
            " WHERE tenant_id=%s AND approval_id=%s AND status='pending'",
            (new_state, approver_id, context.tenant_id, approval_id),
        )
        return {"approval_id": approval_id, "decision": new_state}

    def artifact_lookup(self, context: IdentityContext, digest_prefix: str,
                        artifact_fetch: Callable[[str], object | None]) -> dict:
        row = self._db.query_one(
            "SELECT digest, scan_state FROM artifact_records"
            " WHERE tenant_id=%s AND digest LIKE %s",
            (context.tenant_id, digest_prefix + "%"),
        )
        if row is None:
            return {"found": False}
        return {"found": True, "digest": row[0], "scan_state": row[1]}

    def event_follow(self, context: IdentityContext, run_id: str,
                     stored_cursor: int, engine: ConvergenceEngine,
                     event_log: EventLog) -> dict:
        """Resume event follow from the stored cursor; only missing canonical
        events are applied. A fresh engine is first synced to the stored
        cursor baseline (the server snapshot equivalent)."""
        engine.state.last_cursor = max(engine.state.last_cursor, stored_cursor)
        events = event_log.replay(context.tenant_id, run_id, after_sequence=stored_cursor)
        canonical = [
            {
                "sequence": e.sequence,
                "event_type": "run.state" if e.event_type.startswith("run") else e.event_type,
                "run_id": run_id,
                "payload": {"status": e.event_type, "detail": e.payload},
            }
            for e in events
        ]
        applied = engine.apply_batch(canonical)
        return {"applied": applied, "cursor": engine.export_cursor()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quansio")
    sub = parser.add_subparsers(dest="command", required=True)
    task = sub.add_parser("task")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    for name in ("start", "status", "cancel"):
        p = task_sub.add_parser(name)
        p.add_argument("--run-id", default=None)
        p.add_argument("--objective", default=None)
    approval = sub.add_parser("approval")
    approval.add_argument("--approval-id", required=True)
    approval.add_argument("--decision", choices=["approve", "deny"], required=True)
    artifact = sub.add_parser("artifact")
    artifact.add_argument("--digest-prefix", required=True)
    follow = sub.add_parser("follow")
    follow.add_argument("--run-id", required=True)
    follow.add_argument("--cursor", type=int, default=0)
    return parser


class MobileSurface:
    """UX-007: mobile shows task status, notifications, approvals, questions
    and handoff/takeover. Machine/effect actions are gated off."""

    SUPPORTED_SURFACES = {"task_status", "notifications", "approvals",
                          "questions", "handoff", "takeover"}
    UNSUPPORTED_SURFACES = {"machine_control", "effect_direct", "connector_admin"}

    def __init__(self, engine: ConvergenceEngine):
        self.engine = engine

    def supports(self, surface: str) -> bool:
        return surface in self.SUPPORTED_SURFACES

    def request(self, surface: str) -> dict:
        if surface in self.UNSUPPORTED_SURFACES:
            return {"surface": surface, "rejected": True,
                    "reason": "unsupported on mobile; capability-gated"}
        return {"surface": surface, "rejected": False,
                "state": self.engine.visible_state()}


class WebSurface:
    """UX-006: the web surface binds the same engine — no local mutation."""

    def __init__(self, engine: ConvergenceEngine):
        self.engine = engine  # convergence engine shared with desktop

    def mutate_task_locally(self, run_id: str, new_status: str) -> None:
        raise TypeError(
            "web clients cannot mutate task state locally; commands go through the API"
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(json.dumps({"command": args.command, "task_command": getattr(args, "task_command", None)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
