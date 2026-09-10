"""Canonical contract binding for SkillPackage.

Generated from schemas/SkillPackage.schema.json digest 2355abbb698156f21d00c9d619842adc55124442725c3510b1ebb1e68ceabda1 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "2355abbb698156f21d00c9d619842adc55124442725c3510b1ebb1e68ceabda1"
SCHEMA = json.loads("""{"$id":"quansio://schema/SkillPackage/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"assets":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"capability_requirements":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"compatibility":{"type":"object"},"dependencies":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"evaluation_thresholds":{"type":"object"},"exclusions":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"helpers":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"input_contract":{"type":"object"},"instructions":{"items":{"minLength":1,"type":"string"},"minItems":1,"type":"array"},"intended_use":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"output_contract":{"type":"object"},"owner_scope":{"minLength":1,"type":"string"},"promotion_state":{"enum":["CANDIDATE","QUALIFIED","ACTIVE","RETIRED","REJECTED"]},"purpose":{"minLength":1,"type":"string"},"rollback_target":{"type":["string","null"]},"schema_revision":{"const":"9.0.0"},"skill_id":{"minLength":1,"type":"string"},"source_refs":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"version":{"minLength":1,"type":"string"}},"required":["schema_revision","skill_id","version","owner_scope","purpose","intended_use","exclusions","input_contract","output_contract","instructions","dependencies","source_refs","capability_requirements","evaluation_thresholds","promotion_state","rollback_target"],"title":"SkillPackage","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class SkillPackage:
    capability_requirements: list
    dependencies: list
    evaluation_thresholds: dict
    exclusions: list
    input_contract: dict
    instructions: list
    intended_use: list
    output_contract: dict
    owner_scope: str
    promotion_state: Any
    purpose: str
    rollback_target: str | Any
    schema_revision: Any
    skill_id: str
    source_refs: list
    version: str
    assets: list | None = None
    compatibility: dict | None = None
    helpers: list | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('assets', 'capability_requirements', 'compatibility', 'dependencies', 'evaluation_thresholds', 'exclusions', 'helpers', 'input_contract', 'instructions', 'intended_use', 'output_contract', 'owner_scope', 'promotion_state', 'purpose', 'rollback_target', 'schema_revision', 'skill_id', 'source_refs', 'version',)})
