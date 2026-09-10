"""Canonical contract binding for StateGraph.

Generated from schemas/StateGraph.schema.json digest f133256fb067831e6d093e80d4dd5f0e4f3683ce5a6399860da5a00a109c7e40 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "f133256fb067831e6d093e80d4dd5f0e4f3683ce5a6399860da5a00a109c7e40"
SCHEMA = json.loads("""{"$id":"quansio://schema/StateGraph/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"revision":{"minimum":1,"type":"integer"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"stategraph_id":{"minLength":1,"type":"string"},"states":{"type":"object"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","stategraph_id","tenant_id","run_id","revision","states"],"title":"StateGraph","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class StateGraph:
    revision: int
    run_id: str
    schema_revision: Any
    stategraph_id: str
    states: dict
    tenant_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('revision', 'run_id', 'schema_revision', 'stategraph_id', 'states', 'tenant_id',)})
