"""Canonical contract binding for ContextProjection.

Generated from schemas/ContextProjection.schema.json digest ca274a9fb78d8d7c65b5ea852fddb04c19955209a726c336557bb0d9688086c1 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "ca274a9fb78d8d7c65b5ea852fddb04c19955209a726c336557bb0d9688086c1"
SCHEMA = json.loads("""{"$id":"quansio://schema/ContextProjection/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"capability_snapshot_id":{"minLength":1,"type":"string"},"content_blocks":{"items":{"type":"object"},"type":"array"},"knowledge_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"privacy_decision_id":{"minLength":1,"type":"string"},"projection_id":{"minLength":1,"type":"string"},"revision":{"minimum":1,"type":"integer"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"source_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"step_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"},"token_budget":{"minimum":1,"type":"integer"}},"required":["schema_revision","projection_id","tenant_id","run_id","step_id","revision","token_budget","source_refs","knowledge_refs","content_blocks"],"title":"ContextProjection","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ContextProjection:
    content_blocks: list
    knowledge_refs: list
    projection_id: str
    revision: int
    run_id: str
    schema_revision: Any
    source_refs: list
    step_id: str
    tenant_id: str
    token_budget: int
    capability_snapshot_id: str | None = None
    privacy_decision_id: str | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('capability_snapshot_id', 'content_blocks', 'knowledge_refs', 'privacy_decision_id', 'projection_id', 'revision', 'run_id', 'schema_revision', 'source_refs', 'step_id', 'tenant_id', 'token_budget',)})
