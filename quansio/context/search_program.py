"""Typed, bounded SearchProgram (CTX-001).

A SearchProgram is an ordered list of operator steps with typed, declarative
arguments. Validation happens entirely before execution: unknown operators,
executable predicate text, fan-out above 1000, iteration above 20, or
non-declarative filter arguments fail validation and nothing runs. Operator
outputs are persisted per (program, step, input digest), so a restart
resumes from durable outputs instead of repeating completed retrieval steps.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from psycopg.types.json import Json

from quansio.platform.context import IdentityContext
from quansio.platform.db import PlatformDatabase

ALLOWED_OPERATORS = {
    "SEARCH", "RETRIEVE", "FAN_OUT", "FILTER", "RANK", "DEDUPLICATE",
    "JOIN", "EXTRACT", "RESOLVE_ENTITY", "VERIFY", "ITERATE", "SYNTHESIZE",
}
MAX_FAN_OUT = 1000
MAX_ITERATIONS = 20

_EXECUTABLE_TEXT = re.compile(
    r"\b(lambda\s|eval\(|exec\(|__import__|def\s|os\.system|subprocess)"
)


class ProgramValidationError(Exception):
    """The program is invalid; nothing was executed."""


@dataclass
class Step:
    operator: str
    arguments: dict = field(default_factory=dict)


@dataclass
class CompiledProgram:
    program_id: str
    steps: list[Step]
    max_fan_out: int = 100
    max_iterations: int = 5
    time_budget_seconds: float = 120.0

    def digest(self) -> str:
        material = json.dumps(
            [{"op": s.operator, "args": s.arguments} for s in self.steps],
            sort_keys=True,
        )
        return hashlib.sha256(material.encode()).hexdigest()


def parse_program(spec: dict) -> CompiledProgram:
    """Validate a program spec; raise ProgramValidationError on any violation."""
    if not isinstance(spec, dict):
        raise ProgramValidationError("program spec must be an object")
    steps_raw = spec.get("steps")
    if not isinstance(steps_raw, list) or not steps_raw:
        raise ProgramValidationError("program requires a non-empty steps list")
    max_fan_out = int(spec.get("max_fan_out", 100))
    max_iterations = int(spec.get("max_iterations", 5))
    if max_fan_out > MAX_FAN_OUT:
        raise ProgramValidationError(f"fan-out above {MAX_FAN_OUT} is not permitted (got {max_fan_out})")
    if max_iterations > MAX_ITERATIONS:
        raise ProgramValidationError(f"iteration above {MAX_ITERATIONS} is not permitted (got {max_iterations})")
    steps: list[Step] = []
    for index, raw in enumerate(steps_raw):
        if not isinstance(raw, dict) or "operator" not in raw:
            raise ProgramValidationError(f"step {index}: operator required")
        operator = raw["operator"]
        if operator not in ALLOWED_OPERATORS:
            raise ProgramValidationError(f"step {index}: unknown operator {operator!r}")
        arguments = raw.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ProgramValidationError(f"step {index}: arguments must be an object")
        _validate_arguments_declarative(index, operator, arguments)
        steps.append(Step(operator=operator, arguments=arguments))
    return CompiledProgram(
        program_id=str(uuid.uuid4()),
        steps=steps,
        max_fan_out=max_fan_out,
        max_iterations=max_iterations,
        time_budget_seconds=float(spec.get("time_budget_seconds", 120.0)),
    )


def _validate_arguments_declarative(index: int, operator: str, arguments: dict) -> None:
    """Arguments must be declarative values: no executable predicate text.
    FILTER predicates are field/op/value triples; RANK is a field list; etc."""
    for key, value in arguments.items():
        text = value if isinstance(value, str) else json.dumps(value, default=str)
        if _EXECUTABLE_TEXT.search(str(text)):
            raise ProgramValidationError(
                f"step {index} ({operator}): argument {key!r} contains executable predicate text"
            )
    if operator == "FILTER":
        predicate = arguments.get("predicate")
        if not isinstance(predicate, dict) or "field" not in predicate or "op" not in predicate:
            raise ProgramValidationError(
                f"step {index} (FILTER): predicate must be declarative {{field, op, value}}"
            )
        if predicate["op"] not in ("eq", "ne", "gt", "lt", "contains", "in"):
            raise ProgramValidationError(f"step {index} (FILTER): unsupported op {predicate['op']!r}")
    if operator == "FAN_OUT":
        fan_out = int(arguments.get("count", 0))
        if fan_out > MAX_FAN_OUT:
            raise ProgramValidationError(f"step {index} (FAN_OUT): count above {MAX_FAN_OUT}")
    if operator == "ITERATE":
        iterations = int(arguments.get("max_iterations", 0))
        if iterations > MAX_ITERATIONS:
            raise ProgramValidationError(f"step {index} (ITERATE): iterations above {MAX_ITERATIONS}")


class ProgramRunStore:
    """Durable program runs and operator outputs (resume support)."""

    def __init__(self, database: PlatformDatabase):
        self._db = database

    def open_run(self, context: IdentityContext, program: CompiledProgram) -> str:
        program_id = program.program_id or str(uuid.uuid4())
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO program_runs (tenant_id, program_id, spec_digest, status)
                VALUES (%s, %s, %s, 'running')
                ON CONFLICT (tenant_id, program_id) DO NOTHING
                """,
                (context.tenant_id, program_id, program.digest()),
            )
        return program_id

    def completed_output(self, context: IdentityContext, program_id: str, step_index: int, input_digest: str) -> dict | None:
        row = self._db.query_one(
            """
            SELECT output, status FROM program_step_outputs
            WHERE tenant_id = %s AND program_id = %s AND step_index = %s AND input_digest = %s
              AND status IN ('complete', 'partial')
            """,
            (context.tenant_id, program_id, step_index, input_digest),
        )
        return {"output": row[0], "status": row[1]} if row else None

    def save_output(
        self, context: IdentityContext, program_id: str, step_index: int,
        input_digest: str, operator: str, output: Any, status: str,
    ) -> None:
        with self._db.connection() as connection:
            connection.execute(
                """
                INSERT INTO program_step_outputs
                    (tenant_id, program_id, step_index, input_digest, output, status, operator)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, program_id, step_index, input_digest)
                DO UPDATE SET output = EXCLUDED.output, status = EXCLUDED.status
                """,
                (context.tenant_id, program_id, step_index, input_digest,
                 Json(output), status, operator),
            )

    def finish_run(self, context: IdentityContext, program_id: str, status: str) -> None:
        with self._db.connection() as connection:
            connection.execute(
                "UPDATE program_runs SET status = %s, updated_at = now() WHERE tenant_id = %s AND program_id = %s",
                (status, context.tenant_id, program_id),
            )


def input_digest_of(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()
