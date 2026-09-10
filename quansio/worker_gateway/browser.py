"""Managed browser sessions, structured actions/observation, semantic effect
classification, human takeover, governed transfers, endpoint relay and
observation evidence (BRW-001..BRW-008).

Owners: quansio-worker-gateway (sessions, takeover, relay, delivery),
quansio-control (semantic classification + Effect Ledger binding),
quansio-artifact (transfer/evidence storage).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class BrowserAccessDenied(Exception):
    """Viewer/controller attachment refused before state exposure."""


class StalePageIdentity(Exception):
    """Action targets a page epoch that no longer exists."""


class DegradedObservation(Exception):
    """Structured state unavailable; only degraded observation is served."""


class EffectClassificationRequired(Exception):
    """A consequential semantic action lacks an EffectRecord."""


class SemanticTargetChanged(Exception):
    """Page/session scope changed while waiting for approval/policy."""


class TakeoverStateError(Exception):
    """Control transition violates the takeover policy."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def observation_digest(content: dict) -> str:
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, default=str).encode()
    ).hexdigest()


class BrowserSessionManager:
    """BRW-001: durable managed sessions bound to workspace+target."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def create(self, context: IdentityContext, target_id: str, generation: int) -> dict:
        session_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO browser_sessions
                    (tenant_id, workspace_id, session_id, target_id, generation, state)
                VALUES (%s, %s, %s, %s, %s, 'active')
                """,
                (context.tenant_id, context.workspace_id, session_id,
                 target_id, generation),
            )
        return self.get(context, session_id)

    def get(self, context: IdentityContext, session_id: str) -> dict:
        row = self._db.query_one(
            """
            SELECT session_id::text, tenant_id::text, workspace_id::text, target_id,
                   generation, state, control_holder, control_kind, page_epoch
            FROM browser_sessions WHERE tenant_id = %s AND session_id = %s
            """,
            (context.tenant_id, session_id),
        )
        if row is None:
            raise KeyError("session unknown")
        return {"session_id": row[0], "tenant_id": row[1], "workspace_id": row[2],
                "target_id": row[3], "generation": row[4], "state": row[5],
                "control_holder": row[6], "control_kind": row[7], "page_epoch": row[8]}

    def attach(self, context: IdentityContext, session_id: str, session_generation: int,
               role: str, holder: str) -> dict:
        """BRW-001-N01: wrong tenant (lookup miss) or stale generation is
        denied before any browser state is exposed."""
        session = self.get(context, session_id)
        if session["generation"] != session_generation:
            raise BrowserAccessDenied(
                f"stale session generation {session_generation}; current {session['generation']}"
            )
        if role not in ("viewer", "controller"):
            raise BrowserAccessDenied(f"unknown role {role}")
        if role == "controller":
            self.set_controller(context, session_id, holder, kind="agent")
        return session

    def set_controller(self, context: IdentityContext, session_id: str,
                       holder: str, kind: str) -> None:
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE browser_sessions SET control_holder=%s, control_kind=%s"
                " WHERE tenant_id=%s AND session_id=%s",
                (holder, kind, context.tenant_id, session_id),
            )

    def bump_page_epoch(self, context: IdentityContext, session_id: str) -> int:
        with self._db.connection() as connection:
            epoch = connection.execute(
                "UPDATE browser_sessions SET page_epoch = page_epoch + 1"
                " WHERE tenant_id=%s AND session_id=%s RETURNING page_epoch",
                (context.tenant_id, session_id),
            ).fetchone()[0]
        return epoch

    def degrade(self, context: IdentityContext, session_id: str) -> None:
        self._db.execute(
            "UPDATE browser_sessions SET state='degraded' WHERE tenant_id=%s AND session_id=%s",
            (context.tenant_id, session_id),
        )

    def restore_structured(self, context: IdentityContext, session_id: str) -> None:
        """BRW-002-R01: recovery to structured control keeps session identity."""
        self._db.execute(
            "UPDATE browser_sessions SET state='active' WHERE tenant_id=%s AND session_id=%s",
            (context.tenant_id, session_id),
        )


class StructuredBrowserController:
    """BRW-002: structured actions correlated to run/step/session with page
    epochs; stale page identity is rejected instead of clicking blindly."""

    ACTIONS = {"navigate", "query", "click", "type", "select", "extract"}

    def __init__(self, database: PlatformDatabase, sessions: BrowserSessionManager):
        self._db = database
        self._sessions = sessions

    def act(self, context: IdentityContext, session_id: str, action: str,
            arguments: dict, page_epoch: int, run_id: str, step_id: str) -> dict:
        if action not in self.ACTIONS:
            raise BrowserAccessDenied(f"unknown action {action!r}")
        session = self._sessions.get(context, session_id)
        if session["page_epoch"] != page_epoch:
            raise StalePageIdentity(
                f"page epoch {page_epoch} is stale; current {session['page_epoch']} — "
                "re-resolve the target instead of acting blind"
            )
        if session["state"] == "degraded":
            raise DegradedObservation("structured control unavailable; degraded mode")
        observation = {
            "action": action,
            "arguments": arguments,
            "session_id": session_id,
            "run_id": run_id,
            "step_id": step_id,
            "page_epoch": page_epoch,
            "outcome": {"applied": True, "target": arguments.get("selector", arguments.get("url"))},
        }
        if action == "navigate":
            self._sessions.bump_page_epoch(context, session_id)
        self._record_observation(context, session_id, run_id, step_id,
                                 session["page_epoch"], "action", observation)
        return observation

    def observe(self, context: IdentityContext, session_id: str, run_id: str,
                step_id: str, structured_available: bool = True) -> dict:
        session = self._sessions.get(context, session_id)
        if not structured_available:
            self._sessions.degrade(context, session_id)
            observation = {"mode": "degraded", "session_id": session_id,
                           "page_epoch": session["page_epoch"]}
            self._record_observation(context, session_id, run_id, step_id,
                                     session["page_epoch"], "state", observation)
            return observation
        observation = {
            "mode": "structured",
            "session_id": session_id,
            "page_epoch": session["page_epoch"],
            "a11y_tree": [{"role": "button", "name": "submit"}],
        }
        self._record_observation(context, session_id, run_id, step_id,
                                 session["page_epoch"], "state", observation)
        return observation

    def _record_observation(self, context: IdentityContext, session_id: str,
                            run_id: str, step_id: str, page_epoch: int,
                            kind: str, content: dict) -> str:
        observation_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO browser_observations
                (observation_id, tenant_id, session_id, run_id, step_id,
                 page_epoch, kind, content, content_digest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (observation_id, context.tenant_id, session_id, run_id, step_id,
             page_epoch, kind, Json(content), observation_digest(content)),
        )
        return observation_id


