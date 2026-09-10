"""Canonical contract binding for ModelRequestEnvelope.

Generated from schemas/ModelRequestEnvelope.schema.json digest 1cdbe96e8a532e4069d359ac1fa0062c3c73c81c2fb65d73782104abb7e4869b by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "1cdbe96e8a532e4069d359ac1fa0062c3c73c81c2fb65d73782104abb7e4869b"
SCHEMA = json.loads("""{"$id":"quansio://schema/ModelRequestEnvelope/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"cancellation_id":{"minLength":1,"type":"string"},"capability_snapshot_id":{"minLength":1,"type":"string"},"context_projection_id":{"minLength":1,"type":"string"},"created_at":{"format":"date-time","type":"string"},"execution_generation":{"minimum":1,"type":"integer"},"messages":{"items":{"type":"object"},"minItems":1,"type":"array"},"model_profile_id":{"minLength":1,"type":"string"},"privacy_decision_id":{"minLength":1,"type":"string"},"request_id":{"minLength":1,"type":"string"},"residency_policy_id":{"minLength":1,"type":"string"},"route_decision_id":{"minLength":1,"type":"string"},"run_id":{"minLength":1,"type":"string"},"sampling":{"type":"object"},"schema_revision":{"const":"9.0.0"},"step_id":{"minLength":1,"type":"string"},"stream_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"},"tools":{"items":{"type":"object"},"type":"array"},"trace_id":{"minLength":1,"type":"string"},"usage_reservation_id":{"minLength":1,"type":"string"},"workspace_id":{"minLength":1,"type":"string"}},"required":["schema_revision","request_id","tenant_id","workspace_id","run_id","step_id","execution_generation","route_decision_id","model_profile_id","capability_snapshot_id","context_projection_id","usage_reservation_id","stream_id","cancellation_id","messages","created_at"],"title":"ModelRequestEnvelope","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ModelRequestEnvelope:
    cancellation_id: str
    capability_snapshot_id: str
    context_projection_id: str
    created_at: str
    execution_generation: int
    messages: list
    model_profile_id: str
    request_id: str
    route_decision_id: str
    run_id: str
    schema_revision: Any
    step_id: str
    stream_id: str
    tenant_id: str
    usage_reservation_id: str
    workspace_id: str
    privacy_decision_id: str | None = None
    residency_policy_id: str | None = None
    sampling: dict | None = None
    tools: list | None = None
    trace_id: str | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('cancellation_id', 'capability_snapshot_id', 'context_projection_id', 'created_at', 'execution_generation', 'messages', 'model_profile_id', 'privacy_decision_id', 'request_id', 'residency_policy_id', 'route_decision_id', 'run_id', 'sampling', 'schema_revision', 'step_id', 'stream_id', 'tenant_id', 'tools', 'trace_id', 'usage_reservation_id', 'workspace_id',)})
