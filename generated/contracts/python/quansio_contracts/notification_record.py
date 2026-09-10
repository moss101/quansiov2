"""Canonical contract binding for NotificationRecord.

Generated from schemas/NotificationRecord.schema.json digest b6d5506724a27518e27847fa355aceddc417d8ab81ef2e232ef63007cb209bea by
tools/governance/generate_bindings.py 1.0.0. DO NOT EDIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import jsonschema

SCHEMA_DIGEST = "b6d5506724a27518e27847fa355aceddc417d8ab81ef2e232ef63007cb209bea"
SCHEMA = json.loads("""{"$id":"quansio://schema/NotificationRecord/9.0.0","$schema":"https://json-schema.org/draft/2020-12/schema","additionalProperties":false,"properties":{"approval_request_id":{"type":["string","null"]},"attention_type":{"minLength":1,"type":"string"},"created_at":{"format":"date-time","type":"string"},"deep_link_target":{"minLength":1,"type":"string"},"notification_id":{"minLength":1,"type":"string"},"recipient_id":{"minLength":1,"type":"string"},"schema_revision":{"const":"9.0.0"},"state":{"enum":["PENDING","DELIVERED","ACKNOWLEDGED","EXPIRED","FAILED"]},"tenant_id":{"minLength":1,"type":"string"},"urgency":{"enum":["LOW","NORMAL","HIGH","URGENT"]}},"required":["schema_revision","notification_id","tenant_id","recipient_id","attention_type","deep_link_target","urgency","state","created_at"],"title":"NotificationRecord","type":"object"}""")
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


@dataclass(frozen=True)
class NotificationRecord:
    attention_type: str
    created_at: str
    deep_link_target: str
    notification_id: str
    recipient_id: str
    schema_revision: Any
    state: Any
    tenant_id: str
    urgency: Any
    approval_request_id: str | Any | None = None

    @classmethod
    def validate(cls, payload: dict) -> None:
        errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
        if errors:
            raise ValueError("; ".join(e.message for e in errors))

    @classmethod
    def from_dict(cls, payload: dict) -> Any:
        cls.validate(payload)
        return cls(**{k: payload.get(k) for k in ('approval_request_id', 'attention_type', 'created_at', 'deep_link_target', 'notification_id', 'recipient_id', 'schema_revision', 'state', 'tenant_id', 'urgency',)})
