"""Canonical contract binding for RuntimeEvent.

Generated from schemas/RuntimeEvent.schema.json digest 3cca01f30c04b71c7ef49f22b50fce726d5656b98c262ede5989ee50272e682b by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "3cca01f30c04b71c7ef49f22b50fce726d5656b98c262ede5989ee50272e682b"
SCHEMA = json.loads("""{"$id":"quansio://schema/RuntimeEvent/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"causal_parent_ids":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"committed_at":{"format":"date-time","type":"string"},"event_id":{"minLength":8,"type":"string"},"event_type":{"minLength":1,"type":"string"},"execution_generation":{"minimum":1,"type":"integer"},"occurred_at":{"format":"date-time","type":"string"},"payload":{"type":"object"},"producer_id":{"minLength":1,"type":"string"},"producer_sequence":{"minimum":1,"type":"integer"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"sequence":{"minimum":1,"type":"integer"},"tenant_id":{"minLength":1,"type":"string"},"workspace_id":{"minLength":1,"type":"string"}},"required":["schema_revision","event_id","tenant_id","workspace_id","run_id","sequence","producer_id","execution_generation","event_type","occurred_at","committed_at","payload"],"title":"RuntimeEvent","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class RuntimeEvent:
    committed_at: str
    event_id: str
    event_type: str
    execution_generation: int
    occurred_at: str
    payload: dict
    producer_id: str
    run_id: str
    schema_revision: Any
    sequence: int
    tenant_id: str
    workspace_id: str
    causal_parent_ids: list | None = None
    producer_sequence: int | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('causal_parent_ids', 'committed_at', 'event_id', 'event_type', 'execution_generation', 'occurred_at', 'payload', 'producer_id', 'producer_sequence', 'run_id', 'schema_revision', 'sequence', 'tenant_id', 'workspace_id',)})
