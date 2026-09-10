"""Canonical contract binding for ResearchRecord.

Generated from schemas/ResearchRecord.schema.json digest 95fe77d27b2a9d44627ba1291377ad09321eb1d340861d3f3fde1d27659d6be6 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "95fe77d27b2a9d44627ba1291377ad09321eb1d340861d3f3fde1d27659d6be6"
SCHEMA = json.loads("""{"$id":"quansio://schema/ResearchRecord/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"attributes":{"type":"object"},"claims":{"items":{"type":"object"},"type":"array"},"confidence":{"maximum":1,"minimum":0,"type":"number"},"entity_identity":{"type":"object"},"freshness":{"type":"object"},"record_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"source_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"verification_status":{"enum":["SUPPORTED","UNSUPPORTED","STALE","INACCESSIBLE","CONFLICTING","UNVERIFIED"]}},"required":["schema_revision","record_id","entity_identity","attributes","claims","source_refs","freshness","confidence","verification_status"],"title":"ResearchRecord","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ResearchRecord:
    attributes: dict
    claims: list
    confidence: float
    entity_identity: dict
    freshness: dict
    record_id: str
    schema_revision: Any
    source_refs: list
    verification_status: Any

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('attributes', 'claims', 'confidence', 'entity_identity', 'freshness', 'record_id', 'schema_revision', 'source_refs', 'verification_status',)})
