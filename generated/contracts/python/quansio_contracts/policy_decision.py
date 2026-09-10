"""Canonical contract binding for PolicyDecision.

Generated from schemas/PolicyDecision.schema.json digest 1ecbd62bb617564957d4f2ad77443a3fc432b4f3bf159f51c1c4daf12fecb1c3 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "1ecbd62bb617564957d4f2ad77443a3fc432b4f3bf159f51c1c4daf12fecb1c3"
SCHEMA = json.loads("""{"$id":"quansio://schema/PolicyDecision/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"actor_id":{"minLength":1,"type":"string"},"argument_scope_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"capability_snapshot_id":{"minLength":1,"type":"string"},"data_classification":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"decision":{"enum":["ALLOW","ALLOW_REDACTED","REQUIRE_APPROVAL","DENY"]},"expires_at":{"format":"date-time","type":"string"},"operation_id":{"minLength":1,"type":"string"},"policy_decision_id":{"minLength":1,"type":"string"},"policy_revision":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"target_scope":{"type":"object"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","policy_decision_id","tenant_id","actor_id","capability_snapshot_id","operation_id","argument_scope_digest","target_scope","data_classification","decision","policy_revision","expires_at"],"title":"PolicyDecision","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class PolicyDecision:
    actor_id: str
    argument_scope_digest: str
    capability_snapshot_id: str
    data_classification: list
    decision: Any
    expires_at: str
    operation_id: str
    policy_decision_id: str
    policy_revision: str
    schema_revision: Any
    target_scope: dict
    tenant_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('actor_id', 'argument_scope_digest', 'capability_snapshot_id', 'data_classification', 'decision', 'expires_at', 'operation_id', 'policy_decision_id', 'policy_revision', 'schema_revision', 'target_scope', 'tenant_id',)})
