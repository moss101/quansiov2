"""Canonical contract binding for Checkpoint.

Generated from schemas/Checkpoint.schema.json digest 026460248d64e14f478907fa41378199556b8293ff58740691250557cc9a4c01 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "026460248d64e14f478907fa41378199556b8293ff58740691250557cc9a4c01"
SCHEMA = json.loads("""{"$id":"quansio://schema/Checkpoint/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifact_manifest_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"checkpoint_id":{"minLength":1,"type":"string"},"created_at":{"format":"date-time","type":"string"},"database_position":{"minLength":1,"type":"string"},"event_sequence":{"minimum":0,"type":"integer"},"execution_generation":{"minimum":1,"type":"integer"},"schema_revision":{"const":"9.0.0"},"snapshot_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"state":{"enum":["CREATING","DURABLE","RESTORABLE","INVALID"]},"target_id":{"minLength":1,"type":"string"},"tenant_id":{"minLength":1,"type":"string"},"tier":{"enum":["WORKSPACE","FULL_MACHINE"]}},"required":["schema_revision","checkpoint_id","tenant_id","target_id","execution_generation","tier","state","database_position","event_sequence","artifact_manifest_digest","snapshot_digest","created_at"],"title":"Checkpoint","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class Checkpoint:
    artifact_manifest_digest: str
    checkpoint_id: str
    created_at: str
    database_position: str
    event_sequence: int
    execution_generation: int
    schema_revision: Any
    snapshot_digest: str
    state: Any
    target_id: str
    tenant_id: str
    tier: Any

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('artifact_manifest_digest', 'checkpoint_id', 'created_at', 'database_position', 'event_sequence', 'execution_generation', 'schema_revision', 'snapshot_digest', 'state', 'target_id', 'tenant_id', 'tier',)})
