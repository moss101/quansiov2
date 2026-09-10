"""Canonical contract binding for TurnOutcome.

Generated from schemas/TurnOutcome.schema.json digest 1c8dda3dedf5fcd560f362932f0b6b35292179d3bdaac05b13d1c9fa43c86dd1 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "1c8dda3dedf5fcd560f362932f0b6b35292179d3bdaac05b13d1c9fa43c86dd1"
SCHEMA = json.loads("""{"$id":"quansio://schema/TurnOutcome/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"completed_sequence":{"minimum":1,"type":"integer"},"dispatch_id":{"minLength":1,"type":"string"},"effect_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"error":{"type":["object","null"]},"evidence_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"result_ref":{"type":["string","null"]},"schema_revision":{"const":"9.0.0"},"status":{"enum":["COMPLETED","PARTIAL","CANCELLED","FAILED","TIMED_OUT"]},"worker_id":{"minLength":1,"type":"string"}},"required":["schema_revision","dispatch_id","worker_id","status","completed_sequence"],"title":"TurnOutcome","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class TurnOutcome:
    completed_sequence: int
    dispatch_id: str
    schema_revision: Any
    status: Any
    worker_id: str
    effect_refs: list | None = None
    error: dict | Any | None = None
    evidence_refs: list | None = None
    result_ref: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('completed_sequence', 'dispatch_id', 'effect_refs', 'error', 'evidence_refs', 'result_ref', 'schema_revision', 'status', 'worker_id',)})
