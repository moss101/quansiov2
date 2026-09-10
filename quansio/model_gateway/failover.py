"""Provider failure isolation and failover (MOD-007).

Timeouts, rate limits, malformed responses and outages become typed
outcomes. Failover happens only to policy-allowed candidates and never
after an effect boundary (a committed tool proposal) — replaying a
committed external effect through a second provider is forbidden. A failed
provider leaves the health registry as down; re-entry to routable state
requires a fresh successful probe.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
from psycopg.types.json import Json

from quansio.model_gateway.adapters import (
    ProviderAdapter,
    ProviderProtocolFailure,
    ProviderUnreachable,
)
from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class EffectBoundaryCommitted(Exception):
    """Failover was requested after a committed effect boundary."""


class TypedOutcome:
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    MALFORMED = "malformed_response"
    OUTAGE = "provider_outage"
    PROTOCOL = "protocol_failure"


def classify_failure(error: Exception) -> str:
    if isinstance(error, ProviderUnreachable):
        text = error.reason.lower()
        if "rate limit" in text or "429" in text:
            return TypedOutcome.RATE_LIMIT
        if "timeout" in text:
            return TypedOutcome.TIMEOUT
        return TypedOutcome.OUTAGE
    if isinstance(error, ProviderProtocolFailure):
        return TypedOutcome.MALFORMED if "malformed" in error.reason else TypedOutcome.PROTOCOL
    return TypedOutcome.PROTOCOL


class ProviderHealth:
    """Health registry with fresh-probe re-entry (MOD-007-R01)."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def state(self, context: IdentityContext, profile_id: str) -> str:
        row = self._db.query_one(
            "SELECT state FROM provider_health WHERE tenant_id = %s AND profile_id = %s",
            (context.tenant_id, profile_id),
        )
        return row[0] if row else "healthy"

    def mark(self, context: IdentityContext, profile_id: str, state: str, reason: str) -> None:
        if state not in ("healthy", "suspect", "down"):
            raise ValueError(state)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO provider_health (tenant_id, profile_id, state, reason, probed_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (tenant_id, profile_id)
                DO UPDATE SET state = EXCLUDED.state, reason = EXCLUDED.reason, probed_at = now()
                """,
                (context.tenant_id, profile_id, state, reason),
            )

    def probe_for_reentry(self, context: IdentityContext, profile_id: str, adapter: ProviderAdapter) -> bool:
        """A down provider becomes routable only through a fresh successful
        probe; a failed probe keeps it down."""
        try:
            ok = adapter.probe()
        except Exception:  # noqa: BLE001 - any probe failure keeps the provider down
            ok = False
        self.mark(context, profile_id, "healthy" if ok else "down",
                  "fresh probe on re-entry attempt")
        return ok

    def routable(self, context: IdentityContext, profile_id: str) -> bool:
        return self.state(context, profile_id) != "down"


class FailoverCoordinator:
    def __init__(self, database: PlatformDatabase, health: ProviderHealth):
        self._db = database
        self._health = health

    def record_failure(self, context: IdentityContext, profile_id: str, kind: str, detail: str) -> None:
        self._health.mark(context, profile_id, "down" if kind in (TypedOutcome.OUTAGE, TypedOutcome.TIMEOUT, TypedOutcome.RATE_LIMIT) else "suspect", detail)
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO provider_failures (tenant_id, profile_id, kind, detail)
                VALUES (%s, %s, %s, %s)
                """,
                (context.tenant_id, profile_id, kind, detail),
            )

    def failover_candidate(self, context: IdentityContext, decision_ranked: list[str], failed_profile: str,
                           policy_allowed_profiles: list[str], effect_boundary_committed: bool,
                           adapters: dict[str, ProviderAdapter] | None = None) -> str | None:
        """Pick the next allowed, routable candidate; refuse after a
        committed effect boundary (never replay committed effects)."""
        if effect_boundary_committed:
            raise EffectBoundaryCommitted(
                "failover after a committed tool-proposal effect boundary is forbidden"
            )
        for candidate in decision_ranked:
            if candidate == failed_profile or candidate not in policy_allowed_profiles:
                continue
            if not self._health.routable(context, candidate):
                continue
            return candidate
        return None
