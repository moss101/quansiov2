"""Canonical contract binding for ReleaseCandidate.

Generated from schemas/ReleaseCandidate.schema.json digest 904459696f2c6063216b045862ca483877790c3021c043386f10c2a1f990794a by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "904459696f2c6063216b045862ca483877790c3021c043386f10c2a1f990794a"
SCHEMA = json.loads("""{"$id":"quansio://schema/ReleaseCandidate/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"artifact_digests":{"additionalProperties":{"pattern":"^[a-f0-9]{64}$","type":"string"},"minProperties":1,"type":"object"},"candidate_id":{"minLength":1,"type":"string"},"configuration_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"created_at":{"format":"date-time","type":"string"},"migration_set_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"schema_revision":{"const":"9.0.0"},"source_commit":{"pattern":"^[a-f0-9]{40,64}$","type":"string"},"state":{"enum":["CANDIDATE_CREATED","CANDIDATE_QUALIFIED","CANARY_DEPLOYED","CANARY_QUALIFIED","GO_APPROVED","READINESS_EVIDENCE_SEALED","PRODUCTION_READY","PRODUCTION_RELEASED"]},"support_selection_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"}},"required":["schema_revision","candidate_id","source_commit","artifact_digests","configuration_digest","migration_set_digest","support_selection_digest","state","created_at"],"title":"ReleaseCandidate","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class ReleaseCandidate:
    artifact_digests: dict
    candidate_id: str
    configuration_digest: str
    created_at: str
    migration_set_digest: str
    schema_revision: Any
    source_commit: str
    state: Any
    support_selection_digest: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('artifact_digests', 'candidate_id', 'configuration_digest', 'created_at', 'migration_set_digest', 'schema_revision', 'source_commit', 'state', 'support_selection_digest',)})
