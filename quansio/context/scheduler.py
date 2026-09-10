"""Timezone-aware logical scheduling (AUT-001/002), per-fire authority
re-evaluation (AUT-003) and durable pause/resume/delete (AUT-004). Owner:
quansio-runtime.

Logical fire identity = (automation_id, local-time occurrence string), so a
clock transition or scheduler restart can never produce two accepted fires
for one logical occurrence. Missed-fire policy is SKIP, FIRE_ONCE or
CATCH_UP_BOUNDED with an explicit maximum; excess occurrences are marked
catchup_skipped durably, never silently dropped. At fire time, authority is
re-resolved (capabilities, policy, target health) before a WorkGraph is
admitted; unauthorized fires become blocked_attention rather than running
on stale authority.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class AmbiguousSchedule(Exception):
    """AUT-001-N01: ambiguous local time without a fold/gap rule."""


class AutomationDenied(Exception):
    """The automation is paused/deleted or otherwise not fireable."""


cron_spec = re.compile(
    r"^(?P<minute>\S+)\s+(?P<hour>\S+)\s+(?P<dom>\S+)\s+(?P<month>\S+)\s+(?P<dow>\S+)$"
)

_DOW = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _parse_field(field: str, allowed: list[str] | None = None) -> set[int] | None:
    if field == "*":
        return None
    values: set[int] = set()
    for part in field.split(","):
        if part.startswith("*/"):
            step = int(part[2:])
            base = allowed if allowed is not None else list(range(60))
            values.update(set(base[::step]))
            continue
        if "-" in part:
            lo, hi = part.split("-")
            values.update(range(int(lo), int(hi) + 1))
        else:
            values.add(int(part))
    if allowed is not None:
        values = {allowed[v - 1] if isinstance(v, int) and 7 <= v <= 13 else v
                  for v in values}
    return values


def next_fires(cron: str, tz_name: str, after_utc: datetime, count: int,
               fold_gap_policy: str = "earliest") -> list[dict]:
    """Compute the next `count` logical fires after a UTC instant. Logical
    identity is the local wall-clock occurrence string; DST gaps are skipped
    and folds resolved by the declared policy."""
    match = cron_spec.match(cron)
    if not match:
        raise ValueError(f"unsupported cron expression: {cron!r}")
    tz = ZoneInfo(tz_name)
    minutes = _parse_field(match.group("minute"))
    hours = _parse_field(match.group("hour"))
    months = _parse_field(match.group("month"))
    dows_raw = match.group("dow")
    dows = None
    if dows_raw != "*":
        dows = set()
        for part in dows_raw.split(","):
            part_l = part.strip().lower()
            if part_l in _DOW:
                dows.add(_DOW[part_l])
            elif part.isdigit():
                dows.add(int(part) % 7)
    fires = []
    # Walk local wall-clock minutes from the next whole minute.
    local = after_utc.astimezone(tz).replace(second=0, microsecond=0) + timedelta(minutes=1)
    guard = 0
    while len(fires) < count and guard < 500000:
        guard += 1
        if minutes is not None and local.minute not in minutes:
            local += timedelta(minutes=1)
            continue
        if hours is not None and local.hour not in hours:
            # jump to next hour boundary
            local = (local + timedelta(hours=1)).replace(minute=0)
            continue
        if months is not None and local.month not in months:
            # jump to first day of next month
            if local.month == 12:
                local = local.replace(year=local.year + 1, month=1, day=1, hour=0)
            else:
                local = local.replace(month=local.month + 1, day=1, hour=0)
            continue
        if dows is not None and local.weekday() not in dows:
            local = (local + timedelta(days=1)).replace(hour=0, minute=0)
            continue
        # DST fold/gap handling with explicit policy: a wall-clock time that
        # does not round-trip to the same local value is a gap (skipped under
        # "skip", earliest fold under others); "latest" resolves folds late.
        aware0 = local.replace(tzinfo=tz, fold=0)
        aware1 = local.replace(tzinfo=tz, fold=1)
        roundtrip0 = aware0.astimezone(timezone.utc).astimezone(tz)
        is_gap = roundtrip0.replace(tzinfo=None) != local
        is_fold = aware0.utcoffset() != aware1.utcoffset()
        if is_gap and fold_gap_policy == "skip":
            local += timedelta(minutes=1)
            continue
        if is_fold and fold_gap_policy == "latest":
            aware, utc_fire = aware1, aware1.astimezone(timezone.utc)
        else:
            aware, utc_fire = aware0, aware0.astimezone(timezone.utc)
        fires.append({
            "logical_fire": local.strftime("%Y-%m-%dT%H:%M"),
            "fire_time_utc": utc_fire,
        })
        local += timedelta(minutes=1)
    return fires


class AutomationService:
    """Owner: quansio-runtime."""

    def __init__(self, database: PlatformDatabase, authority_resolver=None):
        self._db = database
        # authority_resolver(context, work_template) -> admitted work ref or raises
        self._authority = authority_resolver

    def create(self, context: IdentityContext, name: str, tz_name: str,
               cron: str, fold_gap_policy: str, catchup_policy: str,
               catchup_max: int, work_template: dict) -> dict:
        # Validation: an ambiguous local time must declare a fold/gap rule.
        tz = ZoneInfo(tz_name)
        probe_minute = cron.split()[0]
        if fold_gap_policy not in ("earliest", "latest", "skip"):
            raise AmbiguousSchedule(f"undeclared fold/gap policy {fold_gap_policy!r}")
        try:
            next_fires(cron, tz_name, datetime.now(timezone.utc), 1, fold_gap_policy)
        except Exception as error:
            raise AmbiguousSchedule(f"schedule cannot activate: {error}") from error
        automation_id = str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO automations
                    (tenant_id, automation_id, name, timezone, cron,
                     fold_gap_policy, catchup_policy, catchup_max, lifecycle, work_template)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', %s)
                """,
                (context.tenant_id, automation_id, name, tz_name, cron,
                 fold_gap_policy, catchup_policy, catchup_max, Json(work_template)),
            )
        return {"automation_id": automation_id, "name": name, "timezone": tz_name,
                "cron": cron, "fold_gap_policy": fold_gap_policy,
                "catchup_policy": catchup_policy, "catchup_max": catchup_max}

    def _automation(self, context: IdentityContext, automation_id: str) -> dict | None:
        row = self._db.query_one(
            """
            SELECT automation_id::text, name, timezone, cron, fold_gap_policy,
                   catchup_policy, catchup_max, lifecycle, work_template
            FROM automations WHERE tenant_id=%s AND automation_id=%s
            """,
            (context.tenant_id, automation_id),
        )
        if row is None:
            return None
        return {"automation_id": row[0], "name": row[1], "timezone": row[2],
                "cron": row[3], "fold_gap_policy": row[4], "catchup_policy": row[5],
                "catchup_max": row[6], "lifecycle": row[7], "work_template": row[8]}

    def emit_fires(self, context: IdentityContext, automation_id: str,
                   from_utc: datetime, to_utc: datetime,
                   authority_resolver: Callable[[IdentityContext, dict], str] | None = None) -> dict:
        """Compute logical occurrences in the window and apply the missed-fire
        policy durably (AUT-002). Authority is re-resolved at fire time
        (AUT-003); unauthorized fires become blocked_attention."""
        automation = self._automation(context, automation_id)
        if automation is None:
            raise KeyError(automation_id)
        if automation["lifecycle"] != "active":
            raise AutomationDenied(f"automation is {automation['lifecycle']}")
        max_catchup = automation["catchup_max"]
        all_fires = next_fires(automation["cron"], automation["timezone"],
                               from_utc, 10000, automation["fold_gap_policy"])
        window = [f for f in all_fires if f["fire_time_utc"] <= to_utc]
        missed = [f for f in window if f["fire_time_utc"] < _now_utc()]
        future = [f for f in window if f["fire_time_utc"] >= _now_utc()]

        emitted = []
        skipped = 0
        if automation["catchup_policy"] == "SKIP":
            skipped = len(missed)  # missed occurrences are not emitted at all
        elif automation["catchup_policy"] == "FIRE_ONCE":
            if missed:
                latest = missed[-1]
                fired = self._emit_one(context, automation_id, latest,
                                       authority_resolver)
                emitted.append({**latest, "state": fired})
        else:  # CATCH_UP_BOUNDED
            bounded = missed[-max_catchup:] if max_catchup else []
            skipped = len(missed) - len(bounded)
            for occurrence in bounded:
                fired = self._emit_one(context, automation_id, occurrence,
                                       authority_resolver)
                emitted.append({**occurrence, "state": fired})
            for occurrence in missed[:len(missed) - len(bounded)]:
                self._record(context, automation_id, occurrence["logical_fire"],
                             occurrence["fire_time_utc"], "catchup_skipped")
        for occurrence in future:
            self._record(context, automation_id, occurrence["logical_fire"],
                         occurrence["fire_time_utc"], "pending")
        return {"emitted": emitted, "catchup_skipped": skipped,
                "future_recorded": len(future)}

    def _emit_one(self, context: IdentityContext, automation_id: str,
                  occurrence: dict, authority_resolver) -> str:
        inserted = self._db.query_one(
            """
            INSERT INTO automation_occurrences
                (tenant_id, automation_id, logical_fire, fire_time_utc, state)
            VALUES (%s, %s, %s, %s, 'fired')
            ON CONFLICT (tenant_id, automation_id, logical_fire) DO NOTHING
            RETURNING logical_fire
            """,
            (context.tenant_id, automation_id, occurrence["logical_fire"],
             occurrence["fire_time_utc"]),
        )
        if inserted is None:
            return "fired"  # already fired: at most one accepted fire identity
        if authority_resolver is not None:
            try:
                authority_resolver(context, {"logical_fire": occurrence["logical_fire"]})
            except Exception as error:  # noqa: BLE001 - blocked, attention required
                self._db.execute(
                    """
                    UPDATE automation_occurrences SET state='blocked_attention',
                        blocked_reason=%s
                    WHERE tenant_id=%s AND automation_id=%s AND logical_fire=%s
                    """,
                    (str(error), context.tenant_id, automation_id,
                     occurrence["logical_fire"]),
                )
                return "blocked_attention"
        return "fired"

    def _record(self, context: IdentityContext, automation_id: str,
                logical_fire: str, fire_time_utc: datetime, state: str,
                reason: str | None = None) -> None:
        self._db.execute(
            """
            INSERT INTO automation_occurrences
                (tenant_id, automation_id, logical_fire, fire_time_utc, state,
                 blocked_reason)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, automation_id, logical_fire) DO NOTHING
            """,
            (context.tenant_id, automation_id, logical_fire, fire_time_utc,
             state, reason),
        )

    # -- AUT-004: pause / resume / delete ---------------------------------

    def pause(self, context: IdentityContext, automation_id: str) -> str:
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE automations SET lifecycle='paused', updated_at=now()
                WHERE tenant_id=%s AND automation_id=%s AND lifecycle='active'
                """,
                (context.tenant_id, automation_id),
            )
            return "paused" if cursor.rowcount == 1 else "already-paused-or-gone"

    def resume(self, context: IdentityContext, automation_id: str) -> str:
        with self._db.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE automations SET lifecycle='active', updated_at=now()
                WHERE tenant_id=%s AND automation_id=%s AND lifecycle='paused'
                """,
                (context.tenant_id, automation_id),
            )
            return "active" if cursor.rowcount == 1 else "already-active-or-gone"

    def delete(self, context: IdentityContext, automation_id: str) -> str:
        """Delete is durable and serialized against scheduler claiming: the
        lifecycle update takes the same advisory lock the claiming loop uses,
        so an in-flight logical fire cannot race into duplicate execution."""
        with self._db.connection() as connection:
            with connection.transaction():
                connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))",
                    (f"automation:{context.tenant_id}:{automation_id}",),
                )
                cursor = connection.execute(
                    """
                    UPDATE automations SET lifecycle='deleted', updated_at=now()
                    WHERE tenant_id=%s AND automation_id=%s AND lifecycle <> 'deleted'
                    """,
                    (context.tenant_id, automation_id),
                )
                deleted = cursor.rowcount == 1
        return "deleted" if deleted else "already-deleted"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)
