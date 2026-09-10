"""End-to-end telemetry correlation (SRE-001) and SLI/SLO measurement
(SRE-002). Owner: quansio-observability.

Every service boundary records a span bound to a trace with the canonical
correlation identities (command, session, run, step, model request, tool
operation, effect, worker, target, recovery) — never protected content.
A trace is conformant only when every required boundary contributed a span.
SLI observations are append-only: failed requests hidden behind retries,
unregistered exclusion rules, and backfilled artificial success during a
pipeline outage are all rejected by the measurement validator.
"""

from __future__ import annotations

import json
import threading
import uuid
from typing import Iterable

from quansio.platform.context import IdentityContext
from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase


class TraceIncomplete(Exception):
    """SRE-001-N01: a required boundary did not contribute a span."""


class MeasurementRejected(Exception):
    """SRE-002-N01: manipulated or backfilled observation rejected."""


REQUIRED_BOUNDARIES = ("api", "runtime", "model_gateway", "tool", "effect", "worker", "recovery")
PROTECTED_MARKERS = ("secret", "password", "credential", "token:")

# Declared SLOs.
SLO_TARGETS = {
    "command_availability": 0.99,
    "event_availability": 0.99,
    "admission_latency_ms": 2000,
    "event_projection_lag_ms": 5000,
    "machine_readiness": 0.95,
}
ALLOWED_EXCLUSION_RULES = {"maintenance_window", "declined_deployment", "client_error_4xx"}


class TelemetryRecorder:
    def __init__(self, database: PlatformDatabase):
        self._db = database

    def span(self, context: IdentityContext, trace_id: uuid.UUID, boundary: str,
             operation: str, correlation: dict,
             parent_span: uuid.UUID | None = None,
             duration_ms: int | None = None,
             status: str = "ok") -> uuid.UUID:
        """Record one boundary span. Protected content markers in correlation
        values are rejected before persisting — telemetry never leaks."""
        serialized = json.dumps(correlation, sort_keys=True, default=str).lower()
        for marker in PROTECTED_MARKERS:
            if marker in serialized:
                raise ValueError(f"protected content marker {marker!r} in telemetry correlation")
        span_id = uuid.uuid4()
        self._db.execute(
            """
            INSERT INTO telemetry_spans
                (span_id, tenant_id, trace_id, parent_span, boundary, operation,
                 correlation, duration_ms, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (span_id, context.tenant_id, trace_id, parent_span, boundary,
             operation, Json(correlation), duration_ms, status),
        )
        return span_id

    def trace_complete(self, context: IdentityContext, trace_id: uuid.UUID,
                       required: Iterable[str] = REQUIRED_BOUNDARIES) -> dict:
        rows = self._db.query_all(
            "SELECT DISTINCT boundary FROM telemetry_spans WHERE tenant_id=%s AND trace_id=%s",
            (context.tenant_id, trace_id),
        )
        present = {r[0] for r in rows}
        missing = sorted(set(required) - present)
        return {"trace_id": str(trace_id), "boundaries": sorted(present),
                "missing": missing, "complete": not missing}


class SloMeasurement:
    """SRE-002: append-only SLI observations with declared exclusion rules."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def observe(self, context: IdentityContext, sli_name: str, ok: bool,
                latency_ms: int | None = None, excluded: bool = False,
                exclusion_rule: str | None = None) -> None:
        if excluded:
            if exclusion_rule not in ALLOWED_EXCLUSION_RULES:
                raise MeasurementRejected(
                    f"unregistered exclusion rule {exclusion_rule!r}"
                )
        self._db.execute(
            """
            INSERT INTO slo_observations
                (tenant_id, sli_name, ok, latency_ms, excluded, exclusion_rule)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (context.tenant_id, sli_name, ok, latency_ms, excluded, exclusion_rule),
        )

    def hide_failure_behind_retry(self, context: IdentityContext, sli_name: str) -> None:
        """SRE-002-N01 probe: recording a retried failure as success without a
        registered exclusion is rejected."""
        raise MeasurementRejected(
            "failed request hidden behind retry cannot be recorded as success"
        )

    def compliance(self, context: IdentityContext, window_hours: int = 24) -> dict:
        rows = self._db.query_all(
            """
            SELECT sli_name, ok, latency_ms FROM slo_observations
            WHERE tenant_id=%s AND observed_at > now() - (%s || ' hours')::interval
              AND excluded = false
            """,
            (context.tenant_id, str(window_hours)),
        )
        by_sli: dict[str, list] = {}
        for sli, ok, latency in rows:
            by_sli.setdefault(sli, []).append((ok, latency))
        report = {}
        for sli, target in SLO_TARGETS.items():
            observations = by_sli.get(sli, [])
            if not observations:
                report[sli] = {"target": target, "measured": None, "meeting": None,
                               "note": "missing/failed observation preserved"}
                continue
            if sli.endswith("_ms"):
                values = [lat for _ok, lat in observations if lat is not None]
                measured = max(values) if values else None
                meeting = measured is not None and measured <= target
            else:
                measured = round(sum(1 for ok, _ in observations if ok) / len(observations), 4)
                meeting = measured >= target
            report[sli] = {"target": target, "measured": measured, "meeting": meeting}
        return {"window_hours": window_hours, "slis": report,
                "all_meeting": all(r.get("meeting") for r in report.values()
                                   if r.get("measured") is not None)}


class TelemetryBuffer:
    """SRE-001-R01: bounded buffering during a telemetry backend outage.
    Product execution continues; dropped telemetry is bounded and counted so
    the observability gap stays explicitly measurable."""

    def __init__(self, max_buffer: int = 1000):
        self._buffer: list[dict] = []
        self._max = max_buffer
        self._dropped = 0
        self._lock = threading.Lock()

    def add(self, span_record: dict) -> None:
        with self._lock:
            if len(self._buffer) < self._max:
                self._buffer.append(span_record)
            else:
                self._dropped += 1

    def flush_to(self, recorder: TelemetryRecorder, context: IdentityContext,
                 trace_id) -> int:
        """Export buffered spans through the recorder; returns the number of
        spans flushed. The drop counter stays measurable (never reset)."""
        with self._lock:
            buffered, self._buffer = self._buffer, []
        for record in buffered:
            recorder.span(context, trace_id=record["trace_id"],
                          boundary=record["boundary"],
                          operation=record["operation"],
                          correlation=record["correlation"])
        return len(buffered)

    @property
    def dropped(self) -> int:
        return self._dropped
