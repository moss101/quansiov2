"""Canonical contract binding for BudgetReservation.

Generated from schemas/BudgetReservation.schema.json digest 0d1c2463a8dc6c99f4d1c2eaea2bc3b7289e7596454c05d61c733e2754382e89 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "0d1c2463a8dc6c99f4d1c2eaea2bc3b7289e7596454c05d61c733e2754382e89"
SCHEMA = json.loads("""{"$id":"quansio://schema/BudgetReservation/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"amount":{"exclusiveMinimum":0,"type":"number"},"idempotency_key":{"minLength":1,"type":"string"},"kind":{"enum":["MODEL","WORKER","RESEARCH","CONNECTOR","STORAGE"]},"parent_reservation_id":{"type":["string","null"]},"reservation_id":{"minLength":1,"type":"string"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"state":{"enum":["RESERVED","SETTLING_PROVIDER_USAGE","SETTLED","RELEASED","ADJUSTED"]},"tenant_id":{"minLength":1,"type":"string"}},"required":["schema_revision","reservation_id","tenant_id","run_id","kind","amount","state","idempotency_key"],"title":"BudgetReservation","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class BudgetReservation:
    amount: float
    idempotency_key: str
    kind: Any
    reservation_id: str
    run_id: str
    schema_revision: Any
    state: Any
    tenant_id: str
    parent_reservation_id: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('amount', 'idempotency_key', 'kind', 'parent_reservation_id', 'reservation_id', 'run_id', 'schema_revision', 'state', 'tenant_id',)})
