"""Canonical contract binding for EndpointActionEnvelope.

Generated from schemas/EndpointActionEnvelope.schema.json digest 5f4e91a66b6301bc5f6dd3691846fd4238d06e4b00a88996be503f8e2b63868e by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "5f4e91a66b6301bc5f6dd3691846fd4238d06e4b00a88996be503f8e2b63868e"
SCHEMA = json.loads("""{"$id":"quansio://schema/EndpointActionEnvelope/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"allOf":[{"if":{"properties":{"approval_required":{"const":true}}},"then":{"properties":{"approval_receipt_id":{"minLength":1,"type":"string"},"approval_scope_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"}},"required":["approval_receipt_id","approval_scope_digest"]}}],"properties":{"action_id":{"minLength":1,"type":"string"},"approval_receipt_id":{"type":["string","null"]},"approval_required":{"type":"boolean"},"approval_scope_digest":{"pattern":"^[a-f0-9]{64}$","type":["string","null"]},"arguments":{"type":"object"},"capability_snapshot_id":{"minLength":1,"type":"string"},"delivery_attempt":{"minimum":1,"type":"integer"},"delivery_id":{"minLength":1,"type":"string"},"effect_class":{"enum":["OBSERVATIONAL","NON_CONSEQUENTIAL","CONSEQUENTIAL","HIGH_RISK"]},"effect_id":{"minLength":1,"type":"string"},"endpoint_id":{"minLength":1,"type":"string"},"execution_generation":{"minimum":1,"type":"integer"},"expires_at":{"format":"date-time","type":"string"},"fence_token":{"minimum":1,"type":"integer"},"idempotency_key":{"minLength":1,"type":"string"},"input_schema_id":{"minLength":1,"type":"string"},"lease_id":{"minLength":1,"type":"string"},"operation_id":{"minLength":1,"type":"string"},"operation_version":{"minLength":1,"type":"string"},"policy_decision_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"target_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","action_id","tenant_id","endpoint_id","target_id","execution_generation","lease_id","fence_token","capability_snapshot_id","policy_decision_id","effect_id","effect_class","delivery_id","delivery_attempt","idempotency_key","operation_id","operation_version","input_schema_id","arguments","expires_at","approval_required"],"title":"EndpointActionEnvelope","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class EndpointActionEnvelope:
    action_id: str
    approval_required: bool
    arguments: dict
    capability_snapshot_id: str
    delivery_attempt: int
    delivery_id: str
    effect_class: Any
    effect_id: str
    endpoint_id: str
    execution_generation: int
    expires_at: str
    fence_token: int
    idempotency_key: str
    input_schema_id: str
    lease_id: str
    operation_id: str
    operation_version: str
    policy_decision_id: str
    schema_revision: Any
    target_id: str
    tenant_id: str
    approval_receipt_id: str | Any | None = None
    approval_scope_digest: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('action_id', 'approval_receipt_id', 'approval_required', 'approval_scope_digest', 'arguments', 'capability_snapshot_id', 'delivery_attempt', 'delivery_id', 'effect_class', 'effect_id', 'endpoint_id', 'execution_generation', 'expires_at', 'fence_token', 'idempotency_key', 'input_schema_id', 'lease_id', 'operation_id', 'operation_version', 'policy_decision_id', 'schema_revision', 'target_id', 'tenant_id',)})
