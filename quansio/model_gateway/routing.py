"""Deterministic capability-demand routing (MOD-003).

A route decision selects one enabled model profile from capability demand,
policy allow-list, residency constraints, context size, availability and
budget using a stable, versioned algorithm over a sorted candidate list.
The decision record carries the catalog revision it was computed against;
an admitted step retries against its pinned decision, so catalog changes
between retries cannot silently drift the route.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class NoQualifiedRoute(Exception):
    """No candidate satisfies the hard constraints; no provider call may start."""


ROUTE_ALGORITHM_VERSION = "route-algo/1"


@dataclass(frozen=True)
class ModelProfile:
    profile_id: str
    provider: str
    residency: list[str]
    max_context_tokens: int
    cost_per_1k_tokens_cents: int
    capabilities: list[str]
    enabled: bool


@dataclass(frozen=True)
class RouteDecision:
    route_decision_id: str
    algorithm_version: str
    catalog_version: str
    selected_profile_id: str
    ranked_profile_ids: list[str]
    decided_at: str


class ModelRouter:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def catalog(self, context: IdentityContext) -> tuple[str, list[ModelProfile]]:
        rows = self._db.query_all(
            """
            SELECT entry_id, revision, definition FROM registry_entries
            WHERE tenant_id = %s AND registry = 'model_profile'
            ORDER BY entry_id
            """,
            (context.tenant_id,),
        )
        profiles = []
        for entry_id, _revision, definition in rows:
            profiles.append(
                ModelProfile(
                    profile_id=entry_id,
                    provider=definition.get("provider", "unknown"),
                    residency=definition.get("residency", []),
                    max_context_tokens=int(definition.get("max_context_tokens", 0)),
                    cost_per_1k_tokens_cents=int(definition.get("cost_per_1k_tokens_cents", 0)),
                    capabilities=definition.get("capabilities", []),
                    enabled=bool(definition.get("enabled", False)),
                )
            )
        catalog_version = hashlib.sha256(
            json.dumps([p.__dict__ for p in profiles], sort_keys=True).encode()
        ).hexdigest()[:16]
        return f"catalog-{catalog_version}", profiles

    def route(
        self,
        context: IdentityContext,
        demand: dict,
        policy_allowed_profiles: list[str],
        residency_required: list[str],
        context_tokens: int,
        budget_cents: int,
        availability: dict[str, bool] | None = None,
        catalog_snapshot: tuple[str, list[ModelProfile]] | None = None,
    ) -> RouteDecision:
        """Deterministically select a profile. Hard constraints (policy,
        residency, context, availability, budget) filter candidates; enabled
        profiles are ranked by (capability coverage, cost, stable id)."""
        if catalog_snapshot is None:
            catalog_snapshot = self.catalog(context)
        catalog_version, profiles = catalog_snapshot
        availability = availability or {}
        capable = [c for c in demand.get("dimensions", {}).get("capabilities", [])]
        candidates = []
        for profile in sorted(profiles, key=lambda p: p.profile_id):
            if profile.profile_id not in policy_allowed_profiles:
                continue
            if not profile.enabled:
                continue
            if residency_required and not set(residency_required) <= set(profile.residency):
                continue
            if profile.max_context_tokens < context_tokens:
                continue
            if availability.get(profile.profile_id, True) is False:
                continue
            kilo_tokens = -(-context_tokens // 1000) or 1
            estimated = kilo_tokens * profile.cost_per_1k_tokens_cents * 2
            if estimated > budget_cents:
                continue
            coverage = len(set(capable) & set(profile.capabilities))
            candidates.append((profile, coverage, estimated))
        if not candidates:
            raise NoQualifiedRoute(
                "no model profile satisfies policy/residency/context/availability/budget constraints"
            )
        ranked = sorted(candidates, key=lambda c: (-c[1], c[2], c[0].profile_id))
        selected = ranked[0][0]
        decision = RouteDecision(
            route_decision_id=str(uuid.uuid4()),
            algorithm_version=ROUTE_ALGORITHM_VERSION,
            catalog_version=catalog_version,
            selected_profile_id=selected.profile_id,
            ranked_profile_ids=[c[0].profile_id for c in ranked],
            decided_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO route_decisions
                    (tenant_id, route_decision_id, algorithm_version, catalog_version,
                     selected_profile_id, ranked_profile_ids, inputs_digest)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    context.tenant_id,
                    decision.route_decision_id,
                    decision.algorithm_version,
                    decision.catalog_version,
                    decision.selected_profile_id,
                    Json(decision.ranked_profile_ids),
                    hashlib.sha256(
                        json.dumps(
                            {
                                "demand": demand,
                                "policy": sorted(policy_allowed_profiles),
                                "residency": residency_required,
                                "context_tokens": context_tokens,
                                "budget_cents": budget_cents,
                            },
                            sort_keys=True,
                        ).encode()
                    ).hexdigest(),
                ),
            )
        return decision
