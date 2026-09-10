"""Canonical contract binding for ModelEvent.

Generated from schemas/ModelEvent.schema.json digest 064735a61877a86f0a271d3a19a902edd90647ef4cc189364d600e2bbc834b39 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "064735a61877a86f0a271d3a19a902edd90647ef4cc189364d600e2bbc834b39"
SCHEMA = json.loads("""{"$id":"quansio://schema/ModelEvent/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"event_id":{"minLength":1,"type":"string"},"event_type":{"enum":["MODEL_STARTED","OUTPUT_DELTA","TOOL_PROPOSAL","USAGE_DELTA","MODEL_COMPLETED","MODEL_CANCELLED","MODEL_FAILED"]},"execution_generation":{"minimum":1,"type":"integer"},"model_profile_id":{"minLength":1,"type":"string"},"occurred_at":{"format":"date-time","type":"string"},"payload":{"type":"object"},"request_id":{"minLength":1,"type":"string"},"route_decision_id":{"minLength":1,"type":"string"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"sequence":{"minimum":1,"type":"integer"},"step_id":{"minLength":1,"type":"string"}},"required":["schema_revision","event_id","request_id","run_id","step_id","execution_generation","model_profile_id","route_decision_id","sequence","event_type","occurred_at","payload"],"title":"ModelEvent","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ModelEvent:
    event_id: str
    event_type: Any
    execution_generation: int
    model_profile_id: str
    occurred_at: str
    payload: dict
    request_id: str
    route_decision_id: str
    run_id: str
    schema_revision: Any
    sequence: int
    step_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('event_id', 'event_type', 'execution_generation', 'model_profile_id', 'occurred_at', 'payload', 'request_id', 'route_decision_id', 'run_id', 'schema_revision', 'sequence', 'step_id',)})
