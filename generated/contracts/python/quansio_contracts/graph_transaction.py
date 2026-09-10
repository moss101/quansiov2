"""Canonical contract binding for GraphTransaction.

Generated from schemas/GraphTransaction.schema.json digest f6f1a5e3bb6340e714fac8e00905e709ba1a3778374d78476746a20af692118e by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "f6f1a5e3bb6340e714fac8e00905e709ba1a3778374d78476746a20af692118e"
SCHEMA = json.loads("""{"$id":"quansio://schema/GraphTransaction/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"expected_revision":{"minimum":0,"type":"integer"},"idempotency_key":{"minLength":1,"type":"string"},"mutations":{"items":{"type":"object"},"minItems":1,"type":"array"},"run_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"tenant_id":{"minLength":1,"type":"string"},"transaction_id":{"minLength":1,"type":"string"}},"required":["schema_revision","transaction_id","tenant_id","run_id","expected_revision","mutations","idempotency_key"],"title":"GraphTransaction","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class GraphTransaction:
    expected_revision: int
    idempotency_key: str
    mutations: list
    run_id: str
    schema_revision: Any
    tenant_id: str
    transaction_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('expected_revision', 'idempotency_key', 'mutations', 'run_id', 'schema_revision', 'tenant_id', 'transaction_id',)})
