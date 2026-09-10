"""Canonical contract binding for ExecutionTarget.

Generated from schemas/ExecutionTarget.schema.json digest 7727b782fefb2972b2b0519b9039c7366847822fe1ac12c09bdfab0abd657d13 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "7727b782fefb2972b2b0519b9039c7366847822fe1ac12c09bdfab0abd657d13"
SCHEMA = json.loads("""{"$id":"quansio://schema/ExecutionTarget/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"execution_generation":{"minimum":1,"type":"integer"},"fence_token":{"minimum":1,"type":["integer","null"]},"health_state":{"minLength":1,"type":"string"},"lease_id":{"type":["string","null"]},"lifecycle_state":{"enum":["PROVISIONING","READY","LEASED","HIBERNATED","MIGRATING","UNHEALTHY","TERMINATED"]},"schema_revision":{"const":"9.0.0"},"support_profile_id":{"minLength":1,"type":"string"},"target_id":{"minLength":1,"type":"string"},"target_type":{"enum":["HOSTED_ISOLATED","PERSISTENT_WORKSPACE","LOCAL_VIRTUALIZED","PRIVATE_WORKER","PERSONAL_ENDPOINT"]},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","target_id","tenant_id","target_type","support_profile_id","lifecycle_state","execution_generation","health_state"],"title":"ExecutionTarget","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ExecutionTarget:
    execution_generation: int
    health_state: str
    lifecycle_state: Any
    schema_revision: Any
    support_profile_id: str
    target_id: str
    target_type: Any
    tenant_id: str
    fence_token: int | Any | None = None
    lease_id: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('execution_generation', 'fence_token', 'health_state', 'lease_id', 'lifecycle_state', 'schema_revision', 'support_profile_id', 'target_id', 'target_type', 'tenant_id',)})
