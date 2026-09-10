"""Canonical contract binding for AutomationSchedule.

Generated from schemas/AutomationSchedule.schema.json digest 257f1b0db5188865620c3599e96e7ee80ec7f57c9f7c5062be90f8777c99dda6 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "257f1b0db5188865620c3599e96e7ee80ec7f57c9f7c5062be90f8777c99dda6"
SCHEMA = json.loads("""{"$id":"quansio://schema/AutomationSchedule/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"automation_id":{"minLength":1,"type":"string"},"dst_fold_policy":{"enum":["FIRST","SECOND","BOTH","REJECT"]},"dst_gap_policy":{"enum":["SKIP","NEXT_VALID_TIME","REJECT"]},"max_catch_up":{"maximum":100,"minimum":0,"type":"integer"},"missed_fire_policy":{"enum":["SKIP","FIRE_ONCE","CATCH_UP_BOUNDED"]},"owner_agent_id":{"minLength":1,"type":"string"},"rule":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"state":{"enum":["ACTIVE","PAUSED","DELETED"]},"tenant_id":{"minLength":1,"type":"string"},"timezone":{"minLength":1,"type":"string"}},"required":["schema_revision","automation_id","tenant_id","owner_agent_id","timezone","rule","dst_gap_policy","dst_fold_policy","missed_fire_policy","max_catch_up","state"],"title":"AutomationSchedule","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class AutomationSchedule:
    automation_id: str
    dst_fold_policy: Any
    dst_gap_policy: Any
    max_catch_up: int
    missed_fire_policy: Any
    owner_agent_id: str
    rule: str
    schema_revision: Any
    state: Any
    tenant_id: str
    timezone: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('automation_id', 'dst_fold_policy', 'dst_gap_policy', 'max_catch_up', 'missed_fire_policy', 'owner_agent_id', 'rule', 'schema_revision', 'state', 'tenant_id', 'timezone',)})
