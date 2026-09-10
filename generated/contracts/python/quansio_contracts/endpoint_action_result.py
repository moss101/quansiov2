"""Canonical contract binding for EndpointActionResult.

Generated from schemas/EndpointActionResult.schema.json digest a635bb039f3983140532816e234496dce44fe388fe079f692acd9454f3970372 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "a635bb039f3983140532816e234496dce44fe388fe079f692acd9454f3970372"
SCHEMA = json.loads("""{"$id":"quansio://schema/EndpointActionResult/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"action_id":{"minLength":1,"type":"string"},"completed_at":{"format":"date-time","type":"string"},"delivery_id":{"minLength":1,"type":"string"},"evidence_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"execution_generation":{"minimum":1,"type":"integer"},"result":{"type":"object"},"schema_revision":{"const":"9.0.0"},"status":{"enum":["COMPLETED","DENIED","FAILED","CANCELLED","EXPIRED"]},"target_id":{"minLength":1,"type":"string"}},"required":["schema_revision","action_id","delivery_id","target_id","execution_generation","status","result","completed_at"],"title":"EndpointActionResult","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class EndpointActionResult:
    action_id: str
    completed_at: str
    delivery_id: str
    execution_generation: int
    result: dict
    schema_revision: Any
    status: Any
    target_id: str
    evidence_refs: list | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('action_id', 'completed_at', 'delivery_id', 'evidence_refs', 'execution_generation', 'result', 'schema_revision', 'status', 'target_id',)})