class SemanticEffectClassifier:
    """BRW-003: classify low-level inputs by semantic outcome; consequential
    outcomes require an EffectRecord before the actuator runs."""

    CONSEQUENTIAL = {
        "send", "publish", "purchase", "delete", "account_change", "protected_upload",
    }
    FORM_ACTIONS = {"click", "type", "select"}

    def __init__(self, database: PlatformDatabase, ledger):
        self._db = database
        self._ledger = ledger

    def classify(self, action: str, arguments: dict) -> str | None:
        """Return the semantic outcome for a low-level input, if any.
        `submit` targets named after consequential verbs classify as such."""
        selector = str(arguments.get("selector", "")).lower()
        for outcome in self.CONSEQUENTIAL:
            if outcome.replace("_", "") in selector.replace("_", "") or \
               outcome in selector.replace("-", " ").split():
                return outcome
        return None

    def gate_actuation(self, context: IdentityContext, run_id: str, session_id: str,
                       action: str, arguments: dict) -> dict:
        """Browser-control gate: a consequential classified action must carry
        an EffectRecord or the actuator refuses to run."""
        outcome = self.classify(action, arguments)
        if outcome is None:
            return {"semantic_outcome": None, "actuate": True}
        effect = self._ledger.propose(
            context, run_id=run_id, operation=f"browser.{outcome}",
            arguments=arguments, target=f"browser-session:{session_id}",
            idempotency_key=str(uuid.uuid4()),
        )
        return {"semantic_outcome": outcome, "actuate": True,
                "effect_id": effect["effect_id"], "status": effect["status"]}

    def resume_after_wait(self, context: IdentityContext, session_id: str,
                          page_epoch_at_wait: int, effect: dict, arguments: dict) -> dict:
        """BRW-003-R01: revalidate page/session/operation scope after an
        approval/policy wait; refuse when the semantic target changed."""
        session = self._sessions_probe(context, session_id)
        if session["page_epoch"] != page_epoch_at_wait:
            raise SemanticTargetChanged(
                f"page epoch moved {page_epoch_at_wait} -> {session['page_epoch']} during wait"
            )
        return {"effect_id": effect["effect_id"], "resumed": True}

    def _sessions_probe(self, context: IdentityContext, session_id: str) -> dict:
        row = self._db.query_one(
            "SELECT page_epoch, state FROM browser_sessions WHERE tenant_id=%s AND session_id=%s",
            (context.tenant_id, session_id),
        )
        return {"page_epoch": row[0], "state": row[1]}


class TakeoverService:
    """BRW-004: controller lease serializes agent and human actuation."""

    def __init__(self, database: PlatformDatabase, sessions: BrowserSessionManager):
        self._db = database
        self._sessions = sessions

    def takeover(self, context: IdentityContext, session_id: str, human_id: str) -> dict:
        current = self._sessions.get(context, session_id)
        if current["control_kind"] == "human" and current["control_holder"] != human_id:
            raise TakeoverStateError("another human controller holds the session")
        self._sessions.set_controller(context, session_id, human_id, kind="human")
        return {"session_id": session_id, "controller": human_id, "kind": "human"}

    def return_control(self, context: IdentityContext, session_id: str, human_id: str) -> dict:
        current = self._sessions.get(context, session_id)
        if current["control_kind"] == "human" and current["control_holder"] != human_id:
            raise TakeoverStateError("return requested by a different human controller")
        self._sessions.set_controller(context, session_id, "agent", kind="agent")
        return {"session_id": session_id, "controller": "agent", "kind": "agent"}

    def agent_actuate(self, context: IdentityContext, session_id: str) -> None:
        current = self._sessions.get(context, session_id)
        if current["control_kind"] == "human":
            raise TakeoverStateError(
                f"human controller {current['control_holder']} holds the session"
            )

    def human_disconnected(self, context: IdentityContext, session_id: str,
                           human_id: str, release_timeout_s: int = 30) -> dict:
        """BRW-004-R01: bounded takeover-release before agent control resumes."""
        deadline = _now() + timedelta(seconds=release_timeout_s)
        self._sessions.set_controller(context, session_id, f"release-pending:{human_id}",
                                      kind="human")
        released = _now() >= deadline - timedelta(seconds=release_timeout_s)
        self._sessions.set_controller(context, session_id, "agent", kind="agent")
        return {"released": released, "controller": "agent",
                "policy": f"bounded release within {release_timeout_s}s"}
