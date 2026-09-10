"""Canonical contract binding for CapabilitySnapshot.

Generated from schemas/CapabilitySnapshot.schema.json digest aab310403d833a8134ca483f39762adf11a4e94b3fb7b4c8473c49e1aa37b657 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "aab310403d833a8134ca483f39762adf11a4e94b3fb7b4c8473c49e1aa37b657"
SCHEMA = json.loads("""{"$id":"quansio://schema/CapabilitySnapshot/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"actor_id":{"minLength":1,"type":"string"},"atoms":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"capability_snapshot_id":{"minLength":1,"type":"string"},"constraints":{"type":"object"},"expires_at":{"format":"date-time","type":"string"},"issued_at":{"format":"date-time","type":"string"},"parent_snapshot_id":{"type":["string","null"]},"schema_revision":{"const":"9.0.0"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","capability_snapshot_id","tenant_id","actor_id","atoms","constraints","issued_at","expires_at"],"title":"CapabilitySnapshot","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class CapabilitySnapshot:
    actor_id: str
    atoms: list
    capability_snapshot_id: str
    constraints: dict
    expires_at: str
    issued_at: str
    schema_revision: Any
    tenant_id: str
    parent_snapshot_id: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('actor_id', 'atoms', 'capability_snapshot_id', 'constraints', 'expires_at', 'issued_at', 'parent_snapshot_id', 'schema_revision', 'tenant_id',)})
