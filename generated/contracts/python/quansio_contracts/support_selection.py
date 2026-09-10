"""Canonical contract binding for SupportSelection.

Generated from schemas/SupportSelection.schema.json digest bd81bfd22ac94516913d5034edb105aa3c582d8abbc93ed91be68133b9e8f76c by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "bd81bfd22ac94516913d5034edb105aa3c582d8abbc93ed91be68133b9e8f76c"
SCHEMA = json.loads("""{"$id":"quansio://schema/SupportSelection/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"candidate_id":{"minLength":1,"type":"string"},"created_at":{"format":"date-time","type":"string"},"profiles":{"items":{"additionalProperties":false,"properties":{"profile_id":{"minLength":1,"type":"string"},"qualification_result_ids":{"items":{"minLength":1,"type":"string"},"type":"array","uniqueItems":true},"state":{"enum":["REQUIRED_GA","DISABLED_UNTIL_QUALIFIED","UNSUPPORTED"]}},"required":["profile_id","state","qualification_result_ids"],"type":"object"},"minItems":1,"type":"array","uniqueItems":true},"schema_revision":{"const":"9.0.0"},"selection_id":{"minLength":1,"type":"string"}},"required":["schema_revision","selection_id","candidate_id","profiles","created_at"],"title":"SupportSelection","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class SupportSelection:
    candidate_id: str
    created_at: str
    profiles: list
    schema_revision: Any
    selection_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('candidate_id', 'created_at', 'profiles', 'schema_revision', 'selection_id',)})
