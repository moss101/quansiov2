"""Canonical contract binding for CommandEnvelope.

Generated from schemas/CommandEnvelope.schema.json digest 88350b175833c113fbaea76b18c272b5fbd0feb5c153d7a57f2811fd8fed1da6 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "88350b175833c113fbaea76b18c272b5fbd0feb5c153d7a57f2811fd8fed1da6"
SCHEMA = json.loads("""{"$id":"quansio://schema/CommandEnvelope/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"actor_id":{"minLength":1,"type":"string"},"arguments":{"type":"object"},"command_id":{"minLength":1,"type":"string"},"command_type":{"minLength":1,"type":"string"},"idempotency_key":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"submitted_at":{"format":"date-time","type":"string"},"tenant_id":{"minLength":1,"type":"string"},"workspace_id":{"minLength":1,"type":"string"}},"required":["schema_revision","command_id","tenant_id","workspace_id","actor_id","command_type","arguments","idempotency_key","submitted_at"],"title":"CommandEnvelope","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class CommandEnvelope:
    actor_id: str
    arguments: dict
    command_id: str
    command_type: str
    idempotency_key: str
    schema_revision: Any
    submitted_at: str
    tenant_id: str
    workspace_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('actor_id', 'arguments', 'command_id', 'command_type', 'idempotency_key', 'schema_revision', 'submitted_at', 'tenant_id', 'workspace_id',)})
