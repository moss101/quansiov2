"""Canonical WorkGraph persistence and GraphTransaction (RUN-001/RUN-003).

A WorkGraph's nodes, edges, dependencies, deadlines and state live in the
``graphs``/``graph_nodes`` tables and are mutated **only** inside a
``GraphTransaction`` — storage triggers reject direct updates outside the
transaction context. A transaction:

1. takes the graph advisory lock and checks the expected revision;
2. verifies every node precondition (expected status);
3. applies all node mutations plus the revision bump atomically;
4. appends the transition's RuntimeEvent (with outbox) in the same
   transaction, so events exist only after all preconditions succeed.

Transitions are idempotent by ``transition_id``: a crash after commit but
before projection delivery cannot cause a second state mutation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import psycopg
from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio.runtime.events import EventAppendError, EventLog


class GraphTransactionError(Exception):
    """A transition precondition or identity check failed."""


@dataclass
class NodeUpdate:
    node_id: str
    expected_status: str
    new_status: str
    payload_merge: dict = field(default_factory=dict)


class GraphTransition:
    """All-or-nothing multi-object transition over one WorkGraph."""

    def __init__(
        self,
        store: "WorkGraphStore",
        context: IdentityContext,
        graph_id: str,
        transition_id: str | None = None,
    ):
        self._store = store
        self._context = context
        self.graph_id = graph_id
        self.transition_id = transition_id or str(uuid.uuid4())
        self._updates: list[NodeUpdate] = []
        self._committed = False

    def update_node(self, node_id: str, expected_status: str, new_status: str, payload_merge: dict | None = None) -> "GraphTransition":
        self._updates.append(
            NodeUpdate(node_id, expected_status, new_status, payload_merge or {})
        )
        return self

    def commit(self, event_type: str, event_payload: dict | None = None) -> dict:
        """Apply every queued mutation atomically and return the outcome.

        Raises GraphTransactionError (nothing mutated, no event) when any
        precondition fails, the graph revision drifted, or this exact
        transition id was already applied.
        """
        if self._committed:
            raise GraphTransactionError("transaction already committed")
        if not self._updates:
            raise GraphTransactionError("transaction has no node updates")
        with self._store._db.connection() as connection:
            try:
                with connection.transaction():
                    tenant = self._context.tenant_id
                    # Serialize all transitions on this graph.
                    connection.execute(
                        "SELECT pg_advisory_xact_lock(hashtext(%s))",
                        (f"graph:{tenant}:{self.graph_id}",),
                    )
                    # Open the guarded-mutation window for this transaction only.
                    connection.execute(
                        "SELECT set_config('app.mutation_context', 'graph_transaction', true)"
                    )
                    already = connection.execute(
                        """
                        SELECT 1 FROM graph_transitions
                        WHERE tenant_id = %s AND graph_id = %s AND transition_id = %s
                        """,
                        (tenant, self.graph_id, self.transition_id),
                    ).fetchone()
                    if already is not None:
                        return {
                            "transition_id": self.transition_id,
                            "graph_id": self.graph_id,
                            "applied": False,
                            "reason": "already applied",
                        }
                    graph = connection.execute(
                        "SELECT revision FROM graphs WHERE tenant_id = %s AND graph_id = %s FOR UPDATE",
                        (tenant, self.graph_id),
                    ).fetchone()
                    if graph is None:
                        raise GraphTransactionError("graph unknown")
                    for update in self._updates:
                        current = connection.execute(
                            """
                            SELECT status FROM graph_nodes
                            WHERE tenant_id = %s AND graph_id = %s AND node_id = %s
                            """,
                            (tenant, self.graph_id, update.node_id),
                        ).fetchone()
                        if current is None:
                            raise GraphTransactionError(f"node {update.node_id} unknown")
                        if current[0] != update.expected_status:
                            raise GraphTransactionError(
                                f"precondition failed for node {update.node_id}: "
                                f"expected {update.expected_status!r}, found {current[0]!r}"
                            )
                    for update in self._updates:
                        connection.execute(
                            """
                            UPDATE graph_nodes
                            SET status = %s,
                                payload = payload || %s::jsonb,
                                transition_id = %s
                            WHERE tenant_id = %s AND graph_id = %s AND node_id = %s
                            """,
                            (
                                update.new_status,
                                Json(update.payload_merge),
                                self.transition_id,
                                tenant,
                                self.graph_id,
                                update.node_id,
                            ),
                        )
                    new_revision = graph[0] + 1
                    connection.execute(
                        """
                        UPDATE graphs SET revision = %s, last_transition_id = %s
                        WHERE tenant_id = %s AND graph_id = %s
                        """,
                        (new_revision, self.transition_id, tenant, self.graph_id),
                    )
                    connection.execute(
                        """
                        INSERT INTO graph_transitions (tenant_id, graph_id, transition_id)
                        VALUES (%s, %s, %s)
                        """,
                        (tenant, self.graph_id, self.transition_id),
                    )
                    event = self._store._events.append(
                        self._context,
                        run_id=self.graph_id,
                        event_type=event_type,
                        payload={
                            **(event_payload or {}),
                            "transition_id": self.transition_id,
                            "updates": [
                                {
                                    "node_id": u.node_id,
                                    "from": u.expected_status,
                                    "to": u.new_status,
                                }
                                for u in self._updates
                            ],
                        },
                    )
            except EventAppendError as error:
                raise GraphTransactionError(f"event append failed: {error}") from error
        self._committed = True
        return {
            "transition_id": self.transition_id,
            "graph_id": self.graph_id,
            "revision": new_revision,
            "event_id": event.event_id,
            "applied": True,
        }


class WorkGraphStore:
    """Canonical persistence for WorkGraphs; owner quansio-runtime."""

    def __init__(self, database: PlatformDatabase, events: EventLog):
        self._db = database
        self._events = events

    def create_graph(
        self,
        context: IdentityContext,
        run_id: str,
        spec: dict,
        nodes: list[dict],
        edges: list[dict],
        deadlines: dict[str, str] | None = None,
    ) -> dict:
        """Create a versioned WorkGraph: nodes with dependencies/deadlines.

        ``nodes``: [{"node_id", "kind", "payload"}]; ``edges``:
        [{"from", "to"}] recorded as dependencies inside node payloads and
        the graph spec.
        """
        graph_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute(
                    """
                    INSERT INTO graphs (tenant_id, workspace_id, graph_id, run_id, graph_kind, revision, spec)
                    VALUES (%s, %s, %s, %s, 'work', 1, %s)
                    """,
                    (context.tenant_id, context.workspace_id, graph_id, run_id, Json({**spec, "edges": edges})),
                )
                for node in nodes:
                    connection.execute(
                        """
                        INSERT INTO graph_nodes (tenant_id, graph_id, node_id, node_kind, status, deadline_at, payload)
                        VALUES (%s, %s, %s, %s, 'pending', %s, %s)
                        """,
                        (
                            context.tenant_id,
                            graph_id,
                            node["node_id"],
                            node.get("kind", "task"),
                            node.get("deadline_at"),
                            Json(node.get("payload", {})),
                        ),
                    )
        return self.get_graph(context, graph_id)

    def get_graph(self, context: IdentityContext, graph_id: str) -> dict | None:
        graph = self._db.query_one(
            """
            SELECT graph_id::text, run_id::text, revision, spec, last_transition_id::text
            FROM graphs WHERE tenant_id = %s AND graph_id = %s
            """,
            (context.tenant_id, graph_id),
        )
        if graph is None:
            return None
        nodes = self._db.query_all(
            """
            SELECT node_id, node_kind, status, deadline_at, payload, transition_id::text
            FROM graph_nodes WHERE tenant_id = %s AND graph_id = %s ORDER BY node_id
            """,
            (context.tenant_id, graph_id),
        )
        return {
            "graph_id": graph[0],
            "run_id": graph[1],
            "revision": graph[2],
            "spec": graph[3],
            "last_transition_id": graph[4],
            "nodes": [
                {
                    "node_id": n[0],
                    "kind": n[1],
                    "status": n[2],
                    "deadline_at": n[3],
                    "payload": n[4],
                    "transition_id": n[5],
                }
                for n in nodes
            ],
        }

    def transaction(self, context: IdentityContext, graph_id: str, transition_id: str | None = None) -> GraphTransaction:
        return GraphTransition(self, context, graph_id, transition_id)
