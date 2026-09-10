"""Canonical contract binding for QualificationResult.

Generated from schemas/QualificationResult.schema.json digest 5baf49a99105cd5343ea96606f5206f4543a76aa76c584b411bf0fcdeb8ee683 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "5baf49a99105cd5343ea96606f5206f4543a76aa76c584b411bf0fcdeb8ee683"
SCHEMA = json.loads("""{"$id":"quansio://schema/QualificationResult/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifact_digests":{"additionalProperties":{"pattern":"^[a-f0-9]{64}$","type":"string"},"type":"object"},"assertion_results":{"items":{"additionalProperties":false,"properties":{"assertion_id":{"minLength":1,"type":"string"},"blocking":{"type":"boolean"},"details":{"type":"string"},"status":{"enum":["PASS","FAIL","BLOCKED"]}},"required":["assertion_id","status","blocking"],"type":"object"},"minItems":1,"type":"array"},"candidate_id":{"minLength":1,"type":"string"},"configuration_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"executed_at":{"format":"date-time","type":"string"},"real_boundary":{"type":"boolean"},"result_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"status":{"enum":["PASS","FAIL","BLOCKED_REAL_BOUNDARY"]},"suite_id":{"minLength":1,"type":"string"}},"required":["schema_revision","result_id","suite_id","candidate_id","configuration_digest","status","assertion_results","artifact_digests","real_boundary","executed_at"],"title":"QualificationResult","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class QualificationResult:
    artifact_digests: dict
    assertion_results: list
    candidate_id: str
    configuration_digest: str
    executed_at: str
    real_boundary: bool
    result_id: str
    schema_revision: Any
    status: Any
    suite_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('artifact_digests', 'assertion_results', 'candidate_id', 'configuration_digest', 'executed_at', 'real_boundary', 'result_id', 'schema_revision', 'status', 'suite_id',)})
