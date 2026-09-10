"""Canonical contract binding for WorkerLease.

Generated from schemas/WorkerLease.schema.json digest 23ab3234e98a9c643eb07a406fe85498fbfae43253c8dfc17749f87d16e5548f by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "23ab3234e98a9c643eb07a406fe85498fbfae43253c8dfc17749f87d16e5548f"
SCHEMA = json.loads("""{"$id":"quansio://schema/WorkerLease/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"execution_generation":{"minimum":1,"type":"integer"},"expires_at":{"format":"date-time","type":"string"},"fence_token":{"minimum":1,"type":"integer"},"issued_at":{"format":"date-time","type":"string"},"lease_id":{"minLength":1,"type":"string"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"state":{"enum":["ACTIVE","RELEASED","EXPIRED","REVOKED"]},"target_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"},"worker_id":{"minLength":1,"type":"string"}},"required":["schema_revision","lease_id","tenant_id","target_id","run_id","worker_id","execution_generation","fence_token","issued_at","expires_at","state"],"title":"WorkerLease","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class WorkerLease:
    execution_generation: int
    expires_at: str
    fence_token: int
    issued_at: str
    lease_id: str
    run_id: str
    schema_revision: Any
    state: Any
    target_id: str
    tenant_id: str
    worker_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('execution_generation', 'expires_at', 'fence_token', 'issued_at', 'lease_id', 'run_id', 'schema_revision', 'state', 'target_id', 'tenant_id', 'worker_id',)})
