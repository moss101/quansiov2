"""Canonical contract binding for TurnDispatch.

Generated from schemas/TurnDispatch.schema.json digest a59f8aceca55327a858c0d83e9be99982604a922d219fb94c14012e941da727b by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "a59f8aceca55327a858c0d83e9be99982604a922d219fb94c14012e941da727b"
SCHEMA = json.loads("""{"$id":"quansio://schema/TurnDispatch/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"cancellation_id":{"type":["string","null"]},"capability_snapshot_id":{"minLength":1,"type":"string"},"deadline":{"format":"date-time","type":"string"},"dispatch_id":{"minLength":1,"type":"string"},"expected_output_schema_id":{"minLength":1,"type":"string"},"idempotency_key":{"minLength":1,"type":"string"},"input_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"parent_run_id":{"minLength":1,"type":"string"},"parent_turn_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"target_agent_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","dispatch_id","tenant_id","parent_run_id","parent_turn_id","target_agent_id","capability_snapshot_id","input_refs","expected_output_schema_id","deadline","idempotency_key"],"title":"TurnDispatch","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class TurnDispatch:
    capability_snapshot_id: str
    deadline: str
    dispatch_id: str
    expected_output_schema_id: str
    idempotency_key: str
    input_refs: list
    parent_run_id: str
    parent_turn_id: str
    schema_revision: Any
    target_agent_id: str
    tenant_id: str
    cancellation_id: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('cancellation_id', 'capability_snapshot_id', 'deadline', 'dispatch_id', 'expected_output_schema_id', 'idempotency_key', 'input_refs', 'parent_run_id', 'parent_turn_id', 'schema_revision', 'target_agent_id', 'tenant_id',)})
