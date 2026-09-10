"""Canonical contract binding for AutomationFire.

Generated from schemas/AutomationFire.schema.json digest 400dcaef59f6ebcaa878b584c93e7d7ae2472937d1114ab6063549310098387d by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "400dcaef59f6ebcaa878b584c93e7d7ae2472937d1114ab6063549310098387d"
SCHEMA = json.loads("""{"$id":"quansio://schema/AutomationFire/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"attempt":{"minimum":1,"type":"integer"},"authority_snapshot_id":{"minLength":1,"type":"string"},"automation_id":{"minLength":1,"type":"string"},"fire_id":{"minLength":1,"type":"string"},"logical_fire_key":{"minLength":1,"type":"string"},"run_id":{"type":["string","null"]},"scheduled_for":{"format":"date-time","type":"string"},"schema_revision":{"const":"9.0.0"},"state":{"enum":["ADMITTED","RUNNING","COMPLETED","SKIPPED","FAILED","CANCELLED"]},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","fire_id","automation_id","tenant_id","logical_fire_key","scheduled_for","attempt","authority_snapshot_id","state"],"title":"AutomationFire","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class AutomationFire:
    attempt: int
    authority_snapshot_id: str
    automation_id: str
    fire_id: str
    logical_fire_key: str
    scheduled_for: str
    schema_revision: Any
    state: Any
    tenant_id: str
    run_id: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('attempt', 'authority_snapshot_id', 'automation_id', 'fire_id', 'logical_fire_key', 'run_id', 'scheduled_for', 'schema_revision', 'state', 'tenant_id',)})
