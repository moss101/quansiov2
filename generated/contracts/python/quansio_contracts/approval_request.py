"""Canonical contract binding for ApprovalRequest.

Generated from schemas/ApprovalRequest.schema.json digest fea463bcacddade1edea5b9adb3e046bf7b011c39bb595779b87e247f16c930b by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "fea463bcacddade1edea5b9adb3e046bf7b011c39bb595779b87e247f16c930b"
SCHEMA = json.loads("""{"$id":"quansio://schema/ApprovalRequest/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"approval_request_id":{"minLength":1,"type":"string"},"argument_scope_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"data_classification":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"effect_id":{"minLength":1,"type":"string"},"expires_at":{"format":"date-time","type":"string"},"financial_scope":{"type":["object","null"]},"operation_id":{"minLength":1,"type":"string"},"requested_authority":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"risk_class":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"target":{"type":"object"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","approval_request_id","tenant_id","effect_id","operation_id","argument_scope_digest","target","risk_class","requested_authority","expires_at"],"title":"ApprovalRequest","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ApprovalRequest:
    approval_request_id: str
    argument_scope_digest: str
    effect_id: str
    expires_at: str
    operation_id: str
    requested_authority: list
    risk_class: str
    schema_revision: Any
    target: dict
    tenant_id: str
    data_classification: list | None = None
    financial_scope: dict | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('approval_request_id', 'argument_scope_digest', 'data_classification', 'effect_id', 'expires_at', 'financial_scope', 'operation_id', 'requested_authority', 'risk_class', 'schema_revision', 'target', 'tenant_id',)})
