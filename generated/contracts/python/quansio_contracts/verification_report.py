"""Canonical contract binding for VerificationReport.

Generated from schemas/VerificationReport.schema.json digest bde578d2c069cda00da1c4bc2ae07de54cb90f42600bfeb42f6b09e4557dd731 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "bde578d2c069cda00da1c4bc2ae07de54cb90f42600bfeb42f6b09e4557dd731"
SCHEMA = json.loads("""{"$id":"quansio://schema/VerificationReport/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifact_records":{"items":{"additionalProperties":false,"allOf":[{"if":{"properties":{"verification_method":{"enum":["REMOTE_DIGEST_LOOKUP","TRUSTED_BUILD_ATTESTATION"]}},"required":["verification_method"]},"then":{"properties":{"verification_receipt_ref":{"minLength":1,"type":"string"}},"required":["verification_receipt_ref"]}}],"properties":{"digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"path_or_uri":{"minLength":1,"type":"string"},"verification_method":{"enum":["LOCAL_HASH","REMOTE_DIGEST_LOOKUP","TRUSTED_BUILD_ATTESTATION"]},"verification_receipt_ref":{"type":["string","null"]}},"required":["path_or_uri","digest","verification_method"],"type":"object"},"type":"array"},"assertion_results":{"items":{"additionalProperties":false,"properties":{"assertion_id":{"minLength":1,"type":"string"},"blocking":{"type":"boolean"},"details":{"type":"string"},"status":{"enum":["PASS","FAIL","BLOCKED"]}},"required":["assertion_id","blocking","status"],"type":"object"},"minItems":1,"type":"array"},"ci_pipeline_id":{"minLength":1,"type":"string"},"ci_run_id":{"minLength":1,"type":"string"},"configuration_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"environment_id":{"minLength":1,"type":"string"},"executed_at":{"format":"date-time","type":"string"},"git_commit":{"pattern":"^[a-f0-9]{40,64}$","type":"string"},"protected_ref":{"minLength":1,"type":"string"},"real_boundary":{"type":"boolean"},"report_id":{"minLength":1,"type":"string"},"repository_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"status":{"enum":["PASS","FAIL","BLOCKED_REAL_BOUNDARY"]},"task_id":{"minLength":1,"type":"string"}},"required":["schema_revision","report_id","task_id","repository_id","git_commit","protected_ref","environment_id","configuration_digest","status","assertion_results","artifact_records","real_boundary","executed_at"],"title":"VerificationReport","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class VerificationReport:
    artifact_records: list
    assertion_results: list
    configuration_digest: str
    environment_id: str
    executed_at: str
    git_commit: str
    protected_ref: str
    real_boundary: bool
    report_id: str
    repository_id: str
    schema_revision: Any
    status: Any
    task_id: str
    ci_pipeline_id: str | None = None
    ci_run_id: str | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('artifact_records', 'assertion_results', 'ci_pipeline_id', 'ci_run_id', 'configuration_digest', 'environment_id', 'executed_at', 'git_commit', 'protected_ref', 'real_boundary', 'report_id', 'repository_id', 'schema_revision', 'status', 'task_id',)})
