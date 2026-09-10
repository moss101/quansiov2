"""Canonical contract binding for ArtifactRecord.

Generated from schemas/ArtifactRecord.schema.json digest 32c7fa65ac7e3365c175ae3dec35a05926b8f01e81323c1a98f79cffa0dce282 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "32c7fa65ac7e3365c175ae3dec35a05926b8f01e81323c1a98f79cffa0dce282"
SCHEMA = json.loads("""{"$id":"quansio://schema/ArtifactRecord/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifact_id":{"minLength":1,"type":"string"},"created_at":{"format":"date-time","type":"string"},"digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"grant_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"media_type":{"minLength":1,"type":"string"},"producer_ref":{"minLength":1,"type":"string"},"scan_state":{"enum":["PENDING","CLEAN","REJECTED","NOT_APPLICABLE"]},"schema_revision":{"const":"9.0.0"},"size_bytes":{"minimum":0,"type":"integer"},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","artifact_id","tenant_id","digest","size_bytes","media_type","producer_ref","scan_state","created_at"],"title":"ArtifactRecord","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    created_at: str
    digest: str
    media_type: str
    producer_ref: str
    scan_state: Any
    schema_revision: Any
    size_bytes: int
    tenant_id: str
    grant_refs: list | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('artifact_id', 'created_at', 'digest', 'grant_refs', 'media_type', 'producer_ref', 'scan_state', 'schema_revision', 'size_bytes', 'tenant_id',)})
