"""Canonical contract binding for EffectRecord.

Generated from schemas/EffectRecord.schema.json digest b34515c9dc93e983e1b257b21193189c3c37e081b87e9981fc23bae0dbe1c518 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "b34515c9dc93e983e1b257b21193189c3c37e081b87e9981fc23bae0dbe1c518"
SCHEMA = json.loads("""{"$id":"quansio://schema/EffectRecord/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"approval_receipt_id":{"type":["string","null"]},"argument_scope_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"created_at":{"format":"date-time","type":"string"},"effect_class":{"enum":["CONSEQUENTIAL","HIGH_RISK"]},"effect_id":{"minLength":1,"type":"string"},"evidence_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"idempotency_key":{"minLength":1,"type":"string"},"operation_id":{"minLength":1,"type":"string"},"policy_decision_id":{"minLength":1,"type":"string"},"receipt_ref":{"type":["string","null"]},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"state":{"enum":["PROPOSED","APPROVAL_REQUIRED","APPROVED","EXECUTING","UNKNOWN","COMMITTED","DENIED","FAILED","RECONCILED"]},"step_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","effect_id","tenant_id","run_id","step_id","operation_id","effect_class","idempotency_key","state","policy_decision_id","argument_scope_digest","created_at"],"title":"EffectRecord","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class EffectRecord:
    argument_scope_digest: str
    created_at: str
    effect_class: Any
    effect_id: str
    idempotency_key: str
    operation_id: str
    policy_decision_id: str
    run_id: str
    schema_revision: Any
    state: Any
    step_id: str
    tenant_id: str
    approval_receipt_id: str | Any | None = None
    evidence_refs: list | None = None
    receipt_ref: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('approval_receipt_id', 'argument_scope_digest', 'created_at', 'effect_class', 'effect_id', 'evidence_refs', 'idempotency_key', 'operation_id', 'policy_decision_id', 'receipt_ref', 'run_id', 'schema_revision', 'state', 'step_id', 'tenant_id',)})
