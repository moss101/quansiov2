"""ModelGateway facade: the exclusive model fulfillment boundary (MOD-001).

All production model fulfillment flows through :meth:`ModelGateway.fulfill`.
Provider credentials exist only inside this package (``credentials.py``).
Fulfillment is restart-safe: every admitted request is durable, and a
gateway restart during an admitted/streaming request resolves it to a typed
interruption outcome with retry semantics — credential custody never moves.

Fulfillment pipeline per request:

1. route decision (pinned to its catalog revision for retries),
2. privacy classification before egress (allow/redact/deny; fail closed),
3. usage reservation against the parent run budget,
4. adapter stream on a worker thread through a bounded channel
   (backpressure), validated into the canonical event contract,
5. terminal handling: completion settlement, cancellation settlement, or
   typed failure with policy-allowed failover.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Iterator

from psycopg.types.json import Json

from quansio.model_gateway.adapters import (
    CanonicalRequest,
    ProviderAdapter,
    ProviderProtocolFailure,
    ProviderUnreachable,
    adapter_for,
)
from quansio.model_gateway.credentials import load_credentials
from quansio.model_gateway.failover import (
    EffectBoundaryCommitted,
    FailoverCoordinator,
    ProviderHealth,
    classify_failure,
)
from quansio.model_gateway.privacy import ModelPrivacyGate, PrivacyDenied, PrivacyFailClosed
from quansio.model_gateway.routing import ModelRouter, NoQualifiedRoute
from quansio.model_gateway.streaming import (
    InvalidStream,
    BoundedEventChannel,
    validated_stream,
)
from quansio.model_gateway.usage import ModelUsageLedger
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase
from quansio.runtime.orchestration import BudgetLedger
from quansio_contracts import ModelEvent as ModelEventContract


class GatewayError(Exception):
    """Gateway-level fulfillment failure."""


class ModelGateway:
    def __init__(self, database: PlatformDatabase):
        self._db = database
        self._router = ModelRouter(database)
        self._privacy = ModelPrivacyGate(database)
        self._budget = BudgetLedger(database)
        self._usage = ModelUsageLedger(database, self._budget)
        self._health = ProviderHealth(database)
        self._failover = FailoverCoordinator(database, self._health)

    # -- admission ---------------------------------------------------------

    def admit(
        self,
        context: IdentityContext,
        run_id: str,
        step_id: str,
        demand: dict,
        messages: list[dict],
        policy_allowed_profiles: list[str],
        required_residency: list[str],
        context_tokens: int,
        budget_cents: int,
        sampling: dict | None = None,
        catalog_snapshot: tuple[str, list] | None = None,
    ) -> dict:
        """Route, classify, reserve and persist the admitted request.

        Returns the canonical ``ModelRequestEnvelope`` fields for the
        admitted request. Nothing has been sent to any provider yet.
        """
        try:
            decision = self._router.route(
                context, demand, policy_allowed_profiles, required_residency,
                context_tokens, budget_cents, catalog_snapshot=catalog_snapshot,
            )
        except NoQualifiedRoute:
            raise
        privacy_decision, outbound_messages = self._privacy.decide(
            context, request_id=str(uuid.uuid4()), destination_profile=decision.selected_profile_id,
            messages=messages, required_residency=required_residency,
            destination_residency=self._profile_residency(context, decision.selected_profile_id, catalog_snapshot),
        )
        request_id = str(uuid.uuid4())
        reservation = self._usage.reserve(
            context, parent_run_id=run_id, request_id=request_id,
            amount_cents=max(budget_cents // 4, 1), worker_generation=1,
        )
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO model_requests
                    (tenant_id, request_id, run_id, step_id, model_profile_id,
                     route_decision_id, usage_reservation_id, state)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'admitted')
                """,
                (context.tenant_id, request_id, run_id, step_id,
                 decision.selected_profile_id, decision.route_decision_id,
                 reservation["reservation_id"]),
            )
        return {
            "schema_revision": "9.0.0",
            "request_id": request_id,
            "tenant_id": context.tenant_id,
            "workspace_id": context.workspace_id,
            "run_id": run_id,
            "step_id": step_id,
            "execution_generation": 1,
            "route_decision_id": decision.route_decision_id,
            "model_profile_id": decision.selected_profile_id,
            "capability_snapshot_id": str(uuid.uuid4()),
            "context_projection_id": str(uuid.uuid4()),
            "usage_reservation_id": reservation["reservation_id"],
            "privacy_decision_id": privacy_decision.privacy_decision_id,
            "residency_policy_id": decision.catalog_version,
            "stream_id": str(uuid.uuid4()),
            "cancellation_id": str(uuid.uuid4()),
            "messages": outbound_messages,
            "sampling": sampling or {"temperature": 0.2},
            "trace_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _profile_residency(self, context: IdentityContext, profile_id: str, catalog_snapshot) -> list[str]:
        _version, profiles = catalog_snapshot or self._router.catalog(context)
        for profile in profiles:
            if profile.profile_id == profile_id:
                return profile.residency
        return []

    # -- fulfillment ---------------------------------------------------------

    def fulfill(self, context: IdentityContext, envelope: dict,
                policy_allowed_profiles: list[str] | None = None) -> Iterator[ModelEventContract]:
        """Stream canonical ModelEvents for an admitted request.

        Handles typed failure outcomes and policy-allowed failover. A
        committed effect boundary (a TOOL_PROPOSAL flagged committed by the
        consumer via :meth:`mark_effect_boundary`) disables further failover.
        """
        request_id = envelope["request_id"]
        run_id = envelope["run_id"]
        policy_allowed_profiles = policy_allowed_profiles or [envelope["model_profile_id"]]
        effect_boundary = {"committed": False}

        _catalog_version, profiles = self._router.catalog(context)
        ranked = [p.profile_id for p in profiles if p.profile_id in policy_allowed_profiles]
        failed: set[str] = set()
        candidate = envelope["model_profile_id"]

        while candidate is not None:
            try:
                adapter = adapter_for(load_credentials(candidate))
            except Exception as error:  # noqa: BLE001 - adapter/config unavailability is typed
                failed_event = self._synthetic_event(envelope, "MODEL_FAILED", {
                    "outcome": "adapter_unavailable",
                    "detail": str(error),
                })
                self._persist_event(context, request_id, failed_event)
                self._mark_request(context, request_id, "failed")
                yield failed_event
                return
            channel: BoundedEventChannel = BoundedEventChannel(maxsize=4)
            outbound_capture: list[bytes] = []
            canonical_request = CanonicalRequest(
                request_id=request_id,
                model_profile_id=candidate,
                messages=envelope["messages"],
                sampling=envelope.get("sampling") or {},
                trace_id=envelope.get("trace_id", ""),
            )

            def _produce(adapter=adapter, canonical_request=canonical_request, channel=channel, capture=outbound_capture):
                try:
                    for event in adapter.stream(canonical_request, outbound_capture=capture):
                        if not channel.put(event):
                            return
                except (ProviderProtocolFailure, ProviderUnreachable) as error:
                    channel.put_error(error)
                finally:
                    channel.close()

            worker = threading.Thread(target=_produce, daemon=True)
            worker.start()

            terminal_from_adapter = None
            failure = None
            try:
                for event in self._validated_channel_stream(channel):
                    if event.event_type == "TOOL_PROPOSAL" and event.payload.get("committed"):
                        effect_boundary["committed"] = True
                    self._persist_event(context, request_id, event)
                    yield event
                    if event.event_type in ("MODEL_COMPLETED", "MODEL_CANCELLED", "MODEL_FAILED"):
                        terminal_from_adapter = event
                        break
            except InvalidStream:
                failure = ("malformed_response", "invalid canonical stream normalized to failure")
            except ProviderUnreachable as error:
                failure = (classify_failure(error), str(error))
            except ProviderProtocolFailure as error:
                failure = (classify_failure(error), str(error))

            channel.cancel()

            if terminal_from_adapter is not None:
                self._mark_request(context, request_id,
                                   "completed" if terminal_from_adapter.event_type == "MODEL_COMPLETED" else "cancelled"
                                   if terminal_from_adapter.event_type == "MODEL_CANCELLED" else "failed")
                usage = terminal_from_adapter.payload.get("usage")
                if usage:
                    self._usage.apply_final_usage(
                        context, run_id, request_id, envelope["usage_reservation_id"], usage,
                        cancelled=terminal_from_adapter.event_type == "MODEL_CANCELLED",
                    )
                return

            kind, detail = failure if failure else ("provider_outage", "adapter stream ended without terminal")
            self._failover.record_failure(context, candidate, kind, detail)
            try:
                candidate = self._failover.failover_candidate(
                    context, ranked, candidate, policy_allowed_profiles,
                    effect_boundary_committed=effect_boundary["committed"],
                    adapters={},
                )
            except EffectBoundaryCommitted as error:
                failed_event = self._synthetic_event(envelope, "MODEL_FAILED", {
                    "outcome": "failover_forbidden_after_effect_boundary",
                    "detail": str(error),
                })
                self._persist_event(context, request_id, failed_event)
                self._mark_request(context, request_id, "failed")
                yield failed_event
                return
            if candidate is None:
                failed_event = self._synthetic_event(envelope, "MODEL_FAILED", {
                    "outcome": f"all candidates exhausted ({kind})",
                    "detail": detail,
                })
                self._persist_event(context, request_id, failed_event)
                self._mark_request(context, request_id, "failed")
                yield failed_event
                return

    # -- streaming helpers ---------------------------------------------------

    def _validated_channel_stream(self, channel: BoundedEventChannel) -> Iterator[ModelEventContract]:
        def raw():
            while True:
                item = channel.get(timeout=30)
                if item is None:
                    return
                if isinstance(item, Exception):
                    raise item
                yield item

        yield from validated_stream(raw())

    def _persist_event(self, context: IdentityContext, request_id: str, event: ModelEventContract) -> None:
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO model_events (tenant_id, request_id, sequence, event_id, event_type, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, request_id, sequence) DO NOTHING
                """,
                (context.tenant_id, request_id, event.sequence, event.event_id,
                 event.event_type, Json(event.payload)),
            )

    def _synthetic_event(self, envelope: dict, event_type: str, payload: dict) -> ModelEventContract:
        from quansio.model_gateway.adapters import _event

        request = CanonicalRequest(
            request_id=envelope["request_id"],
            model_profile_id=envelope["model_profile_id"],
            messages=[], sampling={}, trace_id=envelope.get("trace_id", ""),
        )
        return _event(request, 10**6, event_type, payload)

    def _mark_request(self, context: IdentityContext, request_id: str, state: str) -> None:
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE model_requests SET state = %s, updated_at = now() WHERE tenant_id = %s AND request_id = %s",
                (state, context.tenant_id, request_id),
            )

    # -- restart and interruption ---------------------------------------------

    def recover_after_restart(self, context: IdentityContext) -> list[dict]:
        """MOD-001-R01: requests admitted/streaming when the gateway died
        resolve to a typed interruption outcome; reservations stay bound to
        this request so retries reconcile without credential transfer."""
        rows = self._db.query_all(
            """
            SELECT request_id::text, state, usage_reservation_id::text FROM model_requests
            WHERE tenant_id = %s AND state IN ('admitted', 'streaming')
            """,
            (context.tenant_id,),
        )
        outcomes = []
        for request_id, state, reservation_id in rows:
            with self._db.connection() as connection:
                connection.execute(
                    "UPDATE model_requests SET state = 'interrupted', updated_at = now() WHERE tenant_id = %s AND request_id = %s",
                    (context.tenant_id, request_id),
                )
            outcomes.append({
                "request_id": request_id,
                "previous_state": state,
                "outcome": "retryable_interruption",
                "usage_reservation_id": reservation_id,
            })
        return outcomes
