"""Canonical contract binding for WebhookEnvelope.

Generated from schemas/WebhookEnvelope.schema.json digest 73072d5268ce580486e5695822e9fa458e3a04a2804cdac22ab90ca4a74052d6 by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "73072d5268ce580486e5695822e9fa458e3a04a2804cdac22ab90ca4a74052d6"
SCHEMA = json.loads("""{"$id":"quansio://schema/WebhookEnvelope/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"auth_verification":{"enum":["VERIFIED","REJECTED"]},"body_digest":{"pattern":"^[a-f0-9]{64}$","type":"string"},"connector_id":{"minLength":1,"type":"string"},"delivery_id":{"minLength":1,"type":"string"},"payload":{"type":"object"},"received_at":{"format":"date-time","type":"string"},"schema_revision":{"const":"9.0.0"},"tenant_id":{"minLength":1,"type":"string"},"webhook_id":{"minLength":1,"type":"string"}},"required":["schema_revision","webhook_id","tenant_id","connector_id","delivery_id","received_at","body_digest","auth_verification","payload"],"title":"WebhookEnvelope","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class WebhookEnvelope:
    auth_verification: Any
    body_digest: str
    connector_id: str
    delivery_id: str
    payload: dict
    received_at: str
    schema_revision: Any
    tenant_id: str
    webhook_id: str

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('auth_verification', 'body_digest', 'connector_id', 'delivery_id', 'payload', 'received_at', 'schema_revision', 'tenant_id', 'webhook_id',)})
