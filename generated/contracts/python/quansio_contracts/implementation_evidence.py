"""Canonical contract binding for ImplementationEvidence.

Generated from schemas/ImplementationEvidence.schema.json digest 6ced0e8298bfd6ddb215224cb87ce31f0dd21c8e17cfb02403799c89a29c17fd by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "6ced0e8298bfd6ddb215224cb87ce31f0dd21c8e17cfb02403799c89a29c17fd"
SCHEMA = json.loads("""{"$id":"quansio://schema/ImplementationEvidence/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifact_digests":{"additionalProperties":{"pattern":"^[a-f0-9]{64}$","type":"string"},"type":"object"},"created_at":{"format":"date-time","type":"string"},"evidence_id":{"minLength":1,"type":"string"},"git_commit":{"pattern":"^[a-f0-9]{40,64}$","type":"string"},"real_boundary":{"type":"boolean"},"report_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"report_path":{"minLength":1,"type":"string"},"repository_id":{"minLength":1,"type":"string"},"requirement_assertion_ids":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"requirement_ids":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"rollback_verified":{"type":"boolean"},"schema_revision":{"const":"9.0.0"},"status":{"enum":["PASS","FAIL","BLOCKED_REAL_BOUNDARY"]},"task_assertion_ids":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"task_id":{"minLength":1,"type":"string"}},"required":["schema_revision","evidence_id","task_id","requirement_ids","task_assertion_ids","requirement_assertion_ids","repository_id","git_commit","report_path","report_digest","status","real_boundary","artifact_digests","created_at"],"title":"ImplementationEvidence","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ImplementationEvidence:
    artifact_digests: dict
    created_at: str
    evidence_id: str
    git_commit: str
    real_boundary: bool
    report_digest: str
    report_path: str
    repository_id: str
    requirement_assertion_ids: list
    requirement_ids: list
    schema_revision: Any
    status: Any
    task_assertion_ids: list
    task_id: str
    rollback_verified: bool | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('artifact_digests', 'created_at', 'evidence_id', 'git_commit', 'real_boundary', 'report_digest', 'report_path', 'repository_id', 'requirement_assertion_ids', 'requirement_ids', 'rollback_verified', 'schema_revision', 'status', 'task_assertion_ids', 'task_id',)})
