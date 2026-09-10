"""Canonical contract binding for ReleaseStateRecord.

Generated from schemas/ReleaseStateRecord.schema.json digest 5a66b48351608cfeef8c2348922b9c2a509e891bcc1ac591957cc67a57dbb498 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "5a66b48351608cfeef8c2348922b9c2a509e891bcc1ac591957cc67a57dbb498"
SCHEMA = json.loads("""{"$id":"quansio://schema/ReleaseStateRecord/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"candidate_id":{"minLength":1,"type":"string"},"created_at":{"format":"date-time","type":"string"},"evidence_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"from_state":{"type":["string","null"]},"owner_task_id":{"minLength":1,"type":"string"},"record_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"to_state":{"enum":["CANDIDATE_CREATED","CANDIDATE_QUALIFIED","CANARY_DEPLOYED","CANARY_QUALIFIED","GO_APPROVED","READINESS_EVIDENCE_SEALED","PRODUCTION_READY","PRODUCTION_RELEASED"]}},"required":["schema_revision","record_id","candidate_id","from_state","to_state","owner_task_id","evidence_refs","created_at"],"title":"ReleaseStateRecord","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ReleaseStateRecord:
    candidate_id: str
    created_at: str
    evidence_refs: list
    from_state: str | Any
    owner_task_id: str
    record_id: str
    schema_revision: Any
    to_state: Any

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('candidate_id', 'created_at', 'evidence_refs', 'from_state', 'owner_task_id', 'record_id', 'schema_revision', 'to_state',)})
