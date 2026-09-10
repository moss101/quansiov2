"""Canonical contract binding for ApprovalReceipt.

Generated from schemas/ApprovalReceipt.schema.json digest 044356c3fd75a043f7ddb13bbe1975d75d6fee6eefd2cc5b92939285524886a2 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "044356c3fd75a043f7ddb13bbe1975d75d6fee6eefd2cc5b92939285524886a2"
SCHEMA = json.loads("""{"$id":"quansio://schema/ApprovalReceipt/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"approval_receipt_id":{"minLength":1,"type":"string"},"approval_request_id":{"minLength":1,"type":"string"},"approver_id":{"minLength":1,"type":"string"},"argument_scope_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"decided_at":{"format":"date-time","type":"string"},"decision":{"enum":["APPROVED","DENIED","EXPIRED"]},"effect_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","approval_receipt_id","approval_request_id","tenant_id","effect_id","argument_scope_digest","approver_id","decision","decided_at"],"title":"ApprovalReceipt","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ApprovalReceipt:
    approval_receipt_id: str
    approval_request_id: str
    approver_id: str
    argument_scope_digest: str
    decided_at: str
    decision: Any
    effect_id: str
    schema_revision: Any
    tenant_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('approval_receipt_id', 'approval_request_id', 'approver_id', 'argument_scope_digest', 'decided_at', 'decision', 'effect_id', 'schema_revision', 'tenant_id',)})
