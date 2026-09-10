"""Canonical contract binding for BusinessCapabilityPack.

Generated from schemas/BusinessCapabilityPack.schema.json digest d663982136b8ee97dfb75cc5fcb655f2babf38c25ca3f9b87491ed7ba963fb0e by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "d663982136b8ee97dfb75cc5fcb655f2babf38c25ca3f9b87491ed7ba963fb0e"
SCHEMA = json.loads("""{"$id":"quansio://schema/BusinessCapabilityPack/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"acceptance_thresholds":{"type":"object"},"approval_rules":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"compatibility":{"type":"object"},"connector_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"credential_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"evaluation_cases":{"items":{"type":"object"},"minItems":1,"type":"array"},"evidence_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"input_contracts":{"items":{"type":"object"},"type":"array"},"knowledge_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"lifecycle":{"additionalProperties":false,"properties":{"deprecation_policy":{"minLength":1,"type":"string"},"migration_policy":{"minLength":1,"type":"string"},"rollback_policy":{"minLength":1,"type":"string"}},"required":["migration_policy","deprecation_policy","rollback_policy"],"type":"object"},"output_contracts":{"items":{"type":"object"},"type":"array"},"owner_scope":{"minLength":1,"type":"string"},"pack_id":{"minLength":1,"type":"string"},"permission_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"policies":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"role_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"schema_revision":{"const":"9.0.0"},"skills":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"tool_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"version":{"minLength":1,"type":"string"},"workflow_templates":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true}},"required":["schema_revision","pack_id","version","owner_scope","knowledge_requirements","skills","tool_requirements","connector_requirements","role_requirements","permission_requirements","policies","approval_rules","workflow_templates","input_contracts","output_contracts","evidence_requirements","evaluation_cases","acceptance_thresholds","compatibility","lifecycle"],"title":"BusinessCapabilityPack","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class BusinessCapabilityPack:
    acceptance_thresholds: dict
    approval_rules: list
    compatibility: dict
    connector_requirements: list
    evaluation_cases: list
    evidence_requirements: list
    input_contracts: list
    knowledge_requirements: list
    lifecycle: dict
    output_contracts: list
    owner_scope: str
    pack_id: str
    permission_requirements: list
    policies: list
    role_requirements: list
    schema_revision: Any
    skills: list
    tool_requirements: list
    version: str
    workflow_templates: list
    credential_requirements: list | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('acceptance_thresholds', 'approval_rules', 'compatibility', 'connector_requirements', 'credential_requirements', 'evaluation_cases', 'evidence_requirements', 'input_contracts', 'knowledge_requirements', 'lifecycle', 'output_contracts', 'owner_scope', 'pack_id', 'permission_requirements', 'policies', 'role_requirements', 'schema_revision', 'skills', 'tool_requirements', 'version', 'workflow_templates',)})
