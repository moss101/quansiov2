"""Canonical contract binding for RemoteArtifactVerification.

Generated from schemas/RemoteArtifactVerification.schema.json digest 1cf8923b193018441bab1350ee6859786282eea1b4cd842454f3edeabcd34538 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "1cf8923b193018441bab1350ee6859786282eea1b4cd842454f3edeabcd34538"
SCHEMA = json.loads("""{"$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"allOf":[{"if":{"properties":{"verification_method":{"const":"TRUSTED_BUILD_ATTESTATION"}},"required":["verification_method"]},"then":{"properties":{"attestation_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"attestation_path":{"minLength":1,"type":"string"}},"required":["attestation_path","attestation_digest"]}}],"properties":{"attestation_digest":{"pattern":"^[a-f0-9]{64}$","type":["string","null"]},"attestation_path":{"type":["string","null"]},"environment_id":{"minLength":1,"type":"string"},"expected_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"observed_at":{"format":"date-time","type":"string"},"observed_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"path_or_uri":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"status":{"enum":["PASS","FAIL"]},"verification_id":{"minLength":1,"type":"string"},"verification_method":{"enum":["REMOTE_DIGEST_LOOKUP","TRUSTED_BUILD_ATTESTATION"]},"verifier_identity":{"minLength":1,"type":"string"}},"required":["schema_revision","verification_id","path_or_uri","expected_digest","observed_digest","verification_method","status","verifier_identity","environment_id","observed_at"],"title":"RemoteArtifactVerification","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class RemoteArtifactVerification:
    environment_id: str
    expected_digest: str
    observed_at: str
    observed_digest: str
    path_or_uri: str
    schema_revision: Any
    status: Any
    verification_id: str
    verification_method: Any
    verifier_identity: str
    attestation_digest: str | Any | None = None
    attestation_path: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('attestation_digest', 'attestation_path', 'environment_id', 'expected_digest', 'observed_at', 'observed_digest', 'path_or_uri', 'schema_revision', 'status', 'verification_id', 'verification_method', 'verifier_identity',)})
