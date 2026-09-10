"""Canonical contract binding for CapabilityDemand.

Generated from schemas/CapabilityDemand.schema.json digest 1784dd42f675ecda767fe99e4d5c74b1eb1f4f1a99243aea4aa11200ade7d05f by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "1784dd42f675ecda767fe99e4d5c74b1eb1f4f1a99243aea4aa11200ade7d05f"
SCHEMA = json.loads("""{"$id":"quansio://schema/CapabilityDemand/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"constraints":{"additionalProperties":false,"properties":{"max_cost":{"minimum":0,"type":"number"},"max_latency_ms":{"minimum":1,"type":"integer"},"residency":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true}},"required":["max_cost","max_latency_ms","residency"],"type":"object"},"created_at":{"format":"date-time","type":"string"},"demand_id":{"minLength":1,"type":"string"},"dimensions":{"additionalProperties":false,"properties":{"code":{"maximum":1,"minimum":0,"type":"number"},"context":{"maximum":1,"minimum":0,"type":"number"},"reasoning":{"maximum":1,"minimum":0,"type":"number"},"research":{"maximum":1,"minimum":0,"type":"number"},"risk":{"maximum":1,"minimum":0,"type":"number"},"tool_use":{"maximum":1,"minimum":0,"type":"number"},"vision":{"maximum":1,"minimum":0,"type":"number"}},"required":["reasoning","code","tool_use","research","context","vision","risk"],"type":"object"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"step_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","demand_id","tenant_id","run_id","step_id","dimensions","constraints","created_at"],"title":"CapabilityDemand","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class CapabilityDemand:
    constraints: dict
    created_at: str
    demand_id: str
    dimensions: dict
    run_id: str
    schema_revision: Any
    step_id: str
    tenant_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('constraints', 'created_at', 'demand_id', 'dimensions', 'run_id', 'schema_revision', 'step_id', 'tenant_id',)})
