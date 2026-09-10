"""Canonical contract binding for ToolOperation.

Generated from schemas/ToolOperation.schema.json digest 7f82baadb986d6d7ec34b36275c30e41d1c84623acd8b3f9fdde99d3f1b46957 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "7f82baadb986d6d7ec34b36275c30e41d1c84623acd8b3f9fdde99d3f1b46957"
SCHEMA = json.loads("""{"$id":"quansio://schema/ToolOperation/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"capability_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"effect_class":{"enum":["OBSERVATIONAL","NON_CONSEQUENTIAL","CONSEQUENTIAL","HIGH_RISK","SEMANTICALLY_CLASSIFIED"]},"evidence_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"fidelity":{"enum":["LOSSLESS","LOSSLESS_WITH_CONSTRAINTS","BEST_EFFORT_DEGRADING","IRREVERSIBLE","HUMAN_ONLY","UNSUPPORTED"]},"idempotency":{"enum":["REQUIRED","SUPPORTED","NOT_AVAILABLE"]},"input_schema_id":{"minLength":1,"type":"string"},"operation_id":{"minLength":1,"type":"string"},"output_schema_id":{"minLength":1,"type":"string"},"policy_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"schema_revision":{"const":"9.0.0"},"timeout_ms":{"minimum":1,"type":"integer"},"version":{"minLength":1,"type":"string"}},"required":["schema_revision","operation_id","version","input_schema_id","output_schema_id","effect_class","fidelity","capability_requirements","timeout_ms","idempotency","evidence_requirements"],"title":"ToolOperation","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ToolOperation:
    capability_requirements: list
    effect_class: Any
    evidence_requirements: list
    fidelity: Any
    idempotency: Any
    input_schema_id: str
    operation_id: str
    output_schema_id: str
    schema_revision: Any
    timeout_ms: int
    version: str
    policy_requirements: list | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('capability_requirements', 'effect_class', 'evidence_requirements', 'fidelity', 'idempotency', 'input_schema_id', 'operation_id', 'output_schema_id', 'policy_requirements', 'schema_revision', 'timeout_ms', 'version',)})
