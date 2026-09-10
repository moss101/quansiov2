"""Canonical contract binding for KnowledgeCandidate.

Generated from schemas/KnowledgeCandidate.schema.json digest 96483a2254dca34682b3879ecee51e46dcf8a7c9bcc7b02135d40f9598ef1b4b by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "96483a2254dca34682b3879ecee51e46dcf8a7c9bcc7b02135d40f9598ef1b4b"
SCHEMA = json.loads("""{"$id":"quansio://schema/KnowledgeCandidate/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"candidate_id":{"minLength":1,"type":"string"},"confidence":{"maximum":1,"minimum":0,"type":"number"},"conflict_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"evidence_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"knowledge_type":{"minLength":1,"type":"string"},"provenance":{"type":"object"},"schema_revision":{"const":"9.0.0"},"source_epoch":{"minimum":1,"type":"integer"},"status":{"enum":["CANDIDATE","ACCEPTED","REJECTED","STALE","SUPERSEDED"]},"tenant_id":{"minLength":1,"type":"string"},"valid_from":{"format":"date-time","type":"string"},"valid_until":{"format":"date-time","type":["string","null"]}},"required":["schema_revision","candidate_id","tenant_id","knowledge_type","source_epoch","provenance","evidence_refs","confidence","valid_from","status"],"title":"KnowledgeCandidate","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class KnowledgeCandidate:
    candidate_id: str
    confidence: float
    evidence_refs: list
    knowledge_type: str
    provenance: dict
    schema_revision: Any
    source_epoch: int
    status: Any
    tenant_id: str
    valid_from: str
    conflict_refs: list | None = None
    valid_until: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('candidate_id', 'confidence', 'conflict_refs', 'evidence_refs', 'knowledge_type', 'provenance', 'schema_revision', 'source_epoch', 'status', 'tenant_id', 'valid_from', 'valid_until',)})
