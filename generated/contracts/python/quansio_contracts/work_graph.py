"""Canonical contract binding for WorkGraph.

Generated from schemas/WorkGraph.schema.json digest 248afe64240bee08fa3b3cc15710929543c98d3e7e2a2c130226ff6797004b90 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "248afe64240bee08fa3b3cc15710929543c98d3e7e2a2c130226ff6797004b90"
SCHEMA = json.loads("""{"$id":"quansio://schema/WorkGraph/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"edges":{"items":{"additionalProperties":false,"properties":{"from":{"minLength":1,"type":"string"},"to":{"minLength":1,"type":"string"}},"required":["from","to"],"type":"object"},"type":"array"},"nodes":{"items":{"additionalProperties":true,"properties":{"kind":{"minLength":1,"type":"string"},"node_id":{"minLength":1,"type":"string"},"state":{"minLength":1,"type":"string"}},"required":["node_id","kind","state"],"type":"object"},"type":"array"},"revision":{"minimum":1,"type":"integer"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"state":{"enum":["CREATED","RUNNING","WAITING","CANCELLING","COMPLETED","CANCELLED","FAILED"]},"tenant_id":{"minLength":1,"type":"string"},"workgraph_id":{"minLength":1,"type":"string"},"workspace_id":{"minLength":1,"type":"string"}},"required":["schema_revision","workgraph_id","tenant_id","workspace_id","run_id","revision","nodes","edges","state"],"title":"WorkGraph","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class WorkGraph:
    edges: list
    nodes: list
    revision: int
    run_id: str
    schema_revision: Any
    state: Any
    tenant_id: str
    workgraph_id: str
    workspace_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('edges', 'nodes', 'revision', 'run_id', 'schema_revision', 'state', 'tenant_id', 'workgraph_id', 'workspace_id',)})
